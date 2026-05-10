"""
LLM Service - Vertex AI Integration
Abstracción para permitir cambios de proveedor sin modificar la lógica de negocio
"""

import base64
import io
import logging
import os
from typing import Optional, List, Dict, Any
from config import settings

logger = logging.getLogger(__name__)


class VertexAIProvider:
    """Provider para Vertex AI / Google GenAI SDK"""
    
    def __init__(self):
        try:
            if settings.GCP_CREDENTIALS_JSON and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GCP_CREDENTIALS_JSON

            from google import genai
            self.genai = genai
            self.project_id = settings.GCP_PROJECT_ID
            self.location = settings.GCP_LOCATION
            self.model_name = settings.VERTEX_MODEL
            self.client = genai.Client(vertexai=True, project=self.project_id, location=self.location)
            logger.info(f"✅ Vertex AI initialized: {self.model_name}")
            self.available = True
        except Exception as e:
            logger.error(f"❌ Vertex AI initialization failed: {e}")
            self.available = False
            self.client = None

    def generate_content(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        response_format: str = "text",
        **kwargs
    ) -> str:
        """Generate content using Vertex AI"""
        if not self.available or not self.client:
            raise Exception("Vertex AI provider not available")

        config: Dict[str, Any] = {
            "max_output_tokens": max_tokens,
            "temperature": temperature,
        }

        if response_format == "json":
            config["response_mime_type"] = "application/json"

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt],
                config=config
            )
            return getattr(response, "text", str(response))
        except Exception as e:
            logger.error(f"❌ Vertex AI error: {e}")
            raise

    def extract_text_from_document(
        self,
        file_content: bytes,
        mime_type: str = "application/pdf",
        gcs_uri: Optional[str] = None,
    ) -> str:
        """Extract text from document using Vertex AI multimodal capabilities"""
        if not self.available or not self.client:
            raise Exception("Vertex AI provider not available")

        try:
            from google.genai import types

            parts = []
            if gcs_uri:
                parts.append(types.Part.from_uri(file_uri=gcs_uri, mime_type=mime_type))
            else:
                encoded = base64.b64encode(file_content).decode("utf-8")
                parts.append(types.Part.from_data(data=encoded, mime_type=mime_type))

            extraction_instruction = (
                "Extract all text and structure from this document. "
                "Preserve headings, paragraphs, tables and lists, and return the result in Markdown format."
            )
            parts.append(types.Part.from_text(extraction_instruction))

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=parts,
                config={"max_output_tokens": 8192, "temperature": 0.0}
            )
            return getattr(response, "text", str(response))
        except Exception as e:
            logger.warning(f"⚠️ Vertex AI extraction failed: {e}")
            raise

    @staticmethod
    def _extract_text_locally(file_content: bytes, mime_type: str) -> str:
        """Fallback local extraction for documents when Vertex AI extraction fails."""
        try:
            if "pdf" in mime_type:
                import fitz
                document = fitz.open(stream=file_content, filetype="pdf")
                return "\n".join(page.get_text("text") for page in document)

            if "word" in mime_type or "docx" in mime_type:
                import docx
                from io import BytesIO
                doc = docx.Document(BytesIO(file_content))
                return "\n".join(paragraph.text for paragraph in doc.paragraphs)

            if mime_type.startswith("image/"):
                from PIL import Image
                import pytesseract
                image = Image.open(io.BytesIO(file_content))
                return pytesseract.image_to_string(image, lang="spa+eng")

            return ""
        except Exception as inner:
            logger.error(f"❌ Local document extraction failed: {inner}")
            return ""


class LLMService:
    """Main LLM Service - Routes to appropriate provider"""
    
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.vertex = None
        self.init_providers()
    
    def init_providers(self):
        if self.provider in ("vertex", "google"):
            self.vertex = VertexAIProvider()
            if self.vertex.available:
                logger.info("✅ Vertex AI provider ready")
            else:
                logger.warning("⚠️ Vertex AI not available, will fallback")
        else:
            logger.warning(f"⚠️ Provider {self.provider} not yet implemented")

    def generate_content(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        response_format: str = "text",
    ) -> str:
        if self.provider in ("vertex", "google") and self.vertex and self.vertex.available:
            return self.vertex.generate_content(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                response_format=response_format
            )
        raise Exception(f"LLM Provider {self.provider} not available")

    def extract_document_text(
        self,
        file_content: bytes,
        mime_type: str = "application/pdf",
        gcs_uri: Optional[str] = None,
    ) -> str:
        if self.provider in ("vertex", "google") and self.vertex:
            if self.vertex.available:
                try:
                    return self.vertex.extract_text_from_document(
                        file_content=file_content,
                        mime_type=mime_type,
                        gcs_uri=gcs_uri
                    )
                except Exception:
                    logger.warning("⚠️ Vertex extraction failed, falling back to local document extraction")
            return self.vertex._extract_text_locally(file_content, mime_type)
        raise Exception(f"Document extraction not available for provider {self.provider}")


llm_service = LLMService()
