"""
LexiVault AI - Backend Flask Application
Intelligent Document Vault with Vertex AI and JWT authentication
"""

import os
import logging
from uuid import UUID
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flasgger import Swagger
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session

from config import settings
from models import Base
from auth_service import AuthService
from document_service import document_service
from llm_service import llm_service

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", settings.LOG_LEVEL).upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
app.config["JWT_SECRET_KEY"] = settings.JWT_SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = int(settings.JWT_EXPIRATION_HOURS * 3600)

jwt = JWTManager(app)
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"])

# Swagger Configuration
app.config['SWAGGER'] = {
    'title': 'LexiVault AI API',
    'uiversion': 3,
    'openapi': '3.0.2',
    'specs_route': '/api/docs/'
}
swagger = Swagger(app)

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False,
)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base.metadata.create_all(engine)

@app.before_request
def setup_db_session():
    request.db_session = SessionLocal()

@app.teardown_request
def teardown_db_session(exception=None):
    if hasattr(request, "db_session"):
        request.db_session.close()

@app.route("/", methods=["GET"])
def home():
    """
    Home endpoint
    ---
    responses:
      200:
        description: API Status
    """
    return jsonify({
        "status": "ok",
        "message": "LexiVault AI Backend API is running",
        "version": settings.APP_VERSION
    }), 200

@app.route("/health", methods=["GET"])
def health():
    try:
        request.db_session.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"

    return jsonify({
        "status": "ok" if db_status == "healthy" else "degraded",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }), 200

@app.route("/vault/test-db", methods=["GET"])
def test_db():
    try:
        request.db_session.execute(text("SELECT 1"))
        return jsonify({"message": "Database connection successful!"}), 200
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        return jsonify({"error": "Database connection failed", "details": str(e)}), 500

@app.route("/auth/register", methods=["POST"])
def register():
    """
    User Registration
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: UserRegistration
          required:
            - username
            - password
          properties:
            username:
              type: string
            password:
              type: string
            email:
              type: string
    responses:
      201:
        description: User registered successfully
      400:
        description: Missing credentials
      409:
        description: Username already exists
    """
    try:
        data = request.get_json(silent=True) or {}
        username = data.get("username")
        password = data.get("password")
        email = data.get("email")

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        user = AuthService.register_user(username=username, password=password, email=email)
        return jsonify({
            "message": "User registered successfully",
            "user_id": str(user.id),
            "username": user.username,
            "email": user.email
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 409
    except Exception as e:
        logger.error(f"Error during registration: {e}")
        return jsonify({"error": "Registration failed", "details": str(e)}), 500

@app.route("/auth/login", methods=["POST"])
def login():
    try:
        data = request.get_json(silent=True) or {}
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        auth_result = AuthService.login_user(username=username, password=password)
        return jsonify(auth_result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return jsonify({"error": "Login failed", "details": str(e)}), 500

@app.route("/documents", methods=["GET"])
@jwt_required()
def list_documents():
    try:
        current_user_id = get_jwt_identity()
        logger.info(f"Listing documents for user: {current_user_id}")

        documents = document_service.list_documents(UUID(current_user_id))
        payload = [
            {
                "id": str(doc.id),
                "title": doc.title,
                "category": doc.category,
                "tags": doc.tags or [],
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "last_modified_at": doc.last_modified_at.isoformat() if doc.last_modified_at else None,
                "version_count": len(doc.versions) if getattr(doc, "versions", None) is not None else None,
            }
            for doc in documents
        ]

        return jsonify({"documents": payload}), 200
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        return jsonify({"error": "Failed to list documents", "details": str(e)}), 500

@app.route("/documents", methods=["POST"])
@jwt_required()
def upload_document():
    try:
        current_user_id = get_jwt_identity()

        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        title = request.form.get("title", file.filename)
        category = request.form.get("category")
        tags_raw = request.form.get("tags", "")
        tags = [tag.strip() for tag in tags_raw.split(",") if tag.strip()]
        mime_type = file.mimetype or "application/octet-stream"
        file_bytes = file.read()

        document = document_service.upload_document(
            user_id=UUID(current_user_id),
            filename=file.filename,
            file_content=file_bytes,
            mime_type=mime_type,
            title=title,
            category=category,
            tags=tags,
        )

        return jsonify({
            "message": "Document uploaded successfully",
            "document_id": str(document.id),
            "title": document.title,
            "category": document.category,
            "tags": document.tags or []
        }), 201
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        return jsonify({"error": "Failed to upload document", "details": str(e)}), 500

@app.route("/documents/<document_id>", methods=["GET"])
@jwt_required()
def get_document(document_id):
    try:
        current_user_id = get_jwt_identity()
        logger.info(f"Document retrieval request: {document_id}")

        document = document_service.get_document(UUID(current_user_id), UUID(document_id))
        if not document:
            return jsonify({"error": "Document not found"}), 404

        versions = []
        for version in getattr(document, "versions", []):
            versions.append({
                "version_id": str(version.id),
                "version_number": version.version_number,
                "is_latest": version.is_latest_version,
                "uploaded_by": str(version.uploaded_by) if version.uploaded_by else None,
                "upload_timestamp": version.upload_timestamp.isoformat() if version.upload_timestamp else None,
                "processed_status": version.processed_status,
                "file_metadata": version.file_metadata,
            })

        return jsonify({
            "id": str(document.id),
            "title": document.title,
            "category": document.category,
            "tags": document.tags or [],
            "created_at": document.created_at.isoformat() if document.created_at else None,
            "last_modified_at": document.last_modified_at.isoformat() if document.last_modified_at else None,
            "versions": versions,
        }), 200
    except ValueError:
        return jsonify({"error": "Invalid document id"}), 400
    except Exception as e:
        logger.error(f"Error retrieving document: {e}")
        return jsonify({"error": "Failed to retrieve document", "details": str(e)}), 500

@app.route("/chat", methods=["POST"])
@jwt_required()
def chat():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json(silent=True) or {}
        query = data.get("query")
        document_id = data.get("document_id")

        if not query:
            return jsonify({"error": "Query is required"}), 400

        context_text = None
        if document_id:
            try:
                document = document_service.get_document(UUID(current_user_id), UUID(document_id))
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

        return jsonify({"query": query, "response": answer}), 200
    except Exception as e:
        logger.error(f"Error during chat: {e}")
        return jsonify({"error": "Chat request failed", "details": str(e)}), 500

# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == '__main__':
    logger.info("Starting LexiVault AI Backend")
    app.run(host='0.0.0.0', port=5000, debug=os.getenv('FLASK_DEBUG', False))
