import json
from flask import Flask, request, jsonify
from azure.storage.blob import BlobServiceClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the filename of the JSON file to be retrieved from Azure Blob Storage
filename = os.environ.get("FILENAME")

# Define the name of the Azure Blob Storage container
container_name = os.environ.get("CONTAINER_NAME")

# Define the connection string to access the Azure Blob Storage account
constr = os.environ.get("AZURE_CONNECTION_STRING")

# Create a Flask web application instance
app = Flask(__name__)


# Define a route for handling POST requests to the "/history" endpoint
@app.route("/history", methods=["POST"])
def history():
    # Create a BlobServiceClient using the provided connection string
    blob_service_client = BlobServiceClient.from_connection_string(constr)

    # Get a reference to the Azure Blob Storage container
    container_client = blob_service_client.get_container_client(container_name)

    # Get a reference to the specific blob (JSON file) in the container
    blob_client = container_client.get_blob_client(filename)

    # Download the blob content
    streamdownloader = blob_client.download_blob()

    # Read the JSON data from the downloaded blob and parse it
    cloud_file = json.loads(streamdownloader.readall())

    # Return the JSON data as a response with a status code 200 (OK)
    return jsonify(cloud_file), 200


# Start the Flask application when this script is executed directly
if __name__ == "__main__":
    app.run(debug=True, port=8002)
