from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from api.database import Base


class Integration(Base):
    __tablename__ = "integrations"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False, default="default_user")
    provider = Column(String, nullable=False)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
