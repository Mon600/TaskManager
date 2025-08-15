from typing import Annotated

from fastapi import Depends
from pydantic import Field, BaseModel



class Pagination(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1)


PaginationDep = Annotated[Pagination, Depends()]