from pathlib import Path
from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility,
)
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer


class PDFVectorStore:
    def __init__(
        self,
        host: str = "localhost",
        port: str = "19530",
        user: str | None = None,
        password: str | None = None,
        collection_name: str = "documents",
        model_name: str = "BAAI/bge-m3",
        dimension: int = 1024,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
        reset: bool = False,
        alias: str = "default",
    ):
        self.collection_name = collection_name
        self.dimension = dimension
        self.alias = alias

        # 1. Milvus 연결
        conn_kwargs = {"alias": alias, "host": host, "port": port}
        if user and password:
            conn_kwargs.update({"user": user, "password": password})
        connections.connect(**conn_kwargs)

        # 2. 임베딩 모델
        self.model = SentenceTransformer(model_name)

        # 3. 청크 스플리터
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " "],
        )

        # 4. 컬렉션 준비
        if reset and utility.has_collection(collection_name, using=alias):
            utility.drop_collection(collection_name, using=alias)

        if utility.has_collection(collection_name, using=alias):
            self.collection = Collection(collection_name, using=alias)
        else:
            self.collection = self._create_collection()

        self.collection.load()

    def _create_collection(self) -> Collection:
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dimension),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=8192),
            FieldSchema(name="doc_name", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=1024),
            FieldSchema(name="page", dtype=DataType.INT64),
        ]
        schema = CollectionSchema(fields, description="PDF chunks with embeddings")
        collection = Collection(self.collection_name, schema, using=self.alias)

        # 벡터 필드에 인덱스 생성 (검색 성능용)
        collection.create_index(
            field_name="embedding",
            index_params={
                "index_type": "IVF_FLAT",
                "metric_type": "COSINE",
                "params": {"nlist": 128},
            },
        )
        return collection

    def _embed(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts, normalize_embeddings=True).tolist()

    def add_pdf(
        self,
        pdf_path: str,
        batch_size: int = 32,
    ) -> int:
        """PDF 하나를 로드→청킹→임베딩→Milvus 저장. 삽입한 청크 수 반환."""
        docs = PyMuPDFLoader(pdf_path).load()
        chunks = self.splitter.split_documents(docs)

        doc_name = Path(pdf_path).stem
        total = 0

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [c.page_content for c in batch]
            vectors = self._embed(texts)
            doc_names = [doc_name] * len(batch)
            sources = [c.metadata.get("source", pdf_path) for c in batch]
            pages = [int(c.metadata.get("page", -1)) for c in batch]

            # 컬럼 기반 삽입: 스키마의 id(auto_id) 제외한 순서대로
            self.collection.insert([vectors, texts, doc_names, sources, pages])
            total += len(batch)

        self.collection.flush()
        print(f"[{doc_name}] inserted {total} chunks")
        return total
