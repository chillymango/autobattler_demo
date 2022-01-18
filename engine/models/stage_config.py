from pydantic import BaseModel


class StageConfig(BaseModel):
    stage: int
    round: int
    location: str = ""
