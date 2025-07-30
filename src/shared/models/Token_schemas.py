import datetime

from pydantic import BaseModel, ConfigDict


class TokenModel(BaseModel):
    id: str
    token:  str
    exp: datetime.datetime

    model_config = ConfigDict(from_attributes=True)