
from pydantic import model_validator



from typing import Optional, Dict, Any, Union, Literal, Self
from beanie import Document
from pydantic import BaseModel, Field
from datetime import datetime

from pymongo import IndexModel

from src.shared.schemas.Project_schemas import ProjectMemberExtend
from src.shared.schemas.User_schema import UserSchema


class BaseActionData(BaseModel):
    action_type: str
    timestamp: datetime = Field(default_factory=datetime.now)
    description: Optional[str] = None


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
    deleted_user: ProjectMemberExtend
    reason: str = ""


class ChangeRoleActionData(BaseActionData):
    action_type: Literal["change_role"] = "change_role"
    role_id: int
    old_data: Dict[str, Any]
    new_data: Dict[str, Any]


class ChangeTaskActionData(BaseActionData):
    action_type: Literal["change_task"] = "change_task"
    old_data: Dict[str, Any]
    new_data: Dict[str, Any]


class LinkGenerateActionData(BaseActionData):
    action_type: Literal["link_generate"] = "link_generate"
    link: str

class LinkDeleteActionData(BaseActionData):
    action_type: Literal["delete_link"] = "delete_link"
    is_all: Optional[bool] = Field(default=False)
    link: Optional[str] = ""

    @model_validator(mode='before')
    @classmethod
    def validate(cls, data: Union[Dict[str, Any], Any]) -> Union[Dict[str, Any], Any]:
        if isinstance(data, dict):
            if (data.get('is_all', False) and data.get('link')) or (not data.get('is_all', False) and not data.get('link')):
                raise ValueError("You can delete one OR all links.")
        return data


class ChangeUserRoleActionData(BaseActionData):
    action_type: Literal["change_user_role"] = "change_user_role"
    changed_role_user: Dict[str, Any]
    old_data: Dict[str, Any]
    new_data: Dict[str, Any]


class ChangeDefaultRoleData(BaseActionData):
    action_type: Literal["change_default_role"] = "change_default_role"
    old_data: Dict[str, Any]
    new_data: Dict[str, Any]


class ChangeProjectActionData(BaseActionData):
    action_type: Literal["change_project"] = "change_project"
    old_data: Dict[str, Any]
    new_data: Dict[str, Any]


class UserJoinActionData(BaseActionData):
    action_type: Literal["user_joined"] = "user_joined"


class History(Document):
    project_id: int
    user: UserSchema
    action: Union[
        DeleteUserActionData,
        ChangeRoleActionData,
        ChangeTaskActionData,
        LinkGenerateActionData,
        LinkDeleteActionData,
        ChangeUserRoleActionData,
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
            "user.id"
            "action.action_type",
            "timestamp",
            IndexModel([('created_at', 1)],
                       expireAfterSeconds=3600*48)
        ]