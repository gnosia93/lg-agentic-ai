init container는 성공했는데, main container(triton)가 계속 크래시, 6번 재시작
```
kubectl logs trtllm-qwen-78d96f8d54-lf2bl -c triton --previous
```
--previous는 이전에 크래시한 컨테이너의 로그를 보여준다.

