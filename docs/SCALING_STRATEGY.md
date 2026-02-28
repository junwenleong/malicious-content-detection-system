# Scaling Strategy

## Current Architecture

- FastAPI API server with in-process model inference
- Single predictor loaded at startup
- In-memory metrics and rate limiting
- Batch processing performed by the same API process
- **Resilience:** Circuit breaker pattern for inference protection
- **Consistency:** Shared policy logic for real-time and batch predictions

## Known Bottlenecks

- CPU-bound inference in the API process
- In-memory rate limiting and metrics do not work across replicas
- Batch jobs can compete with real-time requests
- No async queueing for spikes or backpressure

## When Redesign Is Required

- Sustained p95 latency > 500ms under load
- Error rate > 1% for 5 minutes
- Traffic spikes over 5x baseline without recovery
- Batch jobs cause real-time latency degradation

## What Changes at 10k RPS

- Split batch processing into a separate worker service
- Introduce distributed rate limiting and metrics aggregation
- Add horizontal scaling with multiple API workers
- Add request prioritization for real-time traffic

## What Changes at 100k RPS

- Dedicated model-serving tier with autoscaling
- Asynchronous request queue with batching
- Dedicated real-time inference path and separate batch pipeline
- Centralized feature store and model registry for rollouts
