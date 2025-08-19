import os
import logging
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from typing import Optional

# Setup logger
logger = logging.getLogger("FunctionsS3Uploader")
logger.setLevel(logging.INFO)

class FunctionsS3Uploader:
    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        bucket_name: str,
        endpoint_url: Optional[str] = None,
        region_name: str = "us-east-1",
        public_url_base: Optional[str] = None  
    ):
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url
        self.public_url_base = public_url_base or f"{endpoint_url}/{bucket_name}/"

        try:
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                endpoint_url=endpoint_url,
                region_name=region_name
            )
            logger.info("S3 client for functions initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client for functions: {e}")
            raise

    def upload_function_file(self, local_file_path: str, s3_key: str) -> Optional[str]:
        try:
            if not os.path.exists(local_file_path):
                logger.error(f"Function file not found locally: {local_file_path}")
                return None

            self.s3_client.upload_file(local_file_path, self.bucket_name, s3_key)
            logger.info(f"Function file uploaded to S3: {s3_key}")
            return self._public_url(s3_key)
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Failed to upload function file '{local_file_path}' to S3: {e}")
            return None

    def upload_function_bytes(self, data: bytes, s3_key: str, content_type: str = "application/octet-stream") -> Optional[str]:
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=data,
                ContentType=content_type
            )
            logger.info(f"Function byte stream uploaded to S3: {s3_key}")
            return self._public_url(s3_key)
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Failed to upload function bytes to S3 key '{s3_key}': {e}")
            return None

    def _public_url(self, s3_key: str) -> str:
        return f"{self.public_url_base.rstrip('/')}/{s3_key}"
