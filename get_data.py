import snowflake.connector
import pandas as pd
import os

# Hàm kết nối Snowflake và lấy dữ liệu
def get_data_from_snowflake(
    user, 
    password, 
    account, 
    warehouse, 
    database, 
    schema
):
    """
    Kết nối Snowflake và thực hiện truy vấn dữ liệu.
    Trả về một DataFrame.
    """
    # Kết nối
    conn = snowflake.connector.connect(
        user=user,
        password=password,
        account=account,
        warehouse=warehouse,
        database=database,
        schema=schema
    )

    # Ví dụ query, thay đổi tùy vào bảng / cột thực tế
    query = """
    SELECT 
        CAMPAIGN_ID,
        COMPANY,
        CAMPAIGN_TYPE,
        TARGET_AUDIENCE,
        DURATION,
        CHANNEL_USED,
        CONVERSION_RATE,
        ACQUISITION_COST,
        ROI,
        LOCATION,
        LANGUAGE,
        CLICKS,
        IMPRESSIONS,
        ENGAGEMENT_SCORE,
        CUSTOMER_SEGMENT,
        DATE
    FROM CAMPAIN_DATA_TEST
    """

    # Thực hiện truy vấn
    df = pd.read_sql(query, conn)

    # Đóng kết nối
    conn.close()

    return df

def main():
    """
    Đọc thông số kết nối Snowflake từ biến môi trường (env).
    Nếu chưa thiết lập biến môi trường, có thể dùng giá trị mặc định (YOUR_USER, YOUR_PASSWORD, ...)
    """
    SNOWFLAKE_USER = os.environ.get("SNOWFLAKE_USER")
    SNOWFLAKE_PASSWORD = os.environ.get("SNOWFLAKE_PASSWORD")
    SNOWFLAKE_ACCOUNT = os.environ.get("SNOWFLAKE_ACCOUNT")
    SNOWFLAKE_WAREHOUSE = os.environ.get("SNOWFLAKE_WAREHOUSE")
    SNOWFLAKE_DATABASE = os.environ.get("SNOWFLAKE_DATABASE")
    SNOWFLAKE_SCHEMA = os.environ.get("SNOWFLAKE_SCHEMA")

    # Gọi hàm kết nối và lấy data
    df = get_data_from_snowflake(
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        account=SNOWFLAKE_ACCOUNT,
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA
    )

    # Lưu file CSV để phục vụ train
    df.to_csv("marketing_dataset.csv", index=False)
    print("Data is saved to marketing_dataset.csv")

if __name__ == "__main__":
    main()
