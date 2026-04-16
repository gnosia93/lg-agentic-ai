## 인퍼런스용 GPU 선정하기 ##

![](https://github.com/gnosia93/eks-agentic-ai/blob/main/lesson/images/gpu-sel-process.png)


### 모델 메모리 계산 공식 ###
```
모델 메모리 ≈ 파라미터 수 × 바이트/파라미터

FP16: 파라미터 수 × 2 bytes
FP8:  파라미터 수 × 1 byte
INT4: 파라미터 수 × 0.5 bytes
```

### KV 캐시 메모리 계산 ###
```
KV Cache ≈ 2 × num_layers × hidden_dim × seq_len × batch_size × bytes
```
* 실제로는 동시 요청 수와 시퀀스 길이에 따라 수 GB ~ 수십 GB 추가됨.
* 2x 배수를 곱하는 이유는 하나의 Key 다른 하나는 Value 캐시임.
* hidden_dim(임베딩 백터 사이즈)를 곱하는 이유는 각 토큰의 K, V가 hidden_dim 크기의 벡터이기 때문.
  * 예: hidden_dim = 4096이면, K = 4096개의 숫자 / V = 4096개의 숫자

### 빠른 판단 공식 ###

```
필요한 GPU 수 (최소) = 모델 메모리 / (GPU VRAM × 0.8)

예: Llama 70B FP16
= 140GB / (80GB × 0.8)
= 140 / 64
= 2.19 → H100 3장 (KV cache 여유 포함)

예: Llama 70B FP8
= 70GB / (80GB × 0.8)
= 70 / 64
= 1.09 → H100 1장으로 가능 (KV cache 여유 적음)
```
![](https://github.com/gnosia93/eks-agentic-ai/blob/main/lesson/images/gpu-memory-structure.png)

### GPU별 매칭 가이드 (예시) ###
```
GPU              VRAM      FP16 기준     양자화(INT8/FP8) 기준
──────────────────────────────────────────────────────────────
A10G             24GB      7B            13B
L4               24GB      7B            13B
A100 (40GB)      40GB      13B           25B
A100 (80GB)      80GB      30B           55B
H100 (80GB)      80GB      30B           55B
H200 (141GB)     141GB     55B           70B
```

