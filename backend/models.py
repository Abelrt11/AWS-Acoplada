from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import datetime
import uuid

class ContactCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    tag: Literal["friend", "work", "family", "other"] = "other"

class ContactUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    email: Optional[EmailStr] = None
    tag: Optional[Literal["friend", "work", "family", "other"]] = None

class Contact(BaseModel):
    id: str
    name: str
    email: EmailStr
    tag: Literal["friend", "work", "family", "other"] = "other"
    created_at: str
    updated_at: str

    @staticmethod
    def new(name: str, email: str, tag: str = "other") -> "Contact":
        now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        return Contact(
            id=str(uuid.uuid4()),
            name=name,
            email=email,
            tag=tag,
            created_at=now,
            updated_at=now,
        )
