### 훈련데이터 포맷변환 ###

tokenizer.apply_chat_template() 은
알파카 포멧의 데이터를 
```
{
  "instruction": "Kubernetes Pod가 CrashLoopBackOff일 때 디버깅 방법은?",
  "output": "kubectl describe pod, kubectl logs 순서로 확인하고..."
}
```
Qwen의 아래와 같은 포맷으로 변경한다. 
```
<|im_start|>system
You are a helpful DevOps and ML engineering assistant.<|im_end|>
<|im_start|>user
Kubernetes Pod가 CrashLoopBackOff일 때 디버깅 방법은?<|im_end|>
<|im_start|>assistant
kubectl describe pod, kubectl logs 순서로 확인하고...<|im_end|>
```

### 토크나이저 저장 ###
모델 학습시 토크나이저는 변경이 되지 않기 때문에 다음 훈련 또는 인퍼런스시 허깅페이스의 토크나이저를 그래도 사용해도 된다. 
보통 관례적으로 저장하며, 다음과 같은 경우는 꼭 저장해야 한다. 
* 특수 토큰을 추가한 경우 (add_special_tokens, add_tokens)
* pad_token을 변경한 경우 (예: tokenizer.pad_token = tokenizer.eos_token)
* chat template을 커스텀한 경우


