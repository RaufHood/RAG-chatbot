# Chatbot API Project

This project provides a simple yet powerful chatbot API using FastAPI. It's designed to process text input, perform some operations (e.g., querying a database, calling an external API, or applying some logic), and return a response. This readme guides you through setting up and running the project.

## Features

- FastAPI backend with CORS configured for cross-origin requests.
- POST endpoint `/process-text/` for processing questions through a chatbot.
- Utilizes Pydantic for request validation.

## Requirements

- Python 3.6+
- FastAPI
- Uvicorn (for running the application)
- Any additional libraries your project depends on (e.g., requests for external API calls).

## Setup and Installation

1. **Clone the Repository**

```
git clone https://github.com/lankabelgezogen/hip_prototype.git
cd hip_prototype
```

2. **Create a Virtual Environment** (Optional but recommended)

- For Unix/macOS:
  ```
  python3 -m venv env
  source env/bin/activate
  ```

- For Windows:
  ```
  python -m venv env
  .\env\Scripts\activate
  ```

3. **Install Dependencies**

```
pip install -r requirements.txt
```

4. **Environment Variables**

- Create a `.env` and fill in your values for `OPENAI_API_KEY` and `WEAVIATE_API_KEY`, `WEAVIATE_URL` and  `UPLOAD_DATA_ON_STARTUP` = "false" if you don't want to uplload data/ or true if you want to upload data to weaviate.

5. **Run the Application**

```
uvicorn main:app --reload
```
or in case it doesn't work  
```
uvicorn backend.main:app --reload
```

This command will start the FastAPI application on `http://127.0.0.1:8000`.

## Usage

- To interact with the API, you can use tools like [Postman](https://www.postman.com/) or [curl](https://curl.se/).
- For integration into our frontend, just start a live-server and you're good to go.

