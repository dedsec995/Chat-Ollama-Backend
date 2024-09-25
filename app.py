from flask import Flask, render_template, request, jsonify
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage
from cassandra.cluster import Cluster
import uuid

app = Flask(__name__)

# Initialize the Ollama model
llm = ChatOllama(
    model="mistral-nemo"
    # other params...
)

# Cassandra setup
cluster = Cluster(["127.0.0.1"])
session = cluster.connect()

# Create keyspace and table if not already present
session.execute(
    """
    CREATE KEYSPACE IF NOT EXISTS chat_app WITH replication = {
        'class': 'SimpleStrategy',
        'replication_factor': '1'
    };
"""
)

session.execute(
    """
    CREATE TABLE IF NOT EXISTS chat_app.conversations (
        conversation_id uuid,
        message_id uuid,
        user_message text,
        bot_response text,
        PRIMARY KEY (conversation_id, message_id)
    );
"""
)


# Render home page with conversation list
@app.route("/")
def home():
    # Fetch distinct conversation IDs to display as a list
    rows = session.execute(
        "SELECT DISTINCT conversation_id FROM chat_app.conversations;"
    )
    conversations = [str(row.conversation_id) for row in rows]
    return render_template("index.html", conversations=conversations)


# API to handle chatting
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data["message"]

    # If conversation_id is passed as a string, we handle it appropriately
    conversation_id = data.get("conversation_id", None)
    if conversation_id is None:
        conversation_id = uuid.uuid4()  # Generate new UUID for a new conversation
    else:
        conversation_id = uuid.UUID(conversation_id)  # Convert the string to UUID

    # Get response from the LLM
    bot_response = llm.invoke(user_message)
    bot_message = bot_response.content

    # Store the message and bot response in Cassandra
    session.execute(
        """
        INSERT INTO chat_app.conversations (conversation_id, message_id, user_message, bot_response)
        VALUES (%s, %s, %s, %s)
    """,
        (conversation_id, uuid.uuid4(), user_message, bot_message),
    )

    return jsonify({"response": bot_message, "conversation_id": str(conversation_id)})


# API to get a past conversation's messages
@app.route("/conversation/<conversation_id>", methods=["GET"])
def get_conversation(conversation_id):
    # Convert the string conversation_id to UUID
    conversation_uuid = uuid.UUID(conversation_id)

    rows = session.execute(
        """
        SELECT user_message, bot_response FROM chat_app.conversations WHERE conversation_id = %s
    """,
        (conversation_uuid,),
    )

    conversation = [
        {"user_message": row.user_message, "bot_response": row.bot_response}
        for row in rows
    ]
    return jsonify(conversation)


if __name__ == "__main__":
    app.run(debug=True)
