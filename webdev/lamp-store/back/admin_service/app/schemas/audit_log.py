import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.enums import AuditAction


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    log_id: uuid.UUID
    admin_id: uuid.UUID | None
    actor_email: str
    action: AuditAction
    entity_type: str | None
    entity_id: uuid.UUID | None
    payload: dict[str, Any] | None
    ip_address: str | None
    created_at: datetime
