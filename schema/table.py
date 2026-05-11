from sqlmodel import SQLModel, Field, Column
from sqlalchemy import String, BigInteger, Boolean, DateTime
from typing import Optional
from datetime import datetime
from uuid import uuid4
from pydantic import EmailStr

class Users(SQLModel, table=True):
    __tablename__ = "Users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: Optional[EmailStr] = Field(default=None, sa_column=Column(String(255), unique=True))
    username: str = Field(sa_column=Column(String(100)))
    telegram_id: str = Field(sa_column=Column(String(100), unique=True))
    blofin_uuid: Optional[str] = Field(default=None, sa_column=Column(String(100), unique=True))
    bydefi_id: Optional[str] = Field(default=None, sa_column=Column(String(100), unique=True))
    weex_uuid: Optional[str] = Field(default=None, sa_column=Column(String(100), unique=True))
    exchange: Optional[str] = Field(default=None, sa_column=Column(String(100)))
    is_group_member: bool = Field(default=False, sa_column=Column(Boolean))
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime))
    updated_at: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime))

    def __repr__(self) -> str:
        return f"User: {self.username} (ID: {self.telegram_id})"
