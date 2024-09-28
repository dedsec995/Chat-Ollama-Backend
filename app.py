from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from langchain_ollama import ChatOllama
from cassandra.cluster import Cluster
import uuid, os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

UPLOAD_FOLDER = "uploads/"  # Define the folder for uploaded files
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Create the folder if it doesn't exist
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Initialize the Ollama model
llm = ChatOllama(
    model="mistral-nemo"
    # other params...
)

# Cassandra setup
cluster = Cluster(["127.0.0.1"])
session = cluster.connect()

session.execute(
    """
    CREATE TABLE IF NOT EXISTS chat_app.conversations (
    conversation_id uuid,
    message_id uuid,
    user_message text,
    bot_response text,
    message_timestamp timestamp,
    PRIMARY KEY (conversation_id, message_timestamp, message_id)
    ) WITH CLUSTERING ORDER BY (message_timestamp ASC);
    """
)

session.execute(
    """
    CREATE TABLE IF NOT EXISTS chat_app.uploaded_files (
    conversation_id uuid,
    file_id uuid,
    file_path text,
    upload_timestamp timestamp,
    PRIMARY KEY (conversation_id, file_id)
    );
    """
)

# Function to estimate token count (simplified)
def count_tokens(message):
    return len(
        message.split()
    )  # Simplified token count; replace with an appropriate tokenizer if available.


# Render home page with conversation list
@app.route("/")
def home():
    return "Hello From Dedsec995!!"


@app.route("/api/conversations", methods=["GET"])
def get_conversations():
    # Fetch distinct conversation IDs to display as a list
    rows = session.execute(
        "SELECT DISTINCT conversation_id FROM chat_app.conversations;"
    )
    conversations = [str(row.conversation_id) for row in rows]
    return jsonify({"conversations": conversations})


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

    # Retrieve the entire conversation history
    conversation_history = session.execute(
        """
        SELECT user_message, bot_response FROM chat_app.conversations 
        WHERE conversation_id = %s 
        ORDER BY message_timestamp ASC
    """,
        (conversation_id,),
    )

    # Construct the full context for the LLM
    full_conversation = []
    for row in conversation_history:
        full_conversation.append(f"User: {row.user_message}")
        full_conversation.append(f"Bot: {row.bot_response}")

    # Append the new user message
    full_conversation.append(f"User: {user_message}")

    # Check token count and truncate if necessary
    total_tokens = sum(count_tokens(msg) for msg in full_conversation)

    while total_tokens > 8000 and len(full_conversation) > 0:
        # Remove the oldest message (the first two entries if they exist)
        full_conversation.pop(0)  # Remove the oldest user message
        full_conversation.pop(0)  # Remove the oldest bot response (if exists)

        # Recalculate total tokens
        total_tokens = sum(count_tokens(msg) for msg in full_conversation)

    # Join the conversation into a single string
    context = "\n".join(full_conversation)

    # Get response from the LLM
    bot_response = llm.invoke(context)
    bot_message = bot_response.content

    # Get current timestamp
    timestamp = datetime.utcnow()

    # Store the message, bot response, and timestamp in Cassandra
    session.execute(
        """
        INSERT INTO chat_app.conversations (conversation_id, message_id, user_message, bot_response, message_timestamp)
        VALUES (%s, %s, %s, %s, %s)
    """,
        (conversation_id, uuid.uuid4(), user_message, bot_message, timestamp),
    )

    return jsonify({"response": bot_message, "conversation_id": str(conversation_id)})


# API to get a past conversation's messages
@app.route("/conversation/<conversation_id>", methods=["GET"])
def get_conversation(conversation_id):
    # Convert the string conversation_id to UUID
    conversation_uuid = uuid.UUID(conversation_id)

    # Retrieve the conversation ordered by timestamp
    rows = session.execute(
        """
        SELECT user_message, bot_response FROM chat_app.conversations 
        WHERE conversation_id = %s 
        ORDER BY message_timestamp ASC
    """,
        (conversation_uuid,),
    )

    conversation = [
        {"user_message": row.user_message, "bot_response": row.bot_response}
        for row in rows
    ]
    return jsonify(conversation)


@app.route("/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Retrieve the conversation_id from the request
    conversation_id = request.form.get('conversation_id')  

    # Check if the conversation_id exists
    if conversation_id:
        conversation_id = uuid.UUID(conversation_id)
    else:
        conversation_id = uuid.uuid4()

    # Create a new UUID folder for the conversation
    folder_name = str(conversation_id)  # Use the conversation_id as the folder name
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)

    os.makedirs(folder_path, exist_ok=True)  # Create the new folder

    # Save the file in the newly created folder
    file_path = os.path.join(folder_path, secure_filename(file.filename))
    file.save(file_path)

    # Insert the file upload record into the uploaded_files table
    session.execute(
        """
        INSERT INTO chat_app.uploaded_files (conversation_id, file_id, file_path, upload_timestamp)
        VALUES (%s, %s, %s, %s)
        """,
        (conversation_id, uuid.uuid4(), file_path, datetime.utcnow())
    )

    session.execute(
        """
        INSERT INTO chat_app.conversations (conversation_id, message_id, user_message, bot_response, message_timestamp)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (conversation_id, uuid.uuid4(), "File uploaded: " + secure_filename(file.filename), "File received.", datetime.utcnow())
    )

    return jsonify({"message": "File uploaded successfully", "conversation_id": str(conversation_id), "folder": folder_name}), 201


if __name__ == "__main__":
    app.run(debug=True)
