# Scaling Strategy

## Current Architecture

Single-process FastAPI server with in-process model inference. The model loads at startup, predictions run synchronously, and everything (real-time, batch, metrics) shares the same process.

What works well at low-to-moderate traffic:

- In-memory LRU cache (10k items) absorbs repeated queries
- Gunicorn spawns `(2 × CPU cores) + 1` workers for parallelism
- Circuit breaker prevents cascading failures on inference errors
- Shared policy logic keeps real-time and batch predictions consistent

What doesn't scale:

- CPU-bound inference competes with request handling in the same process
- In-memory rate limiting and metrics don't work across replicas
- Batch jobs can starve real-time requests under load
- No backpressure mechanism for traffic spikes

## When to Redesign

Don't optimize prematurely. Redesign when you consistently hit one of these:

| Signal             | Threshold                                    |
| ------------------ | -------------------------------------------- |
| p95 latency        | > 500ms sustained                            |
| Error rate         | > 1% for 5+ minutes                          |
| Traffic spikes     | > 5× baseline without recovery               |
| Batch interference | Real-time latency degrades during batch runs |

## At 10k RPS

Split batch processing into a separate worker service so it can't starve real-time traffic. Move rate limiting and metrics to Redis so they work across replicas. Add horizontal scaling with multiple API workers behind a load balancer. Prioritize real-time requests over batch.

Concrete changes:

- Redis for distributed rate limiting and metrics aggregation
- Separate batch worker (Celery or similar) pulling from a queue
- 3-5 API replicas behind an ALB with health-check routing
- Shared model artifact storage (S3 or EFS) instead of baked-in model files

## At 100k RPS

Dedicated model-serving tier (e.g., TorchServe, Triton, or a custom gRPC service) with autoscaling. Async request queue with batching to maximize GPU/CPU utilization. Completely separate real-time and batch pipelines. Centralized feature store and model registry for safe rollouts.

Concrete changes:

- Model serving decoupled from API layer (gRPC or HTTP internal service)
- Request queue (SQS, Kafka) with consumer autoscaling
- Separate batch pipeline with its own compute (Step Functions, Airflow)
- Model registry (MLflow, SageMaker) for versioned deployments
- CDN or edge caching for repeated queries if applicable
