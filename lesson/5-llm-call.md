
* https://github.com/gnosia93/eks-agentic-ai/blob/main/code/rag/rag-pipeline.py
```
그리고 Bedrock 콘솔에서 모델 액세스 활성화(Model access)도 미리 해둬야 합니다.
리전 확인: Cohere Rerank v3.5와 Claude 모델이 모든 리전에 있는 건 아닙니다. ap-northeast-2에 없는 모델이면 us-west-2 등으로 바꿔야 할 수 있어요
모델 ID: 위 Claude 모델 ID는 예시입니다. Bedrock 콘솔에서 실제 사용 가능한 ID 확인하세요
스트리밍: 실제 앱이면 invoke_model_with_response_stream 쓰는 게 UX 좋습니다
리전/모델 가용성만 확인하면 바로 돌아갈 코드입니다.
```
