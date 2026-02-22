# Multi-LLM-Rag-App
This is a RAG app that uses multiple api keys to get answers from multiple LLM's, then implementing a voting system that makes the LLM's vote for the best answer, thus giving the user the best possible answer.

## FEATURES:
    Backend: FastAPI, SQLAlchemy, LangChain
    Vector DB: ChromaDB 
    Frontend: Streamlit
    Authentification: JWT

### How to run (This app was built on MacOS some features might be different)
#### 1. Create virtual environment in the backend folder:
    - on macOS/Linux:
        python3 -m venv .venv
    - on Windows:
        python -m venv .venv


#### 2. Activate virtual enviroment:
    - on windows(command prompt):
        .venv\Scripts\activate
    
    - windos powershell:
        
        .\.venv\Scripts\activate
    
    - on macOS/Linux:
        
        source .venv/bin/activate


#### 3. Install requirements in the virtual enviroment:
    pip install -r requirements.txt


#### 4. Run the backend:
    cd backend
    uvicorn main:app --reload


#### 5. Run the frontend while the backend is running:
    cd frontend
    streamlit run app.py


#### 6. Access the app:
    Open the browser to the Streamlit URL - http://localhost:8501


#### 7. Log in with the already created credentials:
    email - user@example.com
    password - stringst


### For the api address: http://127.0.0.1:8000

### .env file configuration:

#### API keys:
GOOGLE_API_KEY=your_api_key
GROQ_API_KEY=your_api_key

#### Database 
DATABASE_URL=sqlite:///./sql_app.db

#### Auth 
SECRET_KEY=a_random_secret_string_for_jwt


## For app: 
    First 3 steps remain the same, then:
    Without env active install in /desktop_app: 
        - npm install
        - npm run dump
    
    Then create executable with:
        - npm run app:dist

    Last step open the app executable created in the folder /desktop_app/dist/mac-arm64/MacOS/CounselOfAI