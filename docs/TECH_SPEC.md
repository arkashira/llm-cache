# TECH_SPEC.md – llm‑cache

**Project:** llm‑cache  
**Owner:** Axentx – Large Language Model (LLM) Infrastructure Team  
**Status:** MVP → Production (target Q4 2026)  
**Repository:** `arkashira/llm-cache` (main)  

---  

## 1. Overview  

`llm-cache` is a high‑performance, distributed caching layer built specifically for Large Language Model inference workloads. It sits between the client (e.g., an application, API gateway, or orchestration service) and the LLM inference engine (e.g., vLLM, SGLang) and provides:

* **Deterministic request‑response memoization** – identical prompts (including system messages, temperature, top‑p, etc.) return cached completions.  
* **Token‑level sub‑prompt reuse** – partial overlap detection enables reuse of previously computed token streams, reducing compute cost.  
* **Latency‑SLA enforcement** – cache‑hit paths guarantee sub‑10 ms response for hot prompts.  
* **Cost‑aware eviction** – eviction policy accounts for compute cost saved vs. storage cost.  

The cache is **language‑agnostic** (stores raw token streams) and **framework‑agnostic** (compatible with any LLM server exposing a standard OpenAI‑compatible REST API).  

---  

## 2. Architecture  

```
+-------------------+        +-------------------+        +-------------------+
|   Client / API   | <----> |   Cache Frontend  | <----> |   Cache Workers   |
+-------------------+        +-------------------+        +-------------------+
                                   |   ^   |
                                   |   |   |
                                   v   |   v
                           +---------------------------+
                           |   Distributed KV Store    |
                           | (Redis‑Cluster / DynamoDB)|
                           +---------------------------+
                                   |
                                   v
                           +---------------------------+
                           |   Persistent Object Store |
                           |   (S3 / Azure Blob)       |
                           +---------------------------+
```

* **Cache Frontend** – HTTP/HTTPS gateway exposing an OpenAI‑compatible `/v1/chat/completions` endpoint. Performs request canonicalization, hash computation, and cache‑lookup orchestration.  
* **Cache Workers** – Stateless micro‑services that:
  * Compute **prompt fingerprints** (see §3) and query the KV store.
  * On a miss, forward the request to the downstream LLM server, stream the response, and store the result atomically.
  * Perform **token‑level overlap detection** for partial hits.  
* **Distributed KV Store** – Low‑latency key/value store (Redis‑Cluster) holding metadata and short‑term token blobs (TTL‑based).  
* **Object Store** – Durable storage for large token blobs (> 1 MiB) and for audit logs.  

All components are containerized (Docker) and orchestrated via Kubernetes (Helm chart provided).  

---  

## 3. Data Model  

### 3.1 Prompt Fingerprint  

A deterministic 256‑bit hash generated from the **canonical JSON** representation of the request:

```json
{
  "model": "string",
  "messages": [{ "role": "system|user|assistant", "content": "string" }],
  "temperature": float,
  "top_p": float,
  "max_tokens": int,
  "stop": ["string", ...],
  "seed": int | null
}
```

* Canonicalization steps:  
  1. Sort object keys alphabetically.  
  2. Remove `null` optional fields.  
  3. Serialize with `json.dumps(..., separators=(',', ':'), ensure_ascii=False)`.  
  4. Compute SHA‑256 → hex string (`fingerprint`).  

### 3.2 KV Entry  

| Field | Type | Description |
|-------|------|-------------|
| `fingerprint` | `string` (PK) | Prompt fingerprint (SHA‑256). |
| `token_blob_id` | `string` | Reference to object‑store blob (S3 key). |
| `metadata` | `hash` | `{ created_at, ttl, compute_cost_usd, hit_count }`. |
| `etag` | `string` | Version token for CAS updates. |

### 3.3 Token Blob  

Binary protobuf (`CacheEntry`) stored in object store:

```proto
message CacheEntry {
  repeated string tokens = 1;          // token IDs (int32 encoded as varint)
  repeated float   token_logprobs = 2; // optional per‑token log‑prob
  string   model = 3;                  // model identifier
  uint64   created_at_ms = 4;
}
```

Compression: LZ4 (fast decompression) + optional Brotli for large blobs.

---  

## 4. Key APIs / Interfaces  

### 4.1 Public HTTP API (Cache Frontend)

| Method | Path | Description | Request Body | Response |
|--------|------|-------------|--------------|----------|
| `POST` | `/v1/chat/completions` | OpenAI‑compatible endpoint; cache‑aware. | OpenAI chat request JSON. | Same shape as OpenAI response (streamable). |
| `GET` | `/v1/cache/metrics` | Prometheus‑compatible metrics dump. | – | `text/plain`. |
| `POST` | `/v1/cache/purge` | Purge specific fingerprints (admin). | `{ "fingerprints": ["..."] }` | `{ "purged": n }`. |

### 4.2 Internal gRPC (Cache Workers ↔ KV Store)

```proto
service CacheService {
  rpc GetEntry (Fingerprint) returns (CacheLookup);
  rpc PutEntry (CachePut) returns (CacheAck);
  rpc IncrementHit (Fingerprint) returns (CacheAck);
}
```

*All calls are idempotent and use optimistic concurrency via `etag`.*

### 4.3 Downstream LLM Interface  

The cache forwards miss requests to a configurable LLM endpoint (default: `http://vllm:8000/v1/chat/completions`). The interface must support:

* **Streaming** (`text/event-stream`) – cache streams tokens as they arrive and writes them to the blob concurrently.  
* **Batch** – optional non‑streaming fallback for legacy servers.

---  

## 5. Technology Stack  

| Layer | Technology | Reason |
|-------|------------|--------|
| **Runtime** | Python 3.11 (asyncio) | Mature async HTTP, easy integration with existing Axentx pipelines. |
| **Web Server** | FastAPI + Uvicorn (workers=4) | High‑throughput, OpenAPI auto‑gen, easy testing. |
| **Cache Workers** | Python + `aioredis` + `boto3` | Async Redis client, S3 SDK. |
| **KV Store** | Redis‑Cluster (v7.2) with TLS | Sub‑millisecond latency, built‑in eviction. |
| **Object Store** | Amazon S3 (or compatible MinIO) | Durable, cheap, high‑throughput. |
| **Serialization** | Protobuf v4 + LZ4 | Compact, fast (de)serialization. |
| **Containerisation** | Docker (alpine) | Small footprint. |
| **Orchestration** | Kubernetes 1.28 + Helm 3 | Autoscaling, rolling updates. |
| **Observability** | Prometheus + Grafana + OpenTelemetry (Python) | Metrics, tracing across cache miss/hit paths. |
| **Security** | mTLS between services, API‑key auth for public endpoint | Zero‑trust intra‑cluster, client throttling. |

---  

## 6. Deployment Diagram  

```mermaid
graph LR
  subgraph K8s Cluster
    FE[Cache Frontend (FastAPI)]
    W1[Cache Worker #1]
    W2[Cache Worker #2]
    Redis[Redis‑Cluster]
    S3[(S3 Bucket)]
  end

  Client --> FE
  FE -->|lookup| Redis
  FE -->|miss| W1
  W1 -->|fetch| LLM[Downstream LLM (vLLM/SGLang)]
  LLM -->|stream| W1
  W1 -->|store| Redis
  W1 -->|store| S3
  FE -->|stream| Client
```

* **Autoscaling** – HPA based on CPU and request latency (target 95th‑pct ≤ 30 ms for hits).  
* **Failover** – Redis Cluster with 3‑node quorum; S3 is multi‑AZ. Frontend pods are stateless, can be redeployed without data loss.  

---  

## 7. Operational Concerns  

| Concern | Mitigation |
|---------|------------|
| **Cache Stampede** | Use *single‑flight* (request coalescing) in workers; first miss request owns the downstream call, others await result. |
| **Cold‑Start Latency** | Pre‑warm hot prompts via background job that loads top‑N fingerprints from analytics DB. |
| **Eviction Policy** | Custom *Cost‑Aware LRU*: `score = (compute_cost_usd) / (size_bytes * (1 + hit_count))`. Periodic re‑ranking job runs every 5 min. |
| **Data Consistency** | Writes are performed in a *transactional* fashion: first write metadata to Redis with `SETNX`, then upload blob to S3, finally update Redis with `etag`. On failure, rollback via TTL. |
| **Security** | API‑key per client, rate‑limit (token bucket). All inter‑service traffic encrypted with mTLS. |
| **Observability** | - `cache_hit_total`, `cache_miss_total` <br> - `cache_latency_seconds` (histogram) <br> - `downstream_llm_latency_seconds` <br> - Traces: `frontend → worker → llm`. |
| **Backup / Restore** | Redis AOF + periodic RDB snapshots. S3 versioning enabled. Restore script re‑hydrates Redis from latest snapshot. |

---  

## 8. Testing Strategy  

| Level | Tool | Scope |
|-------|------|-------|
| Unit | `pytest` + `pytest‑asyncio` | Fingerprint generation, protobuf (de)serialization, Redis client wrappers. |
| Integration | `testcontainers` (Redis, MinIO) | End‑to‑end request flow, hit/miss logic, eviction. |
| Load | `locust` (HTTP) & `k6` (gRPC) | 10k RPS sustained, 99th‑pct latency < 30 ms for hits, < 200 ms for misses. |
| Chaos | `chaos‑mesh` | Redis node loss, S3 latency injection, network partition. |
| CI/CD | GitHub Actions → Build → Unit → Integration → Deploy to staging cluster. |

---  

## 9. Release Plan  

| Milestone | Target | Deliverables |
|-----------|--------|--------------|
| **M0 – Prototype** | 2026‑07‑15 | Single‑node FastAPI + Redis (no object store). |
| **M1 – Distributed MVP** | 2026‑08‑30 | Multi‑node Redis‑Cluster, S3 integration, token‑level overlap detection. |
| **M2 – Production‑Ready** | 2026‑10‑15 | Autoscaling, cost‑aware eviction, observability dashboards, security hardening. |
| **M3 – SLA Guarantee** | 2026‑12‑01 | 99.9 % uptime SLA, latency SLA (≤ 10 ms hit). |
| **M4 – Marketplace** | 2027‑02‑01 | Public API key portal, usage‑based billing integration. |

---  

## 10. Glossary  

| Term | Definition |
|------|------------|
| **Fingerprint** | SHA‑256 hash of the canonical request JSON. |
| **Hit** | Cache entry found and returned without invoking downstream LLM. |
| **Miss** | No entry; request forwarded to LLM and result cached. |
| **Token Blob** | Serialized token sequence stored in object store. |
| **Cost‑Aware LRU** | Eviction algorithm that weighs compute cost saved vs. storage cost. |
| **Single‑Flight** | Request coalescing technique to avoid duplicate downstream calls. |

---  

*Prepared by:*  
**Senior Product/Engineering Lead – Axentx**  
*Date:* 2026‑06‑18  

---
