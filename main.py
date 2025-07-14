from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from plots.plot_router import router as plot_router
from reports.report_router import router as report_router
from queries.query_router import router as query_router

app = FastAPI(title="Supply Chain KPI API")

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to specific frontend URL(s) in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(report_router, prefix="/report", tags=["Reports"])
app.include_router(query_router, prefix="/query", tags=["LLM Query"])
app.include_router(plot_router, prefix="/plot", tags=["Plots"])
