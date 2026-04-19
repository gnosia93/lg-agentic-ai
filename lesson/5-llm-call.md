## RAG 검색하기 (검색/리랭킹/LLM 답변) ##

앞 단계에서 Milvus에 저장한 벡터를 실제로 활용해 질의에 답변하는 단계다. 질의 하나가 들어오면 다음 세 단계를 순차로 거쳐 최종 답변이 만들어진다.
```
Query → Milvus 검색 (top 20) → bge-reranker-v2-m3 재정렬 (top 5) → Bedrock LLM 답변 생성
```
각 단계의 역할은 다음과 같다.

* Milvus 검색 : 질의를 벡터로 변환해 유사도가 높은 청크 20개를 빠르게 추려낸다. 속도는 빠르지만 정밀도는 다소 떨어진다.
* Reranker 재정렬 : CrossEncoder가 (질의, 청크) 쌍을 직접 비교해 점수를 매기고, 그중 가장 관련 깊은 5개만 남긴다. 느리지만 정확하다.
* LLM 답변 생성 : 선별된 컨텍스트를 근거로 Bedrock(Claude)이 최종 답변을 생성한다. 컨텍스트에 포함된 내용만 사용하도록 프롬프트로 제약해 환각(hallucination)을 줄인다.

아래 RAGSearch 클래스는 이 세 단계를 하나로 묶은 래퍼이다.

### 1. 프로젝트 구조 ###
```
rag/
├── PDFVectorStore.py   ← 저장용 클래스
├── RAGSearch.py        ← 검색용 클래스 (curl로 받음)
├── main.py             ← PDF 저장 스크립트
├── query.py            ← 검색 실행 스크립트
└── pdfs/
    └── LoRA_Low-Rank_Adaptation.pdf
```

### 2. 환경 준비 ###
Bedrock 호출에 필요한 boto3를 추가로 설치한다. 나머지 패키지(pymilvus, sentence-transformers 등)는 저장 단계에서 이미 설치돼 있다.
```
pip install boto3
```

> [!NOTE]
> aiobotocore 2.25.0 requires botocore<1.40.50,>=1.40.46 와 관련된 의존성 오류가 발생하나,   
> 아래 bedrock-runtime 이 정상적으로 호출되는 경우 무시한다.  
> 파이썬에서 pip 경고 ≠ 실제 오류, 경고는 "이 버전 조합이 테스트 안 됐음" 을 의미한다.
> ```
> python -c "import boto3; print(boto3.client('bedrock-runtime', region_name='ap-northeast-2'))"
> ```


### 3. RAGSearch 클래스 내려받기 ###
미리 작성해 둔 클래스 파일을 가져온다.
```
curl -o RAGSearch.py \
https://raw.githubusercontent.com/gnosia93/eks-agentic-ai/refs/heads/main/code/rag/RAGSearch.py
```
이 파일에는 다음 기능이 구현돼 있다. 
* 저장 때와 동일한 BAAI/bge-m3 모델로 질의 벡터화
* Milvus에서 유사도 기반 top-k 청크 검색
* BAAI/bge-reranker-v2-m3로 CrossEncoder 기반 재정렬
* Bedrock Converse API 호출로 Claude, Nova, Llama 등 모델을 동일한 인터페이스로 사용

### 4. 실행 스크립트 작성 (query.py) ###
```
cat << 'EOF' > query.py
import argparse
from RAGSearch import RAGSearch

def main():
    parser = argparse.ArgumentParser(description="Milvus + Bedrock RAG 질의 응답")
    parser.add_argument("--host", default="localhost", help="Milvus 호스트")
    parser.add_argument("--port", default="19530", help="Milvus 포트")
    parser.add_argument("--collection", default="papers", help="컬렉션 이름")
    parser.add_argument("--region", default="ap-northeast-2", help="AWS 리전")
    parser.add_argument(
        "--model",
        default="apac.anthropic.claude-3-5-sonnet-20241022-v2:0",
        help="Bedrock 모델 ID",
    )
    parser.add_argument("--top-k", type=int, default=20, help="검색 후보 수")
    parser.add_argument("--top-n", type=int, default=5, help="재순위 후 사용할 수")
    parser.add_argument("query", help="질문")

    args = parser.parse_args()

    rag = RAGSearch(
        host=args.host,
        port=args.port,
        collection_name=args.collection,
        bedrock_model_id=args.model,
        aws_region=args.region,
    )

    result = rag.query(args.query, top_k=args.top_k, top_n=args.top_n)

    print("=" * 60)
    print(f"Q: {result['query']}")
    print("=" * 60)
    print(result["answer"])
    print("\n" + "-" * 60)
    print("참조한 컨텍스트:")
    for i, c in enumerate(result["contexts"], 1):
        print(f"  {i}. [{c['doc_name']} p.{c['page']}] "
              f"sim={c['score']:.3f} rerank={c['rerank_score']:.3f}")

if __name__ == "__main__":
    main()
EOF
```

### 5. 실행 ###
#### 5.1 Bedrock 모델 액세스 활성화 ####
AWS 콘솔에서 사용할 모델의 액세스를 먼저 열어줘야 한다.
```
AWS 콘솔 → Bedrock → Model access → 사용할 모델 "Request access"
```

#### 5.2 호출 가능한 Bedrock 모델 확인 ####
```
aws bedrock list-inference-profiles \
  --region ap-northeast-2 \
  --query 'inferenceProfileSummaries[?contains(inferenceProfileName, `Claude 3.5 Sonnet v2`)].[inferenceProfileId]' \
  --output text
```
[결과]
```
apac.anthropic.claude-3-5-sonnet-20241022-v2:0
```

#### 5.3 질의 실행 ####
Milvus가 EKS 내부(ClusterIP)에 있으므로 앞 단계와 동일하게 kubectl port-forward로 터널을 연 뒤 질의를 실행한다.
```
kubectl port-forward -n milvus svc/milvus 19530:19530 &
PF_PID=$!
sleep 3   # 포트 포워딩 준비 대기

export MILVUS_DB_IP=localhost
python query.py --host ${MILVUS_DB_IP} \
  "LoRA에서 low-rank adaptation이 왜 효과적인가?"
```
[결과]
```
Handling connection for 19530
I0419 04:52:45.708652  116637 fork_posix.cc:71] Other threads are currently calling into gRPC, skipping fork() handlers
I0419 04:52:45.745248  116637 fork_posix.cc:71] Other threads are currently calling into gRPC, skipping fork() handlers
I0419 04:52:45.779831  116637 fork_posix.cc:71] Other threads are currently calling into gRPC, skipping fork() handlers
I0419 04:52:45.836325  116637 fork_posix.cc:71] Other threads are currently calling into gRPC, skipping fork() handlers
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
Loading weights: 100%|███████████████████████████████████████████████████████████████████████████| 391/391 [00:00<00:00, 44466.61it/s]
Loading weights: 100%|████████████████████████████████████████████████████████████████████████████| 393/393 [00:00<00:00, 7932.71it/s]
============================================================
Q: LoRA에서 low-rank adaptation이 왜 효과적인가?
============================================================
컨텍스트에 따르면, LoRA의 low-rank adaptation이 효과적인 이유는 다음과 같습니다:

1. 이론적 근거: 학습된 과대 매개변수화(over-parametrized) 모델들이 실제로는 낮은 내재적 차원(low intrinsic dimension)에 존재한다는 것이 밝혀졌습니다. 이를 통해 모델 적응 과정에서의 가중치 변화도 낮은 "내재적 순위(intrinsic rank)"를 가질 것이라는 가설이 제시되었습니다.

2. 실제 적용 사례: GPT-3 175B의 경우, 전체 순위(full rank)가 12,288로 매우 높음에도 불구하고 매우 낮은 순위(r=1 또는 2)만으로도 충분한 성능을 보였습니다.

3. 중요 특징 강화: low-rank adaptation 행렬은 사전 학습 모델에서 학습되었지만 충분히 강조되지 않았던 특정 downstream 작업에 중요한 특징들을 잠재적으로 증폭시키는 효과가 있습니다.

참조:
- 02_LoRA_Low-Rank_Adaptation p.1
- 02_LoRA_Low-Rank_Adaptation p.11

------------------------------------------------------------
참조한 컨텍스트:
  1. [02_LoRA_Low-Rank_Adaptation p.1] sim=0.689 rerank=0.983
  2. [02_LoRA_Low-Rank_Adaptation p.1] sim=0.690 rerank=0.973
  3. [02_LoRA_Low-Rank_Adaptation p.0] sim=0.695 rerank=0.969
  4. [02_LoRA_Low-Rank_Adaptation p.11] sim=0.691 rerank=0.957
  5. [02_LoRA_Low-Rank_Adaptation p.8] sim=0.677 rerank=0.946
```

서비스 포트 포워딩을 삭제한다.
```
kill $PF_PID
```

> [!TIP]
> 본 워크샵에서는 RAG 검색을 위한 임베딩과 검색 결과에 대한 리랭킹 작업을 로컬 VSCode 서버의 CPU에서 실행한다. 실제 운영 환경에서는 SaaS API(예: OpenAI, Cohere, Bedrock Embedding)를 활용하거나, GPU를 탑재한 원격 추론 서버(예: EKS GPU 노드 + vLLM/Triton)를 별도로 구성해 해당 작업을 처리해야 한다.
>  
