"""
Downloads Southern Company's energy demand from API(EIA) and stores it in a Google BigQuery table.
This is scheduled to runs onces per day from GitHub Actions. 
"""

import pandas as pd
import requests 
from google.cloud import bigquery

import os
import time
from datetime import datetime, timedelta, timezone

#environment variables 
EIA_API_KEY = os.getenv("EIA_API_KEY")
GCLOUD_PROJECT = os.getenv("GCLOUD_PROJECT")
RAW_DATASET = "raw_energy"
RAW_TABLE = "eia_demand_raw"
FULL_TABLE_NAME = f"{GCLOUD_PROJECT}.{RAW_DATASET}.{RAW_TABLE}"
BALANCING_AUTH = "SOCO"
DATA_TYPES = ["D", "DF"]
BASE_URL = "https://api.eia.gov/v2/electricity/rto/region-data/data/"

PAGE_SIZE = 5000
HISTORY_DAYS = 365
OVERLAP_DAYS = 2

#Start Date

def get_newest_day(client):
    first_start = datetime.now(timezone.utc) - timedelta(days=HISTORY_DAYS)

    query = f"SELECT MAX(period) AS newest FROM `{FULL_TABLE_NAME}`"

    try:
        results = list(client.query(query).result())
    except Exception as error:
        print("Table was not able to be read but typical of the first run.")        
        print(f"Details: {error}")
        return first_start.strftime("%Y-%m-%dT%H")

    newest_hour = results[0].newest

    if newest_hour is None:
        return first_start.strftime("%Y-%m-%dT%H")

    start = newest_hour - timedelta(days=OVERLAP_DAYS)
    return start.strftime("%Y-%m-%dT%H")

#Getting the data from the API

def api_request(start_date, end_date, skip_rows):

    settings = [
        ("api_key", EIA_API_KEY),
        ("frequency", "hourly"),
        ("data[0]", "value"),
        ("facets[respondent][]", BALANCING_AUTH),
        ("start", start_date),
        ("end", end_date),
        ("sort[0][column]", "period"),
        ("sort[0][direction]", "asc"),
        ("offset", skip_rows),
        ("length", PAGE_SIZE)
    ]

    for data_type in DATA_TYPES:
        settings.append(("facets[type][]", data_type))

    wait_seconds = 1

    for attempt in range(5):
        try:
            response = requests.get(BASE_URL, params=settings, timeout=60)
            if response.status_code == 200:
                return response.json()["response"]
            print(f"Request failed with code {response.status_code}.")
        except requests.exceptions.RequestException as error:
            print(f"Request failed: {error}")

        print(f"Waiting {wait_seconds} seconds before trying again.")
        time.sleep(wait_seconds)
        wait_seconds = wait_seconds * 2

    raise Exception("EIA API kept failing after 5 attempts.")


def get_all_rows(start_date, end_date):

    first_page = api_request(start_date, end_date, 0)

    all_rows = first_page["data"]
    total_rows = int(first_page["total"])

    print(f"EIA has {total_rows} rows from {start_date} to {end_date}")

    skip_rows = PAGE_SIZE
    while skip_rows < total_rows:
        next_page = api_request(start_date, end_date, skip_rows)
        all_rows = all_rows + next_page["data"]
        print(f" download {len(all_rows)} of {total_rows}")
        skip_rows = skip_rows + PAGE_SIZE

    return all_rows


#Cleaning up the data

def clean_rows(all_rows):

    df = pd.DataFrame(all_rows)

    if len(df) == 0:
        return df

    df = df.rename(columns={
        "respondent-name": "respondent_name",
        "type": "type_code",
        "type-name": "type_name"
    })

    df["period"] = pd.to_datetime(df["period"], utc=True)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["ingested_at"] = pd.Timestamp.now(tz="UTC")

    columns_wanted = [

        "period",
        "respondent",
        "respondent_name",
        "type_code",
        "type_name",
        "value",
        "ingested_at"

    ]

    return df[columns_wanted]

#Push to Google BigQuery

def add_to_bigquery(client, df):

    table_schema = [
        bigquery.SchemaField("period", "TIMESTAMP"),
        bigquery.SchemaField("respondent", "STRING"),
        bigquery.SchemaField("respondent_name", "STRING"),
        bigquery.SchemaField("type_code", "STRING"),
        bigquery.SchemaField("type_name", "STRING"),
        bigquery.SchemaField("value", "FLOAT"),
        bigquery.SchemaField("ingested_at", "TIMESTAMP")
    ]

    job_settings = bigquery.LoadJobConfig(
        schema= table_schema,
        write_disposition= "WRITE_APPEND",
        time_partitioning= bigquery.TimePartitioning(field="period")
    )

    upload_job = client.load_table_from_dataframe(df, FULL_TABLE_NAME, job_config=job_settings)
    upload_job.result()

    print(f"{len(df)} rows were added to {FULL_TABLE_NAME}")



def main():
    client = bigquery.Client(project=GCLOUD_PROJECT)

    start_date = get_newest_day(client)
    end_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H")

    all_rows = get_all_rows(start_date, end_date)
    df = clean_rows(all_rows)

    if len(df) == 0:
        print("No new data")
        return

    add_to_bigquery(client, df)


if __name__ == "__main__":
    main()