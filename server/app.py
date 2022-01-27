"""
Application Entrypoint
"""
import logging
import uvicorn
from fastapi import FastAPI
from fastapi_websocket_rpc.logger import logging_config, LoggingModes

from server.api import add_routes

logging_config.set_mode(LoggingModes.UVICORN, level=logging.DEBUG)
#logging_config.set_mode(LoggingModes.UVICORN, level=logging.WARNING)
app =  FastAPI()

# add other APIs
add_routes(app)


if __name__ == "__main__":
    print('Starting Server')
    uvicorn.run(app, host="0.0.0.0", port=8000)
