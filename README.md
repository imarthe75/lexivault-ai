# 🛡️ LexiVault AI: Intelligent Document Vault & Automation

> **Bóveda documental de grado empresarial diseñada para la era de la IA Agéntica**

## 🎯 Overview

LexiVault AI es un ecosistema de gestión documental integrado con CASMARTS que utiliza:

- **Docling**: Reconstrucción estructural de documentos (PDFs, imágenes, Office)
- **LangGraph**: Orquestación de flujos de trabajo inteligentes
- **HashiCorp Vault**: Gestión segura de secretos y cifrado dinámico
- **Valkey (Redis)**: Almacenamiento en caché y persistencia de estado (Checkpointing de LangGraph)
- **MinIO/Ceph**: Almacenamiento S3 soberano de documentos cifrados
- **NVIDIA NIM**: Embeddings y generación de texto local

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│              CASMARTS Core Hub (compartido)              │
├──────────────┬──────────────┬──────────────┐─────────────┤
│ Postgres     │ Valkey       │ Redpanda     │ SeaweedFS   │
│ (5432)       │ (6379)       │ (9092)       │ (9333)      │
└──────────────┴──────────────┴──────────────┴─────────────┘
          ↑                ↑                      ↑
          │                │                      │
┌─────────────────────────────────────────────────────────┐
│            LexiVault AI (este proyecto)                  │
├─────────────────────────────────────────────────────────┤
│  Frontend (React/Vite) → Backend (Flask) → Celery       │
│              ↓                    ↓                       │
│  Valkey Checkpointing    File Processing & Embeddings   │
└─────────────────────────────────────────────────────────┘
```

## 📋 Requisitos Previos

1. **CASMARTS Core levantado**: Necesitas que `core-casmarts/` esté funcionando (Postgres, Valkey, Redpanda, etc.)
2. **Docker & Docker Compose**: Instalados y funcionando
3. **Red aura-network**: DEBE existir (creada por core-casmarts)

## 🚀 Quick Start

### 1. Clonar y Configurar Variables de Entorno

```bash
cd lexivault-ai

# Crear archivo .env desde el template
cp .env.example .env

# Editar .env con tus valores reales
vi .env
```

### 2. Verificar Conectividad a CASMARTS Core

```bash
# Verificar que la red aura-network existe
docker network ls | grep aura-network

# Si no existe, crearla (normalmente la crea core-casmarts)
docker network create aura-network

# Verificar conectividad a Postgres
docker run --rm --network aura-network postgres:18-alpine \
  psql -h casmarts-core-db-primary -U admin -d lexivault -c "SELECT 1"
```

### 3. Levantar LexiVault

```bash
# Construir imágenes y levantar servicios
docker compose up -d

# Verificar logs
docker compose logs -f

# Verificar salud de contenedores
docker compose ps
```

### 4. Verificar que Todo Funciona

```bash
# Health check del backend
curl http://localhost:5000/health

# Health check del frontend
curl http://localhost:8501
```

## 📁 Estructura del Proyecto

```
lexivault-ai/
├── backend/                   # Flask API Backend
│   ├── app.py                 # Aplicación principal (reemplazado)
│   ├── app_old_backup.py      # Backup del archivo viejo
│   ├── requirements.txt        # Dependencias Python (actualizado)
│   ├── database.py            # Configuración de SQLAlchemy
│   ├── models.py              # Modelos de datos (SQLAlchemy)
│   ├── file_processor_service.py  # Servicio de procesamiento de archivos
│   ├── vault_client.py        # Cliente de HashiCorp Vault
│   ├── llm_client.py          # Cliente para Ollama/NVIDIA NIM
│   ├── tasks.py               # Tareas Celery asincrónicas
│   └── user_service.py        # Gestión de usuarios
│
├── frontend-react/            # React + Vite + TailwindCSS
│   ├── src/                   # Código fuente
│   ├── package.json           # Dependencias Node
│   ├── Dockerfile             # Build multi-stage
│   ├── nginx.conf             # Configuración de servicio
│   └── vite.config.js         # Configuración de Vite
│
├── Dockerfile_Flask           # Docker para Flask backend
├── Dockerfile_celery          # Docker para worker Celery
├── docker-compose.yml         # Orquestación de contenedores (actualizado)
├── .env                       # Variables de entorno (NO commitear)
├── .env.example               # Template de variables (NUEVO - seguro)
├── .gitignore                 # Archivos a ignorar en Git
└── README.md                  # Este archivo
```

## 🔐 Configuración de Seguridad

### Variables de Entorno Críticas

Estas **DEBEN** cambiar en producción:

```env
SYSTEM_MASTER_KEY=change_me_fernet_key  # Clave maestra para Fernet (encriptación)
DOCUMENT_ENCRYPTION_KEY=change_me       # Clave para encriptación de documentos
JWT_SECRET_KEY=change_me_long_secret    # Clave para firmar tokens JWT
VAULT_DEV_ROOT_TOKEN_ID=change_me       # Token de autenticación de Vault
```

### Crear una Clave Fernet Válida

```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # Copiar este valor a SYSTEM_MASTER_KEY
```

### .gitignore

Asegúrate de que estos archivos NO se commitean:

```
.env                    # Variables reales (contiene secretos)
backend/__pycache__/
backend/*.pyc
frontend-react/node_modules/
.DS_Store
```

## 🏃 Desarrollo Local

### Backend

```bash
cd backend

# Crear virtual environment
python -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Descargar modelo de spaCy
python -m spacy download es_core_news_lg

# Ejecutar en desarrollo
export FLASK_DEBUG=1
flask run

# O con gunicorn
gunicorn --bind 0.0.0.0:5000 app:app --reload
```

### Frontend

```bash
cd frontend-react

# Instalar dependencias
npm install

# Desarrollo (hot reload)
npm run dev

# Build para producción
npm run build
```

### Celery Worker

```bash
cd backend

# En otra terminal
celery -A tasks.celery_app worker --loglevel=info

# Con autoreload en desarrollo
celery -A tasks.celery_app worker --loglevel=info --autoscale=4,1
```

## 🧪 Pruebas

```bash
# Test de conexión a base de datos
curl http://localhost:5000/vault/test-db

# Health check completo
curl http://localhost:5000/health

# Acceso frontend
open http://localhost:8501
```

## 📚 Endpoints Principales

### Autenticación
- `POST /auth/register` - Registrar usuario
- `POST /auth/login` - Login y obtener JWT token

### Documentos
- `GET /documents` - Listar documentos del usuario
- `POST /documents` - Subir nuevo documento
- `GET /documents/<id>` - Obtener detalles del documento

### RAG/Chat
- `POST /chat` - Consultar documentos con RAG

### Sistema
- `GET /` - Health check básico
- `GET /health` - Health check detallado
- `GET /vault/test-db` - Test de conexión a BD

## 🔄 Flujos de Trabajo (TODO)

1. **Upload → Processing**: El usuario sube un documento
   - Flask procesa el archivo
   - Celery genera embeddings asincronamente
   - Valkey checkpointea el estado del LangGraph

2. **Chat/RAG**: Usuario consulta documentos
   - Query se busca en pgvector (semantic search)
   - LangGraph orquesta la llamada al LLM
   - Respuesta se cachea en Valkey

3. **Extracción de Datos**: Trámites automáticos
   - LangGraph enruta a extractor específico
   - NER extrae entidades
   - Resultados se guardan estructurados

## 🐛 Troubleshooting

### Error: "redis connection refused"
```bash
# Verificar que Valkey/Redis de core-casmarts está corriendo
docker ps | grep casmarts-core-cache
```

### Error: "database does not exist"
```bash
# Crear la base de datos lexivault en Postgres
docker exec casmarts-core-db-primary psql -U admin -c "CREATE DATABASE lexivault;"
```

### Error: "Cannot connect to Docker daemon"
```bash
# Asegurar que Docker está corriendo
sudo systemctl start docker
sudo usermod -aG docker $USER
```

### Logs de Celery muy grandes
```bash
# Cambiar log level en docker-compose.yml
environment:
  - LOG_LEVEL=WARNING
```

## 📖 Documentación Relacionada

- [CASMARTS Architecture](../README.md)
- [Resident Agent Genesis](../resident_agent_genesis.md)
- [Contexto Residente](../contexto_residente.md)

## 🛠️ Stack Tecnológico

| Componente | Versión | Rol |
|-----------|---------|-----|
| **Python** | 3.10+ | Backend runtime |
| **Flask** | 3.0 | Web framework |
| **React** | 18.3 | Frontend |
| **PostgreSQL** | 18.3 | Base datos relacional + pgvector |
| **Valkey** | Latest | Cache + Checkpointing |
| **Celery** | 5.3 | Task queue |
| **Docling** | - | Document parsing |
| **LangGraph** | - | Orchestration |

## 🚧 Roadmap

- [ ] Implementar endpoints de autenticación
- [ ] Integrar HashiCorp Vault
- [ ] Implementar procesamiento de archivos
- [ ] Integrar LangGraph para orquestación
- [ ] Implementar RAG con pgvector
- [ ] Dashboard de administración
- [ ] Soporte para múltiples usuarios
- [ ] WebSockets para actualizaciones en tiempo real

## 📝 Licencia

Ver [LICENSE](LICENSE)

## 👥 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/amazing`)
3. Commit cambios (`git commit -am 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing`)
5. Abre un Pull Request

---

**Última actualización**: May 9, 2026
**Status**: 🚧 En desarrollo

