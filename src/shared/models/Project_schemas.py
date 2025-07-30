import datetime

from babel.dates import format_date
from pydantic import BaseModel, Field, ConfigDict, field_validator

from src.shared.models.Role_schemas import RoleSchema, RoleSchemaWithId
from src.shared.models.Task_schemas import TaskGetSchema
from src.shared.models.User_schema import UserSchema

class ProjectData(BaseModel):
    name: str = Field(max_length=50, min_length=1, description="Название проекта")
    status: str = Field(max_length=5, min_length=4, default="open", description="Статус")
    description: str | None = Field(max_length=1024, description="Описание проекта")

    model_config = ConfigDict(from_attributes=True)

class ProjectMember(BaseModel):
    id: int
    user_id: int
    project_id: int
    role_id: int
    role_rel: RoleSchema

    model_config = ConfigDict(from_attributes=True)

class ProjectMemberExtend(ProjectMember):
    user_rel: UserSchema



    model_config = ConfigDict(from_attributes=True)

class ProjectDataGet(ProjectData):
    creator_user_id: int
    created_at: str
    tasks_rel: list[TaskGetSchema]


    @field_validator('created_at', mode='before')
    def validate(cls, value: datetime.date):
        formatted_date = format_date(value, format='d MMMM, Y', locale='ru')
        return formatted_date


    model_config = ConfigDict(from_attributes=True)

class ProjectRel(ProjectData):
    id: int
    default_role_id: int

class ProjectFromMember(BaseModel):
    project_rel: ProjectRel

    model_config = ConfigDict(from_attributes=True)


class ProjectWithRoles(ProjectRel):
    roles_rel: list[RoleSchemaWithId]

    model_config = ConfigDict(from_attributes=True)


