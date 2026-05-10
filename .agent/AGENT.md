# 🛡️ AGENT.md: Reglas de Operación - LexiVault AI

## 1. Identidad del Servicio

- **Nombre**: LexiVault AI
- **Tipo**: Satélite del Hub core-casmarts
- **Puerto**: 5000 (Backend), 8501 (Frontend)
- **Red**: aura-network (compartida con CASMARTS)
- **Dependencias**: Postgres, Valkey, Redpanda, SeaweedFS

## 2. Principios Operacionales

### 2.1 Soberanía de Datos
- ✅ Todos los documentos residen en MinIO/Ceph (casmarts-core-storage)
- ✅ Encriptación Fernet en tránsito y en reposo
- ✅ Sin dependencias de APIs externas para almacenamiento primario
- ✅ Datos recuperables sin CASMARTS (excepto BD)

### 2.2 Seguridad
- ✅ JWT para autenticación de usuarios
- ✅ HashiCorp Vault para gestión de secretos
- ✅ ClamAV para análisis antivirus de uploads
- ✅ Validación de tipos MIME
- ✅ Rate limiting en endpoints

### 2.3 Performance
- ✅ Valkey para caching de queries frecuentes
- ✅ Celery para procesamiento asincrónico
- ✅ pgvector para búsqueda semántica rápida
- ✅ Compresión gzip en respuestas

## 3. Stack Tecnológico Obligatorio

```
Backend:        Flask 3.0 + Gunicorn
Frontend:       React 18 + Vite
Database:       PostgreSQL 18.3 + pgvector
Cache:          Valkey (Agent Memory Server)
Message Queue:  Redpanda/Kafka
Task Queue:     Celery 5.3
Storage:        MinIO/Ceph S3
Security:       HashiCorp Vault, ClamAV, Fernet
Parsing:        Vertex AI (activo), Docling (ready-to-migrate)
```

## 4. Estándares de Codificación

### 4.1 Python Backend
- ✅ PEP 8 compliance
- ✅ Type hints en todas las funciones
- ✅ Logging con nivel INFO/WARNING/ERROR
- ✅ Manejo de excepciones explícito
- ✅ Docstrings en español para métodos críticos

### 4.2 React Frontend
- ✅ Functional components + hooks
- ✅ TailwindCSS para estilos
- ✅ Axios para HTTP requests
- ✅ OIDC para autenticación
- ✅ Lazy loading de rutas

### 4.3 Estructura de Directorios
```
lexivault-ai/
├── backend/
│   ├── app.py                 # Aplicación principal
│   ├── auth_service.py        # Autenticación JWT
│   ├── document_service.py    # Upload y parsing documental
│   ├── llm_service.py         # Abstracción de proveedor de LLM
│   ├── requirements.txt       # Dependencias pinned
│   └── tasks.py               # Tareas Celery
│
├── frontend-react/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── utils/
│   └── package.json           # Dependencias pinned
│
├── docker-compose.yml          # Orquestación
├── .env.example               # Template seguro
├── setup.sh                   # Inicialización
└── README.md                  # Documentación
```

## 5. Requisitos de Funcionalidad

### 5.1 Backend
- [x] Autenticación JWT funcional
- [x] CRUD de documentos
- [x] Procesamiento de archivos (upload/parsing) con Vertex AI
- [ ] Generación de embeddings con Ollama
- [ ] RAG con pgvector
- [ ] Integración con Vault
- [ ] Health checks
- [ ] Logging centralizado

### 5.2 Frontend
- [ ] Login/Register
- [ ] Dashboard de documentos
- [ ] Upload de archivos
- [ ] Chat interface
- [ ] Búsqueda de documentos
- [ ] Gestión de perfiles

### 5.3 DevOps
- [ ] Multi-stage Docker builds
- [ ] docker-compose.yml con healthchecks
- [ ] Variables de entorno securizadas
- [ ] Backups automáticos de BD
- [ ] Logs centralizados

## 6. Interfaces Requeridas

### 6.1 Con core-casmarts
```
POST   /auth-request         → Keycloak para SSO (futuro)
GET    postgresql://...      → Lectura/escritura de datos
GET    redis://...           → Caching
POST   s3://...              → Almacenamiento documentos
```

### 6.2 Internas
```
Flask ←→ Celery                    (message broker: Valkey)
Frontend ←→ Backend                (REST API + JWT)
Backend ←→ Vertex AI / Docling     (procesamiento documental)
Backend ←→ Ollama/NIM              (embeddings)
```

## 7. Políticas de Desarrollo

### 7.1 Cambios Estructurales
- ✅ ADR en `.agent/DECISIONS/`
- ✅ Versioning con UUID v7
- ✅ Changelog en README
- ✅ Testing de regresión

### 7.2 Secretos
- ❌ NUNCA commitear `.env`
- ❌ NUNCA hardcodear API keys
- ✅ Usar variables de entorno
- ✅ Usar Vault para rotación
- ✅ `.env.example` sin valores reales

### 7.3 Compatibilidad
- Python 3.10+
- Node 22+
- Docker 24+
- PostgreSQL 18+

## 8. Rito de Inicialización

Cada vez que se inicia LexiVault:

1. ✅ Verificar conexión a aura-network
2. ✅ Verificar acceso a Postgres (lexivault DB)
3. ✅ Verificar acceso a Valkey (sesiones)
4. ✅ Verificar acceso a MinIO (bucket lexivault)
5. ✅ Crear tablas si no existen
6. ✅ Ejecutar migraciones Alembic
7. ✅ Iniciar Celery workers
8. ✅ Registrar en health check

## 9. Monitoreo y Observabilidad

### 9.1 Métricas Críticas
- Error rate de endpoints
- Latencia de queries BD
- Tamaño de caché Valkey
- Documentos procesados/día
- Uso de CPU/memoria

### 9.2 Logs
- Nivel: INFO (defecto) → DEBUG (desarrollo)
- Formato: `[timestamp] [level] [module] message`
- Destino: stdout → Agregación central (futuro)

### 9.3 Alertas
- ⚠️ DB connection timeout
- ⚠️ Valkey connection lost
- ⚠️ Celery queue > 1000 items
- ⚠️ Documento processing > 5 minutos

## 10. Ciclo de Vida

### Startup
```
setup.sh → docker compose up -d → health checks → ready
```

### Shutdown
```
docker compose down → save state → cleanup
```

### Actualización
```
git pull → docker compose build → docker compose up -d
```

---

**Última actualización**: May 10, 2026
**Versión**: 1.0.0
**Status**: 🟡 En desarrollo (Fase inicial cerrada, migración a Docling pendiente)
