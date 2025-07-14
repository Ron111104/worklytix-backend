# report_generator.py
import matplotlib.pyplot as plt
from fpdf import FPDF
import os

# ---------- Common Utilities ----------
def create_pie_chart(data, labels, title, filename):
    fig, ax = plt.subplots()
    ax.pie(data, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    plt.title(title)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

def create_bar_chart(x, y, title, xlabel, ylabel, filename):
    fig, ax = plt.subplots()
    ax.bar(x, y, color='skyblue')
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

# ---------- Warehouse Manager Report ----------
def generate_warehouse_report(df, output_path="warehouse_report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Warehouse Manager KPI Report", ln=1, align='C')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Section 1: Visual KPI Dashboard", ln=1)

    create_bar_chart(
        df['Warehouse ID'].value_counts().index[:5],
        df.groupby("Warehouse ID")["Inventory_Turnover"].mean().values[:5],
        "Inventory Turnover by Warehouse",
        "Warehouse ID", "Turnover", "wh_bar1.png"
    )
    pdf.image("wh_bar1.png", w=100)

    create_pie_chart(
        df['Order_Status'].value_counts().values,
        df['Order_Status'].value_counts().index,
        "Order Status Distribution", "wh_pie.png"
    )
    pdf.image("wh_pie.png", w=100)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Section 2: Key Insights", ln=1)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 10, f"Avg Pick Duration: {df['Pick Duration (min)'].mean():.2f} mins\n"
                            f"Avg Inventory Accuracy: {df['Inventory_Accuracy (%)'].mean():.2f}%\n"
                            f"Avg Forecast Accuracy: {df['Forecast_Accuracy_pct'].mean():.2f}%\n"
                            f"Total Profit (Rs.): {df['Profit'].sum():,.2f}\n"
                            f"Total Sales (Rs.): {df['Total_Sales'].sum():,.2f}")

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Section 3: Alerts/Recommendations", ln=1)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 10, "- Investigate high pick durations.\n"
                            "- Improve supplier performance with low scorecards.\n"
                            "- Optimize layout to reduce travel distance.")

    pdf.output(output_path)
    os.remove("wh_bar1.png")
    os.remove("wh_pie.png")
    return output_path

# ---------- Store Manager Report ----------
def generate_store_report(df, output_path="store_report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Store Manager KPI Report", ln=1, align='C')

    create_bar_chart(
        df['Category'].value_counts().index[:5],
        df.groupby("Category")["Stockout Flag"].mean().values[:5],
        "Stockout Rate by Category", "Category", "Stockout Rate", "store_bar1.png"
    )
    pdf.image("store_bar1.png", w=100)

    create_pie_chart(
        [df['Return Rate (%)'].mean(), df['Damage Rate (%)'].mean()],
        ["Return", "Damage"],
        "Return vs Damage Rate", "store_pie.png"
    )
    pdf.image("store_pie.png", w=100)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Section 2: Tabular Insights", ln=1)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 10, f"On-Time Delivery: {df['On Time Delivery'].mean() * 100:.2f}%\n"
                            f"Avg Lead Time: {df['Lead Time (Days)'].mean():.2f} days\n"
                            f"Avg PO Aging: {df['PO Aging (Days)'].mean():.2f} days\n"
                            f"Inventory Health Score: {df['Inventory Health Score'].mean():.2f}\n"
                            f"Suggested Replenishment Avg: {df['Suggested Replenishment'].mean():.2f}")

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Section 3: Alerts/Recommendations", ln=1)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 10, "- Flag suppliers with poor delivery.\n"
                            "- Investigate POs with high aging.\n"
                            "- Prioritize categories with high stockouts.")

    pdf.output(output_path)
    os.remove("store_bar1.png")
    os.remove("store_pie.png")
    return output_path

# ---------- Executive Leader Report ----------
def generate_exec_report(df, output_path="executive_report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Executive Leader Strategic Report", ln=1, align='C')

    create_bar_chart(
        df['Business Unit'].value_counts().index[:5],
        df.groupby("Business Unit")["Net Profit"].sum().values[:5],
        "Net Profit by Business Unit", "Business Unit", "Net Profit", "exec_bar1.png"
    )
    pdf.image("exec_bar1.png", w=100)

    create_pie_chart(
        df['Risk Category'].value_counts().values,
        df['Risk Category'].value_counts().index,
        "Risk Category Distribution", "exec_pie.png"
    )
    pdf.image("exec_pie.png", w=100)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Section 2: Strategic KPI Insights", ln=1)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 10, f"ROI on Automation: {df['ROI on Automation (%)'].mean():.2f}%\n"
                            f"Total Revenue (Rs.): {df['Revenue'].sum():,.2f}\n"
                            f"Total Expenses (Rs.): {df['Expenses'].sum():,.2f}\n"
                            f"Total Logistics Spend (Rs.): {df['Logistics Spend'].sum():,.2f}\n"
                            f"Avg Initiative Impact Score: {df['Initiative Impact Score'].mean():.2f}")

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Section 3: Strategy & Risks", ln=1)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 10, "- Identify regions with high risk score.\n"
                            "- Assess low ROI regions for restructuring.\n"
                            "- Focus on emission reduction and renewable investments.")

    pdf.output(output_path)
    os.remove("exec_bar1.png")
    os.remove("exec_pie.png")
    return output_path
