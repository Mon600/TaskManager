from typing import Optional

from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserSchema(BaseModel):
    id: int = Field(description="ID пользователя на github")
    username: str = Field(description="Имя пользователя")
    email: Optional[EmailStr] = Field(description="Электронная почта")
    avatar_url: Optional[str] = Field(description="Ссылка на аватарку пользователя")

    model_config = ConfigDict(from_attributes=True)

