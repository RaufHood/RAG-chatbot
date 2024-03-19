import weaviate
from langchain_community.vectorstores import Weaviate
from langchain_community.retrievers import WeaviateHybridSearchRetriever
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.docstore.document import Document

import os
from dotenv import load_dotenv
from .utils import extract_content_chunks_from_file

load_dotenv()
script_dir = os.path.dirname(__file__)

def process_input(input_text):
    '''
    Process the input text and generate an answer using a question-answering model.

    Args:
        input_text (str): The input text containing a question.

    Returns:
        str: The generated answer to the question.
    '''

    WEAVIATE_API_KEY = os.environ["WEAVIATE_API_KEY"]

    WEAVIATE_URL =  "https://tum-vl-8tfffgg9.weaviate.network"
 
    client = weaviate.Client(
        url=WEAVIATE_URL,
        auth_client_secret=weaviate.AuthApiKey(WEAVIATE_API_KEY),
        additional_headers={
            "X-Openai-Api-Key": os.getenv("OPENAI_API_KEY"),
        },
    )

    embeddings = OpenAIEmbeddings()

    file_path = os.path.join(script_dir, "paca.html")
    texts = extract_content_chunks_from_file(file_path)

    doc = []
    for k in range(len(texts)):
        if isinstance(texts[k].metadata, dict):
            meta = texts[k].metadata  # Use metadata directly if it's already a dictionary
        else:
            meta = {'source': str(texts[k].metadata)}  # Convert to string if necessary
        a = Document(page_content=texts[k].page_content, metadata=meta)
        doc.append(a)

    docsearch = Weaviate.from_documents(
        documents = doc,
        embedding = embeddings,
        client = client,
        by_text=False,
        #metadatas=[{"source": f"{i}-pl"} for i in range(len(doc))],
    )

    retriever = docsearch.as_retriever()

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

    answer = rag_chain.invoke(input_text)
    return answer


if __name__ == "__main__":
    input_text = input("Enter your question: ")
    result = process_input(input_text)
    print(result)
