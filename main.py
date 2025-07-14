from fastapi import FastAPI
from reports.report_router import router as report_router
from queries.query_router import router as query_router

app = FastAPI(title="Supply Chain KPI API")

app.include_router(report_router, prefix="/report", tags=["Reports"])
app.include_router(query_router, prefix="/query", tags=["LLM Query"])
