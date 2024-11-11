import os
import logging

from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
# from airflow.providers.amazon.aws.operators.redshift_sql import RedshiftSQLOperator

import boto3
import pyarrow.csv as pv
import pyarrow.parquet as pq

# AWS S3 and Redshift configuration
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
S3_BUCKET = os.environ.get("AWS_S3_BUCKET")
S3_KEY = "bank_marketing_dataset"
dataset_file = "marketing_campaign_dataset.csv"
dataset_url = "https://drive.google.com/uc?export=download&id=17CV9DsFtuPHlZOy6O8DvebkfdNYQHlA_"
path_to_local_home = "/opt/airflow"
parquet_file = dataset_file.replace('.csv', '.parquet')
# REDSHIFT_SCHEMA = os.environ.get("REDSHIFT_SCHEMA", 'public')
# REDSHIFT_TABLE = os.environ.get("REDSHIFT_TABLE", 'bank_marketing')

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

default_args = {
    "owner": "airflow",
    "start_date": days_ago(1),
    "depends_on_past": False,
    "retries": 1,
}

with DAG(
    dag_id="data_ingestion_aws_project",
    schedule_interval="@weekly",
    default_args=default_args,
    catchup=False,
    max_active_runs=1,
    tags=['bank-marketing'],
) as dag:

    download_dataset_task = BashOperator(
        task_id="download_dataset_task",
        bash_command="gdrive_connect.sh"
    )

    format_to_parquet_task = PythonOperator(
        task_id="format_to_parquet_task",
        python_callable=format_to_parquet,
        op_kwargs={
            "src_file": f"{path_to_local_home}/{dataset_file}",
        },
    )

    local_to_s3_task = PythonOperator(
        task_id="local_to_s3_task",
        python_callable=upload_to_s3,
        op_kwargs={
            "bucket": S3_BUCKET,
            "key": f"raw/{parquet_file}",
            "local_file": f"{path_to_local_home}/{parquet_file}",
        },
    )

    # create_redshift_external_table_task = RedshiftSQLOperator(
    #     task_id="create_redshift_external_table_task",
    #     sql=f"""
    #         CREATE EXTERNAL TABLE {REDSHIFT_SCHEMA}.{REDSHIFT_TABLE} (
    #             campaign_id INT,
    #             company STRING,
    #             campaign_type STRING,
    #             target_audience STRING,
    #             duration STRING,
    #             channel_used STRING,
    #             conversion_rate FLOAT,
    #             acquisition_cost STRING,
    #             roi FLOAT,
    #             location STRING,
    #             language STRING,
    #             clicks INT,
    #             impressions INT,
    #             engagement_score INT,
    #             customer_segment STRING,
    #             date DATE
    #         )
    #         ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
    #         STORED AS PARQUET
    #         LOCATION 's3://{S3_BUCKET}/raw/'
    #         TABLE PROPERTIES ('parquet.compression'='SNAPPY');
    #     """,
    #     redshift_conn_id="your_redshift_connection"
    # )

    download_dataset_task >> format_to_parquet_task >> local_to_s3_task 
    
    # >> create_redshift_external_table_task
