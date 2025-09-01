import json
import re
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import MessagesState, StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

def make_retrieve_tool(vector_store):
    @tool(response_format="content_and_artifact")
    def retrieve(query: str):
        """Retrieve information related to a query. Leave the query as the user left it to increase the amount of matching characters.
        Just correct syntax if needed"""
        retrieved_docs = vector_store.similarity_search(query, k=4)
        serialized = "\n\n".join(
            (f"Source: {doc.metadata}\nContent: {doc.page_content}")
            for doc in retrieved_docs
        )
        return serialized, retrieved_docs
    return retrieve

# Step 1: Generate an AIMessage that may include a tool-call to be sent.
def make_query_or_respond_node(llm, retrieve):
    def query_or_respond(state: MessagesState):
        """Generate tool call for retrieval or respond."""
        llm_with_tools = llm.bind_tools([retrieve])
        response = llm_with_tools.invoke(state["messages"])
        # MessagesState appends messages to state instead of overwriting
        return {"messages": [response]}
    return query_or_respond


# Step 2: Execute the retrieval.


# Step 3: Generate a response using the retrieved content.
def make_generate_node(llm):
    def generate(state: MessagesState):
        """Generate answer."""
        # Get most recent contiguous block of ToolMessages (skip trailing non-tool markers)
        recent_tool_messages = []
        started = False
        for message in reversed(state["messages"]):
            if message.type == "tool":
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
                content="I don't have access to this information.",
            )
            return {"messages": [fallback]}

        # Format into prompt
        docs_content = "\n\n".join(doc.content for doc in tool_messages)
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
        # Collect tool messages (retrieved docs)
        recent_tool_messages = []
        for message in reversed(state["messages"]):
            if message.type == "tool":
                recent_tool_messages.append(message)
            else:
                break
        tool_messages = recent_tool_messages[::-1]

        if not tool_messages:
            # No docs means we cannot answer safely
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
    def no_answer(state: MessagesState):
        # Friendly fallback when we cannot safely answer
        return {"messages": [AIMessage(content="I don't have access to this information.")]}
    return no_answer

def build_langgraph(llm, vector_store):

    memory = MemorySaver()
    graph_builder = StateGraph(MessagesState)
    retrieve_method = make_retrieve_tool(vector_store)
    tools = ToolNode([retrieve_method])

    graph_builder.add_node(make_query_or_respond_node(llm, retrieve_method))
    graph_builder.add_node(tools)
    graph_builder.add_node(make_assess_node(llm))
    graph_builder.add_node(make_generate_node(llm))
    graph_builder.add_node(make_no_answer_node())

    graph_builder.set_entry_point("query_or_respond")
    graph_builder.add_conditional_edges(
        "query_or_respond",
        tools_condition,
        {END: END, "tools": "tools"},
    )
    # After retrieval, assess relevance and gate generation
    graph_builder.add_edge("tools", "assess")
    graph_builder.add_conditional_edges("assess", _assess_condition, {"generate": "generate", END: "no_answer"})
    graph_builder.add_edge("generate", END)

    return graph_builder.compile(checkpointer=memory)


class FpfRagPipeline:
    """Class-based RAG pipeline with an assessment gate before generation."""
    def __init__(self, llm, vector_store):
        self.llm = llm
        self.vector_store = vector_store
        self.graph = build_langgraph(llm, vector_store)

    def answer(self, question: str, config_key: str):
        last = None
        for step in self.graph.stream(
            {"messages": [{"role": "user", "content": question}]},
            stream_mode="values",
            config={"configurable": {"thread_id": config_key}},
        ):
            last = step
            step["messages"][-1].pretty_print()

        if not last:
            return "I don't have access to this information."
        return last["messages"][-1].content

def rag_answer_process(graph_or_pipeline, question, config_key):
    # Backwards-compatible wrapper: accept compiled graph or pipeline instance
    if hasattr(graph_or_pipeline, "answer"):
        return graph_or_pipeline.answer(question, config_key)
    graph = graph_or_pipeline
    last = None
    for step in graph.stream(
        {"messages": [{"role": "user", "content": question}]},
        stream_mode="values",
        config={"configurable": {"thread_id": config_key}},
    ):
        last = step
        step["messages"][-1].pretty_print()

    if not last:
        return "I don't have access to this information."
    return last["messages"][-1].content
