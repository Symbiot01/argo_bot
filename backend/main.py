from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database.db import Base1, engine1, get_db1, Base2, engine2, get_db2
from models import User, Chat, Message
import uvicorn
import logging
import os

from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database.db import Base1, engine1, get_db1, Base2, engine2
from models import User, Chat, Message
import uvicorn
import logging
import os

Base2.metadata.create_all(bind=engine2)
# Base1.metadata.create_all(bind=engine1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize FastAPI app
app = FastAPI(
    title="Argobot Backend API",
    description="APIs and RAg logic for ARGO Bot",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from routers import userrouter, chatrouter

app.include_router(userrouter.router, prefix="/api/v1", tags=["users"])
app.include_router(chatrouter.router, prefix="/api/v1/chat", tags=["chat"])

@app.get("/")
async def root():
    return {
        "message": "Argobot API is running",
        "version": "1.0.0",
        "docs": "/docs",
        "status_endpoint": "/api/v1/status"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Example of a route with database dependency
@app.get("/documents")
def get_documents(db: Session = Depends(get_db2)):
    # You need to create the Document model first for this to work
    # documents = db.query(models.Document).all()
    # return documents
    return {"message": "This is where you would list documents from the database."}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)), log_level="info")