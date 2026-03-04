# ⚙️ Video Processor - Job Service

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Microserviço responsável pelo processamento de vídeos, extração de frames com FFmpeg e criação de arquivos ZIP.

## 📋 Índice

- [Arquitetura](#-arquitetura)
- [Processamento](#-processamento)
- [API Endpoints](#-api-endpoints)
- [Como Executar](#-como-executar)
- [AWS Lambda](#-aws-lambda)
- [Testes](#-testes)

---

## 🏗️ Arquitetura

```
src/job_service/
├── domain/
│   └── entities/job.py          # Entidade Job
├── application/
│   ├── ports/output/            # IJobRepository
│   └── use_cases/               # CreateJob, ProcessVideo
└── infrastructure/
    ├── adapters/
    │   ├── input/
    │   │   ├── api/             # FastAPI routes
    │   │   ├── worker/          # Celery tasks
    │   │   └── sqs_consumer.py  # Lambda handler
    │   └── output/
    │       ├── persistence/     # SQLAlchemy
    │       ├── storage/         # S3
    │       ├── messaging/       # SNS
    │       └── video_processing/ # FFmpeg
    └── config/
```

---

## 📹 Processamento

### Fluxo

```
1. Recebe mensagem da fila SQS
2. Baixa vídeo do S3
3. Extrai frames com FFmpeg (1 frame/segundo)
4. Cria arquivo ZIP com todos os frames
5. Upload do ZIP para S3
6. Publica evento no SNS (job_completed)
7. Notification Service envia email
```

### FFmpeg Command

```bash
ffmpeg -i input.mp4 -vf fps=1 -q:v 2 frames_%04d.jpg
```

---

## 📡 API Endpoints

| Método | Endpoint | Descrição | Autenticação |
|--------|----------|-----------|--------------|
| GET | `/jobs` | Listar jobs do usuário | ✅ JWT |
| GET | `/jobs/{id}` | Status do job | ✅ JWT |
| DELETE | `/jobs/{id}` | Cancelar job | ✅ JWT |
| GET | `/health` | Health check | ❌ |

### Exemplo de Resposta

```json
{
  "id": "uuid",
  "video_id": "uuid",
  "status": "COMPLETED",
  "progress": 100,
  "frame_count": 120,
  "output_url": "https://s3.../frames.zip",
  "created_at": "2024-01-01T00:00:00Z",
  "completed_at": "2024-01-01T00:02:00Z"
}
```

### Status Possíveis

| Status | Descrição |
|--------|-----------|
| `PENDING` | Aguardando processamento |
| `PROCESSING` | Em processamento |
| `COMPLETED` | Finalizado com sucesso |
| `FAILED` | Erro no processamento |
| `CANCELLED` | Cancelado pelo usuário |

---

## 🚀 Como Executar

### Pré-requisitos

- Python 3.11+
- FFmpeg instalado (`brew install ffmpeg`)
- PostgreSQL, S3 (LocalStack)

### 1. Clone e instale

```bash
git clone https://github.com/morgadope/fiap-soat-video-jobs.git
cd fiap-soat-video-jobs
pip install -e ".[dev]"
```

### 2. Configure

```bash
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5434/job_db"
export AWS_ENDPOINT_URL="http://localhost:4566"
export S3_INPUT_BUCKET="video-uploads"
export S3_OUTPUT_BUCKET="video-outputs"
export SQS_JOB_QUEUE_URL="http://localhost:4566/000000000000/job-queue"
```

### 3. Execute API

```bash
uvicorn job_service.infrastructure.adapters.input.api.main:app --reload --port 8003
```

### 4. Execute Worker (outro terminal)

```bash
python -m job_service.infrastructure.adapters.input.sqs_consumer
```

---

## ☁️ AWS Lambda

O serviço pode rodar como Lambda triggered por SQS:

```python
# sqs_consumer.py
def lambda_handler(event, context):
    for record in event["Records"]:
        body = json.loads(record["body"])
        process_video_task(body["job_id"], body["s3_key"])
```

### Deploy Lambda

1. Crie Lambda Layer com FFmpeg
2. Configure trigger SQS
3. Set timeout para 15 minutos (máximo)

---

## 🐳 Docker

```bash
docker build -t job-service .
docker run -p 8003:8003 \
  -e DATABASE_URL="..." \
  -e AWS_ENDPOINT_URL="..." \
  job-service
```

---

## 🧪 Testes

```bash
pytest tests/ -v --cov=job_service
```

---

## ☸️ Kubernetes + HPA por SQS

Os manifests de Kubernetes estão em `k8s/` e incluem autoscaling do `job-worker` via KEDA com base no tamanho da fila SQS.

Guia de uso:

- `k8s/README.md`

---

## 📄 Licença

MIT License
