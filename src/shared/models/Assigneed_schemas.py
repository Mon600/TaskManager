from pydantic import BaseModel, ConfigDict

from src.shared.models.User_schema import UserSchema


class AssigneesProjectMember(BaseModel):
    user_rel: UserSchema

    model_config = ConfigDict(from_attributes=True)


class AssigneesModel(BaseModel):
    project_member_rel: AssigneesProjectMember

    model_config = ConfigDict(from_attributes=True)

