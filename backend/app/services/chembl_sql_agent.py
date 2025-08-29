from typing import List
from app.core.config import get_settings

_settings = get_settings()


def retrieve_related_table_texts(query: str, vector_store: str, k: int = 5) -> List[str]:
    """Retrieve human-readable table descriptions from the vector store.
    Prefer metadata.text; fallback to the document page_content.
    """
    docs = vector_store.similarity_search(query, k=k)
    seen: List[str] = []
    for d in docs:
        t = (d.metadata or {}).get("text") or getattr(d, "page_content", None)
        if t and t not in seen:
            seen.append(t)
    return seen

def to_structured_table_dict(text: str) -> dict:
    """Parse a ChEMBL table description block into a structured dictionary
    of the shape requested by the frontend, e.g.
    {
      'table': 'ACTION_TYPE',
      'description': '...',
      'columns': [
         {'key': 'PK', 'name': 'ACTION_TYPE', 'type': 'VARCHAR2(50)', 'nullable': 'NOT NULL', 'comment': '...'},
         ...
      ]
    }
    """
    import re

    name = None
    desc = None
    columns: List[dict] = []

    # Table name
    m_name = re.search(r"Table:\s*([A-Za-z0-9_]+)", text, flags=re.IGNORECASE)
    if m_name:
        name = m_name.group(1).strip()

    # Description (from 'Description:' up to 'Columns:' or end)
    m_desc = re.search(r"Description:\s*([\s\S]*?)(?:\n\s*Columns:|$)", text, flags=re.IGNORECASE)
    if m_desc:
        desc = m_desc.group(1).strip()

    # Columns section
    m_cols = re.search(r"Columns:\s*([\s\S]*)", text, flags=re.IGNORECASE)
    if m_cols:
        lines = [l.strip() for l in m_cols.group(1).splitlines() if l.strip()]
        for line in lines:
            # - [PK,UK] COL (TYPE, NOT NULL) — comment
            cm = re.match(r"^[-*]\s*(?:\[([^\]]+)\]\s*)?([A-Za-z0-9_]+)\s*\(([^)]*)\)\s*(?:—|-|:)\s*(.*)?$", line)
            if not cm:
                # try without trailing comment
                cm = re.match(r"^[-*]\s*(?:\[([^\]]+)\]\s*)?([A-Za-z0-9_]+)\s*\(([^)]*)\)\s*$", line)
            if cm:
                keys_raw = (cm.group(1) or '').strip()
                col_name = cm.group(2)
                type_raw = (cm.group(3) or '').strip()
                comment = (cm.group(4) or '').strip()
                # Split out NOT NULL from type
                nullable = 'NOT NULL' if re.search(r"NOT\s+NULL", type_raw, flags=re.IGNORECASE) else ''
                # Remove NOT NULL and trailing commas from type
                type_clean = re.sub(r"\bNOT\s+NULL\b", "", type_raw, flags=re.IGNORECASE).strip().strip(',')
                columns.append({
                    'key': keys_raw,
                    'name': col_name,
                    'type': type_clean,
                    'nullable': nullable,
                    'comment': comment,
                })

    return {
        'table': name or '(unknown)',
        'description': desc or '',
        'columns': columns,
    }

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
    related_texts = retrieve_related_table_texts(enhanced_query, llm.vector_store_sql, k=5)
    # Build structured dicts for UI, but keep original texts for context
    structured = [to_structured_table_dict(t) for t in related_texts]
    print(structured)
    # Provide both signals to LLM via readable text (original) and UI via JSON-serializable structs
    sql = synthesize_sql(enhanced_query, related_texts, llm.llm)
    # Return structured dicts (pydantic will serialize)
    return sql, structured