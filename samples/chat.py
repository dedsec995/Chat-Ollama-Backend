from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage

llm = ChatOllama(
    model="mistral-nemo"
    # other params...
)

messages = [
    (
        "system",
        "You are a helpful assistant helps users create machine learning code.",
    ),
    ("human", "How to create a decision tree?"),
]
ai_msg = llm.invoke(messages)
# print(ai_msg)
print(ai_msg.content)