from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import emotion, chat, auth, settings
from database import engine
import models

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(emotion.router)
app.include_router(chat.router)
app.include_router(settings.router)

@app.get("/")
def read_root():
    return {"Hello": "VibeChat"}
