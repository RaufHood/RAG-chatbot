import weaviate
from langchain_community.vectorstores import Weaviate
from langchain_community.retrievers import WeaviateHybridSearchRetriever
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.docstore.document import Document
#from langchain_community.retrievers import WeaviateSearchRetriever
from langchain_community.retrievers import (
    WeaviateHybridSearchRetriever,
)
from .utils import extract_content_chunks_from_file

import os
from dotenv import load_dotenv

# Load the .env file from the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
env_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=env_path)

retriever = None

# Retrieve the environment variables
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
WEAVIATE_URL = os.getenv("WEAVIATE_URL", 'default-url-if-not-set')

client = weaviate.Client(
    url=WEAVIATE_URL,
    auth_client_secret=weaviate.AuthApiKey(WEAVIATE_API_KEY),
    additional_headers={
        "X-Openai-Api-Key": os.getenv("OPENAI_API_KEY"),
    },
)

try:
    print("Checking Weaviate connection...")
    client.is_ready()  # or client.get_meta() to fetch metadata
    print("Connection established.")
except Exception as e:
    print("Failed to establish connection:", e)
# print(client.schema.get())

#def upload_text_sources(file_path):
    #'''
    #Process the input text and generate an answer using a question-answering model.

    #Args:
    #    input_text (str): The input text containing a question.

    #Returns:
    #    str: The generated answer to the question.
    #'''

    #embeddings = OpenAIEmbeddings()
    #texts = extract_content_chunks_from_file(file_path)
    #doc = []
    #for text in texts:
    #    if isinstance(text.metadata, dict):
    #        meta = text.metadata  # Use metadata directly if it's already a dictionary
    #    else:
    #        meta = {'source': str(text.metadata)}  # Convert to string if necessary
    #    doc.append(Document(page_content=text.page_content, metadata=meta))
    #    #print(text.page_content)
    #
    #docsearch = Weaviate.from_documents(
    #    documents = doc,
    #    embedding = embeddings,
    #    client = client,
    #    by_text=False,
    #)
    #return docsearch.as_retriever()

def upload_text_sources(file_path):
    embeddings = OpenAIEmbeddings()
    texts = extract_content_chunks_from_file(file_path)
    doc = [Document(page_content=text.page_content, metadata={'source': str(text.metadata)}) for text in texts]
    print(f"Uploading {len(doc)} documents")
    try:
        docsearch = Weaviate.from_documents(documents=doc, embedding=embeddings, client=client, by_text=False)
        print("Documents uploaded successfully.")
    except Exception as e:
        print(f"Error uploading documents: {e}")
    return docsearch.as_retriever()

def check_data():
    result = client.query.get('LangChain', ['text']).with_limit(10).do()
    print("DATA:", result)

def check_document_count():
    count = client.query.aggregate('LangChain').with_meta_count().do()
    print("COUNT:", count)

def check_schema():
    schema = client.schema.get()
    print(schema)

def get_retriever():
    #global retriever
    #if retriever is None:
    #    file_path = os.path.join(script_dir, "paca.html")
    #    retriever = upload_text_sources(file_path)
    retriever = WeaviateHybridSearchRetriever(
        client=client,
        index_name="LangChain",
        text_key="text",
        attributes=[],
        create_schema_if_missing=True,
    )
    return retriever

def ask_question(question):
    retriever = get_retriever()

    if retriever is None:
        raise Exception("Retriever is not initialized properly.")
    
    # Attempt to retrieve context based on the question
    context = retriever.get_relevant_documents(question)  
    print("Retrieved context:", context)  # Log the retrieved context

    template = """You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
    Question: {question} 
    Context: {context} 
    Answer:
    """

    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    answer = rag_chain.invoke(question)
    return answer

if __name__ == "__main__":
    check_schema()
    check_data()
    check_document_count()
    retriever = get_retriever()
    input_text = input("Enter your question: ")
    answer = ask_question(input_text)
    print(answer)
