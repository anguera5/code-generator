import os
import sqlite3
from typing import List, Tuple

DB_PATH = os.getenv("CHEMBL_SQLITE_PATH", "app/chembl/chembl_35.db")

READ_ONLY_URI = f"file:{DB_PATH}?mode=ro"


FORBIDDEN_TOKENS = (
    ";",  # prevent multiple statements
    "pragma",
    "attach",
    "detach",
    "vacuum",
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "replace",
    "begin",
    "commit",
    "rollback",
)


def _is_select_only(sql: str) -> bool:
    s = sql.strip().lower()
    return s.startswith("select") or s.startswith("with")


def _enforce_limit(sql: str, limit: int) -> str:
    s = sql.strip().rstrip(";")
    low = s.lower()
    if " limit " in low or low.endswith(" limit"):
        return s
    return f"{s} LIMIT {int(limit)}"


def execute_sql(sql: str, limit: int | None = 100) -> Tuple[List[str], List[List]]:
    if not _is_select_only(sql):
        raise ValueError("Only SELECT/WITH queries are allowed.")
    lower = sql.lower()
    for tok in FORBIDDEN_TOKENS:
        if tok in lower and tok != ";":
            raise ValueError("Forbidden token detected in SQL.")
    print(repr(sql.strip().rstrip(";")))
    if ";" in sql.strip().rstrip(";"):
        # found semicolon not just at end
        raise ValueError("Multiple statements are not allowed.")

    final_sql = _enforce_limit(sql, limit or 100)

    conn = sqlite3.connect(READ_ONLY_URI, uri=True)
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(final_sql)
        rows = cur.fetchall()
        columns = [d[0] for d in cur.description] if cur.description else []
        # Convert sqlite3.Row to plain lists
        result_rows = [list(r) for r in rows]
        return columns, result_rows
    finally:
        conn.close()
