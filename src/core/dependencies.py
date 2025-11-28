import httpx
from fastapi import Request
from src.db.postgresql import get_db as get_database


def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http


def get_db():
    yield from get_database()
