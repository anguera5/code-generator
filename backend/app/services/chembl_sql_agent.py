from typing import List
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from app.core.config import get_settings

_settings = get_settings()


def retrieve_related_tables(query: str, vector_store: str, k: int = 5) -> List[str]:
    docs = vector_store.similarity_search(query, k=k)
    seen: List[str] = []
    for d in docs:
        t = (d.metadata or {}).get("text")
        if t and t not in seen:
            seen.append(t)
    return seen

SQL_PLANNER_SYSTEM_PROMPT = (
    "You are a SQL expert planner for the ChEMBL database.\n"
    "Your role is to analyze user queries and expand them to consider all potential caveats and nuances.\n"
    "Guidelines:\n"
    "- Think critically about the user's intent and possible ambiguities.\n"
    "- Consider typical bottlenecks, edge cases, and data quality issues that may affect the query.\n"
    "- Suggest relevant columns, relationships, and possible interpretations to fully answer the query.\n"
    "- Highlight any assumptions or alternative interpretations that may affect the query results.\n"
    "- Output a concise, structured plan describing how to approach the SQL query, focusing on reasoning, caveats, and improvements."
)

SQL_SYSTEM_PROMPT = (
    "You are a helpful assistant that implements robust and optimized SQLite SQL queries for the ChEMBL database.\n"
    "Rules:\n"
    "- Only output SQL, no prose.\n"
    "- Use table and column names exactly as defined.\n"
    "- Return a concise query that answers the user request.\n"
    "- If retrieved tables are '(none)', respond 'Sorry, I am unable to answer this.'\n"
    "- MOST IMPORTANT RULE: Base your answer solely on the related tables provided.\n"
)

def plan_query(prompt: str, llm) -> str:
    msg = [
        ("system", SQL_PLANNER_SYSTEM_PROMPT),
        ("user", prompt),
    ]
    out = llm.invoke(msg)
    enhanced_query = (out.content or "").strip()
    return enhanced_query


def synthesize_sql(prompt: str, related_tables: List[str], llm) -> str:
    context = "\n\n".join(f"- {t}" for t in related_tables) if related_tables else "(none)"

    user = (
        "User question:\n" + prompt + "\n\n"
        "Related tables (retrieved):\n" + context + "\n\n"
        "Write a single valid SQLite SQL query that best answers the question using these tables."
    )
    msg = [
        ("system", SQL_SYSTEM_PROMPT),
        ("user", user),
    ]
    print(user)
    out = llm.invoke(msg)
    sql = (out.content or "").strip()
    # Remove markdown fences if present
    if sql.startswith("````") or sql.startswith("```"):
        sql = sql.strip('`')
        # Strip optional leading 'sql' language tag
        if sql.lower().startswith("sql"):
            sql = sql[3:]
        sql = sql.strip()
        if sql.endswith("````"):
            sql = sql[:-4].strip()
        elif sql.endswith("```"):
            sql = sql[:-3].strip()
    return sql

def sql_answer_process(prompt, llm):
    enhanced_query = plan_query(prompt, llm.llm)
    related_tables = retrieve_related_tables(enhanced_query, llm.vector_store_sql, k=5)
    sql = synthesize_sql(enhanced_query, related_tables, llm.llm)
    return sql, related_tables