flowchart TB
    subgraph Client["🖥️ Client"]
        User["사용자"]
    end

    subgraph Gateway["🔀 API Gateway"]
        FastAPI["FastAPI Server"]
        Cache["Response Cache"]
        InputGuard["Input Guardrail<br/>유해 입력 필터링"]
    end

    subgraph Retrieval["🔍 Retrieval Layer"]
        Embedding["Embedding Model"]
        VectorDB["Vector DB<br/>(Hybrid Search)"]
        Reranker["Reranker<br/>(Cross-Encoder)"]
    end

    subgraph Generation["🤖 Generation Layer"]
        vLLM["vLLM Server<br/>(LLM Serving)"]
        OutputGuard["Output Guardrail<br/>NLI 환각 검증"]
    end

    subgraph Monitoring["📊 Monitoring"]
        Prometheus["Prometheus"]
        Grafana["Grafana Dashboard"]
        Alert["AlertManager"]
    end

    subgraph AsyncEval["⏳ Async Evaluation"]
        Logger["Request/Response Logger"]
        Sampler["Sampling (10%)"]
        Judge["LLM-as-Judge"]
    end

    subgraph DataPipeline["📄 Data Indexing Pipeline"]
        Docs["새 문서 추가"]
        Parser["Layout Parser"]
        Chunker["Chunking"]
        Indexer["Embedding + 벡터DB 저장"]
    end

    User -->|질문| FastAPI
    FastAPI --> Cache
    Cache -->|캐시 히트| FastAPI
    Cache -->|캐시 미스| InputGuard
    InputGuard --> Embedding
    Embedding --> VectorDB
    VectorDB --> Reranker
    Reranker -->|검색 결과| vLLM
    vLLM --> OutputGuard
    OutputGuard -->|응답| FastAPI
    FastAPI -->|응답| User

    FastAPI -.->|메트릭| Prometheus
    vLLM -.->|메트릭| Prometheus
    VectorDB -.->|메트릭| Prometheus
    Prometheus --> Grafana
    Prometheus --> Alert

    FastAPI -.->|로그| Logger
    Logger --> Sampler
    Sampler --> Judge
    Judge -.->|평가 점수| Prometheus
