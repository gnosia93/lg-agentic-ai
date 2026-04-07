## KEDA ##

아래 명령어로 KEDA 를 설치한다.
```
helm repo add kedacore https://kedacore.github.io/charts
helm repo update
helm install keda kedacore/keda --namespace keda --create-namespace
```

아래와 같이 ScaledObject 를 생성한다. ScaledObject 는 KEDA가 제공하는 CRD(Custom Resource Definition)로 "어떤 Deployment를 어떤 메트릭 기준으로 스케일링할지" 정의하는 리소스이다. ScaledObject를 만들면 KEDA가 알아서 HPA를 생성하고 관리하기 때문에 직접 HPA를 만들 필요 없다.
```
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: vllm-qwen-scaler
spec:
  scaleTargetRef:
    name: vllm-qwen
  minReplicaCount: 2
  maxReplicaCount: 8
  cooldownPeriod: 300          # 축소 전 5분 대기
  triggers:
    - type: prometheus
      metadata:
        serverAddress: http://prometheus-server.monitoring:9090
        query: sum(vllm:num_requests_waiting{namespace="default"})
        threshold: "10"
```
* Prometheus → KEDA (직접 연결) → HPA 자동 생성
* 동작 방식
```
1. 대기 요청 20개 → 파드 8개로 스케일 아웃
2. 트래픽 감소 → 대기 요청 3개 (threshold 10 이하)
3. 5분(cooldownPeriod) 동안 계속 낮은 상태 유지되는지 확인
4. 유지되면 파드 1개 제거 → 7개
5. 또 5분 대기 → 여전히 낮으면 → 6개
6. ...반복...
7. minReplicaCount=2까지만 줄임
```
