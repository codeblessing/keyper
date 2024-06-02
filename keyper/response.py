import json as JSON

from dataclasses import dataclass

from azure.functions import HttpResponse


@dataclass
class Error:
    status: str
    reason: str

    def __dict__(self) -> dict[str, str]:
        return {
            "status": self.status,
            "reason": self.reason
        }

    def json(self) -> str:
        return JSON.dumps(self.__dict__())


@dataclass
class AzureStorageAccessError:
    message: str

    def http(self):
        return HttpResponse(
            headers = {
                "Content-Type": "application/json"
            },
            status_code = 500,
            body = Error("error", self.message).json(),
        )


@dataclass
class InvalidRequestError:
    message: str

    def http(self):
        return HttpResponse(
            headers = {
                "Content-Type": "application/json"
            },
            status_code = 400,
            body = Error("error", self.message).json(),
        )


@dataclass
class UnsupportedMediaError:
    message: str

    def http(self):
        return HttpResponse(
            headers = {
                "Content-Type": "application/json"
            },
            status_code = 415,
            body = Error("error", self.message).json(),
        )


@dataclass
class EntityNotFoundError:
    message: str

    def http(self):
        return HttpResponse(
            headers = {
                "Content-Type": "application/json"
            },
            status_code = 404,
            body = Error("error", self.message).json(),
        )


@dataclass
class Entity:
    id: str
    url: str
    status: str
    results: list

    def __dict__(self) -> dict[str, str]:
        return {
            "id": self.id,
            "url": self.url,
            "status": self.status,
            "results": self.results
        }

    def json(self) -> str:
        return JSON.dumps(self.__dict__())
