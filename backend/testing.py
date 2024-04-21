from database import *
conn = get_db_connection()
create_tables(conn)

def ask_question(question, session_id, db_connection):
    # Retrieve the conversation history from the SQLite database
    context_history_records = get_conversation_context(db_connection, session_id)
    
    # Format the SQLite conversation history into a single string
    sqlite_context = "\n".join([f"Q: {record['question']}\nA: {record['answer']}" for record in context_history_records])

    # Initialize your Weaviate retriever here
    # Assuming you have a function to initialize the retriever
    retriever = initialize_weaviate_retriever()

    # Use the retriever to get context relevant to the current question from the Weaviate database
    weaviate_context = retriever.retrieve(question)  # Adjust this method according to your Weaviate retriever

    # Combine the context from both sources
    combined_context = f"{weaviate_context}\n\nPrevious Conversation:\n{sqlite_context}"

    template = """
    Here is some information I found that might help answer your question, followed by our previous conversation. Use this information to provide a concise and accurate answer. If you don't know the answer, say that you don't know.

    {combined_context}

    New Question:
    {new_question}
    
    Answer:
    """

    # Create the prompt including the combined context and the new question
    full_prompt = template.format(combined_context=combined_context, new_question=question)

    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

    # Send the full prompt to the model
    answer = llm(full_prompt)

    # Process the answer if necessary
    processed_answer = StrOutputParser().parse(answer)

    # Store the new Q&A pair in the SQLite database
    store_conversation(db_connection, session_id, question, processed_answer)

    return processed_answer
