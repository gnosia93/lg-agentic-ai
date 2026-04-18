

* https://github.com/gnosia93/eks-agentic-ai/blob/main/code/rag/rag-mcp-server.py
```
curl -o rag-mcp-server.py \
https://raw.githubusercontent.com/gnosia93/eks-agentic-ai/refs/heads/main/code/rag/rag-mcp-server.py
```
* MILVUS_HOST의 기본값이 milvus.milvus.svc.cluster.local. 같은 클러스터 내부에선 이 이름으로 바로 접근 가능.

```
pip install mcp

# 별도 터미널에서 Milvus port-forward 켜두기
kubectl port-forward -n milvus svc/milvus 19530:19530

# 다른 터미널
export AWS_REGION=ap-northeast-2
npx @modelcontextprotocol/inspector python rag_mcp_server.py
```
