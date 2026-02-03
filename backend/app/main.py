from fastapi import FastAPI

app = FastAPI(title="RAG Backend")


@app.get("/")
async def root():
    return {"message": "RAG backend is running"}
