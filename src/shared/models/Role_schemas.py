from pydantic import BaseModel, ConfigDict, Field


class Permissions(BaseModel):
    create_tasks: bool = Field(default=False)
    delete_tasks: bool = Field(default=False)
    update_tasks: bool = Field(default=False)
    update_project: bool = Field(default=False)
    generate_url: bool = Field(default=False)
    delete_users: bool = Field(default=False)
    change_roles: bool = Field(default=False)
    manage_links: bool = Field(default=False)


class ProjectSchemaForRoles(BaseModel):
    name: str = Field(max_length=50, min_length=1, description="Название проекта")

    model_config = ConfigDict(from_attributes=True)


class RoleSchema(Permissions):
    name: str
    priority: int = Field(default=1, ge=1, le=10)


    model_config = ConfigDict(from_attributes=True)

class RoleSchemaWithId(RoleSchema):
    id: int


class RoleSchemaExtend(RoleSchema):
    project_rel: ProjectSchemaForRoles

    model_config = ConfigDict(from_attributes=True)
