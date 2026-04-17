## 추론 성능 비교 (versus vLLM) ##

```
python --version
```


```
pip install genai-perf

genai-perf profile \
    --model qwen \
    --endpoint-type chat \
    --url http://<서비스주소>:8000 \
    --num-prompts 100 \
    --concurrency 10
```
#### 측정 항목: ####
* TTFT (Time To First Token): 첫 토큰까지 걸리는 시간
* ITL (Inter-Token Latency): 토큰 간 지연
* Throughput: 초당 생성 토큰 수
* Request Latency: 요청당 전체 응답 시간

### 측정 결과 ###
* vLLM
  
* TensorRT-LLM


