from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from database.db import Base2

class Chat(Base2):
    __tablename__ = 'chats'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    description = Column(String)
    started_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<Chat(id={self.id}, user_id={self.user_id})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "description": self.description,
            "started_at": self.started_at.isoformat() if self.started_at else None
        }

    def from_dict(self, data):
        for field in ['user_id', 'description']:
            if field in data:
                setattr(self, field, data[field])