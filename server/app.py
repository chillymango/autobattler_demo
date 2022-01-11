"""
Application Entrypoint
"""
import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.routing import APIRouter
from fastapi_websocket_pubsub import PubSubEndpoint
from pydantic import BaseModel

from api import add_routes

app =  FastAPI()
router = APIRouter()

# add pubsub endpoint
endpoint = PubSubEndpoint()
endpoint.register_route(router)
app.include_router(router)

# add other APIs
add_routes(app)


async def broadcast_state():
    """
    Take the state object from the environment and broadcast it.
    """
    print("lol i broadcast")
    await endpoint.publish(["state"], data={"lol": "Srs"})


class CreateGameRequest(BaseModel):
    name: str
    players: int = 8


class StartGameRequest(BaseModel):
    game_id: str


@app.get("/trigger")
async def trigger_events():
    while True:
        asyncio.create_task(broadcast_state())
        await asyncio.sleep(1.0)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
