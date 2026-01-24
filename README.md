# ⚙️ Video Processor - Job Service

Microserviço responsável pelo processamento de vídeos, extração de frames com FFmpeg e criação de arquivos ZIP.

## 📐 Arquitetura

```
fiap-soat-video-jobs/
├── src/job_service/
│   ├── domain/entities/          # Job entity
│   ├── application/
│   │   ├── ports/                # IJobRepository
│   │   └── use_cases/            # CreateJob, GetJob, ProcessVideo
│   └── infrastructure/
│       ├── adapters/input/
│       │   ├── api/              # FastAPI routes
│       │   └── worker/           # Celery tasks
│       ├── adapters/output/
│       │   ├── persistence/      # PostgreSQL
│       │   ├── storage/          # S3/MinIO
│       │   ├── messaging/        # Event publisher
│       │   └── video_processing/ # FFmpeg
│       └── config/               # Settings
├── Dockerfile
└── pyproject.toml
```

## 🚀 Rodar Localmente

### Pré-requisitos

- Python 3.11+
- FFmpeg instalado (`brew install ffmpeg`)
- PostgreSQL, Redis, MinIO

### 1. Clone e instale

```bash
git clone https://github.com/morgadope/fiap-soat-video-jobs.git
cd fiap-soat-video-jobs
pip install -e ".[dev]"
```

### 2. Configure variáveis de ambiente

```bash
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5434/job_db"
export REDIS_URL="redis://localhost:6379/0"
export AWS_ENDPOINT_URL="http://localhost:9000"
export AWS_ACCESS_KEY_ID="minioadmin"
export AWS_SECRET_ACCESS_KEY="minioadmin123"
export S3_INPUT_BUCKET="video-processor"
export S3_OUTPUT_BUCKET="video-processor"
```

### 3. Execute a API

```bash
uvicorn job_service.infrastructure.adapters.input.api.main:app --reload --port 8003
```

### 4. Execute o Worker (em outro terminal)

```bash
celery -A job_service.infrastructure.adapters.input.worker.celery_app worker -l INFO
```

### 5. Acesse

- Swagger: http://localhost:8003/docs
- Health: http://localhost:8003/health

## 📖 API Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/jobs` | Listar jobs do usuário |
| GET | `/jobs/{job_id}` | Obter status de um job |
| DELETE | `/jobs/{job_id}` | Cancelar job |
| GET | `/health` | Health check |

### Exemplos

**Listar jobs:**
```bash
curl http://localhost:8003/jobs?user_id=UUID \
  -H "Authorization: Bearer $TOKEN"
```

**Status do job:**
```bash
curl http://localhost:8003/jobs/JOB_UUID \
  -H "Authorization: Bearer $TOKEN"
```

## 📊 Fluxo de Processamento

```
1. Worker recebe mensagem do RabbitMQ
2. Baixa vídeo do S3/MinIO
3. Extrai frames com FFmpeg (1 frame/segundo)
4. Cria arquivo ZIP com todos os frames
5. Upload do ZIP para S3/MinIO
6. Atualiza status do job para COMPLETED
7. Publica evento de conclusão
```

## 🐳 Docker

```bash
docker build -t job-service .
docker run -p 8003:8003 \
  -e DATABASE_URL=... \
  -e REDIS_URL=... \
  job-service
```

## 🧪 Testes

```bash
pytest tests/ -v --cov=job_service
```

## 📄 Licença

MIT License
