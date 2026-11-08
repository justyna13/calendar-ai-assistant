from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import health, auth

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["GET"])

app.include_router(health.router)
app.include_router(auth.router)