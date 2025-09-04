import json
import re
import logging
import random
from datetime import datetime, timezone
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import MessagesState, StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

def _fallback_message() -> str:
    """Return a short variation of the no-information message."""
    variations = [
        "I have no information on this topic.",
        "Sorry, I don’t have information about that.",
        "I don’t have enough information on this topic.",
        "I don’t have details about this topic in my sources.",
        "I’m missing information on this topic.",
    ]
    return random.choice(variations)


def _ensure_query_text(q) -> str:
    """Best-effort conversion of an input into a plain query string."""
    if isinstance(q, str):
        return q
    if isinstance(q, dict):
        for key in ("content", "query", "text", "prompt", "message"):
            v = q.get(key)
            if isinstance(v, str) and v.strip():
                return v
    if isinstance(q, list):
        for item in reversed(q):
            s = _ensure_query_text(item)
            if isinstance(s, str) and s.strip():
                return s
    return str(q)

def make_retrieve_tool(vector_store):
    def retrieve(state: MessagesState):
        """Retrieve information for the latest user message and append a retrieval message.
        Emits a SystemMessage starting with [RETRIEVED] and attaches docs in additional_kwargs.artifact.
        """
        # Find the latest human message
        question = ""
        for m in reversed(state["messages"]):
            if m.type == "human":
                question = m.content
                break
        qtext = _ensure_query_text(question).strip()
        if not qtext:
            return {"messages": [SystemMessage(content="[RETRIEVED]")]}  # no docs

        retrieved_docs = vector_store.similarity_search(qtext, k=4)
        serialized = "\n\n".join(
            (f"Source: {doc.metadata}\nContent: {doc.page_content}")
            for doc in retrieved_docs
        )
        msg = SystemMessage(content=f"[RETRIEVED]\n{serialized}", additional_kwargs={"artifact": retrieved_docs})
        return {"messages": [msg]}
    return retrieve


# Step 2: Execute the retrieval.


# Step 3: Generate a response using the retrieved content.
def make_generate_node(llm):
    def generate(state: MessagesState):
        """Generate answer."""
        # Get most recent contiguous block of retrieval messages (tool or [RETRIEVED] markers)
        recent_tool_messages = []
        started = False
        for message in reversed(state["messages"]):
            is_retrieval = message.type == "tool" or (
                isinstance(getattr(message, "content", None), str)
                and getattr(message, "content").startswith("[RETRIEVED]")
            )
            if is_retrieval:
                recent_tool_messages.append(message)
                started = True
            elif started:
                break
            else:
                continue
        tool_messages = recent_tool_messages[::-1]

        # If no retrieval tool messages, return explicit fallback (prevent hallucination)
        if not tool_messages:
            fallback = AIMessage(
                content=_fallback_message(),
            )
            return {"messages": [fallback]}

        # Format into prompt
        # Strip the [RETRIEVED] marker if present
        def _strip_marker(txt: str) -> str:
            return txt.split("\n", 1)[1] if txt.startswith("[RETRIEVED]") else txt
        docs_content = "\n\n".join(_strip_marker(getattr(doc, "content", "")) for doc in tool_messages)
        system_message_content = (
            "You are an assistant for question-answering tasks. "
            "Use the following pieces of retrieved context to answer "
            "the question. If you don't receive no retrieved documents or if the information received is " \
            "unrelated to the question, answer \"I "
            "don't know\". Append the URL of the sources that you received at the bottom of each answer."
            "\n\n"
            f"{docs_content}"
        )
        conversation_messages = []
        for message in state["messages"]:
            if message.type == "system":
                # Exclude internal assessment markers from prompt
                content = getattr(message, "content", None)
                if isinstance(content, str) and content.startswith("[ASSESS]"):
                    continue
                conversation_messages.append(message)
            elif message.type == "human":
                conversation_messages.append(message)
            elif message.type == "ai" and not getattr(message, "tool_calls", None):
                conversation_messages.append(message)
        prompt = [SystemMessage(system_message_content)] + conversation_messages

        # Run
        response = llm.invoke(prompt)
        return {"messages": [response]}
    return generate

def make_assess_node(llm):
    def assess(state: MessagesState):
        """Decide if retrieved documents are sufficient to answer the question."""
        # Collect retrieval messages (tool or [RETRIEVED])
        recent_tool_messages = []
        for message in reversed(state["messages"]):
            is_retrieval = message.type == "tool" or (
                isinstance(getattr(message, "content", None), str)
                and getattr(message, "content").startswith("[RETRIEVED]")
            )
            if is_retrieval:
                recent_tool_messages.append(message)
            else:
                break
        tool_messages = recent_tool_messages[::-1]

        if not tool_messages:
            # No docs means we cannot answer safely
            marker = SystemMessage(content="[ASSESS] can_answer=false reason=no_docs")
            return {"messages": [marker]}

        # Count retrieved docs using artifact when available; fallback to content heuristic
        docs_count = 0
        for msg in tool_messages:
            art = getattr(msg, "artifact", None)
            if art is None:
                add_kwargs = getattr(msg, "additional_kwargs", None)
                if isinstance(add_kwargs, dict):
                    art = add_kwargs.get("artifact")
            if isinstance(art, list):
                docs_count += len(art)
            # Fallback heuristic: count Source: markers in content
            content_text = getattr(msg, "content", "") or ""
            if content_text:
                docs_count += content_text.count("Source:")

        if docs_count <= 0:
            marker = SystemMessage(content="[ASSESS] can_answer=false reason=no_docs")
            return {"messages": [marker]}

        docs_content = "\n\n".join(msg.content for msg in tool_messages)
        # Get the last user question
        question = None
        for m in reversed(state["messages"]):
            if m.type == "human":
                question = m.content
                break
        question = question or ""

        sys = SystemMessage(
            content=(
                "You are a strict relevance judge for a retrieval system at FPF. "
                "Given a user question and retrieved document snippets, decide if there is sufficient, directly relevant information to answer the question without hallucination. "
                "Return ONLY a valid JSON object with keys: can_answer (boolean) and reason (short string)."
            )
        )
        user = HumanMessage(
            content=(
                f"Question:\n{question}\n\nRetrieved context:\n{docs_content}\n\n"
                "Respond as JSON: {\"can_answer\": true|false, \"reason\": \"...\"}"
            )
        )
        res = llm.invoke([sys, user])
        can_answer = False
        reason = ""
        if isinstance(res.content, str):
            text = res.content
            # Extract first JSON object
            match = re.search(r"\{[\s\S]*\}", text)
            if match:
                try:
                    data = json.loads(match.group(0))
                    can_answer = bool(data.get("can_answer", False))
                    reason = str(data.get("reason", ""))
                except json.JSONDecodeError:
                    # Leave defaults when parsing fails
                    pass
        marker = SystemMessage(content=f"[ASSESS] can_answer={'true' if can_answer else 'false'} reason={reason}")
        return {"messages": [marker]}
    return assess

def _assess_condition(state: MessagesState):
    # Route to generate if we see an assessment allowing it; otherwise END
    for m in reversed(state["messages"]):
        content = getattr(m, "content", None)
        if isinstance(content, str) and content.startswith("[ASSESS]"):
            return "generate" if "can_answer=true" in content else END
    return END

def make_no_answer_node():
    def no_answer(_state: MessagesState):
        # Friendly fallback when we cannot safely answer
        return {"messages": [AIMessage(content=_fallback_message())]}
    return no_answer

def build_langgraph(llm, vector_store):

    memory = MemorySaver()
    graph_builder = StateGraph(MessagesState)

    graph_builder.add_node(make_retrieve_tool(vector_store))
    graph_builder.add_node(make_assess_node(llm))
    graph_builder.add_node(make_generate_node(llm))
    graph_builder.add_node(make_no_answer_node())

    graph_builder.set_entry_point("retrieve")
    graph_builder.add_edge("retrieve", "assess")
    graph_builder.add_conditional_edges("assess", _assess_condition, {"generate": "generate", END: "no_answer"})

    return graph_builder.compile(checkpointer=memory)


class FpfRagPipeline:
    """Class-based RAG pipeline with an assessment gate before generation."""
    def __init__(self, llm, vector_store):
        self.llm = llm
        self.vector_store = vector_store
        self.graph = build_langgraph(llm, vector_store)

    def answer(self, question: str, config_key: str):
        log = logging.getLogger(__name__)
        last = None
        for step in self.graph.stream(
            {"messages": [{"role": "user", "content": question}]},
            stream_mode="values",
            config={"configurable": {"thread_id": config_key}},
        ):
            last = step
            msg = step["messages"][-1]
            content = getattr(msg, "content", "")
            # Print and log the step output (traceback of LLM answers)
            ts = datetime.now(timezone.utc).isoformat()
            print(f"[{ts}] [LANGGRAPH][{config_key}] {content[:500]}")
            log.info("[LANGGRAPH][%s] %s", config_key, content)

        if not last:
            return _fallback_message()
        return last["messages"][-1].content

def rag_answer_process(graph_or_pipeline, question, config_key):
    # Backwards-compatible wrapper: accept compiled graph or pipeline instance
    if hasattr(graph_or_pipeline, "answer"):
        return graph_or_pipeline.answer(question, config_key)
    graph = graph_or_pipeline
    log = logging.getLogger(__name__)
    last = None
    for step in graph.stream(
        {"messages": [{"role": "user", "content": question}]},
        stream_mode="values",
        config={"configurable": {"thread_id": config_key}},
    ):
        last = step
        msg = step["messages"][-1]
        content = getattr(msg, "content", "")
        ts = datetime.now(timezone.utc).isoformat()
        print(f"[{ts}] [LANGGRAPH][{config_key}] {content[:500]}")
        log.info("[LANGGRAPH][%s] %s", config_key, content)

    if not last:
        return _fallback_message()
    return last["messages"][-1].content
