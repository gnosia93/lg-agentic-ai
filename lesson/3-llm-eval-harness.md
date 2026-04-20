
### 테스트 대상 모델 ###
```
[대상 모델]
 ├─ 로컬 배포 (GPU Pod)
 │   ├─ Llama 3.1 8B
 │   ├─ Qwen 2.5 7B / 32B
 │   ├─ Gemma 2 9B
 │   └─ Mistral 7B
 └─ API 호출
     ├─ Claude 3.5 Sonnet (Bedrock)
     ├─ Claude 3 Haiku (Bedrock)
     └─ Llama 3.1 70B (Bedrock)
```


### Bedrock 접근 준비 ###

IRSA로 평가 Pod에 권한 부여:
```
cat > bedrock-eval-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
      "bedrock:Converse",
      "bedrock:ConverseStream"
    ],
    "Resource": "*"
  }]
}
EOF

aws iam create-policy \
  --policy-name LLMEvalBedrockAccess \
  --policy-document file://bedrock-eval-policy.json

eksctl create iamserviceaccount \
  --cluster=$CLUSTER_NAME \
  --namespace=llm-eval \
  --name=llm-eval-sa \
  --attach-policy-arn=arn:aws:iam::${ACCOUNT_ID}:policy/LLMEvalBedrockAccess \
  --approve
```

### HuggingFace 토큰 (게이트 모델용) ###
Llama, Gemma 등 승인 필요한 모델은 HF 토큰 시크릿으로 제공:
```
kubectl create secret generic hf-token \
  -n llm-eval \
  --from-literal=token=$HF_TOKEN
```


### Deployment ###
```
# vllm-qwen25-7b.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-qwen25-7b
  namespace: llm-eval
spec:
  replicas: 1
  selector:
    matchLabels: {app: vllm-qwen25-7b}
  template:
    metadata:
      labels: {app: vllm-qwen25-7b}
    spec:
      nodeSelector:
        nvidia.com/gpu.product: NVIDIA-A10G   # 노드에 맞춰 수정
      containers:
        - name: vllm
          image: vllm/vllm-openai:latest
          args:
            - "--model=Qwen/Qwen2.5-7B-Instruct"
            - "--max-model-len=8192"
            - "--gpu-memory-utilization=0.9"
            - "--port=8000"
          ports:
            - containerPort: 8000
          env:
            - name: HUGGING_FACE_HUB_TOKEN
              valueFrom:
                secretKeyRef: {name: hf-token, key: token}
            - name: HF_HOME
              value: /cache/hf
          resources:
            limits:
              nvidia.com/gpu: 1
              memory: "32Gi"
          volumeMounts:
            - name: hf-cache
              mountPath: /cache/hf
      volumes:
        - name: hf-cache
          emptyDir:
            sizeLimit: 50Gi
---
apiVersion: v1
kind: Service
metadata:
  name: vllm-qwen25-7b
  namespace: llm-eval
spec:
  selector: {app: vllm-qwen25-7b}
  ports:
    - port: 8000
      targetPort: 8000
```
