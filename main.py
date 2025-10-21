from fastapi import FastAPI
import user
import methodology
import benefit
import analysis
from db import create_tables

app = FastAPI(lifespan=create_tables, title="Social Impact API")

app.include_router(user.router, tags=["users"], prefix="/users")
app.include_router(methodology.router, tags=["methodologies"], prefix="/methodologies")
app.include_router(benefit.router, tags=["benefits"], prefix="/benefits")
app.include_router(analysis.router, tags=["analyses"], prefix="/analyses")

@app.get("/")
def root():
    return {"message": "Impacto de redes sociales en la economía - API"}

