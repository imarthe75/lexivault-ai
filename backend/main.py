from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import logging
from uuid import UUID
from datetime import datetime

from config import settings
from database import get_db
from auth_service import AuthService
from document_service import document_service
from llm_service import llm_service
from models import Base
from database import engine

# Initialize Database
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LexiVault AI API",
    description="Intelligent Document Vault with Vertex AI and OAuth2/JWT",
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", settings.LOG_LEVEL).upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@app.get("/", tags=["Health"])
def home():
    return {
        "status": "ok",
        "message": "LexiVault AI Backend (FastAPI) is running",
        "version": settings.APP_VERSION
    }

@app.get("/health", tags=["Health"])
def health(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {"status": "ok", "database": "healthy", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "database": "unhealthy"}
        )

from pydantic import BaseModel

class UserAuth(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

@app.post("/auth/register", status_code=status.HTTP_201_CREATED, tags=["Auth"])
def register(user_data: UserAuth):
    try:
        user = AuthService.register_user(
            username=user_data.username, 
            password=user_data.password, 
            email=user_data.email
        )
        return {
            "message": "User registered successfully",
            "user_id": str(user.id),
            "username": user.username,
            "email": user.email
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/auth/login", tags=["Auth"])
def login(user_data: UserAuth):
    try:
        auth_result = AuthService.login_user(
            username=user_data.username, 
            password=user_data.password
        )
        return auth_result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWKClient
import jwt
import uuid

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.AUTHENTIK_URL}/application/o/token/",
    auto_error=False,
)

_jwks_client = PyJWKClient(
    f"{settings.AUTHENTIK_INTERNAL_URL}/application/o/{settings.AUTHENTIK_CLIENT_ID}/jwks/"
)

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.AUTHENTIK_CLIENT_ID,
            options={"verify_exp": True},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except Exception as e:
        logger.warning(f"[lexivault] JWT validation failed: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

def get_user_uuid(user_data: dict) -> uuid.UUID:
    sub = user_data.get("sub")
    if not sub:
        sub = user_data.get("preferred_username") or "default_user"
    try:
        return uuid.UUID(sub)
    except ValueError:
        # Generar un UUID v5 estable y determinista si no es un UUID nativo
        return uuid.uuid5(uuid.NAMESPACE_DNS, sub)

@app.get("/documents", tags=["Documents"])
def list_documents(current_user: dict = Depends(get_current_user)):
    try:
        user_uuid = get_user_uuid(current_user)
        documents = document_service.list_documents(user_uuid)
        return {
            "documents": [
                {
                    "id": str(doc.id),
                    "title": doc.title,
                    "category": doc.category,
                    "tags": doc.tags or [],
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "last_modified_at": doc.last_modified_at.isoformat() if doc.last_modified_at else None,
                }
                for doc in documents
            ]
        }
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to list documents")

@app.post("/documents", status_code=status.HTTP_201_CREATED, tags=["Documents"])
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    tags: Optional[str] = Form(""),
    current_user: dict = Depends(get_current_user)
):
    try:
        user_uuid = get_user_uuid(current_user)
        file_content = await file.read()
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        document = document_service.upload_document(
            user_id=user_uuid,
            filename=file.filename,
            file_content=file_content,
            mime_type=file.content_type,
            title=title or file.filename,
            category=category,
            tags=tag_list,
        )

        return {
            "message": "Document uploaded successfully",
            "document_id": str(document.id),
            "title": document.title,
            "category": document.category,
            "tags": document.tags or []
        }
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload document")

@app.post("/chat", tags=["AI"])
def chat(
    query: str = Form(...), 
    document_id: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    try:
        user_uuid = get_user_uuid(current_user)
        context_text = None
        if document_id:
            try:
                document = document_service.get_document(user_uuid, uuid.UUID(document_id))
                if document:
                    context_text = (
                        f"Document title: {document.title}\n"
                        f"Category: {document.category}\n"
                        f"Tags: {', '.join(document.tags or [])}\n"
                    )
            except Exception:
                context_text = None

        prompt = query
        if context_text:
            prompt = f"{context_text}\nUse the document context above to answer the query below.\n\nQuery: {query}"

        answer = llm_service.generate_content(
            prompt=prompt,
            max_tokens=1024,
            temperature=0.2
        )

        return {"query": query, "response": answer}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Chat request failed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
