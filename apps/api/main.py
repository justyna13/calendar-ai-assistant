from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import health, auth, calendar, chat

from contextlib import asynccontextmanager

from database import Base, engine
from models import google_account, google_session

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["http://localhost:3000"], 
    allow_methods=["GET", "POST"],
    allow_credentials=True,
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(calendar.router)
app.include_router(chat.router)