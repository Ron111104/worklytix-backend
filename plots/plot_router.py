# plots/plot_router.py

from fastapi import APIRouter, Response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from io import BytesIO

router = APIRouter()

# Load datasets
warehouse_df = pd.read_csv("data/warehouse_dataset.csv")
store_df = pd.read_csv("data/store_manager_dataset.csv")
executive_df = pd.read_csv("data/executive_insights_dataset.csv")


def fig_to_response(fig):
    buf = BytesIO()
    fig.tight_layout()
    FigureCanvas(fig).print_png(buf)
    plt.close(fig)
    return Response(content=buf.getvalue(), media_type="image/png")


@router.get("/plot/{role}/{index}")
def get_plot(role: str, index: int):
    fig, ax = plt.subplots(figsize=(8, 4))

    role = role.lower().strip()

    if role == "warehouse ops manager":
        plots = [
            lambda: sns.histplot(warehouse_df["Inventory_Turnover"], kde=True, ax=ax),
            lambda: sns.boxplot(x="Shipping_Mode", y="Shipping_Date", data=warehouse_df, ax=ax),
            lambda: sns.scatterplot(x="Forecast_Accuracy_pct", y="Profit", data=warehouse_df, ax=ax),
            lambda: sns.barplot(x="Order_Region", y="Total_Sales", data=warehouse_df, ax=ax),
        ]
    elif role == "store manager":
        plots = [
            lambda: sns.barplot(x="Supplier Name", y="Total Cost", data=store_df, ax=ax),
            lambda: sns.boxplot(x="On Time Delivery", y="Lead Time (Days)", data=store_df, ax=ax),
            lambda: sns.histplot(store_df["Inventory Health Score"], kde=True, ax=ax),
            lambda: sns.scatterplot(x="Return Rate (%)", y="Damage Rate (%)", data=store_df, ax=ax),
        ]
    elif role == "executive":
        plots = [
            lambda: sns.barplot(x="Product Name", y="Net Profit", data=executive_df, ax=ax),
            lambda: sns.scatterplot(x="ROI on Automation (%)", y="Automation Investment", data=executive_df, ax=ax),
            lambda: sns.boxplot(x="Risk Status", y="Risk Score", data=executive_df, ax=ax),
            lambda: sns.barplot(x="Region", y="Carbon Emission (kg)", data=executive_df, ax=ax),
        ]
    elif role == "supply chain manager":
        if index % 2 == 0:
            plots = [
                lambda: sns.barplot(x="Shipping_Mode", y="Profit", data=warehouse_df, ax=ax),
                lambda: sns.histplot(warehouse_df["Forecast_Accuracy_pct"], kde=True, ax=ax),
            ]
        else:
            plots = [
                lambda: sns.barplot(x="Supplier Country", y="Supplier Rating", data=store_df, ax=ax),
                lambda: sns.scatterplot(x="Lead Time (Days)", y="Total Cost", data=store_df, ax=ax),
            ]
    else:
        return Response(status_code=404, content=f"Unsupported role: {role}")

    try:
        plots[index % len(plots)]()
        return fig_to_response(fig)
    except Exception as e:
        return Response(status_code=500, content=f"Error generating plot: {str(e)}")
