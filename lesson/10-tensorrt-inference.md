
## TensorRT-LLM 배포하기 ##

S3 버킷을 생성하고 테라폼에서 생성한 eks-agentic-ai-s3-access 을 쿠버네티스의 서비스 어카운트에 할당한다
```bash
export CLUSTER_NAME=eks-agentic-ai
export ENGINE_BUCKET=${CLUSTER_NAME}-tensorrt-llm-$(date +%Y%m%d%H%M)
export ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)

aws s3 mb s3://${ENGINE_BUCKET} --region ap-northeast-2

kubectl create serviceaccount s3-access-sa -n default
kubectl annotate serviceaccount s3-access-sa -n default \
  eks.amazonaws.com/role-arn=arn:aws:iam::${ACCOUNT_ID}:role/eks-agentic-ai-s3-access
```

트리톤 서버를 이용하여 Qwen 모델을 컴파일 한다.
```bash
mkdir triton && cd triton
curl -o trtllm-engine-build.yaml \
  https://raw.githubusercontent.com/gnosia93/eks-agentic-ai/refs/heads/main/code/yaml/trtllm-engine-build.yaml

envsubst < trtllm-engine-build.yaml | kubectl apply -f -

kubectl logs job/trtllm-engine-build -f
```
[결과]
```
Download complete. Moving file to /workspace/qwen-hf/model-00003-of-00037.safetensors
Fetching 47 files:  19%|█▉        | 9/47 [00:10<00:43,  1.14s/it]Downloading 'model-00013-of-00037.safetensors' to '/workspace/qwen-hf/.cache/huggingface/download/PWuBP-Hof8RRqr17zbm-lsSqkWg=.091e0a428c3786c0fe75fb9f3445ea7173f0f6af35133a898bf817890d16bec3.incomplete'
Downloading 'model-00014-of-00037.safetensors' to '/workspace/qwen-hf/.cache/huggingface/download/thvUQ1D_SSAk7X9laonYIrmn2cY=.cdb3585244781534f601d22fbba8e2583fe0fc08d46846df86788bb08a4f9b9b.incomplete'
Download complete. Moving file to /workspace/qwen-hf/model-00009-of-00037.safetensors
Downloading 'model-00015-of-00037.safetensors' to '/workspace/qwen-hf/.cache/huggingface/download/5165UonhYHQraDFi8a6AzeYNDDA=.8f6d40610c1470d4097c298a3ad6951ae06bf60458d743fb77be4b52753e0b9c.incomplete'
Download complete. Moving file to /workspace/qwen-hf/model-00005-of-00037.safetensors
Fetching 47 files:  23%|██▎       | 11/47 [00:20<01:33,  2.59s/it]Download complete. Moving file to /workspace/qwen-hf/model-00012-of-00037.safetensors
Download complete. Moving file to /workspace/qwen-hf/model-00014-of-00037.safetensors
Download complete. Moving file to /workspace/qwen-hf/model-00013-of-00037.safetensors
Downloading 'model-00016-of-00037.safetensors' to '/workspace/qwen-hf/.cache/huggingface/download/Pqpxba7EhM6HCzYC2Kg8oCdwqeA=.32b0cb30dcde0bd0a00c2191cd0ced6786aed1126b424e2827987d53cb412eb7.incomplete'
...
```

[trtllm-qwen.yaml](https://github.com/gnosia93/eks-agentic-ai/blob/main/code/yaml/trtllm-engine-build.yaml) 로 TensorRT-LLM 서버를 배포한다.
```
curl -o trtllm-qwen.yaml \
  https://raw.githubusercontent.com/gnosia93/eks-agentic-ai/refs/heads/main/code/yaml/trtllm-qwen.yaml
kubectl apply -f trtllm-qwen.yaml
```

## 레퍼런스 ##
* https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/index.html


