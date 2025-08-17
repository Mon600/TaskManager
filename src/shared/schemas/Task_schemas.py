import datetime
from typing import List, Optional, Union, Any, Dict
from babel.dates import format_date
from pydantic import field_validator, BaseModel, ConfigDict, model_validator, Field

from src.shared.db.models import TaskPriority
from src.shared.schemas.Assigneed_schemas import AssigneesModel

class EditableTaskData(BaseModel):
    name: str
    description: str
    priority: str
    status: str

    model_config = ConfigDict(from_attributes=True)

class UpdateTaskSchema(EditableTaskData):
    assignees: List[int] = Field(default_factory=list)


class BaseTaskSchema(EditableTaskData):
    id: int
    deadline: datetime.date
    started_at: datetime.datetime
    completed_at: Optional[datetime.date] = None
    is_ended: bool
    project_id: int

    model_config = ConfigDict(from_attributes=True)


class CreateTaskSchema(BaseModel):
    name: str
    description: str
    deadline: datetime.date
    priority: TaskPriority
    assignees: list[int]


class TaskSchema(BaseTaskSchema):
    assignees: List[int] = Field(default_factory=list)

    @field_validator('deadline', mode='before')
    @classmethod
    def validate_deadline(cls, value: Union[str, datetime.date]) -> datetime.date:
        if isinstance(value, str):
            try:
                value = datetime.datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError('Неверный формат даты. Ожидается YYYY-MM-DD.')
        if value <= datetime.date.today():
            raise ValueError('Дата окончания (дедлайн) должна быть позже текущей даты.')
        return value


    @model_validator(mode='after')
    def check_deadline_after_started(self):
        if self.deadline <= self.started_at:
            raise ValueError('Дата окончания должна быть позже даты начала.')
        return self

    model_config = ConfigDict(from_attributes=True)


class TaskSchemaExtend(TaskSchema):
    id: int


class TaskGetSchema(EditableTaskData):
    id: int
    deadline: str
    started_at: str
    completed_at: Optional[str]
    assignees_rel: List[AssigneesModel]

    @model_validator(mode='before')
    @classmethod
    def format_dates(cls, data: Union[Dict[str, Any], Any]) -> Union[Dict[str, Any], Any]:
        def format_if_date(value: Any) -> Any:
            if isinstance(value, (datetime.datetime, datetime.date)):
                return format_date(value, format='d MMMM, Y', locale='ru')
            return value

        fields_to_format = ['deadline', 'started_at', 'completed_at']

        if isinstance(data, dict):
            for field in fields_to_format:
                if field in data and data[field] is not None:
                    data[field] = format_if_date(data[field])
        else:

            for field in fields_to_format:
                if hasattr(data, field) and getattr(data, field) is not None:
                    setattr(data, field, format_if_date(getattr(data, field)))

        return data

    model_config = ConfigDict(from_attributes=True)