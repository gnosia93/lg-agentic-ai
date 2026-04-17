### init container는 성공했는데, main container(triton)가 계속 크래시, 6번 재시작 ###
```
kubectl logs trtllm-qwen-78d96f8d54-lf2bl -c triton --previous
```
--previous는 이전에 크래시한 컨테이너의 로그를 보여준다.

```
/usr/local/lib/python3.12/dist-packages/torch/cuda/__init__.py:63: FutureWarning: The pynvml package is deprecated. Please install nvidia-ml-py instead. If you did not install pynvml directly, please report this to the maintainers of the package that installed pynvml for you.
  import pynvml  # type: ignore[import]
W0417 08:21:43.803000 1 torch/utils/cpp_extension.py:2422] TORCH_CUDA_ARCH_LIST is not set, all archs for visible cards are included for compilation. 
W0417 08:21:43.803000 1 torch/utils/cpp_extension.py:2422] If this is not desired, please set os.environ['TORCH_CUDA_ARCH_LIST'] to specific architectures.
[TensorRT-LLM] TensorRT LLM version: 1.1.0
/usr/local/lib/python3.12/dist-packages/pydantic/_internal/_fields.py:192: UserWarning: Field name "schema" in "ResponseFormat" shadows an attribute in parent "OpenAIBaseModel"
  warnings.warn(
[04/17/2026-08:21:45] [TRT-LLM] [I] Using LLM with TensorRT backend
[04/17/2026-08:21:45] [TRT-LLM] [W] Implicitly setting QWenConfig.seq_length = 8192
[04/17/2026-08:21:45] [TRT-LLM] [W] Implicitly setting QWenConfig.qwen_type = qwen2
[04/17/2026-08:21:45] [TRT-LLM] [W] Implicitly setting QWenConfig.moe_intermediate_size = 0
[04/17/2026-08:21:45] [TRT-LLM] [W] Implicitly setting QWenConfig.moe_shared_expert_intermediate_size = 0
[04/17/2026-08:21:45] [TRT-LLM] [W] Implicitly setting QWenConfig.tie_word_embeddings = False
[04/17/2026-08:21:45] [TRT-LLM] [I] Set dtype to bfloat16.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set bert_attention_plugin to auto.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set gpt_attention_plugin to auto.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set gemm_plugin to auto.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set explicitly_disable_gemm_plugin to False.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set gemm_swiglu_plugin to None.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set fp8_rowwise_gemm_plugin to None.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set qserve_gemm_plugin to None.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set identity_plugin to None.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set nccl_plugin to bfloat16.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set lora_plugin to None.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set dora_plugin to False.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set weight_only_groupwise_quant_matmul_plugin to None.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set weight_only_quant_matmul_plugin to None.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set smooth_quant_plugins to True.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set smooth_quant_gemm_plugin to None.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set layernorm_quantization_plugin to None.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set rmsnorm_quantization_plugin to None.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set quantize_per_token_plugin to False.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set quantize_tensor_plugin to False.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set moe_plugin to auto.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set mamba_conv1d_plugin to auto.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set low_latency_gemm_plugin to None.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set low_latency_gemm_swiglu_plugin to None.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set gemm_allreduce_plugin to None.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set context_fmha to True.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set bert_context_fmha_fp32_acc to False.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set paged_kv_cache to True.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set remove_input_padding to True.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set norm_quant_fusion to False.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set reduce_fusion to False.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set user_buffer to False.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set tokens_per_block to 32.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set use_paged_context_fmha to True.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set use_fp8_context_fmha to False.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set fuse_fp4_quant to False.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set multiple_profiles to False.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set paged_state to False.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set streamingllm to False.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set manage_weights to False.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set use_fused_mlp to True.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set pp_reduce_scatter to False.
[04/17/2026-08:21:45] [TRT-LLM] [W] The build_config is ignored for model format of TLLM_ENGINE.
[04/17/2026-08:21:45] [TRT-LLM] [W] Implicitly setting QWenConfig.seq_length = 8192
[04/17/2026-08:21:45] [TRT-LLM] [W] Implicitly setting QWenConfig.qwen_type = qwen2
[04/17/2026-08:21:45] [TRT-LLM] [W] Implicitly setting QWenConfig.moe_intermediate_size = 0
[04/17/2026-08:21:45] [TRT-LLM] [W] Implicitly setting QWenConfig.moe_shared_expert_intermediate_size = 0
[04/17/2026-08:21:45] [TRT-LLM] [W] Implicitly setting QWenConfig.tie_word_embeddings = False
[04/17/2026-08:21:45] [TRT-LLM] [I] Set dtype to bfloat16.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set bert_attention_plugin to auto.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set gpt_attention_plugin to auto.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set gemm_plugin to auto.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set explicitly_disable_gemm_plugin to False.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set gemm_swiglu_plugin to None.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set fp8_rowwise_gemm_plugin to None.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set qserve_gemm_plugin to None.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set identity_plugin to None.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set nccl_plugin to bfloat16.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set lora_plugin to None.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set dora_plugin to False.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set weight_only_groupwise_quant_matmul_plugin to None.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set weight_only_quant_matmul_plugin to None.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set smooth_quant_plugins to True.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set smooth_quant_gemm_plugin to None.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set layernorm_quantization_plugin to None.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set rmsnorm_quantization_plugin to None.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set quantize_per_token_plugin to False.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set quantize_tensor_plugin to False.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set moe_plugin to auto.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set mamba_conv1d_plugin to auto.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set low_latency_gemm_plugin to None.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set low_latency_gemm_swiglu_plugin to None.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set gemm_allreduce_plugin to None.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set context_fmha to True.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set bert_context_fmha_fp32_acc to False.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set paged_kv_cache to True.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set remove_input_padding to True.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set norm_quant_fusion to False.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set reduce_fusion to False.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set user_buffer to False.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set tokens_per_block to 32.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set use_paged_context_fmha to True.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set use_fp8_context_fmha to False.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set fuse_fp4_quant to False.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set multiple_profiles to False.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set paged_state to False.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set streamingllm to False.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set manage_weights to False.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set use_fused_mlp to True.
[04/17/2026-08:21:45] [TRT-LLM] [I] Set pp_reduce_scatter to False.
[04/17/2026-08:21:45] [TRT-LLM] [E] Failed to parse the arguments for the LLM constructor: 1 validation error for TrtLlmArgs
  Value error, max_batch_size [2048] is greater than build_config.max_batch_size [64] in build_config [type=value_error, input_value={'model': '/engines/qwen'...indow_too_large': False}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/value_error
Traceback (most recent call last):
  File "/usr/local/bin/trtllm-serve", line 8, in <module>
    sys.exit(main())
             ^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/click/core.py", line 1485, in __call__
    return self.main(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/click/core.py", line 1406, in main
    rv = self.invoke(ctx)
         ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/click/core.py", line 1873, in invoke
    return _process_result(sub_ctx.command.invoke(sub_ctx))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/click/core.py", line 1269, in invoke
    return ctx.invoke(self.callback, **ctx.params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/click/core.py", line 824, in invoke
    return callback(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/tensorrt_llm/commands/serve.py", line 383, in serve
    launch_server(host, port, llm_args, metadata_server_cfg, server_role)
  File "/usr/local/lib/python3.12/dist-packages/tensorrt_llm/commands/serve.py", line 174, in launch_server
    llm = LLM(**llm_args)
          ^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/tensorrt_llm/llmapi/llm.py", line 789, in __init__
    super().__init__(model, tokenizer, tokenizer_mode, skip_tokenizer_init,
  File "/usr/local/lib/python3.12/dist-packages/tensorrt_llm/llmapi/llm.py", line 171, in __init__
    raise e
  File "/usr/local/lib/python3.12/dist-packages/tensorrt_llm/llmapi/llm.py", line 156, in __init__
    self.args = llm_args_cls.from_kwargs(
                ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/tensorrt_llm/llmapi/llm_args.py", line 1456, in from_kwargs
    ret = cls(**kwargs)
          ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/pydantic/main.py", line 214, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 1 validation error for TrtLlmArgs
  Value error, max_batch_size [2048] is greater than build_config.max_batch_size [64] in build_config [type=value_error, input_value={'model': '/engines/qwen'...indow_too_large': False}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/value_error
```

### 해결방법 ###
trtllm-serve의 기본 max_batch_size가 2048인데, 엔진 빌드할 때 64로 설정하였다. 서빙 시 빌드 값보다 클 수 없다.

```
--max_batch_size 64 추가한다.

args:
  - |
    trtllm-serve serve /engines/qwen \
      --tokenizer /models/qwen-hf \
      --host 0.0.0.0 \
      --port 8000 \
      --tp_size 4 \
      --max_beam_width 1 \
      --max_batch_size 64 \
      --backend tensorrt
```
