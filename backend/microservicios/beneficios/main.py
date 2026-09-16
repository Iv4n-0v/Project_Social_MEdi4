from fastapi import FastAPI

app = FastAPI(title="Servicio de Beneficios")


@app.get("/")
def root():
    return {"servicio": "beneficios", "status": "ok"}