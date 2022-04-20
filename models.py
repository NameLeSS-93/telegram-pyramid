import enum
from datetime import datetime

import pytz
from sqlalchemy import BOOLEAN, INTEGER, VARCHAR, Column, DateTime, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

DeclarativeBase = declarative_base()


class UserType(enum.Enum):
    ADMIN = 0
    USER = 1


class User(DeclarativeBase):
    __tablename__ = "user"

    id = Column(INTEGER, primary_key=True, nullable=False)
    code = relationship("Code", back_populates="user")
    user_type = Column(Enum(UserType), nullable=False)
    register_date = Column(
        DateTime(timezone=True), default=datetime.now(tz=pytz.timezone("Europe/Moscow"))
    )
    update_date = Column(
        DateTime(timezone=True), default=func.now(tz=pytz.timezone("Europe/Moscow"))
    )
    invitor_id = Column(INTEGER, ForeignKey("user.id"))
    invitor_relationship = relationship("User")

    def __init__(self, dict_info: dict):
        self.id = dict_info["user_id"]
        self.user_type = dict_info["user_type"]
        self.register_date = None
        self.update_time = None
        self.invitor_id = dict_info["invitor_id"]


class Code(DeclarativeBase):
    __tablename__ = "code"

    id = Column(INTEGER, primary_key=True, nullable=False)
    code = Column(VARCHAR(10), nullable=False, unique=True)
    is_used = Column(BOOLEAN, default=False)
    generation_time = Column(DateTime(timezone=True), default=datetime.now)
    use_time = Column(DateTime(timezone=True), nullable=True)
    user_relationship = Column(INTEGER, ForeignKey("user.id"))
    user = relationship("User", back_populates="code")

    def __init__(self, dict_info: dict):
        self.code = dict_info["code"]
        self.is_used = None
        self.generation_time = None
        self.use_time = None
        self.user_relationship = None


class Admin(DeclarativeBase):
    __tablename__ = "admin"

    id = Column(INTEGER, primary_key=True, nullable=False)
    admin_code = Column(VARCHAR(256), nullable=False, unique=True)

    def __init__(self, dict_info: dict):
        self.admin_code = dict_info["admin_code"]
