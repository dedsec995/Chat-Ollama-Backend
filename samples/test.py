import ollama
response = ollama.chat(
    model="mistral-nemo",
    messages=[
        {
            "role": "user",
            "content": "Why is the sky blue?",
        },
    ],
)
print(response["message"]["content"])
