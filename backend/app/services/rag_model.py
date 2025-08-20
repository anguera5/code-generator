from langchain_core.tools import tool
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import MessagesState, StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

def make_retrieve_tool(vector_store):
    @tool(response_format="content_and_artifact")
    def retrieve(query: str):
        """Retrieve information related to a query. Leave the query as the user left it to increase the amount of matching characters.
        Just correct syntax if needed"""
        retrieved_docs = vector_store.similarity_search(query, k=2)
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
        # Get generated ToolMessages
        recent_tool_messages = []
        for message in reversed(state["messages"]):
            if message.type == "tool":
                recent_tool_messages.append(message)
            else:
                break
        tool_messages = recent_tool_messages[::-1]

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
        conversation_messages = [
            message
            for message in state["messages"]
            if message.type in ("human", "system")
            or (message.type == "ai" and not message.tool_calls)
        ]
        prompt = [SystemMessage(system_message_content)] + conversation_messages

        # Run
        response = llm.invoke(prompt)
        return {"messages": [response]}
    return generate

def build_langgraph(llm, vector_store):

    memory = MemorySaver()
    graph_builder = StateGraph(MessagesState)
    retrieve_method = make_retrieve_tool(vector_store)
    tools = ToolNode([retrieve_method])

    graph_builder.add_node(make_query_or_respond_node(llm, retrieve_method))
    graph_builder.add_node(tools)
    graph_builder.add_node(make_generate_node(llm))

    graph_builder.set_entry_point("query_or_respond")
    graph_builder.add_conditional_edges(
        "query_or_respond",
        tools_condition,
        {END: END, "tools": "tools"},
    )
    graph_builder.add_edge("tools", "generate")
    graph_builder.add_edge("generate", END)

    return graph_builder.compile(checkpointer=memory)

def rag_answer_process(graph, question, config_key):
    for step in graph.stream(
        {"messages": [{"role": "user", "content": question}]},
        stream_mode="values",
        config={"configurable": {"thread_id": config_key}},
    ):
        step["messages"][-1].pretty_print()

    llm_response = step["messages"][-1].content
    return llm_response
