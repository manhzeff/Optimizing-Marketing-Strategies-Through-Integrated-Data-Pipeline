from confluent_kafka import avro
from confluent_kafka.avro import AvroProducer
import csv
from time import sleep
import re

def load_avro_schema_from_file():
    key_schema = avro.load("marketing_key.avsc")
    value_schema = avro.load("marketing_value.avsc")

    return key_schema, value_schema


def send_record():
    key_schema, value_schema = load_avro_schema_from_file()

    producer_config = {
        "bootstrap.servers": "localhost:9092",
        "schema.registry.url": "http://localhost:8081",
        "acks": "1"
    }

    producer = AvroProducer(producer_config, default_key_schema=key_schema, default_value_schema=value_schema)

    file = open('data/marketing_campaign_dataset.csv')
    csvreader = csv.reader(file)
    header = next(csvreader)
    for row in csvreader:
        key = {"Campaign_ID": int(row[0])}
        
        value = {
            "Campaign_ID": int(row[0]),
            "Company": str(row[1]),
            "Campaign_Type": str(row[2]),
            "Target_Audience": str(row[3]),
            "Duration": str(row[4]),
            "Channel_Used": str(row[5]),
            "Conversion_Rate": float(row[6]),
            "Acquisition_Cost": float(row[7].replace('$', '').replace(',', '')),
            "ROI": float(row[8]),
            "Location": str(row[9]),
            "Language": str(row[10]),
            "Clicks": int(row[11]),
            "Impressions": int(row[12]),
            "Engagement_Score": int(row[13]),
            "Customer_Segment": str(row[14]),
            "Date": str(row[15])
        }

        try:
            producer.produce(topic='marketing_campaign', key=key, value=value)
        except Exception as e:
            print(f"Exception while producing record value - {value}: {e}")
        else:
            print(f"Successfully producing record value - {value}")

        producer.flush()
        sleep(1)

if __name__ == "__main__":
    send_record()