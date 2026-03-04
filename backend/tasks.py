# tasks.py

import os
import logging
from datetime import datetime
from uuid import UUID as UUIDType
from celery import Celery
import requests
from dotenv import load_dotenv
from time import sleep

# --- SQLAlchemy and Models Imports ---
from database import get_db
from models import DocumentVersion, DocumentChunk
# --- Import FileProcessorService ---
from file_processor_service import FileProcessorService
from vault_client import vault_client # Importar cliente de Vault

load_dotenv()

# --- Logger Configuration ---
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(), format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Celery Configuration ---
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
celery_app = Celery('tasks', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
celery_app.conf.broker_connection_retry_on_startup = True

# --- Ollama Configuration ---
OLLAMA_API_BASE_URL = os.getenv("OLLAMA_API_BASE_URL", "http://ollama:11434")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
OLLAMA_GENERATION_MODEL = os.getenv("OLLAMA_GENERATION_MODEL", "mistral")
OLLAMA_EMBEDDING_TIMEOUT = int(os.getenv("OLLAMA_EMBEDDING_TIMEOUT", "1200"))
OLLAMA_GENERATION_TIMEOUT = int(os.getenv("OLLAMA_GENERATION_TIMEOUT", "1200"))

# --- Initialize FileProcessorService for Celery tasks ---
# This requires access to environment variables that would typically be set in the Celery worker's environment.
# Make sure all necessary environment variables (MinIO, Fernet, Kafka, etc.) are available to the Celery worker.
file_processor_service = FileProcessorService(
    s3_endpoint_url=vault_client.get_secret('secret/data/digital_vault', 'CEPH_ENDPOINT_URL', os.getenv("CEPH_ENDPOINT_URL")),
    s3_access_key=vault_client.get_secret('secret/data/digital_vault', 'CEPH_ACCESS_KEY', os.getenv("CEPH_ACCESS_KEY")),
    s3_secret_key=vault_client.get_secret('secret/data/digital_vault', 'CEPH_SECRET_KEY', os.getenv("CEPH_SECRET_KEY")),
    s3_bucket_name=vault_client.get_secret('secret/data/digital_vault', 'CEPH_BUCKET_NAME', os.getenv("CEPH_BUCKET_NAME")),
    master_key=vault_client.get_secret('secret/data/digital_vault', 'SYSTEM_MASTER_KEY', os.getenv("SYSTEM_MASTER_KEY")),
    kafka_bootstrap_servers=vault_client.get_secret('secret/data/digital_vault', 'KAFKA_BOOTSTRAP_SERVERS', os.getenv("KAFKA_BOOTSTRAP_SERVERS")),
    kafka_topic_uploaded=vault_client.get_secret('secret/data/digital_vault', 'KAFKA_TOPIC_FILE_UPLOADED', os.getenv("KAFKA_TOPIC_FILE_UPLOADED"))
)

# --- Utility Functions (keep these as they are, or move them to file_processor_service.py if more appropriate) ---

# --- Import Ollama Client ---
from llm_client import get_ollama_embedding, get_ollama_generation


# --- Modified Celery Task for RAG Indexing ---

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60, time_limit=3600, soft_time_limit=3000)
def generate_embeddings_for_document_chunks(self, document_version_id_str: str):
    """
    Celery task to process a document: generate chunks from markdown,
    generate embeddings, and save them to the database.
    """
    logger.info(f"Celery Task: Starting document processing for indexing: {document_version_id_str}")
    sleep(2) # Small delay to ensure other services are ready

    with get_db() as db_session:
        try:
            document_version = db_session.query(DocumentVersion).filter_by(id=UUIDType(document_version_id_str)).first()

            if not document_version:
                logger.error(f"Celery Task: Document version not found in DB for ID {document_version_id_str}.")
                raise ValueError("Document version record not found.")

            # Update status to processing
            document_version.processed_status = 'processing'
            document_version.last_processed_at = datetime.now()
            db_session.commit()
            db_session.refresh(document_version)

            # --- Call the FileProcessorService method for chunking and embedding ---
            # This method now handles chunk generation, embedding, and DB updates.
            # Note: We don't pass markdown_text because it's not in the DB yet. The service will extract it.
            success = file_processor_service.generate_chunks_and_embeddings_for_celery(
                session=db_session,
                document_version_id=document_version_id_str,
                markdown_text=None 
            )

            if success:
                logger.info(f"Celery Task: Successfully processed document {document_version_id_str} for indexing.")
                return True
            else:
                # Error already logged by generate_chunks_and_embeddings_for_celery
                self.retry(countdown=self.default_retry_delay) # Retry if the internal processing failed

        except Exception as e:
            # Catch any unexpected errors during the Celery task execution
            db_session.rollback() # Rollback any partial DB changes
            logger.error(f"Celery Task: Unhandled exception processing document {document_version_id_str}: {e}", exc_info=True)
            try:
                # Attempt to mark as failed in DB
                with get_db() as update_db_session:
                    failed_doc_version = update_db_session.query(DocumentVersion).filter_by(id=UUIDType(document_version_id_str)).first()
                    if failed_doc_version:
                        failed_doc_version.processed_status = 'failed_indexing'
                        failed_doc_version.last_processed_at = datetime.now()
                        update_db_session.add(failed_doc_version)
                        update_db_session.commit()
            except Exception as update_e:
                logger.error(f"Celery Task: CRITICAL error updating failure status in DB for {document_version_id_str}: {update_e}")
            
            self.retry(exc=e, countdown=self.default_retry_delay) # Retry the task