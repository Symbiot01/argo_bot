# /services/vector_db.py

import time
import logging
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
import config
from utils.document_processor import load_and_split_pdfs

def initialize_pinecone():
    """
    Initializes connection to Pinecone and creates the index if it doesn't exist.
    
    Returns:
        pinecone.Index: The Pinecone index object.
    """

    # logging.info(f'api_key={config.PINECONE_API_KEY}')
    pc = Pinecone(api_key=config.PINECONE_API_KEY)
    index_name = config.PINECONE_INDEX_NAME

    if index_name not in [index["name"] for index in pc.list_indexes()]:
        logging.info(f"Creating new Pinecone index: {index_name}...")
        pc.create_index(
            name=index_name,
            dimension=config.EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(cloud='aws', region='us-east-1')
        )
        while not pc.describe_index(index_name).status["ready"]:
            logging.info("Waiting for index to be ready...")
            time.sleep(5)
        logging.info("Index created successfully.")
    else:
        logging.info(f"Index '{index_name}' already exists.")

    return pc.Index(index_name)

def get_vector_store(index, embeddings):
    """
    Initializes the PineconeVectorStore for retrieval.
    """
    return PineconeVectorStore(index=index, embedding=embeddings)

def setup_knowledge_base(index, embeddings):
    """
    Processes PDF files and upserts them into Pinecone.
    Checks if the index is already populated to avoid re-ingestion.
    """
    if index.describe_index_stats()['total_vector_count'] > 0:
        logging.info("Knowledge base already populated in Pinecone. Skipping ingestion.")
        return

    foundational_chunks = load_and_split_pdfs()

    if foundational_chunks:
        logging.info(f"Adding {len(foundational_chunks)} chunks to the knowledge base.")
        vector_store = get_vector_store(index, embeddings)
        vector_store.add_documents(documents=foundational_chunks, ids=None) # Pinecone will assign IDs
        logging.info("Foundational knowledge base setup in Pinecone is complete.")
    else:
        logging.info("No new documents to process for the knowledge base.")