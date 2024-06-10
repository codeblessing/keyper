import datetime
import json
import logging
import uuid
import requests

from azure.functions import AuthLevel, FunctionApp, HttpRequest, HttpResponse, QueueMessage
from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas
from azure.storage.queue import QueueServiceClient, BinaryBase64DecodePolicy, BinaryBase64EncodePolicy
from azure.data.tables import TableServiceClient
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential

from config import Config
from response import AzureStorageAccessError, EntityNotFoundError, Error, Entity, InvalidRequestError, UnsupportedMediaError

app = FunctionApp(http_auth_level = AuthLevel.ANONYMOUS)

try:
    config = Config()
    table_service_client = TableServiceClient.from_connection_string(config.photos.connection_string)
    queue_service_client = QueueServiceClient.from_connection_string(config.photos.connection_string)
    blob_service_client = BlobServiceClient.from_connection_string(config.photos.connection_string)
except Exception as error:
    logging.error(f"Cannot retrieve configuration. Error: {error}")
    raise error


def generate_sas_token(image_name: str):
    blob_service_client = BlobServiceClient.from_connection_string(config.photos.connection_string)
    blob_client = blob_service_client.get_blob_client(container = config.photos.container.name, blob = image_name)
    token = generate_blob_sas(
        account_name = blob_client.account_name,
        container_name = blob_client.container_name,
        blob_name = blob_client.blob_name,
        account_key = config.photos.access_key,
        permission = BlobSasPermissions(read = True),
        expiry = datetime.datetime.now() + datetime.timedelta(hours = 1),
    )
    return f"{blob_client.url}?{token}"


@app.function_name("postentities")
@app.route(route = "entities", trigger_arg_name = 'request', methods = ["POST"])
def post(request: HttpRequest) -> HttpResponse:
    try:
        table_service_client.create_table_if_not_exists(config.photos.table.name)

        try:
            queue_service_client.list_queues(config.photos.queue.name).__next__()
        except StopIteration:
            queue_service_client.create_queue(config.photos.queue.name)

        try:
            blob_service_client.list_containers(config.photos.container.name).__next__()
        except StopIteration:
            blob_service_client.create_container(config.photos.container.name)
    except Exception as error:
        logging.error(f"@post | Error: {error}")
        return AzureStorageAccessError("Unable to connect to Azure Storage").http()

    logging.info("@post | Uploading a photo to Azure Blob Storage and creating an entry in Azure Table Storage")
    if not request.files:
        return InvalidRequestError("No image was attached. Attach an image to request.").http()

    try:
        file = request.files.values().__next__()
        if file.content_type not in ['image/png', 'image/jpeg']:
            return UnsupportedMediaError("Invalid file was attached. Only PNG and JPEG images are accepted").http()
        body = file.stream.read()
    except Exception as error:
        logging.error(f"@post | Error: {error}")
        return InvalidRequestError("Unable to read the image from the request body").http()

    hash_id = str(uuid.uuid4())
    image_name = f"{hash_id}.png"

    try:
        blob_client = blob_service_client.get_blob_client(container = config.photos.container.name, blob = image_name)
        blob_client.upload_blob(body, overwrite = True)
    except Exception as error:
        logging.error(f"Error: {error.args}")
        return AzureStorageAccessError("Unable to upload image to Azure Blob Storage").http()

    entity = {
        "PartitionKey": hash_id,
        "RowKey": hash_id,
        "id": hash_id,
        "status": "uploaded",
        "results": "[]"
    }

    try:
        table_client = table_service_client.get_table_client(config.photos.table.name)
        table_client.upsert_entity(entity = entity)
    except Exception as error:
        logging.error(f"Error: {error}")
        return AzureStorageAccessError("Unable to create an entry in Azure Table Storage").http()

    try:
        queue_client = queue_service_client.get_queue_client(
            config.photos.queue.name,
            message_encode_policy = BinaryBase64EncodePolicy(),
            message_decode_policy = BinaryBase64DecodePolicy(),
        )
        queue_client.send_message(hash_id.encode("UTF-8"))
    except Exception as error:
        logging.error(f"Error: {error}")
        return AzureStorageAccessError("Unable to add a message to the Azure Queue").http()

    return HttpResponse(
        Entity(entity["id"], generate_sas_token(f"{hash_id}.png"), entity["status"], []).json(),
        status_code = 200,
        headers = {
            "Content-Type": "application/json"
        },
    )


@app.function_name("processentities")
@app.queue_trigger(
    queue_name = config.photos.queue.name,
    connection = "KEYPER_PHOTOS_CONNECTION_STRING",
    arg_name = "message",
)
def process(message: QueueMessage) -> None:
    hash_id = message.get_body().decode("UTF-8")

    try:
        table_client = table_service_client.get_table_client(config.photos.table.name)
        credentials = AzureKeyCredential(config.computer_vision.key)
        image_analizer = ImageAnalysisClient(config.computer_vision.url, credentials)
    except Exception as e:
        logging.error(f"Error: {e}")
        raise e

    entity = None
    try:
        entity = table_client.get_entity(partition_key = hash_id, row_key = hash_id)
    except Exception as e:
        logging.error(f"Error: {e}")
        raise e

    if entity is None:
        return

    try:
        sas_token = generate_sas_token(f"{hash_id}.png")
        image = requests.get(sas_token)
        pass
    except Exception as e:
        logging.error(f"Error: {e}")
        raise e

    try:
        analysis = image_analizer.analyze(
            image.content, [VisualFeatures.DENSE_CAPTIONS, VisualFeatures.TAGS, VisualFeatures.OBJECTS]
        )
        # yapf: enable
        objects = []
        for object in analysis.objects.list:
            if [tag in object.tags for tag in ['key', 'keys']]:
                rect = object.bounding_box
                objects.append({
                    "x": rect.x,
                    "y": rect.y,
                    "w": rect.width,
                    "h": rect.height,
                    "label": "keys",
                    "confidence": 0
                })

        for tag in analysis.tags.list:
            if tag.name in ['key', 'keys']:
                objects.append({
                    "x": -10,
                    "y": -10,
                    "w": -10,
                    "h": -10,
                    "label": tag.name,
                    "confidence": tag.confidence
                })

        for caption in analysis.dense_captions.list:
            if "key" in caption.text:
                objects.append(
                    {
                        "x": caption.bounding_box.x,
                        "y": caption.bounding_box.y,
                        "w": caption.bounding_box.width,
                        "h": caption.bounding_box.height,
                        "label": caption.text,
                        "confidence": caption.confidence
                    }
                )

        logging.info(objects)

        entity["status"] = "processed"
        entity["results"] = json.dumps(objects)

    except Exception as e:
        logging.error(f"Error: {e}")
        raise e

    try:
        table_client.upsert_entity(entity = entity)
    except Exception as e:
        logging.error(f"Error: {e}")
        raise e

    return None


@app.function_name(name = "getentity")
@app.route(route = "entities/{id}", methods = ["GET"], trigger_arg_name = "request")
def get_entity(request: HttpRequest) -> HttpResponse:
    try:
        table_client = table_service_client.get_table_client(config.photos.table.name)
    except Exception as e:
        logging.error(f"Error: {e}")
        return AzureStorageAccessError("Error: Unable to connect to Azure Storage").http()

    id = request.route_params.get("id")
    if id is None:
        return EntityNotFoundError("No entity with such id exists.").http()

    try:
        entities = [entity for entity in table_client.list_entities() if entity["PartitionKey"] == id]
        if len(entities) > 0:
            entry = entities[0]

            entity = Entity(
                id = entry["PartitionKey"],
                url = generate_sas_token(f"{entry['PartitionKey']}.png"),
                status = entry["status"],
                results = json.loads(entry["results"])
            )
        else:
            entity = None
    except Exception as e:
        logging.error(f"Error: {e}")
        return AzureStorageAccessError("Unable to read entities from Azure Table Storage").http()
    return HttpResponse(
        entity.json(),
        status_code = 200,
        headers = {
            "Content-Type": "application/json"
        },
    )

    # @app.function_name(name = "debug-upload-image")
    # @app.route(route = "debug/entities/", methods = ["POST"], trigger_arg_name = "request")
    # def debug_upload_image(request: HttpRequest):
    #     hash_id = str(uuid.uuid4())

    #     entity = {
    #         "id": hash_id,
    #         "status": "uploaded",
    #         "results": None
    #     }

    #     return HttpResponse(json.dumps(entity), status_code = 201, headers = {
    #         "Content-Type": "application/json"
    #     })

    # @app.function_name(name = "debug-get-entity")
    # @app.route(route = "debug/entities/{id}", methods = ["GET"], trigger_arg_name = "request")
    # def debug_get_entity(request: HttpRequest) -> HttpResponse:
    id = request.route_params.get("id")
    if id is None:
        return HttpResponse(
            status_code = 404, body = Error(status = "Invalid request", reason = "No entity with such id exists.")
        )

    entity = Entity(
        id = id,
        url = "",
        status = "processed",
        results = [
            {
                "x": 0,
                "y": 0,
                "w": 4608,
                "h": 2592,
                "label": "a desk with keys and a computer mouse",
                "confidence": 0.5727425813674927
            }, {
                "x": 532,
                "y": 97,
                "w": 3609,
                "h": 2485,
                "label": "a desk with keys and a cord",
                "confidence": 0.5829769968986511
            }, {
                "x": 1815,
                "y": 1360,
                "w": 674,
                "h": 645,
                "label": "a set of keys on a wood surface",
                "confidence": 0.8344246745109558
            }
        ]
    )

    return HttpResponse(
        entity.json(),
        status_code = 200,
        headers = {
            "Content-Type": "application/json"
        },
    )
