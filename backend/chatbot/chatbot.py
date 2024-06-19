import weaviate
from langchain_community.retrievers import WeaviateHybridSearchRetriever
from langchain_openai import OpenAIEmbeddings, ChatOpenAI #, ChatPromptTemplate
from langchain_core.prompts import ChatPromptTemplate 
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv
from .utils import extract_content_chunks_from_file
from .firestore_service import store_conversation, get_conversation_history
import logging

# Load the .env file from the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
env_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=env_path)

# Clear existing environment variables
os.environ.pop("UPLOAD_DATA_ON_STARTUP", None)

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
    client.is_ready()
    print("Connection established.")
except Exception as e:
    print("Failed to establish connection:", e)


def clear_classes():
    print("Clearing existing classes...")  # Added logging
    classes = client.schema.get()["classes"]
    for cls in classes:
        print(f"Deleting class: {cls['class']}")  # Added logging
        client.schema.delete_class(cls["class"])
    print("Existing classes cleared.")  # Added logging

def create_schema():
    print("Creating new schema...")
    schema = {
        "classes": [
            {
                "class": "LangChain",
                "vectorizer": "text2vec-openai",
                "moduleConfig": {
                    "text2vec-openai": {
                        "baseURL": "https://api.openai.com",
                        "model": "ada",
                        "vectorizeClassName": True,
                    },
                },
                "properties": [
                    {
                        "name": "text",
                        "dataType": ["text"],
                        "indexFilterable": True,
                        "indexSearchable": True,
                        "moduleConfig": {
                            "text2vec-openai": {
                                "skip": False,
                                "vectorizePropertyName": False,
                            },
                        },
                        "tokenization": "word",
                    },
                    {
                        "name": "source",
                        "dataType": ["text"],
                        "indexFilterable": True,
                        "indexSearchable": True,
                        "tokenization": "word",
                    },
                ],
            }
        ]
    }
    client.schema.create(schema)
    print("Schema created successfully.")

def upload_text_sources(file_path):
    embeddings = OpenAIEmbeddings()
    texts = extract_content_chunks_from_file(file_path)

    clear_classes()
    create_schema()

    documents = [
        {
            "text": text.page_content,
            "source": str(text.metadata)
        }
        for text in texts
    ]

    print(f"Uploading {len(documents)} documents")

    with client.batch as batch:
        for doc in documents:
            batch.add_data_object(doc, "LangChain")

    print("Documents uploaded successfully.")
    return documents

def retrieve_documents(question, top_k=5):
    retriever = WeaviateHybridSearchRetriever(
        client=client,
        index_name="LangChain",
        text_key="text",
        attributes=["text"],
        create_schema_if_missing=True,
    )

    return retriever.get_relevant_documents(question)

async def ask_question(session_id: str, question: str):
    # Retrieve the conversation history for context
    logging.debug("Fetching conversation history...")
    history_context = get_conversation_history(session_id)
    print("Session_id: ", session_id)
    logging.debug(f"History context retrieved: {history_context}")

    history_formatted = "\n".join([f"Q: {h['question']} A: {h['answer']}" for h in history_context])
    
    logging.debug("Retrieving documents from Weaviate...")
    vector_documents = retrieve_documents(question)
    logging.debug(f"Documents retrieved: {vector_documents}")
    vector_context = "\n".join([doc.page_content for doc in vector_documents])
    # Combine both contexts
    combined_context = f"Previous Conversations:\n{history_formatted}\n\nRelevant Information:\n{vector_context}"
    # print(f"context: {combined_context}") # for debugging
    #logging.debug(f"Combined context: {combined_context}")
    c_combined_context = """
    Chemotherapy commonly causes side effects such as nausea, vomiting, hair loss, fatigue, and increased risk of infection. Other possible side effects include anemia, bleeding problems, mouth sores, and changes in appetite. The severity and type of side effects can vary depending on the specific chemotherapy drugs used and the patient's overall health.
    """

    # You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
    prompt_text = f"""Sie sind ein Assistent für die Beantwortung von Fragen. Beantworten Sie die Frage mit Hilfe der folgenden Kontextinformationen. Wenn Sie die Antwort nicht wissen, sagen Sie einfach, dass Sie sie nicht wissen. Verwenden Sie maximal drei Sätze und fassen Sie die Antwort kurz zusammen.
    Frage: {question} 
    Kontext: {combined_context} 
    Antwort:
    """
    
    #logging.debug("Preparing prompt...")
    prompt = ChatPromptTemplate.from_template(prompt_text)
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
    parser = StrOutputParser()

    inputs = {"context": combined_context, "question": question}
    prompt_output = prompt.invoke(inputs)
    llm_output = llm.invoke(prompt_output) 
    #logging.debug(f"LLM output: {llm_output}")

    answer = parser.invoke(llm_output)
    logging.debug(f"Answer received: {answer}")

    # Store the new conversation entry
    #logging.debug("Storing conversation...")
    store_conversation(session_id, question, answer)
    logging.debug("Conversation stored successfully.")
    
    return answer


def check_schema():
    schema = client.schema.get()
    print("Schema:", schema)

def check_data():
    result = client.query.get('LangChain', ['text', 'source']).with_limit(10).do()
    print("DATA:", result)

def check_document_count():
    count = client.query.aggregate('LangChain').with_meta_count().do()
    print("COUNT:", count)

if __name__ == "__main__":
    #check_schema()        # Verify the schema
    #check_data()          # Verify data in LangChain class
    #check_document_count()# Check document count
    # Re-upload documents
    file_path = "backend/chatbot/paca.html"
    retriever = upload_text_sources(file_path)
    input_text = input("Enter your question: ")
    answer = ask_question(input_text)
    print(answer)
