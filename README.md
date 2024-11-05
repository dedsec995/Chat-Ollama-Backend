# Chat-Ollama-Backend
A flask backend service to serve real-time chat UI, built using Flask, Cassnadra and Ollama. It allows users to send and receive messages, with the data store in cassandra database.

### Prerequisites
Before running the backend, ensure you have the following installed:

- Python 3.7 or higher
- Docker and Docker Compose
- Ollama (click here to install[!https://ollama.com/]

### Installation
1. Clone the repo:
```bask
git clone https://github.com/yourusername/chat-backend-flask.git
cd chat-backend-flask
```
2. Set up a Python virtual environment:
```bash
python3 -m venv env
source env/bin/activate
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Set up Cassandra:
- We provide a `docker-compose.yml` file to set up a Cassandra instance locally.
- Simply run the following command to start Cassandra
```bash
docker-compose up -d
```
This will pull the official Cassandra image, start the Cassandra container, and expose it on port 9042. The keyspace and table will be automatically created on the first run by the backend application.
- Keyspace and table will be created automatically on the first run, just make sure to change `cluster = Cluster(["127.0.0.1"])` in `app.py`.

### Running the App:
Fire up the backend by following command:
```bash
python app.py
```

Feel free to take the source code and use it as you like. It is a boiler plated code to start your own chat app powered by llm. Do check out the [frontend](https://github.com/dedsec995/Chat-Ollama-Frontend) for this project.


Give it a star if you liked it!!
