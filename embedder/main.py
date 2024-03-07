import os
from connection import MongoDBConnection

# Nice way to load environment variables for deployments
from dotenv import load_dotenv
load_dotenv()

# Find out what vector provider we're using so we can load the right libraries
provider = os.environ["PROVIDER"]

# OpenAI Stuff
if provider == "openai":
    from openai import OpenAI
    oai_client = OpenAI(api_key=os.environ["OPENAI_KEY"])
elif provider == "vectorservice":
    import requests
elif provider == "mistral":
    from mistralai.client import MistralClient
    mistral_client = MistralClient(api_key=os.environ["MISTRAL_API_KEY"])

# Set up your MongoDB connection and specify collection and inputs/outputs
connection=MongoDBConnection()
db=connection.connect()
collection = db.docs
chunks_collection = db.docs_chunks

# Initialize the change stream
change_stream = collection.watch([], full_document='updateLookup')

# Function to get embeddings from a VectorService endpoint  
def get_embedding_VectorService(embed_text):
    response = requests.get(os.environ["VECTOR_SERVICE_URL"], params={"text":embed_text }, headers={"accept": "application/json"})
    vector_embedding = response.json()
    return vector_embedding

# Function to get embeddings from OpenAI
def get_embedding_OpenAI(text):
   text = text.replace("\n", " ")
   vector_embedding = oai_client.embeddings.create(input = [text], model="text-embedding-ada-002").data[0].embedding
   return vector_embedding

# Function to get embeddings from Mistral
def get_embedding_Mistral(text):
    vector_embedding = mistral_client.embeddings(model="mistral-embed", input=[text]).data[0].embedding
    return vector_embedding

# Providing multiple embedding services depending on config
def get_embedding(text):
    if provider == "openai":
        return get_embedding_OpenAI(text)
    elif provider == "vectorservice":
        return get_embedding_VectorService(text)
    elif provider == "mistral":
        return get_embedding_Mistral(text)

# Create chunks from summary and array of paragraphs
def chunk_and_embed_content(entry):
    chunks = []
    if 'summary' in entry:
        content = "# {title}\n## Summary\n{summary}".format(title=entry['title'][entry['lang']],summary=entry['summary'][entry['lang']])
        chunks.append({
            'parent_id':entry['id'],
            'type':'summary',
            'content':content,
            'embedding':get_embedding(content)
        })

    if len(entry['content'][entry['lang']]) > 0:
        for i,paragraph in enumerate(entry['content'][entry['lang']]):
            content = "# {title}\n## Paragraph {number}\n{paragraph}".format(title=entry['title'][entry['lang']],number=i+1,paragraph=paragraph)
            chunks.append({
                'parent_id':entry['id'],
                'type':'paragraph',
                'content':content,
                'embedding':get_embedding(content),
            })
            
    for i,chunk in enumerate(chunks):
        chunk.update({'chunk':i})
        if 'tags' in entry:
            chunk.update({'tags':entry['tags']})
        if 'published' in entry:
            chunk.update({'published':entry['published']})
    
    return chunks

def insert_chunks(session,parent,chunks):
    chunks_collection.insert_many(chunks,session=session)
    collection.update_one({'_id': parent["_id"]},{"$set": {'embedded': True}},session=session)

# Function to populate all the initial embeddings by detecting any fields with missing embeddings
def initial_sync():
    # We only care about documents with missing keys
    query = {
        "$or": [
            {"embedded": False},
            {"embedded": {"$exists": False}}
        ]
    }
    results = collection.find(query)

    # Every document gets a new embedding
    total_records = 0
    for result in results:
        total_records = total_records + 1
        chunks = chunk_and_embed_content(result)

        # Store the vector embeddings back into collection
        with connection.get_session() as session:
            session.with_transaction(lambda session: insert_chunks(session,result,chunks))

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
        chunks = chunk_and_embed_content(entry)
        # Store the vector embeddings back into collection
        with connection.get_session() as session:
            session.with_transaction(lambda session: insert_chunks(session,entry,chunks))
            

# Perform initial sync
print(f"Initial sync for {db.name} db and {collection.name} collection. Watching for changes to 'content' and writing to 'embedding'...")
total_records = initial_sync()
print(f"Sync complete {total_records} missing embeddings")
print(f"Change stream active...")

# Start consuming changes from the change stream
for change in change_stream:
    handle_changes(change)