지식 그래프 구축 샘플
앞 단계에서 Milvus에 넣은 논문 10편을 이번엔 관계 기반 지식 그래프로 구축해본다. 다음과 같은 구조를 만들 것이다.

(Author) -[:AUTHORED]-> (Paper)
(Paper) -[:HAS_TOPIC]-> (Topic)
(Paper) -[:CITES]-> (Paper)      # 논문이 다른 논문을 인용
이 구조가 생기면 다음 같은 질의가 가능해진다.

"LoRA 저자가 쓴 다른 논문은?"
"RAG 관련 논문을 인용한 논문들의 공통 주제는?"
"Attention is All You Need를 인용한 논문 중 2024년 이후 발표된 것은?"
벡터 검색만으로는 풀기 어려운 "관계 기반" 질문들이다.

1. 스키마 설계
노드	속성
Paper	title, year, arxiv_id
Author	name
Topic	name
관계	방향
AUTHORED	Author → Paper
HAS_TOPIC	Paper → Topic
CITES	Paper → Paper
2. 데이터 적재
load_papers.py 파일 작성:

from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "neo4j-admin")

# 논문 데이터 (실제 워크샵에 쓰는 10편)
PAPERS = [
    {
        "arxiv_id": "1706.03762",
        "title": "Attention Is All You Need",
        "year": 2017,
        "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
        "topics": ["Transformer", "Attention"],
    },
    {
        "arxiv_id": "2106.09685",
        "title": "LoRA: Low-Rank Adaptation",
        "year": 2021,
        "authors": ["Edward Hu", "Yelong Shen", "Phillip Wallis"],
        "topics": ["PEFT", "Fine-tuning"],
    },
    {
        "arxiv_id": "2005.11401",
        "title": "Retrieval-Augmented Generation",
        "year": 2020,
        "authors": ["Patrick Lewis", "Ethan Perez"],
        "topics": ["RAG", "Retrieval"],
    },
    {
        "arxiv_id": "2201.11903",
        "title": "Chain-of-Thought Prompting",
        "year": 2022,
        "authors": ["Jason Wei", "Xuezhi Wang"],
        "topics": ["Prompting", "Reasoning"],
    },
    {
        "arxiv_id": "2210.03629",
        "title": "ReAct: Reasoning and Acting",
        "year": 2022,
        "authors": ["Shunyu Yao", "Jeffrey Zhao"],
        "topics": ["Agent", "Reasoning"],
    },
    {
        "arxiv_id": "2205.14135",
        "title": "FlashAttention",
        "year": 2022,
        "authors": ["Tri Dao", "Daniel Fu"],
        "topics": ["Attention", "Optimization"],
    },
    {
        "arxiv_id": "2407.21783",
        "title": "The Llama 3 Herd of Models",
        "year": 2024,
        "authors": ["Aaron Grattafiori", "Abhimanyu Dubey"],
        "topics": ["LLM", "Foundation Model"],
    },
    {
        "arxiv_id": "2402.03216",
        "title": "BGE-M3",
        "year": 2024,
        "authors": ["Jianlv Chen", "Shitao Xiao"],
        "topics": ["Embedding", "Retrieval"],
    },
    {
        "arxiv_id": "2501.12948",
        "title": "DeepSeek-R1",
        "year": 2025,
        "authors": ["DeepSeek-AI"],
        "topics": ["Reasoning", "RL"],
    },
    {
        "arxiv_id": "1909.08053",
        "title": "Megatron-LM",
        "year": 2019,
        "authors": ["Mohammad Shoeybi"],
        "topics": ["Training", "Distributed"],
    },
]

# 인용 관계 (일부만 샘플로)
CITATIONS = [
    ("2106.09685", "1706.03762"),  # LoRA → Attention
    ("2005.11401", "1706.03762"),  # RAG → Attention
    ("2210.03629", "2201.11903"),  # ReAct → CoT
    ("2205.14135", "1706.03762"),  # FlashAttention → Attention
    ("2407.21783", "2205.14135"),  # Llama3 → FlashAttention
    ("2407.21783", "1909.08053"),  # Llama3 → Megatron
    ("2501.12948", "2201.11903"),  # DeepSeek-R1 → CoT
    ("2402.03216", "1706.03762"),  # BGE-M3 → Attention
]


def build_graph(driver):
    with driver.session() as session:
        # 기존 데이터 삭제 (매번 깨끗하게 시작)
        session.run("MATCH (n) DETACH DELETE n")

        # 제약 조건: 동일 논문/저자/토픽 중복 방지
        session.run("CREATE CONSTRAINT paper_id IF NOT EXISTS FOR (p:Paper) REQUIRE p.arxiv_id IS UNIQUE")
        session.run("CREATE CONSTRAINT author_name IF NOT EXISTS FOR (a:Author) REQUIRE a.name IS UNIQUE")
        session.run("CREATE CONSTRAINT topic_name IF NOT EXISTS FOR (t:Topic) REQUIRE t.name IS UNIQUE")

        # 논문, 저자, 토픽 + 관계 생성
        for p in PAPERS:
            session.run("""
                MERGE (paper:Paper {arxiv_id: $arxiv_id})
                SET paper.title = $title, paper.year = $year

                WITH paper
                UNWIND $authors AS author_name
                MERGE (a:Author {name: author_name})
                MERGE (a)-[:AUTHORED]->(paper)

                WITH paper
                UNWIND $topics AS topic_name
                MERGE (t:Topic {name: topic_name})
                MERGE (paper)-[:HAS_TOPIC]->(t)
            """, **p)

        # 인용 관계 생성
        for citing, cited in CITATIONS:
            session.run("""
                MATCH (a:Paper {arxiv_id: $citing})
                MATCH (b:Paper {arxiv_id: $cited})
                MERGE (a)-[:CITES]->(b)
            """, citing=citing, cited=cited)

        print("Graph built successfully")


if __name__ == "__main__":
    driver = GraphDatabase.driver(URI, auth=AUTH)
    build_graph(driver)
    driver.close()
실행:

python load_papers.py
# Graph built successfully
3. Cypher로 그래프 탐색
http://localhost:7474 접속 후 비주얼로 확인한다.

전체 그래프 보기:

MATCH (n) RETURN n LIMIT 100
특정 저자가 쓴 논문:

MATCH (a:Author {name: "Edward Hu"})-[:AUTHORED]->(p:Paper)
RETURN a, p
Attention 논문을 인용한 논문들:

MATCH (p:Paper)-[:CITES]->(target:Paper {title: "Attention Is All You Need"})
RETURN p.title AS citing_paper, p.year AS year
ORDER BY p.year
Reasoning 토픽을 다루는 논문:

MATCH (p:Paper)-[:HAS_TOPIC]->(t:Topic {name: "Reasoning"})
RETURN p.title, p.year
2단계 확장 질의 (벡터 검색으론 어려운 유형):

"Attention 논문을 인용한 논문들이 다루는 주제는 뭐뭐야?"

MATCH (root:Paper {title: "Attention Is All You Need"})
MATCH (citing:Paper)-[:CITES]->(root)
MATCH (citing)-[:HAS_TOPIC]->(topic:Topic)
RETURN DISTINCT topic.name AS topic, count(citing) AS count
ORDER BY count DESC
결과 예시:

topic       count
Attention   2
PEFT        1
Retrieval   2
...
4. Python에서 질의 실행
query_graph.py:

from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "neo4j-admin"),
)


def papers_citing(title: str):
    with driver.session() as session:
        result = session.run("""
            MATCH (p:Paper)-[:CITES]->(target:Paper {title: $title})
            RETURN p.title AS title, p.year AS year
            ORDER BY p.year
        """, title=title)
        return [dict(r) for r in result]


def papers_by_topic(topic: str):
    with driver.session() as session:
        result = session.run("""
            MATCH (p:Paper)-[:HAS_TOPIC]->(t:Topic {name: $topic})
            RETURN p.title AS title, p.year AS year
        """, topic=topic)
        return [dict(r) for r in result]


if __name__ == "__main__":
    print("\n[Attention Is All You Need를 인용한 논문]")
    for r in papers_citing("Attention Is All You Need"):
        print(f"  - ({r['year']}) {r['title']}")

    print("\n[Reasoning 토픽 논문]")
    for r in papers_by_topic("Reasoning"):
        print(f"  - ({r['year']}) {r['title']}")

driver.close()
실행:

python query_graph.py
출력 예시:

[Attention Is All You Need를 인용한 논문]
  - (2020) Retrieval-Augmented Generation
  - (2021) LoRA: Low-Rank Adaptation
  - (2022) FlashAttention
  - (2024) BGE-M3

[Reasoning 토픽 논문]
  - (2022) Chain-of-Thought Prompting
  - (2022) ReAct: Reasoning and Acting
  - (2025) DeepSeek-R1
5. 시각화
Neo4j Browser(http://localhost:7474)에서 다음 쿼리를 실행하면 노드가 색상별로 시각화된다.

MATCH p=()-[:CITES]->() RETURN p
![그래프 예시](이미지 첨부 시)

파란 노드가 Paper, 주황이 Author, 초록이 Topic처럼 Neo4j Browser가 자동으로 색을 지정해준다.

다음 단계
이제 지식 그래프가 준비됐다. 이후 단계에서는:

자동 KG 추출: LangChain LLMGraphTransformer로 논문 PDF에서 자동으로 Entity/Relation을 추출해 그래프를 생성
GraphRAG: Milvus 벡터 검색 + Neo4j 관계 탐색을 결합한 하이브리드 RAG
Cypher 자동 생성: LLM이 자연어 질문을 Cypher 쿼리로 변환 (GraphCypherQAChain)
이렇게 넣으면 "DB 설치 → 데이터 넣기 → 탐색 → 시각화" 한 바퀴를 돌려볼 수 있어서 워크샵 참가자가 감을 잡기 좋아요.

몇 가지 포인트:

인용 관계는 일부만 샘플로 넣었어요. 실제론 더 많지만 워크샵 설명용으론 8개 정도면 충분.
MERGE 사용해서 재실행해도 중복 안 생김.
CREATE CONSTRAINT 로 제약 조건 걸어둠 (실무 권장 패턴).
벡터 RAG로는 어려운 "2-hop 질의" 예시를 일부러 넣어서 그래프의 가치를 보여줌.
다음 단계로 "자동 KG 추출" 또는 "GraphRAG" 섹션 이어서 만들까요?
