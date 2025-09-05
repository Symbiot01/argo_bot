from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from database.db import Base2

class Message(Base2):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    chat_id = Column(Integer, ForeignKey('chats.id'), index=True)
    message = Column(String)
    response = Column(String)
    message_index = Column(Integer)
    response_media_urls = Column(String)  # Storing as a string is fine for now
    timestamp = Column(DateTime, server_default=func.now())

    def __repr__(self):
        # A good __repr__ should uniquely identify the object.
        return f"<Message(id={self.id}, user_id={self.user_id}, chat_id={self.chat_id})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "message": self.message,
            "response": self.response,
            "message_index": self.message_index,
            "response_media_urls": self.response_media_urls,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
    
    def from_dict(self, data):
        # Only include fields that a client might send for creation/update.
        for field in ['user_id', 'chat_id', 'message', 'response', 'message_index', 'response_media_urls']:
            if field in data:
                setattr(self, field, data[field])