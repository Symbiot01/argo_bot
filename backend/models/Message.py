from sqlalchemy import Column, Integer, String

from database.db import Base2


class Message(Base2):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, foreign_key='users.id')
    chat_id = Column(Integer, index=True, foreign_key='chats.id')
    message = Column(String)
    response = Column(String)
    message_index = Column(Integer)
    response_media_urls = Column(String)  # Comma-separated URLs
    timestamp = Column(String)

    def __repr__(self):
        return f"<Message(user_id={self.user_id}, message={self.message}, response={self.response})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "message": self.message,
            "response": self.response,
            "message_index": self.message_index,
            "response_media_urls": self.response_media_urls,
            "timestamp": self.timestamp
        }
    
    def from_dict(self, data):
        for field in ['user_id', 'chat_id', 'message', 'response', 'timestamp']:
            if field in data:
                setattr(self, field, data[field])