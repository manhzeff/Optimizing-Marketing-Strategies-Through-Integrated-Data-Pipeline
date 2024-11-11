#!/bin/bash
fileid="17CV9DsFtuPHlZOy6O8DvebkfdNYQHlA_"
filename="marketing_campaign_dataset.csv"
html=`curl -c ./cookie -s -L "https://drive.google.com/uc?export=download&id=${fileid}"`
curl -Lb ./cookie "https://drive.google.com/uc?export=download&`echo ${html}|grep -Po '(confirm=[a-zA-Z0-9\-_]+)'`&id=${fileid}" -o "/opt/airflow/${filename}"