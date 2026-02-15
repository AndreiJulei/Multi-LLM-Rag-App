from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import db
from app.routers import user, documents, collections, chat, admin, settings

app = FastAPI(title="Multi-LLM RAG System")

#Configuration
origins = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
    "http://localhost:3000",      
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#database initialization
db.create_tables()

#adding routers
app.include_router(user.router)
app.include_router(documents.router)
app.include_router(collections.router)
app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(settings.router)


@app.get("/")
def root():
    return {"status": "Backend is running"}