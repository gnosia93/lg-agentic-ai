## 파인튜닝 ##

이 코드는 HuggingFace에서 Qwen 27B 모델을 다운로드하여 GPU에 올린 후, LoRA 기법을 적용해 전체 파라미터의 0.3%만 선택적으로 학습한다. DevOps/ML 도메인의 질문-답변 데이터를 모델이 이해하는 Chat 형식으로 변환하고, 이를 3 epoch 반복 학습한 뒤 학습된 LoRA 어댑터만 저장한다. LoRA 덕분에 원본 모델은 그대로 두고 작은 어댑터만 추가 학습하므로, 단일 GPU에서도 27B 모델 파인튜닝이 가능하다

### 파인튜닝 해보기 ###

주피터 노트북의 셀에 아래 qwen_finetune_inst.py 를 복사하여 실행한다. 

* https://github.com/gnosia93/agentic-ai-eks/blob/main/code/qwen_finetune_inst.py

![](https://github.com/gnosia93/agentic-ai-eks/blob/main/lesson/images/ft-code.png)


### 필요 샘플수 ###
파인 튜닝의 목적에 따라서 필요 샘플수는 달라진다. 
![](https://github.com/gnosia93/agentic-ai-eks/blob/main/lesson/images/ft-sample.png)


## 추론 ##
PeftModel.from_pretrained(base_model, "./qwen-devops-lora") 에서 기존 base_model 의 가중치 값과 LoRA 로 튜닝된 가중치 값을 합쳐서 모델을 로딩한다.
```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# 1. 원본 모델 + LoRA 어댑터 합치기
base_model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen3.5-27B",
    torch_dtype=torch.bfloat16,
    device_map={"": 0},
)
model = PeftModel.from_pretrained(base_model, "./qwen-devops-lora")
tokenizer = AutoTokenizer.from_pretrained("./qwen-devops-lora")

# 2. 추론
messages = [
    {"role": "system", "content": "You are a helpful DevOps and ML engineering assistant."},
    {"role": "user", "content": "GPU OOM이 발생했을 때 해결 방법을 알려줘"},
]

text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(text, return_tensors="pt").to(model.device)

with torch.no_grad():
    outputs = model.generate(**inputs, max_new_tokens=512)

response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
print(response)
```

### vLLM 서빙 ###

* 가중치 머지후 서빙 
```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

# 베이스 모델 + LoRA 어댑터 로드
base_model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.1-8B-Instruct")
model = PeftModel.from_pretrained(base_model, "./lora-adapter")

# 머지
merged_model = model.merge_and_unload()

# 저장
merged_model.save_pretrained("./merged-model")
AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B-Instruct").save_pretrained("./merged-model")

# 머지된 모델 서빙
vllm serve ./merged-model --port 8000
```

* 자주쓰는 옵션
```bash
vllm serve ./my-model \
  --port 8000 \
  --tensor-parallel-size 2 \        # GPU 2장에 모델 분할
  --gpu-memory-utilization 0.9 \    # GPU 메모리 90% 사용
  --max-model-len 4096 \            # 최대 컨텍스트 길이
  --dtype auto \                    # 데이터 타입 자동 (bf16/fp16)
  --quantization awq \              # 양자화 모델일 경우 (awq, gptq, squeezellm)
  --chat-template ./template.jinja  # 커스텀 채팅 템플릿
```


## 파인튜닝된 모델 성능 검증 ##

1. Golden Dataset (필수):
```
from sentence_transformers import SentenceTransformer, util

# 임베딩 모델
model = SentenceTransformer('all-MiniLM-L6-v2')

def similarity(text1: str, text2: str) -> float:
    """두 텍스트 유사도 (0-1)"""
    emb1 = model.encode(text1)
    emb2 = model.encode(text2)
    
    score = util.cos_sim(emb1, emb2).item()
    return score

# 파인튜닝 전에 미리 준비
golden_test = [
    {"input": "환불 방법은?", "expected": "고객센터 1234..."},
    {"input": "배송 조회", "expected": "주문번호를 입력..."},
    # 50-100개 정도
]

# 자동 평가
pass_rate = 0
for case in golden_test:
    response = model.invoke(case["input"])
    if similarity(response, case["expected"]) > 0.7:
        pass_rate += 1

print(f"Pass rate: {pass_rate / len(golden_test)}")
```

2. A/B 테스트 (실전):
```
# 실제 트래픽 10%만 새 모델로
if random.random() < 0.1:
    response = finetuned_model.invoke(query)
else:
    response = base_model.invoke(query)

# 사용자 피드백 수집 (👍👎)
# 1주일 후 비교
```

3. 샘플 사람 검증:
```
# 매일 랜덤 10개만 사람이 확인
daily_sample = random.sample(responses, 10)

# Slack/이메일로 전송
# 팀원이 간단히 체크
```

4. 자동 Regression 체크:
```
import json

def load_previous_good_cases():
    """이전에 잘 작동했던 케이스 로드"""
    
    # JSON 파일에서 로드
    with open("regression_test.json") as f:
        return json.load(f)

# regression_test.json
[
    {
        "input": "환불 방법은?",
        "expected_quality": "good",
        "timestamp": "2024-01-01"
    },
    {
        "input": "배송 조회",
        "expected_quality": "good",
        "timestamp": "2024-01-02"
    }
]

def quality_check(query: str, response: str) -> str:
    """질문과 응답 함께 체크"""
    
    # 1. 기본 체크
    if len(response) < 10 or not response.strip():
        return "fail"
    
    # 2. 질문과 관련성
    if not is_relevant(query, response):
        return "fail"
    
    # 3. 에러 메시지
    if "error" in response.lower():
        return "fail"
    
    return "pass"

def is_relevant(query: str, response: str) -> bool:
    """질문과 응답 관련성 체크"""
    # 임베딩 유사도
    score = similarity(query, response)
    return score > 0.3  # 최소 관련성


# 기존 잘 되던 케이스 자동 테스트
regression_test = load_previous_good_cases()

for case in regression_test:
    response = model.invoke(case["input"])
    assert quality_check(response) == "pass"
```
결론: Golden Dataset + A/B 테스트 + 샘플 검증이 가장 현실적이다.


