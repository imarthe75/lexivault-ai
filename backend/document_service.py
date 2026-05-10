"""
Document Service - Document Processing and Storage
Abstraction layer ready for Docling migration
"""

import io
import logging
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from minio import Minio
import minio.error as minio_error

from config import settings
from database import SessionLocal
from models import Document, DocumentVersion, DocumentChunk
from llm_service import llm_service

logger = logging.getLogger(__name__)


class DocumentService:
    """Manages document storage, retrieval, and processing"""

    def __init__(self):
        self.bucket_name = settings.CEPH_BUCKET_NAME
        self.minio_client = self._init_minio()

    def _init_minio(self) -> Optional[Minio]:
        """Initialize MinIO/Ceph client"""
        try:
            endpoint = settings.CEPH_ENDPOINT_URL.replace("http://", "").replace("https://", "")
            secure = settings.CEPH_ENDPOINT_URL.startswith("https://")
            client = Minio(
                endpoint,
                access_key=settings.CEPH_ACCESS_KEY,
                secret_key=settings.CEPH_SECRET_KEY,
                secure=secure,
            )

            if not client.bucket_exists(self.bucket_name):
                client.make_bucket(self.bucket_name)
                logger.info(f"✅ Bucket created: {self.bucket_name}")
            else:
                logger.info(f"✅ MinIO/Ceph initialized, bucket: {self.bucket_name}")

            return client
        except Exception as e:
            logger.error(f"❌ MinIO/Ceph initialization failed: {e}")
            return None

    def upload_document(
        self,
        user_id: UUID,
        filename: str,
        file_content: bytes,
        mime_type: str = "application/pdf",
        title: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Document:
        """Upload a new document and prepare it for processing."""
        if not self.minio_client:
            raise RuntimeError("MinIO/Ceph client is not available")

        session = SessionLocal()
        try:
            document = Document(
                id=uuid4(),
                title=title or filename.rsplit('.', 1)[0],
                category=category or "Uncategorized",
                tags=tags or [],
                created_by=user_id,
                last_modified_by=user_id,
                created_at=datetime.utcnow(),
            )
            session.add(document)
            session.flush()

            object_key = f"{user_id}/{document.id}/{filename}"
            self.minio_client.put_object(
                self.bucket_name,
                object_key,
                io.BytesIO(file_content),
                length=len(file_content),
                content_type=mime_type,
            )
            logger.info(f"✅ File uploaded to MinIO: {object_key}")

            version = DocumentVersion(
                id=uuid4(),
                document_id=document.id,
                version_number=1,
                ceph_path=object_key,
                encryption_key_encrypted="",
                original_filename=filename,
                mimetype=mime_type,
                size_bytes=len(file_content),
                processed_status="processing",
                upload_timestamp=datetime.utcnow(),
                uploaded_by=user_id,
            )
            session.add(version)
            session.flush()

            extracted_text = self._extract_document_text(file_content, mime_type)
            chunks = self._generate_chunks(
                document_id=document.id,
                document_version_id=version.id,
                text=extracted_text,
                session=session,
            )

            version.processed_status = "completed"
            version.file_metadata = {
                "extracted_length": len(extracted_text),
                "chunks_count": len(chunks),
                "extraction_provider": settings.DOCLING_PROVIDER,
            }

            session.commit()
            logger.info(f"✅ Document processed: {document.id} ({len(chunks)} chunks)")
            return document
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Document upload failed: {e}")
            raise
        finally:
            session.close()

    def _extract_document_text(
        self,
        file_content: bytes,
        mime_type: str,
    ) -> str:
        """Extract text from document using the configured provider."""
        try:
            if settings.DOCLING_PROVIDER == "vertex":
                return llm_service.extract_document_text(
                    file_content=file_content,
                    mime_type=mime_type,
                )
            raise NotImplementedError(f"Provider {settings.DOCLING_PROVIDER} not yet supported")
        except Exception as e:
            logger.warning(f"⚠️ Vertex extraction failed, falling back to local extraction: {e}")
            return self._extract_text_locally(file_content, mime_type)

    @staticmethod
    def _extract_text_locally(file_content: bytes, mime_type: str) -> str:
        """Fallback local extraction for documents."""
        try:
            if "pdf" in mime_type:
                import fitz
                document = fitz.open(stream=file_content, filetype="pdf")
                return "\n".join(page.get_text("text") for page in document)

            if "word" in mime_type or "docx" in mime_type:
                import docx
                from io import BytesIO
                document = docx.Document(BytesIO(file_content))
                return "\n".join(paragraph.text for paragraph in document.paragraphs)

            if mime_type.startswith("image/"):
                from PIL import Image
                import pytesseract
                image = Image.open(io.BytesIO(file_content))
                return pytesseract.image_to_string(image, lang="spa+eng")

            return ""
        except Exception as exc:
            logger.error(f"❌ Local document extraction failed: {exc}")
            return ""

    def _generate_chunks(
        self,
        document_id: UUID,
        document_version_id: UUID,
        text: str,
        session: Session,
    ) -> List[DocumentChunk]:
        """Generate chunks from document text."""
        chunks = []
        chunk_size = settings.CHUNK_SIZE
        overlap = settings.CHUNK_OVERLAP

        if not text:
            logger.warning("⚠️ No extracted text available for document chunking")
            return []

        start = 0
        chunk_order = 0
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunk = DocumentChunk(
                    id=uuid4(),
                    document_version_id=document_version_id,
                    chunk_text=chunk_text,
                    chunk_embedding=None,
                    chunk_order=chunk_order,
                    created_at=datetime.utcnow(),
                )
                session.add(chunk)
                chunks.append(chunk)
                chunk_order += 1
            start = end - overlap if end < len(text) else end

        session.flush()
        logger.info(f"✅ Generated {len(chunks)} chunks")
        return chunks

    def get_document(self, user_id: UUID, document_id: UUID) -> Optional[Document]:
        """Retrieve document metadata with versions and chunks loaded."""
        session = SessionLocal()
        try:
            doc = session.query(Document).options(
                joinedload(Document.versions).joinedload(DocumentVersion.chunks)
            ).filter(
                Document.id == document_id,
                Document.created_by == user_id,
            ).first()
            return doc
        finally:
            session.close()

    def list_documents(
        self,
        user_id: UUID,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Document]:
        """List user's documents with optional filters."""
        session = SessionLocal()
        try:
            query = session.query(Document).filter(Document.created_by == user_id)
            if category:
                query = query.filter(Document.category == category)
            if tags:
                query = query.filter(Document.tags.contains(tags))
            return query.order_by(Document.last_modified_at.desc()).limit(limit).offset(offset).all()
        finally:
            session.close()

    def delete_document(self, user_id: UUID, document_id: UUID) -> bool:
        """Delete document and its files."""
        session = SessionLocal()
        try:
            doc = session.query(Document).filter(
                Document.id == document_id,
                Document.created_by == user_id,
            ).first()
            if not doc:
                raise ValueError("Document not found")
            for version in doc.versions:
                try:
                    self.minio_client.remove_object(self.bucket_name, version.ceph_path)
                except minio_error.S3Error as e:
                    logger.warning(f"⚠️ Could not delete file {version.ceph_path}: {e}")
            session.delete(doc)
            session.commit()
            logger.info(f"✅ Document deleted: {document_id}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Document deletion failed: {e}")
            raise
        finally:
            session.close()


document_service = DocumentService()
