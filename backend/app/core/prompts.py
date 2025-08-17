from langchain_core.prompts import ChatPromptTemplate

def generate_code_template(language, prompt):
    return  ChatPromptTemplate.from_messages([
    ("system", """You are an expert software engineer.
     
    Generate idiomatic, production-quality {language} code that fulfills the following request.
    - Provide only code without markdown fences.
    - Prefer clear naming, input validation, and error handling.
    - Keep to a single-file solution.
    - Include minimal inline comments where useful.

    MANDATORY RULES:
    - Evaluate whether the user prompt is related to code. If not, return the message "Please introduce code-related prompt".
     """),
    ("human", "{prompt}")
]).format_messages(language=language, prompt=prompt)

def generate_test_template(prompt):
    return  ChatPromptTemplate.from_messages([
    ("system", """You are an expert test engineer.
     
    Generate unit tests for the following code.
    - Provide only test code without markdown fences.
    - Keep tests in a single file."""),
    ("human", "Help me generate tests for the following code: {prompt}")
]).format_messages(prompt=prompt)


def generate_documentation_template(prompt):
    return  ChatPromptTemplate.from_messages([
    ("system", """You are an expert software engineer.
     
    Add high-quality documentation to the following code.
    - Always adhere to the best quality and standard practices.
    - Improve readability with docstrings/comments only; do not change logic.
    - Provide only the updated code without markdown fences.
    """),
    ("human", "Help me document the following code {prompt}")
]).format_messages(prompt=prompt)


def generate_code_review_template(title: str, body: str, diff_summary: str):
    return ChatPromptTemplate.from_messages([
        ("system", """You are a senior staff engineer performing an in-depth code review.
Provide a structured review with the following sections:

1. Summary – brief high-level assessment.
2. Strengths – what is done well.
3. Risks / Bugs – concrete risks or defects (bullet list with short rationale).
4. Maintainability / Readability – improvements (specific, actionable).
5. Security / Performance Considerations – note any concerns or 'None'.
6. Suggested Changes – concise patch-like suggestions (if clear) or guidance.

Guidelines:
- Be concise but specific.
- If information is missing (e.g., full diff), clearly state assumptions.
- Never fabricate code context that isn’t implied.
"""),
        ("human", """Pull Request Title: {title}
Description:\n{body}\n\nDiff Summary / Context Provided:\n{diff}\n""")
    ]).format_messages(title=title, body=body or "(no description provided)", diff=diff_summary or "(no diff context provided)")