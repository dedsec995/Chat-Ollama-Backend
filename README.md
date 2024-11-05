# Chat-Ollama
A flask backend service to serve real-time chat UI, built using Flask, Cassnadra and Ollama. It allows users to send and receive messages, with the data store in cassandra database.

### Prerequisites
Before running the backend, ensure you have the following installed:

- Python 3.7 or higher
- Apache Cassandra (or access to a Cassandra cluster)
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
- Install Cassandra on your system
- Keyspace and table will be created automatically on the first run, just make sure to change `cluster = Cluster(["127.0.0.1"])` in `app.py`.

### Running the App:
Fire up the backend by following command:
```bash
python app.py
```
