## vLLM 배포하기 ##

Qwen2.5-27B 모델을 g6e.12xlarge (L40S 48GB * 4EA, TP=4) 설정으로 2개의 파드로 구성한다.
[g6e.12xlarge](https://aws.amazon.com/ko/ec2/instance-types/g6e/) 인스턴스는 2대가 필요하다.

* https://github.com/gnosia93/eks-agentic-ai/blob/main/code/yaml/vllm-deployment.yaml
```bash
kubectl -f https://raw.githubusercontent.com/gnosia93/eks-agentic-ai/refs/heads/main/code/yaml/vllm-deployment.yaml
```

vLLM은 시작 시 먼저 모델 가중치를 GPU 메모리에 로드하고, gpu-memory-utilization 설정값에 따라 사용 가능한 전체 메모리 범위를 결정한다. 그런 다음 모델 가중치와 내부 버퍼를 제외한 나머지 메모리를 KV Cache로 자동 할당하며, 이 KV Cache 크기와 max-model-len을 기반으로 동시에 처리할 수 있는 최대 요청 수를 자동으로 결정한다.
모델 가중치 로드 → 남은 메모리 계산 (gpu-memory-utilization 기준) → 남은 메모리를 KV Cache로 자동 할당 → KV Cache 크기 + max-model-len 기반으로 동시 처리 가능 수 자동 결정

* vLLM 파라미터 
  * --model                     사용모델
  * --tensor-parallel-size      GPU 갯수
  * --max-model-len             최대 시퀀스 길이
  * --gpu-memory-utilization    GPU 메모리 상용률(90% 권장)
     - CUDA 커널 실행 오버헤드, Activation 임시 버퍼, Tensor 연산 중간 결과물, NCCL 통신 버퍼 (TP 사용시)


### 테스트 하기 ###
```bash
# 클러스터 내부에서 테스트 (임시 파드)
kubectl run test --rm -it --image=curlimages/curl -- \
  curl http://vllm-qwen-svc/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }'
```
또는
```bash
# 터미널 1: 포트 포워딩
kubectl port-forward svc/vllm-qwen-svc 8080:80

# 터미널 2: 테스트
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }'
```

### 성능 밴치마크 ###
```bash
kubectl get pods

# vLLM 벤치마크 (파드 안에서 실행)
kubectl exec -it <vllm-pod-name> -- python -m vllm.entrypoints.openai.api_server &

python -m vllm.entrypoints.openai.bench_serving \
  --backend openai \
  --base-url http://localhost:8000 \
  --model qwen \
  --num-prompts 100 \
  --request-rate 10
```

