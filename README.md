# 🛡️ LexiVault AI: Intelligent Document Vault & Automation

<p align="center">
<img src="docs/lexivault-logo.png" alt="LexiVault AI Logo" width="500px">
</p>

**LexiVault AI** es un ecosistema de gestión documental de grado empresarial diseñado para la era de la IA Agéntica. Utiliza **Docling** para la reconstrucción estructural de documentos y **LangGraph** para orquestar flujos de trabajo inteligentes. A diferencia de las soluciones RAG tradicionales, LexiVault garantiza la soberanía de los datos, seguridad gestionada por secretos dinámicos y persistencia de estado avanzada.

---

## 🎯 Objetivos del Proyecto

* **Comprensión Estructural Profunda:** Uso de **Docling** para entender tablas, jerarquías y layouts complejos, transformando archivos binarios en Markdown semántico.
* **Automatización Agéntica (Camino Dual):** Un router inteligente basado en **LangGraph** que distingue entre consultas conversacionales (**Chatbot**) y procesos de extracción de datos (**Trámites**).
* **Privacidad Soberana:** Procesamiento 100% local mediante **Ollama (Qwen 3.5)**.
* **Seguridad de Grado Bancario:** Gestión de identidades y secretos mediante **HashiCorp Vault** y cifrado **Fernet** en el almacenamiento.

---

## 🏗️ Arquitectura y Componentes Clave

| Componente | Tecnología | Función Crítica en LexiVault |
| --- | --- | --- |
| **Orquestador** | **LangGraph** | Gestiona ciclos de decisión y lógica de agentes (Router/RAG/Extractor). |
| **Persistencia de Estado** | **Valkey** | Actúa como **Checkpointer** de LangGraph; guarda el estado exacto de cada trámite y gestiona colas de Celery. |
| **Gestor de Secretos** | **HashiCorp Vault** | Inyecta dinámicamente claves de cifrado, tokens y credenciales de DB en tiempo de ejecución. |
| **Parser Motor** | **Docling** | Análisis de maquetación visual para convertir PDFs e imágenes en datos estructurados. |
| **Cerebro (LLM)** | **Ollama** | Ejecución local de Qwen 3.5 para razonamiento y extracción sin salida a internet. |
| **Bóveda Física** | **MinIO** | Almacenamiento S3 de documentos cifrados con soporte para versionado. |

---

## 🔐 Seguridad y Gestión de Secretos

LexiVault AI implementa un modelo de **Confianza Cero (Zero Trust)**:

* **HashiCorp Vault Integrado:** No se almacenan credenciales en archivos `.env`. El sistema autentica cada microservicio con Vault para obtener secretos dinámicos.
* **Cifrado Dinámico:** Los documentos se cifran en tránsito y en reposo (AES-128 via Fernet) con llaves gestionadas y rotadas por Vault.
* **Firma Digital (Roadmap):** Próxima implementación de firmas electrónicas para garantizar el no repudio de los documentos procesados.

---

## 🧠 El Rol de Valkey: Más que un Caché

Valkey es el sistema nervioso del proyecto, encargado de:

1. **Memory Checkpointing:** Permite que los agentes de LangGraph "recuerden" en qué paso de un trámite largo se encuentran, incluso tras un reinicio del sistema.
2. **Escalabilidad Asíncrona:** Broker de alto rendimiento para que los Workers procesen el análisis de layout de Docling de forma paralela.
3. **Context Management:** Mantiene la ventana de contexto de las conversaciones de chat para una respuesta inmediata.

---

## 📄 Formatos y Análisis de Layout Integral

Gracias a modelos de visión artificial, procesamos documentos preservando su semántica:

* **Documentos:** `.pdf` (tablas, encabezados), `.docx`, `.xlsx` (preservación de celdas), `.pptx`.
* **Imágenes (OCR Estructural):** `.png`, `.jpg`, `.tiff`. Detecta firmas y sellos.
* **E-books y Estructurados:** `.epub`, `.json`, `.html`, `.md`.

---

## 🔄 Flujo de Trabajo (Pipeline)

1. **Ingesta:** El archivo se recibe, se escanea y se cifra con llaves obtenidas de **Vault**.
2. **Estructuración:** **Docling** reconstruye el documento en Markdown.
3. **Enrutamiento:** **LangGraph** consulta a **Valkey** el estado actual y decide:
* **Ruta RAG:** Búsqueda en `pgvector` para responder dudas.
* **Ruta Extracción:** Mapeo de datos a esquemas **Pydantic** para trámites automáticos.



---

## 🛠️ Instalación

1. **Configurar Vault:** Asegúrate de que tu instancia de HashiCorp Vault sea accesible y los roles de política estén creados.
2. **Levantar Infraestructura:**
```bash
docker compose up -d

```


3. **Sincronizar IA:**
```bash
docker exec -it lexivault-ai-brain ollama pull qwen2.5:7b
