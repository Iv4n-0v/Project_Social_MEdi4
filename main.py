from fastapi import FastAPI
import user, methodology, benefit, analysis
from db import create_tables
import reports

app = FastAPI(lifespan=create_tables, title="Social Impact API")

app.include_router(user.router, prefix="/users")
app.include_router(methodology.router, prefix="/methodologies")
app.include_router(benefit.router, prefix="/benefits")
app.include_router(analysis.router, prefix="/analyses")
app.include_router(reports.router, prefix="/reports", tags=["reports"])