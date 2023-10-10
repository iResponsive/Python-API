import os
import json
from langchain.document_loaders import TextLoader
from langchain.document_loaders import DirectoryLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain.chat_models import ChatOpenAI
from flask import Flask, request, jsonify
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the filename and Azure Blob Storage connection string
filename = os.environ.get("FILENAME")
container_name = os.environ.get("CONTAINER_NAME")
constr = os.environ.get("AZURE_CONNECTION_STRING")

# Initialize Azure Blob Storage client
blob_service_client = BlobServiceClient.from_connection_string(constr)
container_client = blob_service_client.get_container_client(container_name)
blob_client = container_client.get_blob_client(filename)
streamdownloader = blob_client.download_blob()

# Load data from the Azure Blob Storage file into cloud_file
cloud_file = json.loads(streamdownloader.readall())

# Set the OpenAI API key
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY")

# Initialize document loader, index, and Flask app
loader = DirectoryLoader("./texts", glob="*.txt", loader_cls=TextLoader)
data = loader.load()
index = VectorstoreIndexCreator().from_loaders([loader])
app = Flask(__name__)

# Determine the initial counter value based on the existing data
last_item = cloud_file[-1] if len(cloud_file) > 0 else {"id": 0}
counter = last_item["id"] + 1


# Define the /new-question route
@app.route("/new-question", methods=["POST"])
def new_question():
    global counter

    # Extract all "answer" attributes from cloud_file and concatenate them
    answer_dump = " ".join(item.get("answer", "") for item in cloud_file)

    data = request.get_json()
    question = data.get("question", "")
    query = question

    # Perform a query using the concatenated answers
    ans = index.query(
        "You pretend to be named Sara" + answer_dump + query,
        llm=ChatOpenAI(),
        retriever_kwargs={"search_kwargs": {"k": 1}},
    )

    new_json_data = {"id": counter, "question": question, "answer": ans}

    # Append new data to the cloud_file list
    cloud_file.append(new_json_data)

    # Upload the updated JSON data to Azure Blob Storage
    updated_json_data = json.dumps(cloud_file)
    blob_client.upload_blob(updated_json_data, overwrite=True)

    # Save the updated JSON data locally
    # with open("dump.json", "w") as json_file:
    #    json.dump(cloud_file, json_file)

    counter += 1

    response = {"answer": ans}
    return jsonify(response), 201


if __name__ == "__main__":
    app.run(debug=True, port=8001)
