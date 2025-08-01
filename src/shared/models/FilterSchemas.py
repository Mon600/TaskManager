import datetime
import enum
from typing import Optional

from pydantic import BaseModel, model_validator

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
    priority: Optional[list[TaskPriority]] = None
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