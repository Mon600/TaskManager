import datetime
from types import NoneType

from babel.dates import format_datetime
from pydantic import BaseModel, ConfigDict, field_validator

from src.shared.models.Project_schemas import ProjectRel



class CreatorSchema(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)

class GetLinksSchema(BaseModel):
    link: str
    creator_rel: CreatorSchema
    end_at: str
    
    @field_validator('end_at', mode='before')
    def end_at_validate(cls, value):
        if value is None:
            return "Бессрочна"
        formatted_date = format_datetime(value, format='d MMMM, Y HH:mm', locale='ru')
        return formatted_date

    @field_validator('link', mode='before')
    def link_validate(cls, value):
        return f'http://127.0.0.1/project/invite/{value}'

    model_config = ConfigDict(from_attributes=True)


class LinkSchema(BaseModel):
    ex: int

class GetLinkSchema(BaseModel):
    end_at: str | None
    project_rel: ProjectRel

    model_config = ConfigDict(from_attributes=True)

    @field_validator('end_at', mode='before')
    def validate(cls, value: datetime.datetime | None):
        if isinstance(value, NoneType):
            return "Бессрочна"
        elif isinstance(value, str):
            return value.title()
        formatted_date = format_datetime(value, format='d MMMM, Y HH:mm', locale='ru')
        return formatted_date