## 2. 도구 + 조건부 라우팅 + HITL ##

### 1. 왜 이 패턴을 배우는가 ###
챕터 1에서 만든 그래프는 정해진 순서대로 흐르는 파이프라인이었다. 하지만 실제 에이전트는 상황에 따라 다르게 움직여야 한다.

* 사용자의 질문을 보고 어떤 도구를 쓸지 LLM이 결정해야 한다
* 필요하면 도구를 여러 번 반복 호출해야 한다 (ReAct 루프)
* 돈이 드는 작업이나 되돌릴 수 없는 작업은 사람의 승인을 받아야 한다
이 세 가지를 조합한 구조가 업무용 에이전트의 표준 뼈대다.

### 2. 이번 모듈에서 만들 것 ###
* 사용자: "us-west-2의 c7i 인스턴스 가격 알려줘. Graviton 대안도."
* 에이전트가 판단해서 도구를 호출
  - list_ec2_instances(region)
  - get_pricing(instance_type)
  - recommend_graviton_alternative(instance_type)
* 민감 작업(terminate_instance)은 사람 승인 후에만 실행
