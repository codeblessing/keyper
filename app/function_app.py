import azure.functions as func
import datetime
import json
import logging
import os 
import uuid

from azure.data.tables import TableServiceClient
from azure.storage.blob import BlobServiceClient
from azure.storage.queue import QueueServiceClient

app = func.FunctionApp()

# Configure the Azure Table Storage and Azure Blob Storage
try: 
    PHOTOS_QUEUE_URL = os.environ['ENV_PHOTOS_QUEUE_URL']
    PHOTOS_TABLE_URL = os.environ['ENV_PHOTOS_TABLE_URL']
    PHOTOS_CONTAINER_URL = os.environ['ENV_PHOTOS_CONTAINER_URL']
    PHOTOS_TABLE_NAME = os.environ['ENV_PHOTOS_TABLE_NAME']
    PHOTOS_QUEUE_NAME = os.environ['ENV_PHOTOS_QUEUE_NAME']
    PHOTOS_CONTAINER_NAME = os.environ['ENV_PHOTOS_CONTAINER_NAME']
    PHOTOS_PRIMARY_KEY = os.environ['ENV_PHOTOS_PRIMARY_KEY']
    CREDENTIALS = {
        "account_name": os.environ['ENV_PHOTOS_ACCOUNT_NAME'],
        "account_key": PHOTOS_PRIMARY_KEY
    }
    PHOTOS_CONNSTRING = os.environ['ENV_PHOTOS_CONNSTR']
except KeyError as e:
    logging.error(f"Error: {e}")
    raise e


@app.function_name(name="post")
@app.route(route="post", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def post(req: func.HttpRequest) -> func.HttpResponse:
    """ Post image from body to Azure Blob Storage and create an entry in Azure Table Storage 
    """
    try:
        table_service_client = TableServiceClient.from_connection_string(PHOTOS_CONNSTRING)
        table_client = table_service_client.get_table_client(PHOTOS_TABLE_NAME)
        blob_service_client = BlobServiceClient.from_connection_string(PHOTOS_CONNSTRING)  
    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(
            "Error: Unable to connect to Azure Storage",
            status_code=500
        )

    logging.info('Uploading a photo to Azure Blob Storage and creating an entry in Azure Table Storage')

    if not req.get_body():
        return func.HttpResponse(
            "Please pass an image in the request body",
            status_code=400
        )
    
    if not req.get_body().get_raw():
        return func.HttpResponse(
            "Please pass an image in the request body",
            status_code=400
        )
    
    body = req.get_body().get_raw()
    image_name = str(uuid.uuid4()) + '.png'
    blob_client = blob_service_client.get_blob_client(container=PHOTOS_CONTAINER_NAME, blob=image_name)
    blob_client.upload_blob(body, overwrite=True)
    
    entity = {
        'PartitionKey': image_name,
        'RowKey': str(uuid.uuid4()),
        'Timestamp': datetime.datetime.now(),
        'Url': blob_client.url,
        'State': 'uploaded'
    }
    table_client.upsert_entity(entity=entity)
    
    return func.HttpResponse(
        json.dumps(entity),
        status_code=200
    )

@app.function_name(name="list")
@app.route(route="list", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def list(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )
