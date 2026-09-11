import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ManufacturerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None)
    logo_url: str | None = Field(default=None, max_length=500)


class ManufacturerCreate(ManufacturerBase):
    pass


class ManufacturerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    logo_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class ManufacturerRead(ManufacturerBase):

    model_config = ConfigDict(from_attributes=True)

    manufacturer_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
