### 1. 환경 설정 ###
```
# 설치
pip install langfuse

# .env 파일
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# 코드
from dotenv import load_dotenv
load_dotenv()

langfuse_handler = CallbackHandler()  # 자동으로 환경변수 읽음
```

### 2. 호출 추적 ###
```
방법 1: 콜백 직접 전달 (수동)
llm.invoke(input, config={"callbacks": [langfuse_handler]})

방법 2: 데코레이터 사용 (자동, 추천!)
@observe()
def my_function():
    llm.invoke(input)  # 자동으로 추적됨
데코레이터 방식이 훨씬 편해요. 어떤 방식으로 하실 건가요?
```

### 3. 커스텀 메트릭(트레이스) ###
```
from langfuse.decorators import observe, langfuse_context

@observe()
def rag_with_custom_metrics(query: str):
    # 검색
    docs = vector_db.search(query, top_k=10)
    
    # LLM 생성
    llm = ChatOpenAI(model="gpt-4")
    response = llm.invoke(query)
    
    # 커스텀 메트릭만 추가 (나머지는 자동)
    langfuse_context.update_current_trace(
        metadata={
            "num_docs_retrieved": len(docs),
            "avg_relevance_score": sum(d['score'] for d in docs) / len(docs)
        }
    )
    
    return response.content
```

