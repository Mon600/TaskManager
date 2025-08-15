import datetime
import enum
from typing import Optional, Annotated, Union, Literal, List

from fastapi import Depends, Query
from pydantic import BaseModel, model_validator, Field

from src.shared.db.models import TaskPriority


class SortField(enum.Enum):
    CREATED = "created"
    DEADLINE = "deadline"
    PRIORITY = "priority"
    STATUS = "status"

class SortDirection(enum.Enum):
    ASC = "asc"
    DESC = "desc"

class TaskFilter(BaseModel):
    status: Optional[list[str]] = None
    priority: List[Optional[TaskPriority]] = Field(default=None, max_length=3)
    deadline_after: Optional[datetime.date] = None
    deadline_before: Optional[datetime.date] = None
    created_after: Optional[datetime.datetime] = None
    created_before: Optional[datetime.datetime]  = None
    sort_by: Optional[SortField] = None
    sort_dir: SortDirection = SortDirection.DESC


    @model_validator(mode="after")
    def check_date_ranges(self):
        if self.deadline_after and self.deadline_before:
            if self.deadline_after > self.deadline_before:
                raise ValueError("deadline_after must be <= deadline_before")
        if self.created_after and self.created_before:
            if self.created_after > self.created_before:
                raise ValueError("created_after must be <= created_before")
        return self

class ActionType(enum.Enum):
    delete_user = 'delete_user'
    change_role = 'change_role'
    change_task = 'change_task'
    link_generate = 'link_generate'
    delete_link = 'delete_link'
    change_user_role = 'change_user_role'
    change_default_role = 'change_default_role'
    change_project = 'change_project'
    user_joined = 'user_joined'



class HistoryFilter(BaseModel):
    from_user: Optional[int] = Field(default=None)
    action_type: List[Optional[ActionType]] = Field(default=Query(None, style='form', explode=True), max_length=9)
    time_interval_start: Optional[datetime.date] = Field(default=None)
    time_interval_end: Optional[datetime.date] = Field(default=None)


    @model_validator(mode="after")
    def check_date_ranges(self):
        if self.time_interval_start and self.time_interval_end:
            if self.time_interval_start > self.time_interval_end:
                raise ValueError("start of interval must be less then end of interval")


FiltersDep = Annotated[HistoryFilter, Depends()]
