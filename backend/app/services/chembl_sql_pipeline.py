from __future__ import annotations

import os
import json
import re
import time
import sqlite3
from typing import Any, List, Tuple, TypedDict
import uuid

from langgraph.graph import StateGraph, END


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


class SqlState(TypedDict, total=False):
    prompt: str
    enhanced_query: str
    related_texts: List[str]
    structured_tables: List[dict]
    sql: str
    limit: int
    retries: int
    columns: List[str]
    rows: List[List[Any]]
    error: str
    no_context: bool
    not_chembl: bool
    chembl_reason: str


class ChemblSqlPipeline:
    """End-to-end ChEMBL SQL pipeline (plan → retrieve → synthesize → execute) using LangGraph."""

    def __init__(self, llm, vector_store_sql):
        self.llm = llm
        self.vector_store = vector_store_sql
    # Graph is constructed per run to avoid any internal runner state leaks.
    # See run_all for per-call build.

    # ----------------- Utilities (logging) -----------------
    def _preview(self, text: str, max_len: int = 140) -> str:
        t = (text or "").strip().replace("\n", " ⏎ ")
        return (t[: max_len - 1] + "…") if len(t) > max_len else t

    def _log_step(self, step: str, **fields: Any) -> None:
        parts = [f"{k}={v}" for k, v in fields.items() if v is not None]
        message = " | ".join(parts)
        print(f"[CHEMBL][pipe][{step}] {message}")

    # ----------------- Public API -----------------
    def plan_and_synthesize(self, prompt: str) -> Tuple[str, List[dict]]:
        t0 = time.perf_counter()
        self._log_step("START", prompt_preview=self._preview(prompt), limit="n/a")
        enhanced = self._plan_query(prompt)
        self._log_step("PLAN.done", len=len(enhanced), preview=self._preview(enhanced))
        related_texts = self._retrieve_related_texts(enhanced, k=5)
        names_preview = self._extract_table_names_preview(related_texts)
        self._log_step("RETRIEVE.done", docs=len(related_texts), tables=names_preview)
        structured = [self._to_structured_table_dict(t) for t in related_texts]
        sql = self._synthesize_sql(enhanced, related_texts)
        self._log_step("SYNTH.done", sql_len=len(sql), sql_head=self._preview(sql, 100))
        self._log_step("END", took_ms=int((time.perf_counter() - t0) * 1000))
        return sql, structured

    def execute_only(self, sql: str, limit: int | None = 100) -> Tuple[List[str], List[List[Any]]]:
        return self._execute_sql(sql, limit or 100)

    def run_all(self, prompt: str, limit: int | None = 100) -> SqlState:
        """Run the full graph and return final state with sql, structured tables, and results.

        - Builds a fresh graph per run (robust after exceptions, thread-safe by isolation).
        - Soft timeout: 55s overall to avoid client/proxy 60s limits.
        """
        run_id = uuid.uuid4().hex[:8]
        inputs: SqlState = {"prompt": prompt, "limit": int(limit or 100), "retries": 0}
        self._log_step("START", run_id=run_id, prompt_preview=self._preview(prompt), limit=inputs["limit"])
        t0 = time.perf_counter()
        last = None
        graph = self._build_graph()  # per-run
        for step in graph.stream(inputs, stream_mode="values"):
            last = step
            if (time.perf_counter() - t0) > 55:
                # Leave a clear message; frontend will show it in the snackbar
                raise ValueError("Pipeline timeout: exceeded 55s. Please try again or refine your prompt.")
        self._log_step(
            "END",
            run_id=run_id,
            sql_len=len((last or {}).get("sql", "")),
            rows=len((last or {}).get("rows", [])),
            cols=len((last or {}).get("columns", [])),
            took_ms=int((time.perf_counter() - t0) * 1000),
        )
        return last or {}

    # ----------------- LangGraph -----------------
    def _build_graph(self):
        g = StateGraph(SqlState)

        def node_classify(state: SqlState) -> SqlState:
            t0 = time.perf_counter()
            is_chembl, reason, conf = self._classify_chembl_relevance(state.get("prompt") or "")
            self._log_step(
                "CLASSIFY.done",
                is_chembl=is_chembl,
                confidence=f"{conf:.2f}",
                took_ms=int((time.perf_counter() - t0) * 1000),
                reason_preview=self._preview(reason or "", 160),
            )
            if not is_chembl:
                return {
                    "not_chembl": True,
                    "no_context": True,
                    "chembl_reason": reason or "Query not related to ChEMBL domain.",
                    "related_texts": [],
                    "structured_tables": [],
                    "sql": "",
                    "columns": [],
                    "rows": [],
                }
            return {"not_chembl": False, "chembl_reason": reason or ""}

        def node_plan(state: SqlState) -> SqlState:
            t0 = time.perf_counter()
            if state.get("not_chembl"):
                self._log_step("PLAN.skip", reason="not_chembl")
                return {}
            enhanced = self._plan_query(state["prompt"]) if state.get("prompt") else ""
            self._log_step("PLAN.done", len=len(enhanced), took_ms=int((time.perf_counter() - t0) * 1000))
            return {"enhanced_query": enhanced}

        def node_retrieve(state: SqlState) -> SqlState:
            t0 = time.perf_counter()
            if state.get("not_chembl"):
                self._log_step("RETRIEVE.skip", reason="not_chembl")
                return {"related_texts": [], "structured_tables": [], "no_context": True}
            eq = state.get("enhanced_query") or ""
            related_texts = self._retrieve_related_texts(eq, k=5)
            names_preview = self._extract_table_names_preview(related_texts)
            self._log_step("RETRIEVE.done", docs=len(related_texts), tables=names_preview, took_ms=int((time.perf_counter() - t0) * 1000))
            structured = [self._to_structured_table_dict(t) for t in related_texts]
            return {"related_texts": related_texts, "structured_tables": structured, "no_context": len(related_texts) == 0}

        def node_synthesize(state: SqlState) -> SqlState:
            t0 = time.perf_counter()
            if state.get("not_chembl"):
                self._log_step("SYNTH.skip", reason="not_chembl")
                return {"sql": "", "no_context": True}
            if not state.get("related_texts"):
                self._log_step("SYNTH.skip", reason="no_context")
                return {"sql": "", "no_context": True}
            sql = self._synthesize_sql(state.get("enhanced_query") or "", state.get("related_texts") or [])
            self._log_step("SYNTH.done", sql_len=len(sql), sql_head=self._preview(sql, 100), took_ms=int((time.perf_counter() - t0) * 1000))
            return {"sql": sql}

        def node_execute(state: SqlState) -> SqlState:
            t0 = time.perf_counter()
            sql = state.get("sql") or ""
            limit = state.get("limit") or 100
            retries = int(state.get("retries") or 0)
            if state.get("no_context"):
                self._log_step("EXEC.skip", reason="no_context")
                return {"columns": [], "rows": [], "error": "", "retries": retries, "no_context": True}
            try:
                cols, rows = self._execute_sql(sql, limit)
                self._log_step("EXEC.done", rows=len(rows), cols=len(cols), took_ms=int((time.perf_counter() - t0) * 1000))
                return {"columns": cols, "rows": rows, "error": "", "retries": retries}
            except ValueError as e:
                err = str(e)
                self._log_step("EXEC.fail", retries=retries, error_preview=self._preview(err, 160))
                if retries >= 1:
                    raise
                repaired_sql = self._repair_sql(
                    state.get("prompt") or "",
                    sql,
                    err,
                    state.get("related_texts") or [],
                )
                self._log_step("REPAIR.sql", head=self._preview(repaired_sql, 160))
                try:
                    cols2, rows2 = self._execute_sql(repaired_sql, limit)
                    self._log_step("REPAIR.done", rows=len(rows2), cols=len(cols2))
                    return {"sql": repaired_sql, "columns": cols2, "rows": rows2, "error": "", "retries": retries + 1}
                except ValueError as e2:
                    self._log_step("REPAIR.fail", error_preview=self._preview(str(e2), 160))
                    raise

        # Wire graph
        g.add_node("classify", node_classify)
        g.add_node("plan", node_plan)
        g.add_node("retrieve", node_retrieve)
        g.add_node("synthesize", node_synthesize)
        g.add_node("execute", node_execute)

        g.set_entry_point("classify")
        # Early-exit when not ChEMBL related
        g.add_conditional_edges(
            "classify",
            lambda s: "end" if s.get("not_chembl") else "plan",
            {"plan": "plan", "end": END},
        )
        g.add_edge("plan", "retrieve")
        g.add_edge("retrieve", "synthesize")
        g.add_edge("synthesize", "execute")
        g.add_edge("execute", END)

        return g.compile()

    # ----------------- Steps (logic) -----------------
    def _plan_query(self, prompt: str) -> str:
        system = (
            "You are a SQL expert planner for the ChEMBL database.\n"
            "Analyze the user's request and expand it considering caveats, relationships, and edge cases."
        )
        msg = [("system", system), ("user", prompt)]
        self._log_step("PLAN.start", prompt_len=len(prompt))
        try:
            out = self.llm.invoke(msg)
        except Exception as e:  # noqa: BLE001 - upstream API may raise various exceptions
            raise ValueError(f"Planner LLM error: {e}") from e
        return (getattr(out, "content", "") or "").strip()

    def _retrieve_related_texts(self, query: str, k: int = 5) -> List[str]:
        self._log_step("RETRIEVE.start", query_preview=self._preview(query), k=k)
        docs = self.vector_store.similarity_search(query, k=k)
        seen: List[str] = []
        for d in docs:
            t = (d.metadata or {}).get("text") or getattr(d, "page_content", None)
            if t and t not in seen:
                seen.append(t)
        return seen

    def _synthesize_sql(self, prompt: str, related_tables: List[str]) -> str:
        context = "\n\n".join(f"- {t}" for t in related_tables) if related_tables else "(none)"
        user = (
            "User question:\n" + prompt + "\n\n" "Related tables (retrieved):\n" + context + "\n\n"
            "Write a single valid and optimized SQLite SQL query that best answers the question using these tables."
        )
        system = (
            "You are a helpful assistant that implements robust and optimized SQLite SQL queries for the ChEMBL database.\n"
            "Rules:\n- Only output SQL, no prose.\n- Use exact table/column names.\n"
            "- If retrieved tables are '(none)', respond 'Sorry, I am unable to answer this.'.\n"
            "- IMPORTANT: Base your answer solely on the related tables provided."
        )
        self._log_step("SYNTH.start", prompt_len=len(prompt), tables=len(related_tables))
        try:
            out = self.llm.invoke([("system", system), ("user", user)])
        except Exception as e:  # noqa: BLE001 - upstream API may raise various exceptions
            raise ValueError(f"Synthesis LLM error: {e}") from e
        sql = (getattr(out, "content", "") or "").strip()
        # Remove markdown code fences if present
        if sql.startswith("````") or sql.startswith("```"):
            sql = sql.strip('`')
            if sql.lower().startswith("sql"):
                sql = sql[3:]
            sql = sql.strip()
            if sql.endswith("````"):
                sql = sql[:-4].strip()
            elif sql.endswith("```"):
                sql = sql[:-3].strip()
            self._log_step("SYNTH.unfence", sql_head=self._preview(sql, 100))
        return sql

    def _classify_chembl_relevance(self, prompt: str) -> Tuple[bool, str, float]:
        """Decide if the prompt is related to the ChEMBL database domain.

        Returns (is_chembl, reason, confidence[0..1]).
        """
        description = (
            "ChEMBL is a large-scale bioactivity database focused on small molecules, targets (proteins), assays, and activities. "
            "It contains tables for molecules/compounds (identifiers, structures like SMILES/InChI), targets (e.g., CHEMBL IDs, UniProt links), assays, activities (IC50, EC50, Ki, potency, pChEMBL), mechanisms of action, indications, references/publications, and related metadata. "
            "Queries typically involve discovering relationships between compounds, targets, assays, activities, mechanisms, and properties (e.g., molecular weight)."
        )
        system = (
            "You are a strict classifier that determines whether a user question is about the ChEMBL bioactivity database domain.\n"
            "Respond ONLY with a compact JSON object of the form {\"is_chembl\": true|false, \"confidence\": number, \"reason\": string}.\n"
            "Consider if the question is about drug-like small molecules, targets, assays, bioactivity metrics, mechanisms of action, indications, or the schema itself."
        )
        user = (
            "ChEMBL description:\n" + description + "\n\n" +
            "User question:\n" + (prompt or "").strip()
        )
        try:
            out = self.llm.invoke([("system", system), ("user", user)])
            text = (getattr(out, "content", "") or "").strip()
            data = None
            # Attempt robust JSON parse
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                # Try to extract JSON object if surrounded by prose or code fences
                m = re.search(r"\{[\s\S]*\}", text)
                if m:
                    data = json.loads(m.group(0))
            if isinstance(data, dict):
                is_chembl = bool(data.get("is_chembl"))
                conf = float(data.get("confidence", 0))
                reason = str(data.get("reason") or "")
                return is_chembl, reason, max(0.0, min(1.0, conf))
        except Exception as e:  # noqa: BLE001
            self._log_step("CLASSIFY.error", error=str(e))

        # Heuristic fallback
        p = (prompt or "").lower()
        keywords = [
            "chembl", "assay", "assays", "activity", "activities", "bioactivity", "ic50", "ec50", "ki", "potency", "pchembl",
            "compound", "compounds", "molecule", "molecules", "smiles", "inchi", "target", "targets", "uniprot",
            "mechanism", "indication", "binding", "affinity"
        ]
        score = sum(1 for k in keywords if k in p) / max(1, len(keywords))
        is_chembl = ("chembl" in p) or score >= 0.08
        reason = "Heuristic classification based on keyword overlap."
        return is_chembl, reason, min(1.0, max(0.0, score))

    def _repair_sql(self, original_prompt: str, prev_sql: str, error_message: str, related_tables: List[str]) -> str:
        """Ask the model to fix the previous SQL using the SQLite error as feedback."""
        context = "\n\n".join(f"- {t}" for t in related_tables) if related_tables else "(none)"
        system = (
            "You are a SQLite expert that fixes invalid queries for the ChEMBL database.\n"
            "Rules:\n- Only output SQL, no prose.\n- Keep to the provided tables/columns.\n- Prefer minimal changes that address the error."
        )
        user = (
            "User question (for context):\n" + original_prompt + "\n\n"
            "Previous SQL (failed):\n" + prev_sql + "\n\n"
            "SQLite error message:\n" + error_message + "\n\n"
            "Related tables (retrieved):\n" + context + "\n\n"
            "Produce a corrected, valid SQLite SQL query that answers the user's question using the related tables."
        )
        self._log_step("REPAIR.start")
        try:
            out = self.llm.invoke([("system", system), ("user", user)])
        except Exception as e:  # noqa: BLE001 - upstream API may raise various exceptions
            raise ValueError(f"Repair LLM error: {e}") from e
        sql = (getattr(out, "content", "") or "").strip()
        if sql.startswith("````") or sql.startswith("```"):
            sql = sql.strip('`')
            if sql.lower().startswith("sql"):
                sql = sql[3:]
            sql = sql.strip()
            if sql.endswith("````"):
                sql = sql[:-4].strip()
            elif sql.endswith("```"):
                sql = sql[:-3].strip()
            self._log_step("REPAIR.unfence", sql_head=self._preview(sql, 100))
        return sql

    # --------- Execution & Safety ---------
    def _is_select_only(self, sql: str) -> bool:
        s = sql.strip().lower()
        return s.startswith("select") or s.startswith("with")

    def _strip_sql_comments(self, sql: str) -> str:
        # Remove block and line comments for scanning
        no_block = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
        no_line = re.sub(r"--.*?$", " ", no_block, flags=re.M)
        return no_line

    def _enforce_limit(self, sql: str, limit: int) -> str:
        s = sql.strip().rstrip(";")
        scan_compact = re.sub(r"\s+", " ", self._strip_sql_comments(s))
        if re.search(r"\blimit\b", scan_compact, flags=re.I):
            self._log_step("LIMIT.detected")
            return s
        self._log_step("LIMIT.append", limit=int(limit))
        return f"{s}\nLIMIT {int(limit)}"

    def _execute_sql(self, sql: str, limit: int) -> Tuple[List[str], List[List[Any]]]:
        if not self._is_select_only(sql):
            raise ValueError("Only SELECT/WITH queries are allowed.")
        lower = sql.lower()
        for tok in FORBIDDEN_TOKENS:
            if tok in lower and tok != ";":
                raise ValueError("Forbidden token detected in SQL.")
        if ";" in sql.strip().rstrip(";"):
            raise ValueError("Multiple statements are not allowed.")
        final_sql = self._enforce_limit(sql, limit or 100)
        self._log_step("EXEC.start", preview=self._preview(sql, 120))
        self._log_step("EXEC.final_sql", head=self._preview(final_sql, 160))

        conn = sqlite3.connect(READ_ONLY_URI, uri=True)
        try:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            try:
                cur.execute(final_sql)
                rows = cur.fetchall()
            except sqlite3.Error as e:
                self._log_step("EXEC.error", message=str(e))
                raise ValueError(f"SQLite error: {e}") from e
            columns = [d[0] for d in cur.description] if cur.description else []
            result_rows = [list(r) for r in rows]
            return columns, result_rows
        finally:
            conn.close()

    # --------- Parser for UI struct ---------
    def _to_structured_table_dict(self, text: str) -> dict:
        name = None
        desc = None
        columns: List[dict] = []

        m_name = re.search(r"Table:\s*([A-Za-z0-9_]+)", text, flags=re.IGNORECASE)
        if m_name:
            name = m_name.group(1).strip()

        m_desc = re.search(r"Description:\s*([\s\S]*?)(?:\n\s*Columns:|$)", text, flags=re.IGNORECASE)
        if m_desc:
            desc = m_desc.group(1).strip()

        m_cols = re.search(r"Columns:\s*([\s\S]*)", text, flags=re.IGNORECASE)
        if m_cols:
            lines = [l.strip() for l in m_cols.group(1).splitlines() if l.strip()]
            for line in lines:
                cm = re.match(r"^[-*]\s*(?:\[([^\]]+)\]\s*)?([A-Za-z0-9_]+)\s*\(([^)]*)\)\s*(?:—|-|:)\s*(.*)?$", line)
                if not cm:
                    cm = re.match(r"^[-*]\s*(?:\[([^\]]+)\]\s*)?([A-Za-z0-9_]+)\s*\(([^)]*)\)\s*$", line)
                if cm:
                    keys_raw = (cm.group(1) or '').strip()
                    col_name = cm.group(2)
                    type_raw = (cm.group(3) or '').strip()
                    comment = (cm.group(4) or '').strip()
                    nullable = 'NOT NULL' if re.search(r"NOT\s+NULL", type_raw, flags=re.IGNORECASE) else ''
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

    # --------- Helpers ---------
    def _extract_table_names_preview(self, texts: List[str]) -> str:
        names: List[str] = []
        for t in texts:
            m = re.search(r"Table:\s*([A-Za-z0-9_]+)", t, flags=re.IGNORECASE)
            if m:
                names.append(m.group(1))
        if not names:
            return "(none)"
        return ", ".join(names[:5]) + ("…" if len(names) > 5 else "")
