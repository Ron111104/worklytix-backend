from fastapi import APIRouter
from fastapi.responses import FileResponse
import pandas as pd
from reports.report_generator import generate_warehouse_report, generate_store_report, generate_exec_report

router = APIRouter()

@router.get("/warehouse")
def generate_warehouse():
    df = pd.read_csv("data/warehouse_dataset.csv")
    pdf_path = generate_warehouse_report(df)
    return FileResponse(pdf_path, media_type="application/pdf", filename="warehouse_report.pdf")

@router.get("/store")
def generate_store():
    df = pd.read_csv("data/store_manager_dataset.csv")
    pdf_path = generate_store_report(df)
    return FileResponse(pdf_path, media_type="application/pdf", filename="store_report.pdf")

@router.get("/executive")
def generate_exec():
    df = pd.read_csv("data/executive_insights_dataset.csv")
    pdf_path = generate_exec_report(df)
    return FileResponse(pdf_path, media_type="application/pdf", filename="executive_report.pdf")
