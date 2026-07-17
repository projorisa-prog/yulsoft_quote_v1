import_error_here_for_testing  # <-- 의도적인 문법 에러 삽입

from fastapi import FastAPI

app = FastAPI(title="Yulsoft Quotation System MVP")

@app.get("/")
def read_root():
    return {"status": "healthy", "message": "Yulsoft API Server is running."}