import datetime
from types import NoneType

from babel.dates import format_datetime
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy.ext.indexable import index_property

from src.shared.schemas.Project_schemas import ProjectRel



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
        return f'http://127.0.0.1/links/invite/{value}'

    model_config = ConfigDict(from_attributes=True)


class LinkSchema(BaseModel):
    ex: int


class LinkSchemaExtend(BaseModel):
    end_at: datetime.datetime | None
    created_at: datetime.datetime
    project_id: int
    creator_id: int
    link: str

    model_config = ConfigDict(from_attributes=True)


class GetLinkSchema(BaseModel):
    end_at: datetime.datetime | str | None
    project_rel: ProjectRel

    model_config = ConfigDict(from_attributes=True)

    @field_validator('end_at', mode='before')
    def validate(cls, value: datetime.datetime | str | None):
        if isinstance(value, NoneType):
            return "Бессрочна"
        elif isinstance(value, str):
            return value
        elif isinstance(value, datetime.datetime):
            print(123)
            formatted_date = format_datetime(value, format='d MMMM, Y HH:mm', locale='ru')
            return formatted_date
        else:
            raise TypeError('Invalid type of field "end_at"')