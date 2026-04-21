
### 종합 선택 기준 ###

실무에서 모델 고를 때 체크하는 것들:

* 품질: MMLU, 도메인 벤치, LLM-as-Judge 점수
* 속도: TTFT, TPOT, throughput
* 메모리: VRAM 요구량, 최대 컨텍스트 길이
* 라이선스: 상업 사용 가능 여부
* 언어: 한국어 지원 수준
운영 비용: 위 1+2+3 합산해서 "달러당 품질"

### 측정방법 ###

```
# vLLM 소스 받기
cd ~
git clone https://github.com/vllm-project/vllm.git
cd vllm

# 현재 설치된 vLLM 버전과 같은 태그로 체크아웃 (중요)
pip show vllm | grep Version
# 예: Version: 0.6.3
git checkout v0.6.3

# 의존성만 추가 설치 (vLLM 본체는 이미 있음)
pip install aiohttp datasets transformers
```

```
cd ~/vllm

python benchmarks/benchmark_serving.py \
  --backend vllm \
  --base-url http://localhost:8000 \
  --model Qwen/Qwen2.5-7B-Instruct \
  --dataset-name sharegpt \
  --dataset-path ShareGPT_V3_unfiltered_cleaned_split.json \
  --num-prompts 100 \
  --request-rate 10
```

### 전용 벤치마크 도구 ###
* GenAI-Perf (NVIDIA): https://github.com/triton-inference-server/perf_analyzer
* llmperf (Anyscale): https://github.com/ray-project/llmperf
