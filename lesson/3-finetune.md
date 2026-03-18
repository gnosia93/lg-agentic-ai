
## 파인튜닝 ##

이 코드는 HuggingFace에서 Qwen 27B 모델을 다운로드하여 GPU에 올린 후, LoRA 기법을 적용해 전체 파라미터의 0.3%만 선택적으로 학습합니다. DevOps/ML 도메인의 질문-답변 데이터를 모델이 이해하는 Chat 형식으로 변환하고, 이를 3 epoch 반복 학습한 뒤 학습된 LoRA 어댑터만 저장합니다. LoRA 덕분에 원본 모델은 그대로 두고 작은 어댑터만 추가 학습하므로, 단일 GPU에서도 27B 모델 파인튜닝이 가능합니다.

### 파인튜닝 해보기 ###

주피터 노트북의 셀에서 아래 qwen_finetune.py 를 실행합니다. 

* https://github.com/gnosia93/agentic-ai-eks/blob/main/code/qwen_finetune.py

![](https://github.com/gnosia93/agentic-ai-eks/blob/main/lesson/images/ft-code.png)



### 필요 샘플수 ###
![](https://github.com/gnosia93/agentic-ai-eks/blob/main/lesson/images/ft-sample.png)
