import os
import time
import logging

from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.utils.trigger_rule import TriggerRule
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator

import boto3
import pyarrow.csv as pv
import pyarrow.parquet as pq

from airflow.providers.amazon.aws.operators.emr import EmrAddStepsOperator
from airflow.providers.amazon.aws.operators.emr import EmrTerminateJobFlowOperator




# ------------------------------------------------
# 1. AWS S3 và EMR Serverless Configuration
# ------------------------------------------------
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.environ.get("AWS_REGION") or "ap-southeast-2"  # Hoặc region khác

S3_BUCKET = os.environ.get("AWS_S3_BUCKET")
 

dataset_file = "marketing_campaign_dataset.csv"
dataset_url = "https://drive.google.com/uc?export=download&id=1osgD5kTc7p6wNbe9yL0biuYT9KUqQxJ3"
path_to_local_home = "/opt/airflow"
parquet_file = dataset_file.replace('.csv', '.parquet')

# Đường dẫn PySpark trên S3 (bạn cần tải pyspark_clean.py lên S3)
PYSPARK_S3_PATH = f"s3://zeffmarketingbucket/jobs/pyspark_clean.py"

# Cluster ID đã tồn tại
EXISTING_CLUSTER_ID = "j-3L9HEZV9ZESEU"

# ------------------------------------------------
# 2. Định nghĩa các hàm xử lý CSV -> Parquet -> S3
# ------------------------------------------------
def format_to_parquet(src_file):
    if not src_file.endswith('.csv'):
        logging.error("Can only accept source files in CSV format, for the moment")
        return
    table = pv.read_csv(src_file)
    return pq.write_table(table, src_file.replace('.csv', '.parquet'))

def upload_to_s3(bucket, key, local_file):
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    s3_client.upload_file(local_file, bucket, key)

# ------------------------------------------------
# 3. Hàm gọi EMR Serverless (thay thế EmrAddStepsOperator)


# ------------------------------------------------

SPARK_STEPS = [
    {
        "Name": "Run PySpark Clean Script",
        "ActionOnFailure": "CANCEL_AND_WAIT",
        "HadoopJarStep": {
            "Jar": "command-runner.jar",
            "Args": [
                "spark-submit",
                "--deploy-mode", "cluster",
                "--master", "yarn",
                # Nếu cần thêm jar/whl:
                "--jars", "s3://zeffmarketingbucket/libs/spark-snowflake_2.12-2.12.0-spark_3.4.jar,s3://zeffmarketingbucket/libs/snowflake-jdbc-3.19.0.jar",
                # "--py-files", "s3://<bucket>/libs/some-whl.whl",
                PYSPARK_S3_PATH
            ]
        },
    }
]

# ------------------------------------------------
# 4. Cấu hình DAG
# ------------------------------------------------
default_args = {
    "owner": "airflow",
    "start_date": days_ago(1),
    "depends_on_past": False,
    "retries": 1,
}

with DAG(
    dag_id="data_ingestion_aws_project_emr_serverless",
    schedule_interval="@weekly",
    default_args=default_args,
    catchup=False,
    max_active_runs=1,
    tags=['marketing-campaign'],
) as dag:

    # Task 1: Tải file CSV từ Google Drive
    download_dataset_task = BashOperator(
        task_id="download_dataset_task",
        bash_command="gdrive_connect.sh"
    )

    # Task 2: Chuyển CSV -> Parquet
    format_to_parquet_task = PythonOperator(
        task_id="format_to_parquet_task",
        python_callable=format_to_parquet,
        op_kwargs={
            "src_file": f"{path_to_local_home}/{dataset_file}",
        },
    )

    # Task 3: Upload Parquet lên S3
    local_to_s3_task = PythonOperator(
        task_id="local_to_s3_task",
        python_callable=upload_to_s3,
        op_kwargs={
            "bucket": S3_BUCKET,
            "key": f"raw/{parquet_file}",
            "local_file": f"{path_to_local_home}/{parquet_file}",
        },
    )

    # Task 4: Làm mới bảng dữ liệu Snowflake
    load_data_to_snowflake = SnowflakeOperator(
        snowflake_conn_id = 'snowflake_connection',
        sql = """
            ALTER EXTERNAL TABLE EXTERNAL_CAMPAIGN_DATA REFRESH
        """,
        task_id = 'SnowFlake_Refresh',
        trigger_rule = TriggerRule.NONE_FAILED
    )



    # Task 5: Add Spark Steps để chạy pyspark_clean.py
    add_emr_steps = EmrAddStepsOperator(
        task_id="add_emr_steps",
        job_flow_id=EXISTING_CLUSTER_ID,
        aws_conn_id="emr_spark_default",
        steps=SPARK_STEPS,
    )

    # Task 6: Chờ các step chạy xong
    # Step này sẽ poll trạng thái step EMR
    # steps[0] => index=0 -> step_id="{{ ti.xcom_pull(task_ids='add_emr_steps', key='return_value')[0] }}"
    step_checker = BashOperator(
        task_id="watch_step_status",
        bash_command="""
        echo "Đợi step_id={{ ti.xcom_pull(task_ids='add_emr_steps')[0] }} chạy xong..."
        """,
        # Hoặc có thể dùng EmrStepSensor.  
        # Ở đây demo command-line:
    )

    # Task 7: Terminate EMR cluster (để tiết kiệm chi phí)
    terminate_emr_cluster = EmrTerminateJobFlowOperator(
        task_id="terminate_emr_cluster",
        job_flow_id=EXISTING_CLUSTER_ID,
        aws_conn_id="emr_spark_default",
        trigger_rule=TriggerRule.ALL_DONE  # Luôn chạy, kể cả step fail
    )

    # ------------------------------------------------
    # 5. Luồng DAG
    # ------------------------------------------------
    download_dataset_task >> format_to_parquet_task >> local_to_s3_task >> load_data_to_snowflake >> add_emr_steps >> step_checker >> terminate_emr_cluster
