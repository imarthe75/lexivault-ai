# 🛡️ LexiVault AI - Agent Memory

## 📋 Project Overview

**LexiVault AI** es un satélite del ecosistema CASMARTS que proporciona:

- **Bóveda Documental Inteligente**: Gestión de documentos con soberanía de datos local
- **Procesamiento de Documentos**: Conversión de PDFs e imágenes a datos estructurados
- **RAG/Chat sobre Documentos**: Consultas en lenguaje natural sobre la bóveda
- **Orquestación Agéntica**: LangGraph para flujos de trabajo complejos

## 🏗️ Integración con CASMARTS

LexiVault utiliza servicios compartidos del Hub core-casmarts:

```
┌─────────────────────────────────────┐
│   LexiVault AI (Satélite)           │
├─────────────────────────────────────┤
│ - Flask Backend (5000)              │
│ - React Frontend (8501)             │
│ - Celery Workers                    │
└────────────┬────────────────────────┘
             │
             ├─→ casmarts-core-db-primary (Postgres 5432)
             ├─→ casmarts-core-cache (Valkey 6379)
             ├─→ casmarts-core-redpanda (Kafka 9092)
             └─→ casmarts-core-storage (MinIO 9333)
```

## 🔐 Servicios Compartidos Requeridos

| Servicio | Puerto | Rol |
|----------|--------|-----|
| **Postgres** | 5432 | Base de datos relacional + pgvector |
| **Valkey** | 6379 | Cache + Checkpointing de LangGraph |
| **Redpanda** | 9092 | Event streaming (Kafka) |
| **SeaweedFS** | 9333 | Almacenamiento S3 de documentos |

## 📝 Estado Actual

- ✅ Vertex AI activo como motor de extracción documental
- ✅ JWT Authentication implementada
- ✅ Arquitectura de proveedor de parsing abstraída para permitir Docling en el futuro
- ✅ Docker Compose, `.env.example` y credenciales GCP actualizados

## 📝 Contexto de Migración

LexiVault AI opera actualmente con **Vertex AI** para el procesamiento documental en esta fase. La migración a **Docling** se mantiene como objetivo estratégico; el código está diseñado para intercambiar fácilmente el proveedor documental mediante una capa de abstracción definida en `backend/llm_service.py` y `backend/document_service.py`.

## 🚀 Inicialización Rápida

```bash
cd lexivault-ai

# Ejecutar setup automático
./setup.sh

# Verificar salud
curl http://localhost:5000/health
curl http://localhost:8501
```

##  Configuración Crítica

### Variables de Entorno Obligatorias

```env
# Estos deben cambiar en producción
SYSTEM_MASTER_KEY=<clave_fernet_aquí>
JWT_SECRET_KEY=<clave_jwt_aquí>
VAULT_DEV_ROOT_TOKEN_ID=<token_vault_aquí>
DOCUMENT_ENCRYPTION_KEY=<clave_doc_aquí>
```

### Generar Clave Fernet

```bash
docker run --rm python:3.10 python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## 📊 Endpoints Base

```
GET  /               → Health check
GET  /health         → Health detallado
GET  /vault/test-db  → Test conexión BD

POST /auth/register  → Registrar usuario
POST /auth/login     → Login JWT

GET  /documents      → Listar documentos
POST /documents      → Subir documento
GET  /documents/<id> → Ver documento

POST /chat           → Consultar con RAG
```

## 🐛 Troubleshooting Común

### "Cannot connect to database"
```bash
# Verificar que postgres de core-casmarts está corriendo
docker ps | grep casmarts-core-db

# Verificar red
docker network ls | grep aura-network
```

### "Valkey connection refused"
```bash
# Verificar redis de core-casmarts
docker ps | grep casmarts-core-cache
```

### "Frontend no carga"
```bash
# Revisar logs del frontend
docker compose logs frontend

# Verificar que nginx puede llegar al backend
docker exec lexivault-frontend curl http://flask_backend:5000/
```

## 📚 Archivos Importantes

- `backend/app.py` - Aplicación Flask (ACTUALIZADO)
- `backend/requirements.txt` - Dependencias (ACTUALIZADO)
- `docker-compose.yml` - Orquestación (ACTUALIZADO)
- `.env.example` - Template seguro (NUEVO)
- `setup.sh` - Script de setup (NUEVO)
- `README.md` - Documentación (ACTUALIZADO)

## 🔗 Relación con CASMARTS

LexiVault es un **Satélite** del Hub core-casmarts. Siguiendo la arquitectura Hub & Spoke:

- **Hereda**: Identidad (SSO/Keycloak), persistencia (Postgres), cache (Valkey)
- **Contribuye**: Procesamiento documental, RAG local, orquestación de trámites
- **Independencia**: Puede operar con su propio docker-compose mientras tenga acceso a aura-network

## 🎯 Próximos Pasos

1. Implementar autenticación con JWT
2. Conectar con HashiCorp Vault
3. Integrar Docling para parsing
4. Agregar generación de embeddings
5. Implementar chat RAG
6. Dashboard de administración

## 📞 Referencias

- `../resident_agent_genesis.md` - Protocolo de operación
- `../contexto_residente.md` - Contexto del ecosistema
- `../core-casmarts/README.md` - Hub central
