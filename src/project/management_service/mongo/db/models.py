from datetime import datetime
from typing import Optional, Dict, Any, Union, Literal

from beanie import Document
from pydantic import BaseModel, Field
from pydantic import model_validator
from pymongo import IndexModel

from src.shared.schemas.Link_schemas import LinkSchemaExtend
from src.shared.schemas.Project_schemas import ProjectMemberSchemaExtend, ProjectData, ProjectRel
from src.shared.schemas.Role_schemas import RoleSchema, RoleSchemaWithId
from src.shared.schemas.Task_schemas import TaskGetSchema, BaseTaskSchema
from src.shared.schemas.User_schema import UserSchema


class BaseActionData(BaseModel):
    action_type: str
    timestamp: datetime = Field(default_factory=datetime.now)

    @model_validator(mode="before")
    @classmethod
    def validate_action_data(cls, data: Union[Dict[str, Any], Any]) -> Union[Dict[str, Any], Any]:
        if isinstance(data, dict) and 'new_data' in data.keys() and 'old_data' in data.keys():
            old_data = data.get('old_data', None)
            new_data = data.get('new_data', None)
            if old_data == new_data and (not old_data is None and not new_data is None):
                raise ValueError("old_data and new_data cannot be identical for change actions")
        return data


class DeleteUserActionData(BaseActionData):
    action_type: Literal["delete_user"] = "delete_user"
    deleted_user: ProjectMemberSchemaExtend
    reason: str = ""


class ChangeRoleActionData(BaseActionData):
    action_type: Literal["change_role"] = "change_role"
    role_id: int
    old_data: RoleSchema
    new_data: RoleSchema


class CreateTaskActionData(BaseActionData):
    action_type: Literal["create_task"] = "create_task"
    created_task: TaskGetSchema


class DeleteTaskActionData(BaseActionData):
    action_type: Literal["delete_task"] = "delete_task"
    deleted_task: BaseTaskSchema


class ChangeTaskActionData(BaseActionData):
    action_type: Literal["change_task"] = "change_task"
    old_data: TaskGetSchema
    new_data: TaskGetSchema


class CompleteTaskActionData(BaseActionData):
    action_type: Literal['complete_task'] = "complete_task"
    completed_task: BaseTaskSchema


class LinkGenerateActionData(BaseActionData):
    action_type: Literal["link_generate"] = "link_generate"
    link: str


class LinkDeleteActionData(BaseActionData):
    action_type: Literal["delete_link"] = "delete_link"
    is_all: Optional[bool] = Field(default=False)
    link: list[LinkSchemaExtend]

    @model_validator(mode='before')
    @classmethod
    def validate(cls, data: Union[Dict[str, Any], Any]) -> Union[Dict[str, Any], Any]:
        if isinstance(data, dict):
            if ((data.get('is_all', False) == False) and (len(data.get('link')) > 1)) or (
                    (data.get('is_all', False)) == True and (not data.get('link'))):
                raise ValueError("You can delete one OR all links.")
        return data


class ChangeUserRoleActionData(BaseActionData):
    action_type: Literal["change_user_role"] = "change_user_role"
    changed_role_user: UserSchema
    old_data: RoleSchema
    new_data: RoleSchema


class ChangeDefaultRoleData(BaseActionData):
    action_type: Literal["change_default_role"] = "change_default_role"
    old_data: RoleSchema
    new_data: RoleSchema


class DeleteRoleActionData(BaseActionData):
    action_type: Literal["delete_role"] = "delete_role"
    role_id: int
    deleted_role: RoleSchema


class CreateRoleActionData(BaseActionData):
    action_type: Literal["create_role"] = "create_role"
    created_role: RoleSchema


class EditRoleActionData(BaseActionData):
    action_type: Literal['edit_role'] = 'edit_role'
    role_id: int
    old_data: RoleSchema
    new_data: RoleSchema


class ChangeProjectActionData(BaseActionData):
    action_type: Literal["change_project"] = "change_project"
    old_data: ProjectData
    new_data: ProjectData


class UserJoinActionData(BaseActionData):
    action_type: Literal["user_joined"] = "user_joined"
    project_data: ProjectRel


class History(Document):
    project_id: int
    user: UserSchema
    created_at: datetime = Field(default=datetime.now())
    action: Union[
            DeleteUserActionData,
            ChangeRoleActionData,
            CreateTaskActionData,
            CompleteTaskActionData,
            DeleteTaskActionData,
            ChangeTaskActionData,
            LinkGenerateActionData,
            LinkDeleteActionData,
            ChangeUserRoleActionData,
            DeleteRoleActionData,
            EditRoleActionData,
            CreateRoleActionData,
            ChangeDefaultRoleData,
            ChangeProjectActionData,
            UserJoinActionData
    ]

    @model_validator(mode="before")
    @classmethod
    def validate_action_data(cls, data: Union[Dict[str, Any], Any]) -> Union[Dict[str, Any], Any]:
        if isinstance(data, dict) and 'action' in data:
            action = data['action']
            if isinstance(action, dict):

                if action.get('action_type') in ['change_role', 'change_task', 'change_default_role', 'change_project']:
                    old_data = action.get('old_data', {})
                    new_data = action.get('new_data', {})
                    if isinstance(old_data, dict) and isinstance(new_data, dict) and old_data == new_data:
                        raise ValueError("old_data and new_data cannot be identical for change actions")
        return data

    class Settings:
        name = "history"
        indexes = [
            "project_id",
            "user.id",
            "action.action_type",
            "timestamp",
            IndexModel([('created_at', 1)],
                       expireAfterSeconds=3600 * 48)
        ]
