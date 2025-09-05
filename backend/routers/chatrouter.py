from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database.db import get_db2
from models.Chat import Chat
from config import SECRET_KEY, ALGORITHM, CHAT_TOKEN_EXPIRE_DAYS
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import List
import logging

router = APIRouter()

class NewChatRequest(BaseModel):
    userid: int
    description: str

class ChatToken(BaseModel):
    chat_token: str
    token_type: str

class ValidateTokenRequest(BaseModel):
    token: str

def create_chat_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=CHAT_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/newchat", response_model=ChatToken)
def create_new_chat(chat_request: NewChatRequest, db: Session = Depends(get_db2)):
    logging.info(f"Creating new chat for user {chat_request.userid}")
    expires_delta = timedelta(days=CHAT_TOKEN_EXPIRE_DAYS)
    expires_at = datetime.utcnow() + expires_delta
    
    new_chat = Chat(
        user_id=chat_request.userid,
        description=chat_request.description,
        started_at=datetime.utcnow(),
        expires_at=expires_at
    )
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)

    logging.info(f"New chat created with id {new_chat.id}")

    chat_token = create_chat_token(
        data={"chat_id": new_chat.id}, expires_delta=expires_delta
    )
    return {"chat_token": chat_token, "token_type": "bearer"}

@router.post("/validatechat")
def validate_chat_token(token_request: ValidateTokenRequest, db: Session = Depends(get_db2)):
    logging.info("Validating chat token")
    try:
        payload = jwt.decode(token_request.token, SECRET_KEY, algorithms=[ALGORITHM])
        chat_id: int = payload.get("chat_id")
        if chat_id is None:
            logging.warning("Invalid token: chat_id not found")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        logging.info(f"Token contains chat_id: {chat_id}")
    except JWTError as e:
        logging.error(f"Token validation failed: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        logging.warning(f"Chat with id {chat_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    if chat.expires_at < datetime.utcnow():
        logging.warning(f"Chat with id {chat_id} has expired")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Chat has expired")

    logging.info(f"Chat with id {chat_id} is active")
    return {"status": "active", "chat_id": chat.id, "expires_at": chat.expires_at}

@router.get("/getactivechats", response_model=List[dict])
def get_active_chats(db: Session = Depends(get_db2)):
    active_chats = db.query(Chat).filter(Chat.expires_at > datetime.utcnow()).all()
    return [chat.to_dict() for chat in active_chats]
