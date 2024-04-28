import os
from packages import MongoDBConnection

# Nice way to load environment variables for deployments
from dotenv import load_dotenv
load_dotenv()

# Find out what vector provider we're using so we can load the right libraries
provider = os.getenv("PROVIDER",default="azure_openai")

# Embedding services. Default to using Azure OpenAI.
if provider == "openai":
    from openai import OpenAI
    oai_client = OpenAI(api_key=os.getenv("OPENAIAPIKEY"))
elif provider == "vectorservice":
    import requests
elif provider == "mistral":
    from mistralai.client import MistralClient
    mistral_client = MistralClient(api_key=os.getenv("MISTRAL_API_KEY"))
elif provider == "azure_openai":
    from openai import AzureOpenAI
    oai_client = AzureOpenAI(api_key=os.getenv("OPENAIAPIKEY"))
elif provider == "fireworks":
    from openai import OpenAI
    fireworks_client = OpenAI(
        api_key=os.getenv("FIREWORKS_API_KEY"),
        base_url="https://api.fireworks.ai/inference/v1"
    )
elif provider == "nomic":
    from nomic import embed
else:
    print("No valid provider specified. Defaulting to Azure OpenAI.")
    provider = "azure_openai"
    from openai import AzureOpenAI
    oai_client = AzureOpenAI(
        api_key=os.getenv("OPENAIAPIKEY"),
        api_version="2023-12-01-preview",
        azure_endpoint=os.getenv("OPENAIENDPOINT")
    )

# Set up your MongoDB connection and specify collection and inputs/outputs
connection=MongoDBConnection()
db=connection.connect()
collection = db.docs_chunks

# Initialize the change stream
change_stream = collection.watch([], full_document='updateLookup')

# Function to get embeddings from a VectorService endpoint  
def get_embedding_VectorService(embed_text):
    response = requests.get(os.getenv("VECTOR_SERVICE_URL"), params={"text":embed_text }, headers={"accept": "application/json"})
    vector_embedding = response.json()
    return vector_embedding

# Function to get embeddings from OpenAI
def get_embedding_OpenAI(text):
   text = text.replace("\n", " ")
   vector_embedding = oai_client.embeddings.create(input = [text], model="text-embedding-ada-002").data[0].embedding
   return vector_embedding

# Function to get embeddings from Azure OpenAI
def get_embedding_Azure_OpenAI(text):
   text = text.replace("\n", " ")
   vector_embedding = oai_client.embeddings.create(input = [text], model=os.getenv("OPENAIDEPLOYMENT")).data[0].embedding
   return vector_embedding

# Function to get embeddings from Mistral
def get_embedding_Mistral(text):
    vector_embedding = mistral_client.embeddings(model="mistral-embed", input=[text]).data[0].embedding
    return vector_embedding

# Function to get embeddings from Fireworks.ai
def get_embedding_Fireworks(text):
    text = text.replace("\n", " ")
    vector_embedding = fireworks_client.embeddings.create(
        model="nomic-ai/nomic-embed-text-v1.5",
        input=f"search document: {text}",
        dimensions=os.getenv("EMBEDDING_DIMENSIONS",768)
    ).data[0].embedding
    return vector_embedding

def get_embedding_Nomic(text):
    vector_embedding = embed.text(
        texts=[text],
        model='nomic-embed-text-v1.5',
        task_type="search_document",
        dimensionality=os.getenv("EMBEDDING_DIMENSIONS",768)
    )['embeddings']
    return vector_embedding

# Providing multiple embedding services depending on config
def get_embedding(text):
    if provider == "openai":
        return get_embedding_OpenAI(text)
    elif provider == "vectorservice":
        return get_embedding_VectorService(text)
    elif provider == "mistral":
        return get_embedding_Mistral(text)
    elif provider == "azure_openai":
        return get_embedding_Azure_OpenAI(text)
    elif provider == "fireworks":
        return get_embedding_Fireworks(text)
    elif provider == "nomic":
        return get_embedding_Nomic(text)
# Function to populate all the initial embeddings by detecting any fields with missing embeddings
def initial_sync():
    # We only care about documents with missing keys
    query = {"embedding": {"$exists": False}}
    results = collection.find(query)

    # Every document gets a new embedding
    total_records = 0
    for result in results:
        collection.update_one({"_id":result["_id"]}, {"$set": {"embedding":get_embedding(result['content'])}})

    return total_records

# Function to handle changes in the collection
def handle_changes(change):
    # Extract the necessary information from the change document
    operation_type = change['operationType']

    # Bail out if the detected update is the embedding we just did!
    if operation_type == "update" and 'embedding' in change['updateDescription']['updatedFields']:
        return

    # Anytime we create, update or replace documents, the embedding needs to be updated
    if operation_type == "replace" or operation_type == "update" or operation_type == "insert":
        # Get the _id for update later and our input field to vectorize
        entry = change['fullDocument']
        collection.update_one({"_id":entry["_id"]}, {"$set": {"embedding":get_embedding(entry['content'])}})
            
# Perform initial sync
print(f"Initial sync for {db.name} db and {collection.name} collection. Watching for changes to 'content' and writing to 'embedding'...")
total_records = initial_sync()
print(f"Sync complete {total_records} missing embeddings")
print(f"Change stream active...")

# Start consuming changes from the change stream
for change in change_stream:
    handle_changes(change)