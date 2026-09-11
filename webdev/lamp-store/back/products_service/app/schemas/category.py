import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    pass

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    is_active: bool | None = None


class CategoryRead(CategoryBase):

    model_config = ConfigDict(from_attributes=True)

    category_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
