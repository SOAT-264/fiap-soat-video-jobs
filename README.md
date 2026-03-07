# fiap-soat-video-jobs

## Introdução
Microserviço responsável pelo processamento assíncrono de vídeos. Ele possui API para consulta de jobs e worker SQS para consumir eventos, extrair frames e publicar resultado do processamento.

## Sumário
- Explicação do projeto
- Objetivo
- Como funciona
- Repositórios relacionados
- Integrações com outros repositórios
- Como executar
- Como testar

## Repositórios relacionados
- [fiap-soat-video-service](https://github.com/SOAT-264/fiap-soat-video-service)
- [fiap-soat-video-notifications](https://github.com/SOAT-264/fiap-soat-video-notifications)
- [fiap-soat-video-shared](https://github.com/SOAT-264/fiap-soat-video-shared)
- [fiap-soat-video-local-dev](https://github.com/SOAT-264/fiap-soat-video-local-dev)
- [fiap-soat-video-obs](https://github.com/SOAT-264/fiap-soat-video-obs)

## Explicação do projeto
O projeto combina duas partes:
- API FastAPI para consultar jobs (`/jobs`).
- Worker (`python -m job_service.infrastructure.adapters.input.sqs_consumer`) para consumir mensagens da fila e processar vídeos.

O processamento usa S3 para leitura/escrita de arquivos e publica eventos de estado (`job-events`) para continuidade do fluxo.

## Objetivo
Executar o processamento de vídeo de forma desacoplada da API de upload, com resiliência e escalabilidade orientadas à fila.

## Como funciona
1. O worker consome mensagens da `job-queue` (SQS), incluindo mensagens encapsuladas por SNS.
2. Para mensagens de upload (`video_id`, `user_id`, `filename`), o consumer cria um job pendente e resolve o `s3_key`.
3. O `process_video_task` baixa o vídeo do S3, extrai frames (FFmpeg), gera zip e envia para `video-outputs`.
4. O status do job é atualizado no banco e eventos de sucesso/falha são publicados em `job-events` (SNS).
5. A API expõe consulta de jobs:
`GET /jobs/{job_id}` e `GET /jobs`, com health em `GET /health` e prontidão em `GET /health/ready`.
6. Em Kubernetes local-dev, o worker pode escalar com KEDA baseado no tamanho da fila.

## Integrações com outros repositórios
| Repositório integrado | Como integra | Para que serve |
| --- | --- | --- |
| `fiap-soat-video-service` | Consome eventos originados de uploads (pipeline `video-events -> job-queue`) | Iniciar criação e processamento de jobs para vídeos enviados |
| `fiap-soat-video-notifications` | Publica eventos `job-events` consumidos pelo worker de notificações | Disparar notificação ao usuário quando job termina/falha |
| `fiap-soat-video-auth` | URL de auth parametrizada no ambiente integrado (`AUTH_SERVICE_URL`) | Manter contrato de identidade entre serviços no ecossistema |
| `fiap-soat-video-shared` | Uso de eventos/exceções/value objects compartilhados (`JobCompletedEvent`, `JobFailedEvent`, `JobStatus`) | Padronizar semântica de domínio e contratos de mensagem |
| `fiap-soat-video-local-dev` | Provisiona DB/Redis/LocalStack, deploy API+worker e filas SNS/SQS | Executar pipeline assíncrono completo localmente |
| `fiap-soat-video-obs` | Exposição de `/health` e `/metrics` para scraping | Monitorar API e comportamento operacional do serviço |

## Como executar
### Pré-requisitos
- Python 3.11+
- FFmpeg disponível no ambiente local para processamento de vídeo
- Infra local recomendada via `fiap-soat-video-local-dev`

### Execução local da API
```powershell
cd /fiap-soat-video-jobs
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev,worker]"

$env:DATABASE_URL="postgresql+asyncpg://postgres:postgres123@localhost:5434/job_db"
$env:REDIS_URL="redis://localhost:6379/2"
$env:AWS_ENDPOINT_URL="http://localhost:4566"
$env:AWS_ACCESS_KEY_ID="test"
$env:AWS_SECRET_ACCESS_KEY="test"
$env:AWS_DEFAULT_REGION="us-east-1"
$env:S3_INPUT_BUCKET="video-uploads"
$env:S3_OUTPUT_BUCKET="video-outputs"
$env:SQS_JOB_QUEUE_URL="http://localhost:4566/000000000000/job-queue"
$env:SNS_TOPIC_ARN="arn:aws:sns:us-east-1:000000000000:job-events"

uvicorn job_service.infrastructure.adapters.input.api.main:app --host 0.0.0.0 --port 8003 --reload
```

### Execução local do worker
```powershell
cd /fiap-soat-video-jobs
.\.venv\Scripts\Activate.ps1
python -m job_service.infrastructure.adapters.input.sqs_consumer
```

### Execução integrada (recomendada)
```powershell
cd /fiap-soat-video-local-dev
.\start.ps1
```

## Como testar
```powershell
cd /fiap-soat-video-jobs
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev,worker]"
pytest
```

