from trl import DPOTrainer, DPOConfig


dpo_data = [
    {
        "prompt": "GPU OOM이 발생했을 때 해결 방법을 알려줘",
        "chosen": "GPU OOM 해결 방법: 1) 배치 크기 줄이기 + Gradient Accumulation 2) Mixed Precision(BF16) 사용 3) Activation Checkpointing 적용 4) ZeRO Stage 3 또는 FSDP 사용",
        "rejected": "GPU를 더 사세요. 메모리가 부족하면 더 큰 GPU를 쓰면 됩니다."
    },
    {
        "prompt": "Kubernetes Pod가 CrashLoopBackOff 상태일 때 디버깅 방법은?",
        "chosen": "kubectl logs <pod> --previous로 이전 크래시 로그 확인, kubectl describe pod로 이벤트 확인, 리소스 제한 초과 여부 확인, probe 설정 확인",
        "rejected": "Pod를 삭제하고 다시 만드세요."
    },
]

def format_dpo(example):
    system = "You are a helpful DevOps and ML engineering assistant."
    prompt_msgs = [
        {"role": "system", "content": system},
        {"role": "user", "content": example["prompt"]},
    ]
  
    return {
        "prompt": tokenizer.apply_chat_template(prompt_msgs, tokenize=False, add_generation_prompt=True),
        "chosen": example["chosen"],
        "rejected": example["rejected"],
    }


dataset = Dataset.from_list(dpo_data)
dataset = dataset.map(format_dpo)

training_args = DPOConfig(
    output_dir="./qwen-devops-dpo",
    num_train_epochs=3,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    learning_rate=5e-5,          # DPO는 SFT보다 lr 낮게
    bf16=True,
    logging_steps=1,
    save_strategy="epoch",
    optim="adamw_torch",
    beta=0.1,                    # DPO 핵심 파라미터: 작을수록 공격적
    max_length=2048,
    max_prompt_length=512,
)

trainer = DPOTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    processing_class=tokenizer,
)

trainer.train()
