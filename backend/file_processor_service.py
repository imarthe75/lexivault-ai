import os
import io
import uuid
import logging
import json
import re # Importar regex para el número de acta
from datetime import datetime, date # Importar date
from typing import Optional # Para el tipo de retorno de parse_spanish_date

from minio import Minio
from minio.error import S3Error
from cryptography.fernet import Fernet
import pyclamd
from kafka import KafkaProducer
import pymupdf
from pymupdf4llm import to_markdown
from uuid import UUID
import spacy # Importar spaCy

# Asegúrate de que DocumentChunk y DocumentVersion estén disponibles
# Si DocumentVersion no está en models.py, asegúrate de que su ruta sea correcta
from models import DocumentChunk, DocumentVersion # Asumiendo que DocumentVersion está aquí

# --- Extractor NER específico para Actas de Nacimiento (si lo creas aparte) ---
# Si creaste un archivo ner_extractor.py con una clase BirthCertificateExtractor,
# descomenta y ajusta la siguiente línea.
# import ner_extractor

class FileProcessorService:
    def __init__(self, s3_endpoint_url, s3_access_key, s3_secret_key, s3_bucket_name, master_key, kafka_bootstrap_servers=None, kafka_topic_uploaded=None):
        logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(), format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # --- Configuración de MinIO ---
        # Extraer el host y determinar si la conexión es segura
# --- Configuración de MinIO ---
        minio_host = s3_endpoint_url
        secure_connection = False  # Initialize to a default value

        if minio_host:
            secure_connection = minio_host.startswith("https://")
            minio_host = minio_host.replace("http://", "").replace("https://", "")
        else:
            self.logger.warning("S3 endpoint URL is not configured.")
            raise ValueError("S3 endpoint URL is required.")            # You might want to raise an error here if the endpoint is mandatory:
            # raise ValueError("S3 endpoint URL is required.")

        self.minio_host = minio_host

        try:
            self.s3_client = Minio(
                minio_host,
                access_key=s3_access_key,
                secret_key=s3_secret_key,
                secure=secure_connection  # Now secure_connection is defined
            )
            self.s3_bucket_name = s3_bucket_name
            self.logger.info(f"Cliente MinIO inicializado para {s3_endpoint_url}.")
        except Exception as e:
            self.logger.error(f"Error al inicializar el cliente MinIO: {e}")
            raise

        try:
            # Verificar si el bucket existe, crearlo si no es así
            if not self.s3_client.bucket_exists(self.s3_bucket_name):
                self.s3_client.make_bucket(self.s3_bucket_name)
                self.logger.info(f"Bucket '{self.s3_bucket_name}' creado en MinIO/Ceph.")
            else:
                self.logger.info(f"Bucket '{self.s3_bucket_name}' ya existe.")
        except S3Error as e:
            self.logger.error(f"Error al verificar/crear bucket en MinIO/Ceph: {e}", exc_info=True)
            raise # Re-lanzar la excepción
        
        # ... (resto de la inicialización de Fernet, Kafka, ClamAV, spaCy) ...

        # --- Configuración de Fernet (encriptación simétrica) ---
        try:
            self.fernet_master = Fernet(master_key.encode('utf-8'))
            self.logger.info("Clave maestra de Fernet cargada correctamente.")
        except Exception as e:
            self.logger.error(f"Error al cargar la clave maestra de Fernet: {e}. Asegúrate de que SYSTEM_MASTER_KEY sea una clave Fernet válida en Base64.", exc_info=True)
            raise

        # --- Configuración de Kafka ---
        self.kafka_producer = None
        self.kafka_topic_uploaded = kafka_topic_uploaded
        self.kafka_enabled = os.getenv("ENABLE_KAFKA", "False").lower() == "true"

        if self.kafka_enabled and kafka_bootstrap_servers:
            try:
                self.kafka_producer = KafkaProducer(
                    bootstrap_servers=kafka_bootstrap_servers.split(','),
                    value_serializer=lambda v: v.encode('utf-8')
                )
                self.logger.info(f"Kafka Producer inicializado para {kafka_bootstrap_servers}")
            except Exception as e:
                self.logger.error(f"Error al inicializar Kafka Producer: {e}", exc_info=True)
                self.kafka_producer = None
                self.kafka_enabled = False
        else:
            self.logger.info("Kafka deshabilitado por configuración o parámetros.")

        # --- Configuración de ClamAV ---
        self.clamav_enabled = os.getenv("CLAMAV_ENABLED", "true").lower() == "true"
        self.clamav_client = None

        if self.clamav_enabled:
            clamav_host = os.getenv("CLAMAV_HOST", "clamav")
            clamav_port = int(os.getenv("CLAMAV_PORT", "3310"))
            try:
                self.clamav_client = pyclamd.ClamdNetworkSocket(clamav_host, clamav_port)
                self.clamav_client.ping()
                self.logger.info(f"Conexión a ClamAV establecida en {clamav_host}:{clamav_port}.")
            except pyclamd.ClamdError as e:
                self.logger.error(f"No se pudo conectar a ClamAV en {clamav_host}:{clamav_port}: {e}", exc_info=True)
                self.clamav_enabled = False
            except Exception as e:
                self.logger.error(f"Error inesperado al inicializar ClamAV: {e}", exc_info=True)
                self.clamav_enabled = False

        # --- Cargar el modelo de spaCy ---
        try:
            # Carga el modelo de español. Si no lo tienes descargado, spaCy te lo indicará.
            # Puedes descargarlo con: python -m spacy download es_core_news_lg
            self.nlp = spacy.load("es_core_news_lg") # o "es_core_news_sm", "es_core_news_lg"
            self.logger.info("Modelo de spaCy 'es_core_news_lg' cargado correctamente.")
        except OSError:
            self.logger.error("Modelo de spaCy 'es_core_news_lg' no encontrado. Descárgalo ejecutando: python -m spacy download es_core_news_lg")
            # Podrías querer lanzar un error aquí o manejarlo de otra manera.
            # raise RuntimeError("Modelo de spaCy no disponible.")

        # --- Inicializar el extractor NER específico para actas de nacimiento (si existe) ---
        # Si tienes un archivo `ner_extractor.py` con una clase `BirthCertificateExtractor`:
        # try:
        #     self.birth_cert_extractor = ner_extractor.BirthCertificateExtractor()
        #     self.logger.info("Extractor NER para Actas de Nacimiento inicializado.")
        # except NameError:
        #     self.logger.warning("No se encontró el módulo 'ner_extractor' o la clase 'BirthCertificateExtractor'. La extracción NER específica de actas no estará disponible.")
        #     self.birth_cert_extractor = None

        # Si no tienes un archivo aparte, la lógica NER estará dentro de `extract_birth_certificate_entities_spacy`

    def _generate_file_key(self):
        """Genera una clave de encriptación aleatoria para un archivo."""
        return Fernet.generate_key()

    def _encrypt_data(self, data: bytes, file_key: bytes) -> bytes:
        """Encripta datos usando una clave de archivo."""
        f = Fernet(file_key)
        return f.encrypt(data)

    def _decrypt_data(self, encrypted_data: bytes, file_key: bytes) -> bytes:
        """Desencripta datos usando una clave de archivo."""
        f = Fernet(file_key)
        return f.decrypt(encrypted_data)

    def _scan_for_viruses(self, data: bytes) -> str:
        """Escanea los datos en busca de virus usando ClamAV."""
        if not self.clamav_enabled or not self.clamav_client:
            self.logger.warning("ClamAV no está configurado o no se pudo conectar. Omitiendo escaneo de virus.")
            return "scan_skipped"

        try:
            self.logger.info("Iniciando escaneo de virus con ClamAV...")
            scan_result = self.clamav_client.scan_stream(io.BytesIO(data))

            if scan_result and list(scan_result.values())[0][0] == 'FOUND':
                virus_name = list(scan_result.values())[0][1]
                self.logger.warning(f"Virus '{virus_name}' detectado en el archivo.")
                return "infected"
            else:
                self.logger.info("Archivo escaneado: Limpio de virus.")
                return "scanned_clean"
        except pyclamd.ClamdError as e:
            self.logger.error(f"Error durante el escaneo de virus (ClamAV connection/protocol error): {e}", exc_info=True)
            return "scan_failed"
        except Exception as e:
            self.logger.error(f"Error inesperado durante el escaneo de virus: {e}", exc_info=True)
            return "scan_failed"

    # --- MÉTODOS PARA RAG (Procesamiento General de Documentos) ---

    def _generate_chunks_from_markdown(self, markdown_text, document_version_id):
        """
        Divide el texto Markdown en chunks para RAG.
        No extrae información específica de actas aquí.
        """
        chunks = []
        current_chunk_text = ""
        current_title = ""
        chunk_order = 0
        for line in markdown_text.split('\n'):
            if line.startswith('#'):
                if current_chunk_text.strip():
                    chunks.append(DocumentChunk(
                        document_version_id=document_version_id,
                        chunk_text=current_chunk_text.strip(),
                        chunk_order=chunk_order,
                        metadata={"title": current_title}
                    ))
                    chunk_order += 1
                current_title = line.strip('# ').strip()
                current_chunk_text = line + '\n'
            elif line.strip() == "" and current_chunk_text.strip() != "":
                if current_chunk_text.strip():
                    chunks.append(DocumentChunk(
                        document_version_id=document_version_id,
                        chunk_text=current_chunk_text.strip(),
                        chunk_order=chunk_order,
                        metadata={"title": current_title}
                    ))
                    chunk_order += 1
                current_chunk_text = ""
            else:
                current_chunk_text += line + '\n'

        # Agregar el último chunk si existe
        if current_chunk_text.strip():
            chunks.append(DocumentChunk(
                document_version_id=document_version_id,
                chunk_text=current_chunk_text.strip(),
                chunk_order=chunk_order,
                metadata={"title": current_title}
            ))
            chunk_order += 1
        return chunks

    def process_file_data(self, file_stream, user_id: UUID):
        """
        Procesa un archivo subido: escaneo de virus, encriptación y subida a MinIO.
        NO realiza extracción de texto ni embeddings (eso se delega a Celery).
        Devuelve la información necesaria para crear el registro DocumentVersion.
        """
        original_filename = file_stream.filename
        mimetype = file_stream.mimetype

        file_stream.seek(0)
        file_content = file_stream.read()
        actual_file_size = len(file_content)

        self.logger.info(f"Procesando archivo (fase inicial): '{original_filename}' (Tamaño: {actual_file_size} bytes, Tipo: {mimetype}) para usuario: {user_id}")

        scan_status = self._scan_for_viruses(file_content)
        if scan_status == "infected":
            self.logger.error(f"Archivo '{original_filename}' infectado, no se almacenará.")
            raise ValueError(f"Virus detectado: {scan_status}. No se pudo procesar el archivo.")

        # Generar clave y encriptar archivo
        file_key = self._generate_file_key()
        encrypted_data = self._encrypt_data(file_content, file_key)
        encryption_key_encrypted = self.fernet_master.encrypt(file_key)
        
        # Generar path único para MinIO/Ceph
        ceph_path = f"{user_id}/{uuid.uuid4()}-{original_filename}"

        # Subir archivo ENCRIPTADO a MinIO
        try:
            self.s3_client.put_object(
                self.s3_bucket_name,
                ceph_path,
                io.BytesIO(encrypted_data),
                len(encrypted_data),
                content_type="application/octet-stream"
            )
            self.logger.info(f"Archivo encriptado '{original_filename}' subido a Minio/Ceph como '{ceph_path}'.")
        except S3Error as e:
            self.logger.error(f"Error S3 al subir el archivo '{original_filename}': {e}")
            raise Exception(f"Error al subir el archivo a Minio/Ceph: {e}")

        # Devolver información para la creación del registro DocumentVersion
        # NOTA: chunks_text es None porque esto se hará asíncronamente
        return {
            "original_filename": original_filename,
            "mimetype": mimetype,
            "ceph_path": ceph_path,
            "encryption_key_encrypted": encryption_key_encrypted.decode('utf-8'),
            "size_bytes": actual_file_size,
            "chunks_text": None, 
            "scan_status": scan_status
        }

    # --- MÉTODOS PARA NER (Procesamiento Específico de Actas de Nacimiento) ---

    def extract_birth_certificate_entities_spacy(self, text: str) -> dict:
        """
        Extrae entidades de un acta de nacimiento usando un modelo spaCy.
        Retorna un diccionario con los datos extraídos.
        """
        data = {}
        doc = self.nlp(text) # Procesar el texto con spaCy

        # Mapeo de etiquetas NER de spaCy a tus campos de base de datos.
        # NOTA: Las etiquetas ('PER', 'LOC', 'DATE', etc.) dependen del modelo de spaCy.
        # Puede que necesites entrenar un modelo personalizado para actas mexicanas.

        names = []
        dates = []
        locations = []
        
        for ent in doc.ents:
            self.logger.debug(f"Entidad encontrada (spaCy NER): Texto='{ent.text}', Etiqueta='{ent.label_}'")

            if ent.label_ == "PER": # Persona (nombres, apellidos)
                names.append(ent.text)
            elif ent.label_ == "DATE": # Fecha
                dates.append(ent.text)
            elif ent.label_ == "LOC": # Ubicación
                locations.append(ent.text)
            # Añade más `elif` si tu modelo spaCy tiene etiquetas personalizadas
            # (ej. 'CERT_NUMBER', 'GENDER', etc.)

        # --- Lógica para procesar las entidades extraídas y asignarlas a los campos ---
        # Esto es CRUCIAL y requiere lógica específica para actas de nacimiento mexicanas.

        # Ejemplo básico: Asignar el primer nombre y apellido encontrados
        if names:
            # Esto asume un orden simple: Nombre Apellido. Puede necesitar refinamiento.
            data["first_name"] = names[0] if names else None
            data["last_name"] = names[1] if len(names) > 1 else None

        # Ejemplo básico: Intentar asignar la primera fecha como fecha de nacimiento
        if dates:
            # Intenta parsear la fecha. Si el formato es 'DD de MES de YYYY',
            # parse_spanish_date debería funcionar.
            data["date_of_birth"] = self.parse_spanish_date(dates[0])

        # Ejemplo básico: Intentar asignar la primera ubicación como lugar de nacimiento
        if locations:
            data["place_of_birth"] = locations[0]

        # --- Campos que probablemente requieran Regex o Etiquetado NER personalizado ---
        # Género, número de acta, nombres de padres, fecha de registro, etc.

        # Para el número de acta (ej. "Número de Acta: ABC-12345")
        num_acta_match = re.search(r"Número de Acta:\s*([\w-]+)", text, re.IGNORECASE)
        if num_acta_match:
            data["certificate_number"] = num_acta_match.group(1)

        # Para el género (ej. "Sexo: Masculino" o "Sexo: Femenino")
        gender_match = re.search(r"Sexo:\s*(Masculino|Femenino)", text, re.IGNORECASE)
        if gender_match:
            data["gender"] = gender_match.group(1)

        # Nombres de los padres (esto es más complejo y depende del formato)
        # Podrías necesitar buscar patrones específicos, o un modelo NER entrenado.
        # Ejemplo muy simplista si están en líneas separadas:
        # father_name_match = re.search(r"Padre:\s*(.*)", text, re.IGNORECASE)
        # mother_name_match = re.search(r"Madre:\s*(.*)", text, re.IGNORECASE)
        # if father_name_match and mother_name_match:
        #     data["parents_names"] = f"{father_name_match.group(1).strip()} y {mother_name_match.group(1).strip()}"
        
        # Fecha de registro (similar a fecha de nacimiento, pero buscar patrón específico)
        reg_date_match = re.search(r"Fecha de registro:\s*(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})", text, re.IGNORECASE)
        if reg_date_match:
            data["registration_date"] = self.parse_spanish_date(reg_date_match.group(1))


        # Asegurar que todos los campos esperados existan, incluso si son None
        expected_fields = [
            "first_name", "last_name", "date_of_birth", "place_of_birth",
            "gender", "parents_names", "registration_date", "certificate_number"
        ]
        for field in expected_fields:
            if field not in data:
                data[field] = None
        
        return data

    def parse_spanish_date(self, date_str: str) -> Optional[date]:
        """
        Intenta parsear una cadena de fecha en español (ej. '15 de mayo de 2020').
        Esta es una función de ayuda esencial para el NER.
        """
        if not date_str:
            return None
        
        month_map = {
            "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
            "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
        }
        
        try:
            date_str = date_str.lower().strip()
            parts = date_str.split()

            day, month_name, year = None, None, None

            # Patrones comunes para fechas en español
            if len(parts) == 5 and parts[1] == "de" and parts[3] == "de": # "DD de MES de YYYY"
                day = int(parts[0])
                month_name = parts[2]
                year = int(parts[4])
            elif len(parts) == 3 and parts[1] in month_map: # "DD MES YYYY"
                day = int(parts[0])
                month_name = parts[1]
                year = int(parts[2])
            elif len(parts) == 4 and parts[0].isdigit() and parts[2] in month_map: # "DD de MES AAAA" (ej. "15 de Mayo 2020")
                day = int(parts[0])
                month_name = parts[2]
                year = int(parts[3])
            elif len(parts) == 5 and parts[0].isdigit() and parts[2] in month_map and parts[3] == 'de': # "DD de MES de AAAA" (ej. "15 de Mayo de 2020")
                day = int(parts[0])
                month_name = parts[2]
                year = int(parts[4])

            if day and month_name and year:
                month_num = month_map.get(month_name)
                if month_num:
                    return datetime(year, month_num, day).date()
        except (ValueError, IndexError) as e:
            self.logger.warning(f"No se pudo parsear la fecha '{date_str}': {e}")
            return None
        
        self.logger.warning(f"Formato de fecha no reconocido: '{date_str}'")
        return None

    def process_birth_certificate_data(self, file_stream, user_id: UUID):
        """
        Procesa un acta de nacimiento: extrae texto, realiza NER con spaCy,
        y devuelve los datos extraídos y la información del archivo para su almacenamiento.
        Esta función se enfoca exclusivamente en el NER para actas.
        """
        original_filename = file_stream.filename
        mimetype = file_stream.mimetype

        file_stream.seek(0)
        file_content = file_stream.read()
        actual_file_size = len(file_content)

        self.logger.info(f"Procesando acta de nacimiento (NER): '{original_filename}' (Tamaño: {actual_file_size} bytes, Tipo: {mimetype}) para usuario: {user_id}")

        scan_status = self._scan_for_viruses(file_content)
        if scan_status == "infected":
            self.logger.error(f"Acta de nacimiento '{original_filename}' infectada, no se almacenará.")
            raise ValueError(f"Virus detectado: {scan_status}. No se pudo procesar el archivo.")

        # --- Extracción de Texto del PDF ---
        markdown_text = ""
        try:
            doc = pymupdf.open(stream=file_content, filetype="pdf")
            markdown_text = to_markdown(doc)
            self.logger.info(f"Texto extraído del PDF para NER (primeros 500 chars): {markdown_text[:500]}...")
        except Exception as e:
            self.logger.error(f"Error al procesar el PDF con PyMuPDF para NER: {e}")
            raise Exception("No se pudo extraer texto del archivo PDF.")

        # --- Extracción de Entidades con spaCy ---
        extracted_data = {}
        if markdown_text:
            # Llama a la función de extracción NER usando spaCy
            extracted_data = self.extract_birth_certificate_entities_spacy(markdown_text)
            self.logger.info(f"Datos extraídos con spaCy para acta de nacimiento: {extracted_data}")
        else:
            self.logger.warning("No se pudo extraer texto del PDF, no se realizará extracción NER.")

        # Generar clave para el archivo y encriptarlo
        file_key = self._generate_file_key()
        encrypted_data = self._encrypt_data(file_content, file_key)
        encryption_key_encrypted = self.fernet_master.encrypt(file_key)
        
        # Generar path único para MinIO/Ceph
        ceph_path = f"{user_id}/{uuid.uuid4()}-{original_filename}"

        # --- Subir el archivo ENCRIPTADO a MinIO ---
        try:
            self.s3_client.put_object(
                self.s3_bucket_name,
                ceph_path,
                io.BytesIO(encrypted_data),
                len(encrypted_data),
                content_type="application/octet-stream" # Tipo genérico para datos binarios encriptados
            )
            self.logger.info(f"Archivo encriptado '{original_filename}' subido a Minio/Ceph como '{ceph_path}'.")
        except S3Error as e:
            self.logger.error(f"Error S3 al subir el archivo '{original_filename}' para NER: {e}")
            raise Exception(f"Error al subir el archivo a Minio/Ceph: {e}")

        # Devolver toda la información necesaria para la creación del registro en la base de datos
        return {
            "original_filename": original_filename,
            "mimetype": mimetype,
            "ceph_path": ceph_path,
            "encryption_key_encrypted": encryption_key_encrypted.decode('utf-8'),
            "size_bytes": actual_file_size,
            "extracted_data": extracted_data, # Aquí van los datos del NER
            "scan_status": scan_status
        }

    def generate_chunks_and_embeddings_for_celery(self, session, document_version_id, markdown_text=None):
        """
        Método llamado por Celery para realizar el trabajo pesado:
        1. Recuperar archivo de MinIO y desencriptar (si markdown_text es None).
        2. Extraer texto (si markdown_text es None).
        3. Generar chunks.
        4. Generar embeddings (llamando a Ollama).
        5. Guardar chunks y embeddings en DB.
        """
        self.logger.info(f"Iniciando procesamiento asíncrono (Celery) para document_version_id: {document_version_id}")
        
        # Importar aquí para evitar ciclos, o asegurar que tasks.py pase la función de embedding
        # Para simplificar, asumiremos que tasks.py maneja la llamada a Ollama o lo hacemos aquí si tenemos acceso.
        # Dado que tasks.py tiene `get_ollama_embedding`, lo ideal es que tasks.py pase una función de callback o
        # que movamos `get_ollama_embedding` a este servicio o a un módulo de utilidades común.
        # Por ahora, importaremos la función de tasks (cuidado con ciclos) o duplicaremos la lógica simple de request.
        # MEJOR OPCIÓN: Mover `get_ollama_embedding` a un `utils.py` o definirlo aquí como método estático/privado.
        
        from llm_client import get_ollama_embedding

        # --- Importar extractor NER y modelo de atributos ---
        from ner_extractor import BirthCertificateExtractor
        from models import DocumentAttribute

        try:
            document_version = session.get(DocumentVersion, UUID(document_version_id))
            if not document_version:
                self.logger.error(f"DocumentVersion {document_version_id} no encontrada.")
                return False

            # 1. y 2. Si no hay markdown_text, obtenerlo del archivo
            if not markdown_text:
                self.logger.info("No se proporcionó markdown_text, extrayendo del archivo original...")
                try:
                    decrypted_data = self.retrieve_and_decrypt_file(document_version)
                    
                    # Detectar tipo de archivo y extraer
                    if document_version.mimetype == 'application/pdf' or document_version.original_filename.lower().endswith('.pdf'):
                        doc = pymupdf.open(stream=decrypted_data, filetype="pdf")
                        markdown_text = to_markdown(doc)
                    elif document_version.mimetype in ['image/png', 'image/jpeg', 'image/jpg', 'image/tiff'] or \
                         document_version.original_filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff')):
                        import pytesseract
                        from PIL import Image
                        
                        self.logger.info(f"Detectada imagen ({document_version.mimetype}), iniciando OCR con Tesseract...")
                        image = Image.open(io.BytesIO(decrypted_data))
                        # Usar español e inglés como idiomas
                        markdown_text = pytesseract.image_to_string(image, lang='spa+eng')
                        self.logger.info(f"OCR completado. Longitud del texto extraído: {len(markdown_text)} caracteres.")
                    else:
                        # Fallback para texto plano u otros
                        markdown_text = decrypted_data.decode('utf-8', errors='ignore')
                except Exception as e:
                    self.logger.error(f"Error al extraer texto del archivo: {e}")
                    return False

            if not markdown_text:
                self.logger.warning("El texto extraído está vacío.")
                return False

            # --- NUEVO: Extracción NER para Actas de Nacimiento ---
            # Detectar si es un acta de nacimiento (heurística simple)
            is_birth_certificate = "ACTA DE NACIMIENTO" in markdown_text.upper() or "ESTADOS UNIDOS MEXICANOS" in markdown_text.upper()
            
            if is_birth_certificate:
                self.logger.info(f"Documento {document_version_id} identificado como posible Acta de Nacimiento. Ejecutando NER...")
                try:
                    extractor = BirthCertificateExtractor()
                    extracted_data = extractor.extract_entities(markdown_text)
                    
                    # Actualizar metadatos del archivo en la base de datos (JSONB)
                    current_metadata = document_version.file_metadata or {}
                    current_metadata.update(extracted_data)
                    document_version.file_metadata = current_metadata
                    session.add(document_version)

                    # --- NUEVO: Guardar en tabla DocumentAttribute ---
                    # Limpiar atributos anteriores si existen para esta versión (re-procesamiento)
                    session.query(DocumentAttribute).filter_by(document_version_id=document_version.id).delete()
                    
                    for key, value in extracted_data.items():
                        if value:
                            # Si es una lista (ej. padres), guardamos cada uno o serializamos
                            if isinstance(value, list):
                                for i, item in enumerate(value):
                                    attr = DocumentAttribute(
                                        document_version_id=document_version.id,
                                        key=f"{key}_{i+1}", # ej. parents_1
                                        value=str(item), # Guardamos como string/JSON
                                        source='ner_regex_hybrid'
                                    )
                                    session.add(attr)
                            else:
                                attr = DocumentAttribute(
                                    document_version_id=document_version.id,
                                    key=key,
                                    value=str(value),
                                    source='ner_regex_hybrid'
                                )
                                session.add(attr)
                    
                    self.logger.info(f"Datos NER extraídos y guardados en DocumentAttribute para {document_version_id}")
                except Exception as e:
                    self.logger.error(f"Error durante la extracción NER para {document_version_id}: {e}", exc_info=True)
                    # No abortamos el proceso principal si falla el NER
            
            # 3. Generar chunks
            chunks = self._generate_chunks_from_markdown(markdown_text, UUID(document_version_id))
            self.logger.info(f"Se generaron {len(chunks)} chunks.")

            # 4. Generar embeddings para cada chunk
            OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
            
            for chunk in chunks:
                try:
                    embedding = get_ollama_embedding(chunk.chunk_text, OLLAMA_EMBEDDING_MODEL)
                    chunk.chunk_embedding = embedding
                except Exception as e:
                    self.logger.error(f"Error generando embedding para chunk {chunk.chunk_order}: {e}")
                    # Podríamos decidir abortar o continuar con los que funcionen.
                    # Abortamos para consistencia.
                    raise e

            # 5. Guardar en DB
            session.bulk_save_objects(chunks)
            
            # Actualizar estado
            document_version.processed_status = 'indexed'
            document_version.last_processed_at = datetime.now()
            session.add(document_version)
            session.commit()
            
            self.logger.info(f"Procesamiento completado exitosamente para {document_version_id}")
            return True

        except Exception as e:
            session.rollback()
            self.logger.error(f"Error en generate_chunks_and_embeddings_for_celery: {e}", exc_info=True)
            return False

    def retrieve_and_decrypt_file(self, document_version_entry):
        """
        Recupera un archivo de MinIO y lo desencripta usando la clave maestra.
        Este método es genérico y funciona tanto para RAG como para NER.
        """
        self.logger.info(f"Recuperando y desencriptando archivo: '{document_version_entry.original_filename}' (MinIO path: {document_version_entry.ceph_path})")
        try:
            encryption_key_encrypted = document_version_entry.encryption_key_encrypted
            if not isinstance(encryption_key_encrypted, bytes):
                encryption_key_encrypted = encryption_key_encrypted.encode('utf-8')
            
            file_key = self.fernet_master.decrypt(encryption_key_encrypted)
            
            response = self.s3_client.get_object(self.s3_bucket_name, document_version_entry.ceph_path)
            encrypted_data = response.read()
            response.close()
            response.release_conn()
            self.logger.info(f"Archivo '{document_version_entry.ceph_path}' descargado de MinIO/Ceph.")
            
            decrypted_data = self._decrypt_data(encrypted_data, file_key)
            self.logger.info(f"Archivo '{document_version_entry.original_filename}' desencriptado exitosamente.")
            return decrypted_data
        except S3Error as e:
            self.logger.error(f"Error S3 al recuperar o desencriptar el archivo: {e}")
            raise ValueError(f"Error al recuperar el archivo de almacenamiento: {e}")
        except Exception as e:
            self.logger.error(f"Error al desencriptar o procesar el archivo: {e}", exc_info=True)
            raise ValueError(f"Error al procesar el archivo: {e}")

    def delete_file_from_minio(self, ceph_path: str):
        """Elimina un archivo de MinIO/Ceph."""
        self.logger.info(f"Eliminando archivo: '{ceph_path}' de MinIO/Ceph.")
        try:
            self.s3_client.remove_object(self.s3_bucket_name, ceph_path)
            self.logger.info(f"Archivo '{ceph_path}' eliminado de MinIO/Ceph.")
        except S3Error as e:
            self.logger.error(f"Error S3 al eliminar el archivo '{ceph_path}' de MinIO/Ceph: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error inesperado al eliminar el archivo '{ceph_path}' de Minio/Ceph: {e}", exc_info=True)
            raise