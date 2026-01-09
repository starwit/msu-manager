from pydantic import BaseModel

class Position(BaseModel):
    lat: float
    lon: float
    fix: bool