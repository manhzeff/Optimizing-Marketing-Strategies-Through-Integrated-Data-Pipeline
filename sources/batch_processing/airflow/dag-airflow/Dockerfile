# First-time build can take up to 4 mins.
FROM apache/airflow:2.4.3

ENV AIRFLOW_HOME=/opt/airflow

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR $AIRFLOW_HOME

ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
USER root
RUN apt update -y
RUN apt install default-jdk -y
RUN apt install git -y
USER airflow
RUN pip install pandas
