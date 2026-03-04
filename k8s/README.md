# Kubernetes - fiap-soat-video-jobs

Este diretório contém os manifests para subir o `job-api-service` e o `job-worker` no Kubernetes, com autoscaling baseado no tamanho da fila SQS via KEDA.

## Estrutura

- `base/`: manifests base reutilizáveis
- `overlays/local-dev/`: integração com o ambiente `fiap-soat-video-local-dev` (LocalStack + PostgreSQL + Redis rodando via Docker Compose)

## Pré-requisitos

- Cluster Kubernetes ativo
- `kubectl`
- KEDA instalado no cluster

Instalação rápida do KEDA:

```bash
helm repo add kedacore https://kedacore.github.io/charts
helm repo update
helm install keda kedacore/keda --namespace keda --create-namespace
```

## Deploy local integrado com fiap-soat-video-local-dev

1. Suba a infraestrutura local (fora do cluster):

```bash
cd ../fiap-soat-video-local-dev
docker-compose -f docker-compose.infra.yml up -d
./init-scripts/localstack-init.sh
```

2. Faça build local da imagem (sem GHCR/ECR):

```bash
cd ..
docker build -t fiap-soat-video-jobs:local -f fiap-soat-video-jobs/Dockerfile .
```

3. Aplique os manifests do Job Service no cluster:

```bash
cd ../fiap-soat-video-jobs
kubectl apply -k k8s/overlays/local-dev
```

## Como funciona o HPA por SQS

- O `ScaledObject` (`job-worker-sqs-scaler`) monitora a fila configurada em `SQS_JOB_QUEUE_URL`.
- O KEDA cria automaticamente um `HorizontalPodAutoscaler` para o `Deployment/job-worker`.
- O gatilho usa:
  - `queueLength`: alvo de mensagens por pod
  - `awsEndpoint`: endpoint LocalStack/AWS
  - `awsRegion`: região da fila

## Parametrizar o tamanho da fila (threshold)

No overlay local, altere `queueLength` em:

- `k8s/overlays/local-dev/patch-scaledobject-worker.yaml`

Exemplo:

- `queueLength: "10"` → 1 pod a cada 10 mensagens aproximadas na fila.

## Verificação

```bash
kubectl get pods -n video-processor
kubectl get scaledobject -n video-processor
kubectl get hpa -n video-processor
```
