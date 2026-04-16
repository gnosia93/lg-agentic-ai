### On-Deman Node 상태 Ready -> Not Ready ###

보통 아래와 같은 경우에 발생한다. 
* 노드 디스크 부족 — 디스크가 꽉 차면 kubelet이 노드를 NotReady로 전환하고 파드를 evict
* kubelet 헬스체크 실패 — GPU 드라이버 문제나 메모리 부족으로 kubelet이 응답 못하는 경우
* 노드 메모리(OOM) — 시스템 메모리가 부족하면 커널이 프로세스를 kill

### 원인 파악 ###
```
kubectl describe node <노드이름>
```
Conditions 섹션에서 MemoryPressure, DiskPressure, PIDPressure 중 True인 게 있는지 확인

추가로 이벤트 로그 확인:
```
kubectl get events --sort-by='.lastTimestamp' | grep NotReady
```
NotReady 발생하면 이 두 명령어 결과를 알려주시면 원인을 찾을 수 있다.
