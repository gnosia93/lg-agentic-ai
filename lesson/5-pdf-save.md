## PDF 문서 저장하기 (레이아웃 파싱/청킹/임베딩) ##

### 프로젝트 구조 ### 
```
rag/
├── PDFVectorStore.py       ← curl로 받은 파일
└── main.py                 ← 여기서 from PDFVectorStore import ...
```

### 실행하기 ###
```
mkdir rag && cd rag
pip install pymilvus langchain langchain-community pymupdf sentence-transformers

curl -o PDFVectorStore.py
https://raw.githubusercontent.com/gnosia93/eks-agentic-ai/refs/heads/main/code/rag/PDFVectorStore.py
```

[main.py]
```
from PDFVectorStore import PDFVectorStore

store = PDFVectorStore(
    host="<리모트_IP_또는_호스트>",
    port="19530",
    collection_name="papers",
    reset=True,  # 처음 한 번만
)

store.add_pdf("LoRA_Low-Rank_Adaptation.pdf")
# 이후 다른 PDF도 계속
# store.add_pdf("another.pdf")
```
