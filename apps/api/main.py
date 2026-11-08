from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["GET"])

@app.get("/health")
def health_check():
    return {"message": "API is running"}