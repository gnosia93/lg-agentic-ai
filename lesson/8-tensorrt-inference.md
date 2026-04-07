
```bash
kubectl apply -f https://raw.githubusercontent.com/gnosia93/eks-agentic-ai/refs/heads/main/code/yaml/trtllm-engine-build.yaml

kubectl wait --for=condition=complete job/trtllm-engine-build --timeout=60m

kubectl logs job/trtllm-engine-build

kubectl apply -f trtllm-deployment.yaml
```
