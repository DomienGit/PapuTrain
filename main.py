from fastapi import FastAPI

app = FastAPI(title="PapuTrain API")


@app.get("/hello")
def hello():
    return {"message": "Cześć, PapuTrain działa!"}
