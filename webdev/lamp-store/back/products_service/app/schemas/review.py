import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ReviewBase(BaseModel):
    user_name: str = Field(..., min_length=1, max_length=100)
    user_email: EmailStr
    description: str | None = Field(default=None)
    rating: int = Field(..., ge=1, le=5)

    @field_validator("user_email")
    @classmethod
    def normalize_email(cls, value: str) -> str:

        return value.lower()


class ReviewCreate(ReviewBase):

    product_id: uuid.UUID


class ReviewModerate(BaseModel):

    is_approved: bool


class ReviewRead(ReviewBase):

    model_config = ConfigDict(from_attributes=True)

    review_id: uuid.UUID
    product_id: uuid.UUID
    is_approved: bool
    created_at: datetime
