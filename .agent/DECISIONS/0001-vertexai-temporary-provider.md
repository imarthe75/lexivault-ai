# DECISION 0001: Vertex AI como proveedor temporal de parsing

## Fecha: 2026-05-10

## Contexto
LexiVault AI requiere un motor de extracción documental para procesar archivos y avanzar con el flujo de trabajo. El ecosistema CASMARTS define a Docling como el proveedor ideal de largo plazo, pero Docling aún no está completamente desplegado o validado para esta instancia.

## Decisión
- Usar **Vertex AI** como proveedor activo de extracción y parsing documental en la fase actual.
- Mantener la abstracción de proveedor en `backend/llm_service.py` y `backend/document_service.py` para permitir una migración limpia a **Docling** cuando esté disponible.
- Documentar claramente esta elección en `.agent/DECISIONS/` y en los archivos de estado de la memoria residente.

## Consecuencias
- ✅ Arranque rápido de LexiVault AI con un proveedor de extracción estable.
- ✅ Reducción del bloqueo tecnológico por dependencia directa de Docling.
- ⚠️ Requiere control de credenciales de GCP (`GOOGLE_APPLICATION_CREDENTIALS`).
- ⚠️ Debe preservarse la ruta de migración a Docling sin reescribir la API.
- ✅ El sistema queda preparado para soportar tanto Vertex AI como Docling en el mismo modelo de despliegue.

## Recomendaciones
- Implementar tests de integración que verifiquen el intercambio de proveedor.
- Mantener los adaptadores de Docling documentados y listos en el repositorio.
- En la próxima fase, priorizar la conexión de HashiCorp Vault y la generación de embeddings.
