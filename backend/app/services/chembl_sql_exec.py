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


def _strip_sql_comments(sql: str) -> str:
    """Remove SQL comments (both -- line comments and /* block */ comments).
    This is used only for scanning, not for execution.
    """
    import re
    # Remove block comments
    no_block = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    # Remove line comments
    no_line = re.sub(r"--.*?$", " ", no_block, flags=re.M)
    return no_line


def _enforce_limit(sql: str, limit: int) -> str:
    """Append a LIMIT clause if one isn't already present.

    The previous implementation only detected " limit " with spaces and could miss
    cases like newlines ("\nLIMIT 50"), causing a duplicate LIMIT to be appended
    and a syntax error. Here we strip comments and use a regex word-boundary search
    for LIMIT, ignoring case and whitespace/newlines.
    """
    import re

    s = sql.strip().rstrip(";")
    scan = _strip_sql_comments(s)
    # Collapse whitespace to make detection robust across newlines/tabs
    scan_compact = re.sub(r"\s+", " ", scan)
    if re.search(r"\blimit\b", scan_compact, flags=re.I):
        return s
    return f"{s}\nLIMIT {int(limit)}"


def execute_sql(sql: str, limit: int | None = 100) -> Tuple[List[str], List[List]]:
    if not _is_select_only(sql):
        raise ValueError("Only SELECT/WITH queries are allowed.")
    lower = sql.lower()
    for tok in FORBIDDEN_TOKENS:
        if tok in lower and tok != ";":
            raise ValueError("Forbidden token detected in SQL.")
    # Debug: original SQL (sanitized)
    print("[chembl][exec] original:", repr(sql.strip().rstrip(";")))
    if ";" in sql.strip().rstrip(";"):
        # found semicolon not just at end
        raise ValueError("Multiple statements are not allowed.")

    final_sql = _enforce_limit(sql, limit or 100)
    print("[chembl][exec] final:", repr(final_sql))

    conn = sqlite3.connect(READ_ONLY_URI, uri=True)
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        try:
            cur.execute(final_sql)
            rows = cur.fetchall()
        except sqlite3.Error as e:
            # Normalize DB errors to ValueError so the API layer returns HTTP 400
            raise ValueError(f"SQLite error: {e}") from e
        columns = [d[0] for d in cur.description] if cur.description else []
        # Convert sqlite3.Row to plain lists
        result_rows = [list(r) for r in rows]
        return columns, result_rows
    finally:
        conn.close()
