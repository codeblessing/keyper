from dataclasses import dataclass
from os import environ as env


@dataclass
class Resource:
    name: str
    url: str


@dataclass
class Credentials:
    name: str
    key: str


@dataclass
class Service:
    url: str
    key: str


@dataclass
class Photos:
    access_key: str
    connection_string: str
    container: Resource
    queue: Resource
    table: Resource


class Config:
    credentials: Credentials
    photos: Photos
    computer_vision: Service

    def __init__(self) -> None:
        # yapf: disable
        self.credentials = Credentials(env["KEYPER_PHOTOS_ACCOUNT_NAME"], env["KEYPER_PHOTOS_ACCOUNT_ACCESS_KEY"])
        self.computer_vision = Service(env["KEYPER_COGNITIVE_URL"], env["KEYPER_COGNITIVE_KEY"])
        self.photos = Photos(
            env["KEYPER_PHOTOS_ACCOUNT_ACCESS_KEY"],
            env["KEYPER_PHOTOS_CONNECTION_STRING"],
            Resource(env["KEYPER_PHOTOS_CONTAINER_NAME"], env["KEYPER_PHOTOS_CONTAINER_URL"]),
            Resource(env["KEYPER_PHOTOS_QUEUE_NAME"], env["KEYPER_PHOTOS_QUEUE_URL"]),
            Resource(env["KEYPER_PHOTOS_TABLE_NAME"], env["KEYPER_PHOTOS_TABLE_URL"])
        )
        # yapf: enable
