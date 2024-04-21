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

import os
from dotenv import load_dotenv
from .utils import extract_content_chunks_from_file

load_dotenv()
script_dir = os.path.dirname(__file__)
# Global variable for the retriever
retriever = None

WEAVIATE_API_KEY = os.environ["WEAVIATE_API_KEY"]
WEAVIATE_URL =  os.getenv("WEAVIATE_URL", 'default-url-if-not-set')
print("Weaviate URL:", WEAVIATE_URL)


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

def upload_text_sources(file_path):
    '''
    Process the input text and generate an answer using a question-answering model.

    Args:
        input_text (str): The input text containing a question.

    Returns:
        str: The generated answer to the question.
    '''

    embeddings = OpenAIEmbeddings()

    
    texts = extract_content_chunks_from_file(file_path)

    doc = []
    for text in texts:
        if isinstance(text.metadata, dict):
            meta = text.metadata  # Use metadata directly if it's already a dictionary
        else:
            meta = {'source': str(text.metadata)}  # Convert to string if necessary
        doc.append(Document(page_content=text.page_content, metadata=meta))

    docsearch = Weaviate.from_documents(
        documents = doc,
        embedding = embeddings,
        client = client,
        by_text=False,
    )

    return docsearch.as_retriever()

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

    # retrieval
    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    answer = rag_chain.invoke(question)
    return answer

if __name__ == "__main__":
    retriever = get_retriever()
    input_text = input("Enter your question: ")
    answer = ask_question(input_text)
    print(answer)
