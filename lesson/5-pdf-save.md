### 1. 레이아웃 파싱 ###
PDF는 단순 텍스트가 아니라서 도구 선택이 품질을 좌우합니다.

* PyPDF / pdfplumber — 가볍고 빠름. 단순 텍스트 PDF에 적합. 표/이미지는 약함
* unstructured — 요소별로 분류해줌 (제목, 본문, 표, 리스트). 실무에서 많이 씀
* PyMuPDF (fitz) — 속도 빠르고 레이아웃 정보 풍부
* Docling — IBM이 만든 최신 도구. 레이아웃/표 인식 우수
* LlamaParse — SaaS. 복잡한 문서에 강력함. 유료
* AWS Textract — AWS 환경이면 좋은 선택. 표 인식 훌륭


### 2. 청킹 ###
레이아웃 파싱 결과를 살려서 청킹하는 게 핵심입니다.

#### 청킹 전략 ####
* Fixed size — 글자/토큰 수로 자름. 단순하지만 문맥 깨짐
* Recursive — 구분자 우선순위로 자름 (문단 → 문장 → 단어). 일반적인 기본값
* Semantic — 의미 단위로 자름. 품질 좋지만 느리고 비쌈
* Document-aware — 레이아웃 정보 활용 (제목 단위, 섹션 단위). 레이아웃 파싱과 궁합 최고
  
추천 파라미터 (한국어 기준):
```
chunk_size: 300500 토큰 (또는 8001200자)
chunk_overlap: 1020% (50100 토큰)
```

꼭 챙길 메타데이터:
```
{
    "source": "document.pdf",
    "page": 12,
    "section": "3.2 아키텍처",
    "chunk_id": "doc1_p12_c3",
    "type": "paragraph"  # or "table", "heading"
}
```
나중에 검색 결과에 출처 표시하거나 필터링할 때 꼭 필요합니다.


### 3. 임베딩 ###
모델 선택 (한국어 포함):

* BAAI/bge-m3 — 다국어, 성능 우수, 8192 토큰 지원. 추천
* intfloat/multilingual-e5-large — 안정적
* jhgan/ko-sroberta-multitask — 한국어 특화, 가벼움
* OpenAI text-embedding-3-small/large — API, 비용 발생
* Cohere embed-multilingual-v3 — API

배치 처리 주의:
```
# 한 번에 다 때려넣지 말고 배치로
batch_size = 32
for i in range(0, len(chunks), batch_size):
    batch = chunks[i:i+batch_size]
    embeddings = model.encode(batch, normalize_embeddings=True)
    # Milvus insert
normalize_embeddings=True로 하면 COSINE 유사도 쓸 때 편합니다.
```

## 샘플 코드 ##
```
# 1. 레이아웃 파싱
from unstructured.partition.pdf import partition_pdf

elements = partition_pdf(
    filename="doc.pdf",
    strategy="hi_res",       # 레이아웃 인식
    infer_table_structure=True
)

# 2. 청킹 (레이아웃 인식)
from unstructured.chunking.title import chunk_by_title

chunks = chunk_by_title(
    elements,
    max_characters=1000,
    overlap=100
)

# 3. 임베딩
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-m3")
texts = [c.text for c in chunks]
embeddings = model.encode(texts, normalize_embeddings=True)

# 4. Milvus 저장
from pymilvus import Collection

collection = Collection("docs")
data = [
    texts,                                    # text 필드
    embeddings.tolist(),                      # embedding 필드
    [c.metadata.page_number for c in chunks], # page 필드
    [c.metadata.filename for c in chunks],    # source 필드
]
collection.insert(data)
collection.flush()
```
* "파싱 품질이 RAG 품질을 좌우한다" — 표가 깨지거나 순서가 섞이면 검색 결과 엉망
* "청크 크기 vs 검색 정확도 trade-off" — 작으면 정밀하지만 문맥 부족, 크면 반대
* "메타데이터는 나중에 반드시 쓰인다" — 필터링, 출처 표시, 디버깅
* "임베딩 모델과 거리 메트릭 짝 맞추기" — normalize + COSINE이 제일 무난
