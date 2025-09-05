from sqlalchemy import Column, Integer, String
from database.db import Base2

class Chat(Base2):
    __tablename__ = 'chats'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True,foreign_key='users.id')
    description = Column(String)
    started_at = Column(String)

    def __repr__(self):
        return f"<Chat(user_id={self.user_id}, message={self.message}, response={self.response})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "description": self.description,

            "started_at": self.started_at
        }
    
    def from_dict(self, data):
        for field in ['user_id', 'description', 'started_at']:
            if field in data:
                setattr(self, field, data[field])