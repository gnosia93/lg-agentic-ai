# qwen_distill.py
# 응답 기반 증류 (Response-based Distillation)
# Teacher: Qwen3.5-27B → Student: Qwen3.5-3B

import torch
import json
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer, SFTConfig

# ============================================================
# 1. Teacher 모델로 응답 생성
# ============================================================
teacher_name = "Qwen/Qwen3.5-27B"

teacher_bnb = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

teacher = AutoModelForCausalLM.from_pretrained(
    teacher_name,
    quantization_config=teacher_bnb,
    torch_dtype=torch.bfloat16,
    device_map={"": 0},
    trust_remote_code=True,
)
teacher_tokenizer = AutoTokenizer.from_pretrained(teacher_name, trust_remote_code=True)
teacher.eval()

# 증류용 질문 목록
questions = [
    "GPU OOM이 발생했을 때 해결 방법을 알려줘",
    "Kubernetes Pod가 CrashLoopBackOff 상태일 때 디버깅 방법은?",
    "Docker 컨테이너에서 GPU를 사용하려면 어떻게 해야 해?",
    "Prometheus에서 GPU 메트릭을 수집하는 방법은?",
    "MLflow로 실험 추적하는 기본 코드를 보여줘",
    "Terraform으로 AWS VPC를 생성하는 기본 코드는?",
    "Ray를 사용한 분산 학습 기본 코드를 보여줘",
    "Slurm에서 멀티노드 GPU 학습 작업을 제출하는 sbatch 스크립트를 보여줘",
    "PyTorch FSDP와 DeepSpeed ZeRO의 차이점은?",
    "NCCL 통신 최적화 방법을 알려줘",
]

# Teacher가 응답 생성
print("=== Generating teacher responses ===")
distill_data = []
for q in questions:
    messages = [
        {"role": "system", "content": "You are a helpful DevOps and ML engineering assistant."},
        {"role": "user", "content": q},
    ]
    text = teacher_tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = teacher_tokenizer(text, return_tensors="pt").to("cuda")

    with torch.no_grad():
        output = teacher.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.7,
            do_sample=True,
        )

    # 입력 부분 제외하고 응답만 추출
    response = teacher_tokenizer.decode(output[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    distill_data.append({"instruction": q, "output": response})
    print(f"  [{len(distill_data)}/{len(questions)}] {q[:30]}...")

# 증류 데이터 저장 (재사용 가능)
with open("distill_data.json", "w", encoding="utf-8") as f:
    json.dump(distill_data, f, ensure_ascii=False, indent=2)
print(f"=== Saved {len(distill_data)} samples to distill_data.json ===")

# Teacher 메모리 해제
del teacher
torch.cuda.empty_cache()


# ============================================================
# 2. Student 모델 로드
# ============================================================
student_name = "Qwen/Qwen3.5-3B"

student_bnb = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

student = AutoModelForCausalLM.from_pretrained(
    student_name,
    quantization_config=student_bnb,
    torch_dtype=torch.bfloat16,
    device_map={"": 0},
    trust_remote_code=True,
)

student_tokenizer = AutoTokenizer.from_pretrained(student_name, trust_remote_code=True)
student_tokenizer.pad_token = student_tokenizer.eos_token

# ============================================================
# 3. LoRA 설정
# ============================================================
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=[
        "q_proj", "v_proj", "k_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

student = get_peft_model(student, lora_config)
student.print_trainable_parameters()

# ============================================================
# 4. 증류 데이터를 Chat 형식으로 변환
# ============================================================
# distill_data.json에서 로드 (Teacher 단계를 별도로 실행한 경우)
# with open("distill_data.json", "r", encoding="utf-8") as f:
#     distill_data = json.load(f)

def format_chat(example):
    messages = [
        {"role": "system", "content": "You are a helpful DevOps and ML engineering assistant."},
        {"role": "user", "content": example["instruction"]},
        {"role": "assistant", "content": example["output"]},
    ]
    text = student_tokenizer.apply_chat_template(messages, tokenize=False)
    return {"text": text}

dataset = Dataset.from_list(distill_data)
dataset = dataset.map(format_chat)

# ============================================================
# 5. Student SFT 학습 (Teacher 응답으로)
# ============================================================
training_args = SFTConfig(
    output_dir="./qwen-3b-distilled",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    bf16=True,
    logging_steps=1,
    save_strategy="epoch",
    optim="adamw_torch",
    dataset_text_field="text",
    max_length=2048,
)

trainer = SFTTrainer(
    model=student,
    args=training_args,
    train_dataset=dataset,
    processing_class=student_tokenizer,
)

trainer.train()

# ============================================================
# 6. 저장
# ============================================================
student.save_pretrained("./qwen-3b-distilled")
student_tokenizer.save_pretrained("./qwen-3b-distilled")
print("Done! Distilled model saved to ./qwen-3b-distilled")
