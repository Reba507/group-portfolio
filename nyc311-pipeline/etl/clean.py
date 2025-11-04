# etl/clean.py
import pandas as pd
import boto3
from dotenv import load_dotenv
import os
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

S3_BUCKET = os.getenv("S3_BUCKET", "your-team-311-bucket")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

def extract_and_clean():
    logger.info("Extracting raw CSV...")
    df = pd.read_csv("data/raw/nyc311.csv", nrows=2500)

    logger.info(f"Starting with {len(df)} rows")
    df = df[['Unique Key', 'Created Date', 'Complaint Type', 'Agency', 'Borough', 'Incident Zip']].copy()
    df.columns = ['unique_key', 'created_date', 'complaint_type', 'agency', 'borough', 'incident_zip']

    df['created_date'] = pd.to_datetime(df['created_date'], errors='coerce')
    df = df.dropna(subset=['unique_key', 'created_date'])
    df['borough'] = df['borough'].str.title()
    df['complaint_type'] = df['complaint_type'].str.strip()

    before = len(df)
    df = df.drop_duplicates(subset=['unique_key'])
    logger.info(f"Removed {before - len(df)} duplicates")

    df.to_parquet("results/fact_311_clean.parquet", index=False)
    logger.info(f"Cleaned: {len(df)} rows → results/fact_311_clean.parquet")

    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        try:
            s3 = boto3.client('s3',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY
            )
            s3.upload_file(
                "results/fact_311_clean.parquet",
                S3_BUCKET,
                "processed/fact_311_clean.parquet"
            )
            logger.info(f"Uploaded to s3://{S3_BUCKET}/processed/fact_311_clean.parquet")
        except Exception as e:
            logger.warning(f"S3 upload failed: {e}")
    else:
        logger.warning("No AWS creds → S3 upload skipped. Ask Person 1.")

    return df

if __name__ == "__main__":
    extract_and_clean()