from typing import TypedDict, Annotated
import uuid
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from sentence_transformers import CrossEncoder

# ──────────────────────────────────────
# 벡터스토어 & 모델 준비
# ──────────────────────────────────────
docs = [
    Document(page_content="LangGraph는 LangChain 팀이 만든 에이전트 프레임워크입니다."),
    Document(page_content="LangGraph는 상태 기반 그래프로 복잡한 워크플로우를 구성합니다."),
    Document(page_content="FastAPI는 Python의 고성능 웹 프레임워크입니다."),
    Document(page_content="RAG는 Retrieval Augmented Generation의 약자입니다."),
    Document(page_content="RAG는 외부 문서를 검색해서 LLM의 답변 품질을 높이는 기법입니다."),
]
vectorstore = FAISS.from_documents(docs, OpenAIEmbeddings())
cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
llm = ChatOpenAI(model="gpt-4o")

rag_prompt = ChatPromptTemplate.from_messages([
    ("system", """컨텍스트를 참고하여 답변하세요.
컨텍스트에 없는 내용은 "제공된 문서에서 해당 정보를 찾을 수 없습니다"라고 답하세요.

컨텍스트:
{context}"""),
    ("human", "{question}")
])

# ──────────────────────────────────────
# 상태 & 노드 & 그래프 (동일)
# ──────────────────────────────────────
class RAGState(TypedDict):
    messages: Annotated[list, add_messages]
    question: str
    retrieved_docs: list[Document]
    reranked_docs: list[Document]
    answer: str

def retrieve(state: RAGState):
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
    docs = retriever.invoke(state["question"])
    return {"retrieved_docs": docs}

def rerank(state: RAGState):
    question = state["question"]
    docs = state["retrieved_docs"]
    pairs = [(question, doc.page_content) for doc in docs]
    scores = cross_encoder.predict(pairs)
    scored_docs = sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)
    top_docs = [doc for score, doc in scored_docs[:3]]
    return {"reranked_docs": top_docs}

def generate(state: RAGState):
    context = "\n".join([doc.page_content for doc in state["reranked_docs"]])
    response = llm.invoke(
        rag_prompt.invoke({"context": context, "question": state["question"]})
    )
    return {
        "answer": response.content,
        "messages": [
            {"role": "user", "content": state["question"]},
            {"role": "assistant", "content": response.content}
        ]
    }

graph_builder = StateGraph(RAGState)
graph_builder.add_node("retrieve", retrieve)
graph_builder.add_node("rerank", rerank)
graph_builder.add_node("generate", generate)
graph_builder.add_edge(START, "retrieve")
graph_builder.add_edge("retrieve", "rerank")
graph_builder.add_edge("rerank", "generate")
graph_builder.add_edge("generate", END)

memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

# ──────────────────────────────────────
# FastAPI (response 파라미터 방식)
# ──────────────────────────────────────
app = FastAPI()

@app.post("/ask")
async def ask(request: Request, response: Response):
    body = await request.json()
    question = body["question"]

    thread_id = request.cookies.get("thread_id")

    if not thread_id:
        thread_id = str(uuid.uuid4())
        response.set_cookie(
            key="thread_id",
            value=thread_id,
            httponly=True,
            max_age=60 * 60 * 24 * 7
        )

    config = {"configurable": {"thread_id": thread_id}}
    result = await graph.ainvoke({"question": question}, config=config)

    return {
        "answer": result["answer"],
        "sources": [doc.page_content for doc in result["reranked_docs"]],
        "thread_id": thread_id
    }


@app.get("/history")
async def history(request: Request):
    thread_id = request.cookies.get("thread_id")
    if not thread_id:
        return {"messages": []}

    config = {"configurable": {"thread_id": thread_id}}
    state = await graph.aget_state(config)

    if state.values and "messages" in state.values:
        return {
            "messages": [
                {"role": "user" if m.type == "human" else "assistant", "content": m.content}
                for m in state.values["messages"]
            ]
        }
    return {"messages": []}


@app.post("/new-session")
async def new_session(response: Response):
    thread_id = str(uuid.uuid4())
    response.set_cookie(key="thread_id", value=thread_id, httponly=True, max_age=60*60*24*7)
    return {"thread_id": thread_id, "status": "created"}
