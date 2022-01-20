from uuid import UUID

from pydantic import BaseModel
from pydantic import Field
from utils.strings import uuid_as_str


class Entity(BaseModel):
    """
    Unique object (carries an ID)
    """

    id: str = Field(default_factory=uuid_as_str)

    def __hash__(self):
        return hash(UUID(self.id))
