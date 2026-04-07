```bash
kubectl -f https://raw.githubusercontent.com/gnosia93/eks-agentic-ai/refs/heads/main/code/yaml/vllm-deployment.yaml
```


### 메모리 계산 
* L40S 48GB per GPU:
  * 모델 가중치:  13.5 GB (TP=4)      <--- 27B * 2byte = 54 GB
  * KV Cache:    ~28 GB
  * 여유분:       ~4.8 GB (activation, CUDA, NCCL)        <--- vllm 파라미터 --gpu-memory-utilization=0.90 
  * 미사용:       ~1.7 GB (10% 밖)
