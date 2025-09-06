# utility_functions/chat_history.py

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc
from database.db import engine2
from models.Chat import Chat
from models.Message import Message

def get_chat_history(chat_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent chat history for a specific chat session.
    
    Args:
        chat_id: The ID of the chat session
        limit: Maximum number of messages to retrieve (default 10)
    
    Returns:
        List of message dictionaries with user messages and system responses
    """
    try:
        # Create database session
        SessionLocal = sessionmaker(bind=engine2)
        db = SessionLocal()
        
        # Query recent messages for the chat
        messages = db.query(Message).filter(
            Message.chat_id == chat_id
        ).order_by(desc(Message.timestamp)).limit(limit).all()
        
        # Convert to list of dictionaries and reverse to get chronological order
        chat_history = []
        for message in reversed(messages):
            if message.message:  # User message
                chat_history.append({
                    "type": "user",
                    "content": message.message,
                    "timestamp": message.timestamp.isoformat() if message.timestamp else None,
                    "message_index": message.message_index
                })
            if message.response:  # System response
                chat_history.append({
                    "type": "assistant",
                    "content": message.response,
                    "timestamp": message.timestamp.isoformat() if message.timestamp else None,
                    "message_index": message.message_index
                })
        
        db.close()
        logging.info(f"Retrieved {len(chat_history)} messages from chat {chat_id}")
        return chat_history
        
    except Exception as e:
        logging.error(f"Error retrieving chat history for chat {chat_id}: {e}")
        return []

def format_chat_history_for_context(chat_history: List[Dict[str, Any]]) -> str:
    """
    Format chat history into a readable string for LLM context.
    
    Args:
        chat_history: List of message dictionaries from get_chat_history
    
    Returns:
        Formatted string representation of the chat history
    """
    if not chat_history:
        return "No previous conversation history available."
    
    formatted_history = "PREVIOUS CONVERSATION HISTORY:\n\n"
    
    for message in chat_history:
        if message["type"] == "user":
            formatted_history += f"User: {message['content']}\n"
        elif message["type"] == "assistant":
            formatted_history += f"Assistant: {message['content']}\n"
        formatted_history += "\n"
    
    formatted_history += "--- END OF CONVERSATION HISTORY ---\n"
    return formatted_history

def get_active_chat_info(chat_id: int) -> Optional[Dict[str, Any]]:
    """
    Get information about an active chat session.
    
    Args:
        chat_id: The ID of the chat session
    
    Returns:
        Dictionary with chat information or None if not found
    """
    try:
        # Create database session
        SessionLocal = sessionmaker(bind=engine2)
        db = SessionLocal()
        
        # Query chat information
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        
        if chat:
            chat_info = chat.to_dict()
            db.close()
            return chat_info
        else:
            db.close()
            return None
            
    except Exception as e:
        logging.error(f"Error retrieving chat info for chat {chat_id}: {e}")
        return None
