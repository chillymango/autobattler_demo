"""
Help with transmitting and reconstructing messages over UDP

I'm not sure

UDP message format:
first two bytes: message type
next two bytes: packet number
next two bytes: total number of packets in this message
next 8 bytes: timestamp of message construction
"""
import typing as T
from pydantic import BaseModel
from engine.models.state import State


MESSAGE_TYPES: T.Dict[int, T.Type[BaseModel]] = {
    0: "UpdateItem",
}
