import os
import logging
import requests
import json

# --- Logger Configuration ---
logger = logging.getLogger(__name__)

# --- Ollama Configuration ---
OLLAMA_API_BASE_URL = os.getenv("OLLAMA_API_BASE_URL", "http://ollama:11434")
OLLAMA_EMBEDDING_TIMEOUT = int(os.getenv("OLLAMA_EMBEDDING_TIMEOUT", "1200"))
OLLAMA_GENERATION_TIMEOUT = int(os.getenv("OLLAMA_GENERATION_TIMEOUT", "1200"))

def get_ollama_embedding(text: str, model_name: str):
    """Generates an embedding for the given text using the Ollama API."""
    headers = {'Content-Type': 'application/json'}
    data = {
        "model": model_name,
        "prompt": text
    }
    try:
        response = requests.post(f"{OLLAMA_API_BASE_URL}/api/embeddings", headers=headers, json=data, timeout=OLLAMA_EMBEDDING_TIMEOUT)
        response.raise_for_status()
        response_json = response.json()
        embedding = response_json.get('embedding')
        if not embedding or len(embedding) != 768:
            error_msg = f"Embedding de Ollama no válido: se esperaban 768 dimensiones, se obtuvieron {len(embedding) if embedding else 0}."
            logger.error(error_msg)
            raise ValueError(error_msg)
        return embedding
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al obtener embedding de Ollama: {e}")
        raise
    except (KeyError, TypeError) as e:
        error_msg = f"Respuesta de Ollama mal formada. El campo 'embedding' no se encontró o tiene un formato incorrecto: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg)

def get_ollama_generation(prompt: str, model_name: str, json_mode: bool = False):
    """Generates a response for the given prompt using the Ollama API."""
    headers = {'Content-Type': 'application/json'}
    data = {
        "model": model_name,
        "prompt": prompt,
        "stream": False, # We want the full response at once
        "format": "json" if json_mode else None
    }
    try:
        response = requests.post(f"{OLLAMA_API_BASE_URL}/api/generate", headers=headers, json=data, timeout=OLLAMA_GENERATION_TIMEOUT)
        response.raise_for_status()
        return response.json()['response']
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al obtener generación de Ollama: {e}")
        raise
