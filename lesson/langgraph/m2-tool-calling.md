## 2. 도구 + 조건부 라우팅 + HITL ##

### 1. 왜 이 패턴을 배우는가 ###
챕터 1에서 만든 그래프는 정해진 순서대로 흐르는 파이프라인이었다. 하지만 실제 에이전트는 상황에 따라 다르게 움직여야 한다.

* 사용자의 질문을 보고 어떤 도구를 쓸지 LLM이 결정해야 한다
* 필요하면 도구를 여러 번 반복 호출해야 한다 (ReAct 루프)
* 돈이 드는 작업이나 되돌릴 수 없는 작업은 사람의 승인을 받아야 한다
이 세 가지를 조합한 구조가 업무용 에이전트의 표준 뼈대다.

### 2. 핵심 개념 ###
#### 2-1. 도구 — @tool 데코레이터 ####
함수에 @tool만 붙이면 LangChain 표준 도구가 된다. LLM 은 독스트링을 보고 "언제 이 도구를 쓸지" 판단한다. 독스트링이 부실하면 LLM이 엉뚱한 도구를 고른다. 

```
from langchain_core.tools import tool

@tool
def get_pricing(instance_type: str) -> str:
    """EC2 인스턴스 타입의 시간당 가격(USD)을 조회한다.
    예: 'c7i.large', 'c7g.large'
    """
```

#### 2-2. ToolNode — 도구 실행을 담당하는 노드 ####
LangGraph가 제공하는 기성 노드. LLM이 tool_calls를 만들면, ToolNode가 그걸 파싱해서 실제 함수를 호출하고 결과를 ToolMessage로 상태에 넣는다. 직접 구현할 수 있지만 99%는 이걸 쓰면 된다.
```
from langgraph.prebuilt import ToolNode
tool_node = ToolNode([get_pricing, list_ec2_instances, ...])
```

#### 2-3. 조건부 엣지 — tools_condition ####
"LLM이 도구를 호출했는가?"를 보고 분기한다.

* LLM이 tool_calls를 만들었다 → tools 노드로
* 그냥 최종 답변만 했다 → END로
```
from langgraph.prebuilt import tools_condition

builder.add_conditional_edges("agent", tools_condition)
#                                       ↑ 라우팅 함수가 다음 노드 이름을 반환
builder.add_edge("tools", "agent")      # 도구 실행 후 다시 LLM에게
```
이 구조가 ReAct 루프다. 도구 호출이 없어질 때까지 agent ↔ tools를 오간다.

#### 2-4. Human-in-the-loop — interrupt ####
특정 지점에서 그래프 실행을 멈추고, 외부(사람)로부터 값을 받아 재개한다.
```
from langgraph.types import interrupt, Command

def human_approval(state):
    decision = interrupt({
        "question": "정말로 이 인스턴스를 종료할까요?",
        "tool_call": state["messages"][-1].tool_calls[0],
    })
    # ↑ 여기서 그래프가 멈춤. 외부에서 Command(resume=...)로 재개해야 함
    
    if decision == "approve":
        return {"approved": True}
    return {"approved": False}
```
재개는 이렇게 한다.
```
graph.invoke(Command(resume="approve"), config=...)
```
interrupt는 체크포인터가 있어야 동작한다. 실습에서는 MemorySaver를 붙인다.

### 3. 그래프 구조 ###
```
       ┌─────────┐
START ▶│  agent  │◀──────────┐
       └────┬────┘           │
            │                │
   tools_condition           │
            │                │
     ┌──────┴──────┐         │
     ▼             ▼         │
 ┌───────┐        END        │
 │ tools │──────────────────┘
 └───┬───┘
     │ (민감 도구면)
     ▼
 ┌─────────┐       ┌─────────┐
 │approval │──────▶│ execute │
 └─────────┘       └─────────┘
```

### 4. 실습 코드 (시작 템플릿) ###
```
"""
실습: AWS 비용 질의 에이전트 (ReAct + HITL)
TODO 표시된 곳을 채워 완성하세요.
"""
from typing import Annotated, TypedDict
from dotenv import load_dotenv

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import BaseMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import Command, interrupt

load_dotenv()


# ── 1) 도구 정의 ──────────────────────────────────────────────
# (실습용 가짜 데이터. 오후 실습에서 실제 AWS API로 바꿀 수 있음)

PRICING = {
    "c7i.large": 0.1020, "c7i.xlarge": 0.2040,
    "c7g.large": 0.0816, "c7g.xlarge": 0.1632,
    "c8g.large": 0.0870,
}

INSTANCES = [
    {"id": "i-001", "type": "c7i.large",  "region": "us-west-2"},
    {"id": "i-002", "type": "c7i.xlarge", "region": "us-west-2"},
    {"id": "i-003", "type": "c7g.large",  "region": "us-west-2"},
]


@tool
def list_ec2_instances(region: str) -> list[dict]:
    """지정한 리전의 EC2 인스턴스 목록을 반환한다. 예: 'us-west-2'"""
    return [i for i in INSTANCES if i["region"] == region]


@tool
def get_pricing(instance_type: str) -> str:
    """EC2 인스턴스 타입의 시간당 가격(USD)을 조회한다. 예: 'c7i.large'"""
    price = PRICING.get(instance_type)
    if price is None:
        return f"{instance_type}: 가격 정보 없음"
    return f"{instance_type}: ${price}/hour"


@tool
def recommend_graviton_alternative(instance_type: str) -> str:
    """x86 인스턴스 타입에 대응하는 Graviton(ARM) 대안과 예상 절감률을 제시한다."""
    mapping = {
        "c7i.large":  ("c7g.large",  "약 20% 저렴"),
        "c7i.xlarge": ("c7g.xlarge", "약 20% 저렴"),
    }
    alt = mapping.get(instance_type)
    if not alt:
        return f"{instance_type}의 Graviton 대안 정보 없음"
    return f"{instance_type} → {alt[0]} ({alt[1]})"


@tool
def terminate_instance(instance_id: str) -> str:
    """지정한 EC2 인스턴스를 종료한다. 주의: 되돌릴 수 없음."""
    return f"Instance {instance_id} terminated."


SAFE_TOOLS = [list_ec2_instances, get_pricing, recommend_graviton_alternative]
SENSITIVE_TOOLS = [terminate_instance]
ALL_TOOLS = SAFE_TOOLS + SENSITIVE_TOOLS
SENSITIVE_NAMES = {t.name for t in SENSITIVE_TOOLS}


# ── 2) 모델 + 도구 바인딩 ─────────────────────────────────────

llm = ChatBedrockConverse(
    model="anthropic.claude-3-5-sonnet-20241022-v2:0",
    region_name="ap-northeast-2",
    temperature=0,
    max_tokens=2048,
)
llm_with_tools = llm.bind_tools(ALL_TOOLS)


# ── 3) 상태 정의 ──────────────────────────────────────────────

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# ── 4) 노드 정의 ──────────────────────────────────────────────

def agent(state: State) -> dict:
    """LLM이 다음 행동을 결정하는 노드."""
    
    # TODO 1: llm_with_tools로 state["messages"]를 invoke하고,
    #         결과를 {"messages": [resp]} 형태로 반환하세요.
    resp = llm_with_tools.invoke(state["messages"])
    return {"messages": [resp]}

def route_after_agent(state: State) -> str:
    """LLM이 도구를 호출했는지, 민감 도구인지에 따라 분기."""
    last = state["messages"][-1]
    if not getattr(last, "tool_calls", None):
        return END
    # 민감 도구가 포함돼 있으면 approval로
    if any(tc["name"] in SENSITIVE_NAMES for tc in last.tool_calls):
        return "approval"
    return "tools"

def approval(state: State) -> dict:
    """민감 도구 호출 직전에 사람에게 승인 요청."""
    last = state["messages"][-1]
    sensitive_calls = [
        tc for tc in last.tool_calls if tc["name"] in SENSITIVE_NAMES
    ]
    
    # TODO 2: interrupt(...)로 사용자 결정을 받고,
    #         "approve"면 sensitive_tools 노드로, 아니면 END로 가도록
    #         반환 dict를 설계하세요.
    #         힌트: approval에서는 라우팅을 위한 플래그를
    #         별도 상태 필드로 넣거나, ToolMessage로 거절 답변을 남기는 방식이 있습니다.
    decision = interrupt({
        "question": "아래 민감 작업을 실행할까요?",
        "tool_calls": sensitive_calls,
    })

    if decision == "approve":
        return {}  # 상태 변경 없음 → sensitive_tools로 진행
    # 거절: LLM에게 거절 사실을 알려주는 ToolMessage 추가
    from langchain_core.messages import ToolMessage
    return {
        "messages": [
            ToolMessage(content="사용자가 실행을 거부했습니다.",
                        tool_call_id=tc["id"])
            for tc in sensitive_calls
        ]
    }

def route_after_approval(state: State) -> str:
    """approval 이후 라우팅: 마지막이 ToolMessage면 거절된 것."""
    last = state["messages"][-1]
    if last.__class__.__name__ == "ToolMessage":
        return "agent"
    return "sensitive_tools"

safe_tools = ToolNode(SAFE_TOOLS)
sensitive_tools = ToolNode(SENSITIVE_TOOLS)


# ── 5) 그래프 조립 ────────────────────────────────────────────

def build_graph():
    builder = StateGraph(State)
    builder.add_node("agent", agent)
    builder.add_node("tools", safe_tools)
    builder.add_node("approval", approval)
    builder.add_node("sensitive_tools", sensitive_tools)

    builder.add_edge(START, "agent")
    # TODO 3: "agent"에서 route_after_agent로 조건부 엣지를 추가하세요.
    #         가능한 목적지: "tools", "approval", END
    builder.add_conditional_edges(
        "agent", route_after_agent,
        {"tools": "tools", "approval": "approval", END: END},
    )
    builder.add_conditional_edges(
        "approval", route_after_approval,
        {"agent": "agent", "sensitive_tools": "sensitive_tools"},
    )
    
    builder.add_edge("tools", "agent")
    builder.add_edge("sensitive_tools", "agent")

    # interrupt를 쓰려면 체크포인터 필수
    return builder.compile(checkpointer=MemorySaver())


# ── 6) 실행 ───────────────────────────────────────────────────

if __name__ == "__main__":
    graph = build_graph()
    cfg = {"configurable": {"thread_id": "demo-1"}}

    # 시나리오 1: 안전한 조회 (HITL 안 걸림)
    print("=" * 60, "\n[시나리오 1] 가격 조회\n")
    result = graph.invoke(
        {"messages": [("user", "us-west-2에 있는 c7i.large의 Graviton 대안과 가격을 알려줘")]},
        config=cfg,
    )
    print(result["messages"][-1].content)

    # 시나리오 2: 민감 작업 (HITL 걸림)
    print("=" * 60, "\n[시나리오 2] 인스턴스 종료 요청\n")
    cfg2 = {"configurable": {"thread_id": "demo-2"}}
    first = graph.invoke(
        {"messages": [("user", "i-002 인스턴스를 종료해줘")]},
        config=cfg2,
    )
    # interrupt가 걸렸다면 __interrupt__ 키가 채워진다
    print("중단됨:", first.get("__interrupt__"))

    # 사람의 승인(또는 거절)으로 재개
    resumed = graph.invoke(Command(resume="approve"), config=cfg2)
    print(resumed["messages"][-1].content)
```
#### 확인 포인트 ####
* 시나리오 1에서 에이전트가 list_ec2_instances → get_pricing → recommend_graviton_alternative 순으로 여러 번 도구를 호출하는지 (ReAct 루프 확인)
* 시나리오 2에서 __interrupt__ 키에 질문이 들어오며 그래프가 멈추는지
* Command(resume="approve")와 Command(resume="deny")를 각각 돌려 결과가 달라지는지
* graph.get_graph().draw_mermaid()로 네 개 노드와 조건부 엣지가 그려지는지


### 5. 보너스 과제 ###
#### 사전 정의된 tools_condition 써보기 ####
route_after_agent를 직접 짜지 말고 tools_condition으로 먼저 가게 한 뒤, 도구 노드 안에서 민감 여부를 따지는 방식으로도 같은 결과를 만들어 본다. 두 설계의 장단점 비교.

#### 실제 boto3로 바꾸기 ####
get_pricing과 list_ec2_instances를 실제 AWS API 호출로 교체.
```
@tool
def list_ec2_instances(region: str) -> list[dict]:
    """지정한 리전의 EC2 인스턴스 목록을 반환한다."""
    import boto3
    ec2 = boto3.client("ec2", region_name=region)
    resp = ec2.describe_instances()
    return [
        {"id": i["InstanceId"], "type": i["InstanceType"], "region": region}
        for r in resp["Reservations"] for i in r["Instances"]
    ]
```    
#### LangGraph Studio로 디버깅 ####
langgraph.json을 만들고 langgraph dev로 띄우면 Studio UI에서 HITL 중단 지점을 시각적으로 확인하고 승인/거절을 눌러볼 수 있다.
