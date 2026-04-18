import boto3
from pymilvus import connections, Collection
from sentence_transformers import SentenceTransformer, CrossEncoder


class RAGSearch:
    def __init__(
        self,
        host: str = "localhost",
        port: str = "19530",
        collection_name: str = "papers",
        embed_model: str = "BAAI/bge-m3",
        rerank_model: str = "BAAI/bge-reranker-v2-m3",
        bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0",
        aws_region: str = "ap-northeast-2",
        alias: str = "default",
    ):
        # 1. Milvus 연결
        connections.connect(alias=alias, host=host, port=port)
        self.collection = Collection(collection_name, using=alias)
        self.collection.load()

        # 2. 임베딩 모델 (저장 때와 동일해야 함)
        self.embedder = SentenceTransformer(embed_model)

        # 3. Reranker
        self.reranker = CrossEncoder(rerank_model)

        # 4. Bedrock 클라이언트
        self.bedrock = boto3.client("bedrock-runtime", region_name=aws_region)
        self.model_id = bedrock_model_id

    # ---------- 단계별 메서드 ----------

    def retrieve(self, query: str, top_k: int = 20) -> list[dict]:
        """Milvus에서 유사도 기반 top-k 청크 검색"""
        vec = self.embedder.encode([query], normalize_embeddings=True).tolist()
        results = self.collection.search(
            data=vec,
            anns_field="embedding",
            param={"metric_type": "COSINE", "params": {"nprobe": 16}},
            limit=top_k,
            output_fields=["text", "doc_name", "page", "source"],
        )
        return [
            {
                "text": hit.entity.get("text"),
                "doc_name": hit.entity.get("doc_name"),
                "page": hit.entity.get("page"),
                "source": hit.entity.get("source"),
                "score": float(hit.score),
            }
            for hit in results[0]
        ]

    def rerank(self, query: str, hits: list[dict], top_n: int = 5) -> list[dict]:
        """CrossEncoder로 (query, doc) 관련도 재평가 후 상위 top_n 반환"""
        if not hits:
            return []
        pairs = [(query, h["text"]) for h in hits]
        scores = self.reranker.predict(pairs)
        for h, s in zip(hits, scores):
            h["rerank_score"] = float(s)
        hits.sort(key=lambda x: x["rerank_score"], reverse=True)
        return hits[:top_n]

    def generate(self, query: str, contexts: list[dict]) -> str:
        """Bedrock Converse API로 답변 생성"""
        context_block = "\n\n".join(
            f"[출처: {c['doc_name']} p.{c['page']}]\n{c['text']}"
            for c in contexts
        )

        system_prompt = (
            "당신은 논문 기반 질의응답 도우미입니다. "
            "반드시 주어진 컨텍스트 안의 내용만 근거로 답하고, "
            "근거가 부족하면 모른다고 답하세요. "
            "답변 끝에 참조한 문서명과 페이지를 명시하세요."
        )
        user_message = f"[컨텍스트]\n{context_block}\n\n[질문]\n{query}"

        response = self.bedrock.converse(
            modelId=self.model_id,
            system=[{"text": system_prompt}],
            messages=[{"role": "user", "content": [{"text": user_message}]}],
            inferenceConfig={
                "maxTokens": 1024,
                "temperature": 0.2,
            },
        )
        return response["output"]["message"]["content"][0]["text"]

    def query(self, query: str, top_k: int = 20, top_n: int = 5) -> dict:
        retrieved = self.retrieve(query, top_k=top_k)
        reranked = self.rerank(query, retrieved, top_n=top_n)
        answer = self.generate(query, reranked)
        return {
            "query": query,
            "answer": answer,
            "contexts": reranked,
        }
