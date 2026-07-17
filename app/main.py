from fastapi import FastAPI

app = FastAPI(title="Yulsoft Quotation System MVP")

@app.get("/")
def read_root():
    return {"status": "healthy", "message": "Yulsoft API Server is running."}

@app.get("/api/v1/health")
def health_check():
    return {"status": "UP"}