from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContainerClient, BlobBlock, BlobClient, StandardBlobTier

from agents.keyvault import get_secret

import os
import io
import uuid


class blob_storage:
    def __init__(self):
        self.blob_secret = get_secret().get_secret_value(secret_name="blob-storage-uri")
        self.credential = DefaultAzureCredential()
        self.blob_service_client = BlobServiceClient(self.blob_secret, credential=self.credential)
        #self.blob_service_client = blob_service_client

    def upload_blob_file(self, container_name: str,file_path: str,file_name: str):
        container_client = self.blob_service_client.get_container_client(container=container_name)
        with open(file=os.path.join(file_path, file_name), mode="rb") as data:
            blob_client = container_client.upload_blob(name=file_name, data=data, overwrite=True)


    def upload_zip_file(self, container_name: str,file_path: str,file_name: str):
        container_client = self.blob_service_client.get_container_client(container=container_name)

        blob_name = "RFx_Brief_Package.zip" # Name for the blob in Azure
        local_file_path = os.path.join(file_path,file_name) # Path to your local zip file

        with open(local_file_path, "rb") as data:
            container_client.upload_blob(name=blob_name, data=data, overwrite=True)
        print(f"Uploaded {local_file_path} to Azure Blob Storage as {blob_name}")

    def writing_docx_file(self, container_name: str, data,blob_name: str):
        container_client = self.blob_service_client.get_container_client(container=container_name)

        #blob_name = "RFx_Brief_Package.docx" # Name for the blob in Azure
        
        container_client.upload_blob(name=blob_name, data=data, overwrite=True)
        #print(f"Uploaded {local_file_path} to Azure Blob Storage as {blob_name}")