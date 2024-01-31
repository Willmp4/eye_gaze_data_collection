import boto3
from botocore.exceptions import ClientError
import os
import numpy as np
import json
class DataHandler:
    def __init__(self, bucket_name, local_base_dir):
        self.s3_client = boto3.client('s3')
        self.bucket_name = bucket_name
        self.local_base_dir = local_base_dir

    def get_camera_info(self, camera_info):
        camera_matrix = np.array(camera_info[0], dtype='double')
        dist_coeffs = np.array(camera_info[1], dtype='double')
        return camera_matrix, dist_coeffs
        
    def get_metadata(self, bucket_name, metadata_file_key, s3_client):
        try:
            metadata_object = s3_client.get_object(Bucket=bucket_name, Key=metadata_file_key)
            metadata_content = metadata_object['Body'].read().decode('utf-8')
            metadata = json.loads(metadata_content)
            return metadata
        except Exception as e:
            print(f"Error retrieving metadata from S3: {e}")
            return None
        
    def get_image_paths(self, bucket_name, key_prefix, subdirectory, s3_client):
        paginator = s3_client.get_paginator('list_objects_v2')
        image_paths = []

        # List objects within a specific subdirectory
        for page in paginator.paginate(Bucket=bucket_name, Prefix=f"{key_prefix}{subdirectory}"):
            for obj in page.get('Contents', []):
                # Skip directories
                if obj['Key'].endswith('/'):
                    continue
                image_paths.append(obj['Key'])

        return image_paths

    def download_data(self, key_prefix, local_base_dir, s3_client, bucket_name):
        paginator = s3_client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket_name, Prefix=key_prefix):
            print(f"Downloading data from {key_prefix}")
            for obj in page.get('Contents', []):
                s3_object_key = obj['Key']
                if s3_object_key.endswith('/'):
                    continue
                local_file_path = os.path.join(local_base_dir, s3_object_key)
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

                try:
                    local_file_info = os.stat(local_file_path)
                    s3_object_info = s3_client.head_object(Bucket=bucket_name, Key=s3_object_key)
                    if local_file_info.st_size == s3_object_info['ContentLength']:
                        continue
                except (FileNotFoundError, ClientError):
                    pass

                s3_client.download_file(bucket_name, s3_object_key, local_file_path)

    def get_all_metadata_keys(self, bucket_name, s3_client):
        metadata_keys = []
        paginator = s3_client.get_paginator('list_objects_v2')
        print(f"Looking for metadata files in bucket {bucket_name}")
        for page in paginator.paginate(Bucket=bucket_name, Prefix='data/'):
            for content in page.get('Contents', []):
                key = content['Key']
                if key.endswith('metadata.json'):
                    metadata_keys.append(key)
        print(f"Found {len(metadata_keys)} metadata files")
        return metadata_keys

    def process_s3_bucket_data(self, bucket_name, local_base_dir, process_data_if_needed, data_handler, image_processor, csv_manager):
        s3_client = boto3.client('s3')
        
        # First, get a list of all metadata files
        metadata_keys = self.get_all_metadata_keys(bucket_name, s3_client)
        
        # Now process each metadata and its associated directory
        for metadata_key in metadata_keys:
            subdir_prefix = '/'.join(metadata_key.split('/')[:-1]) + '/'
            print(f"Processing data in {subdir_prefix}")
            self.download_data(subdir_prefix, local_base_dir, s3_client, bucket_name)
            process_data_if_needed(subdir_prefix, local_base_dir, s3_client, bucket_name, data_handler, image_processor, csv_manager)