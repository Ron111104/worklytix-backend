# Enhanced report_generator_test.py - Cleaned and Organized
import matplotlib
matplotlib.use('Agg')
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
from fpdf import FPDF
from datetime import datetime

sns.set(style="whitegrid")

# ---------- PDF Base Class ----------
class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "GenAI-Powered Dynamic Supply Chain Report", 0, 1, "C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

# ---------- Utilities ----------
def save_plot(fig, filename):
    """Save plot and verify it's a valid PNG"""
    try:
        fig.tight_layout()
        fig.savefig(filename, format='png')
        plt.close(fig)

        # Validate PNG header (first 8 bytes: \x89PNG\r\n\x1a\n)
        with open(filename, 'rb') as f:
            header = f.read(8)
            if header != b'\x89PNG\r\n\x1a\n':
                raise ValueError(f"{filename} is not a valid PNG file.")
    except Exception as e:
        print(f"Error saving {filename}: {e}")
        raise


def draw_table(pdf, title, dataframe, col_widths=None, max_rows=10):
    """Draw a formatted table in PDF"""
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, title, ln=True)
    pdf.set_font("Arial", size=8)
    
    if col_widths is None:
        col_widths = [pdf.w / (len(dataframe.columns) + 1)] * len(dataframe.columns)
    
    # Header
    for i, col in enumerate(dataframe.columns):
        pdf.cell(col_widths[i], 7, str(col), border=1, align="C")
    pdf.ln(7)
    
    # Rows (limit to max_rows)
    for idx in range(min(len(dataframe), max_rows)):
        for i, col in enumerate(dataframe.columns):
            text = str(dataframe.iloc[idx][col])
            pdf.cell(col_widths[i], 6, text[:30], border=1)
        pdf.ln(6)
    pdf.ln(5)

def add_insight_section(pdf, insights):
    """Add insights section to PDF"""
    pdf.set_font("Arial", size=10)
    for insight in insights:
        pdf.multi_cell(0, 8, f"- {insight}")

# ---------- Warehouse Weekly Report ----------
def generate_warehouse_report(df, output_path="warehouse_weekly_report.pdf"):
    """Generate comprehensive warehouse weekly operations report"""
    pdf = PDF()
    pdf.add_page()
    
    today = datetime.today().strftime('%Y-%m-%d')
    warehouse_id = df['Warehouse ID'].unique()[0] if 'Warehouse ID' in df.columns else 'N/A'
    
    # --- COVER INFO ---
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 10, f"Prepared by: Warehouse Manager", ln=True)
    pdf.cell(0, 10, f"Warehouse ID: {warehouse_id}", ln=True)
    pdf.cell(0, 10, f"Reporting Period: Week ending {today}", ln=True)
    pdf.cell(0, 10, f"Department: Operations", ln=True)
    pdf.ln(5)
    
    # --- I. EXECUTIVE SUMMARY ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "I. Executive Summary", ln=True)
    pdf.set_font("Arial", size=10)
    
    total_orders = df['Order ID'].nunique()
    avg_pick_dur = round(df['Pick Duration (min)'].mean(), 2)
    avg_fill_rate = round(df['Fill_Rate_pct'].mean(), 2) if 'Fill_Rate_pct' in df.columns else 0
    avg_fulfillment = round(df['Order_Fulfillment (Days)'].mean(), 2)
    
    pdf.cell(0, 8, f"Orders Processed: {total_orders}", ln=True)
    pdf.cell(0, 8, f"Avg Pick Duration: {avg_pick_dur} min", ln=True)
    pdf.cell(0, 8, f"Avg Fill Rate: {avg_fill_rate}%", ln=True)
    pdf.cell(0, 8, f"Order Fulfillment Time: {avg_fulfillment} days", ln=True)
    pdf.multi_cell(0, 8, "Highlights: Optimal picking accuracy achieved; minimal transportation delays; efficient resource utilization.")
    pdf.ln(4)
    
    # --- II. ORDER PROCESSING ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "II. Order Processing & Fulfillment", ln=True)
    pdf.set_font("Arial", size=10)
    
    if 'Scheduled_Shipping_Days' in df.columns and 'Actual_Shipping_Days' in df.columns:
        avg_sched = df['Scheduled_Shipping_Days'].mean()
        avg_actual = df['Actual_Shipping_Days'].mean()
        on_time = round((df['Actual_Shipping_Days'] <= df['Scheduled_Shipping_Days']).mean() * 100, 2)
        
        pdf.cell(0, 8, f"Scheduled vs Actual Shipping (Avg Days): {round(avg_sched,2)} vs {round(avg_actual,2)}", ln=True)
        pdf.cell(0, 8, f"Shipping Accuracy (%): {on_time}%", ln=True)
    
    # Graph 1: Order Fulfillment Time Distribution
    fig, ax = plt.subplots()
    sns.histplot(df['Order_Fulfillment (Days)'], kde=True, ax=ax)
    ax.set_title("Order Fulfillment Time Distribution")
    save_plot(fig, "fulfill.png")
    pdf.image("fulfill.png", w=180)
    
    # Graph 2: Daily Orders
    if 'Order_Date' in df.columns:
        fig, ax = plt.subplots()
        daily_orders = df.groupby('Order_Date')['Order ID'].count()
        daily_orders.plot(kind='bar', ax=ax)
        ax.set_title("Daily Orders Processed")
        ax.tick_params(axis='x', rotation=45)
        save_plot(fig, "daily_orders.png")
        pdf.image("daily_orders.png", w=180)
    
    # Graph 3: Order Status Breakdown
    if 'Order_Status' in df.columns:
        fig, ax = plt.subplots()
        df['Order_Status'].value_counts().plot.pie(autopct="%1.1f%%", ax=ax)
        ax.set_title("Order Status Breakdown")
        save_plot(fig, "status.png")
        pdf.image("status.png", w=140)
    
    # --- III. INVENTORY METRICS ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "III. Inventory & Accuracy Metrics", ln=True)
    pdf.set_font("Arial", size=10)
    
    inv_turn = round(df['Inventory_Turnover'].mean(), 2) if 'Inventory_Turnover' in df.columns else 0
    inv_acc = round(df['Inventory_Accuracy (%)'].mean(), 2) if 'Inventory_Accuracy (%)' in df.columns else 0
    forecast_acc = round(df['Forecast_Accuracy_pct'].mean(), 2) if 'Forecast_Accuracy_pct' in df.columns else 0
    
    pdf.cell(0, 8, f"Inventory Turnover Rate: {inv_turn}", ln=True)
    pdf.cell(0, 8, f"Inventory Accuracy (%): {inv_acc}%", ln=True)
    pdf.cell(0, 8, f"Forecast Accuracy (%): {forecast_acc}%", ln=True)
    
    # Graph 4: Inventory vs Forecast Accuracy
    if 'Inventory_Accuracy (%)' in df.columns and 'Forecast_Accuracy_pct' in df.columns:
        fig, ax = plt.subplots()
        df[['Inventory_Accuracy (%)', 'Forecast_Accuracy_pct']].plot(ax=ax)
        ax.set_title("Inventory Accuracy vs Forecast Accuracy")
        save_plot(fig, "inv_forecast.png")
        pdf.image("inv_forecast.png", w=180)
    
    # Graph 5: Fill Rate by Category
    if 'Category' in df.columns and 'Fill_Rate_pct' in df.columns:
        fig, ax = plt.subplots()
        sns.barplot(data=df, x='Category', y='Fill_Rate_pct', ax=ax)
        ax.set_title("Fill Rate by Category")
        ax.tick_params(axis='x', rotation=45)
        save_plot(fig, "fillrate.png")
        pdf.image("fillrate.png", w=180)
    
    # --- IV. PICKING PERFORMANCE ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "IV. Picking Performance & Labor Efficiency", ln=True)
    pdf.set_font("Arial", size=10)
    
    total_items = df['Items_Picked'].sum() if 'Items_Picked' in df.columns else 0
    pick_acc = round(df['Picking_Accuracy (%)'].mean(), 2) if 'Picking_Accuracy (%)' in df.columns else 0
    total_labor = df['Labor_Hours'].sum() if 'Labor_Hours' in df.columns else 1
    items_per_hour = round(total_items / total_labor, 2) if total_labor > 0 else 0
    avg_travel = round(df['Travel_Distance (m)'].mean(), 2) if 'Travel_Distance (m)' in df.columns else 0
    
    pdf.cell(0, 8, f"Total Items Picked: {total_items}", ln=True)
    pdf.cell(0, 8, f"Avg Picking Accuracy (%): {pick_acc}%", ln=True)
    pdf.cell(0, 8, f"Total Labor Hours: {total_labor}", ln=True)
    pdf.cell(0, 8, f"Avg Items Picked per Hour: {items_per_hour}", ln=True)
    pdf.cell(0, 8, f"Avg Travel Distance: {avg_travel} m", ln=True)
    
    # Graph 6: Picking Accuracy by Department
    if 'Department' in df.columns and 'Picking_Accuracy (%)' in df.columns:
        fig, ax = plt.subplots()
        pick_by_dept = df.groupby("Department")['Picking_Accuracy (%)'].mean()
        pick_by_dept.plot(kind='bar', ax=ax)
        ax.set_title("Picking Accuracy by Department")
        save_plot(fig, "pickdept.png")
        pdf.image("pickdept.png", w=180)
    
    # Graph 7: Labor Efficiency
    if 'Labor_Hours' in df.columns and 'Items_Picked' in df.columns:
        fig, ax = plt.subplots()
        ax.scatter(df['Labor_Hours'], df['Items_Picked'])
        ax.set_xlabel("Labor Hours")
        ax.set_ylabel("Items Picked")
        ax.set_title("Labor Hours vs Items Picked")
        save_plot(fig, "laboreff.png")
        pdf.image("laboreff.png", w=180)
    
    # --- V. SHIPPING & TRANSPORTATION ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "V. Shipping & Transportation", ln=True)
    pdf.set_font("Arial", size=10)
    
    if 'Transportation_Delay_Days' in df.columns:
        delay = round(df['Transportation_Delay_Days'].mean(), 2)
        on_time_delivery = round((df['Transportation_Delay_Days'] <= 0).mean() * 100, 2)
        pdf.cell(0, 8, f"Avg Transportation Delay: {delay} days", ln=True)
        pdf.cell(0, 8, f"On-Time Delivery Rate: {on_time_delivery}%", ln=True)
    
    if 'Shipping_Mode' in df.columns:
        top_modes = df['Shipping_Mode'].value_counts().head(3).index.tolist()
        pdf.cell(0, 8, f"Preferred Shipping Modes: {', '.join(top_modes)}", ln=True)
    
    # Graph 8: Transportation Delay by Region
    if 'Order_Region' in df.columns and 'Transportation_Delay_Days' in df.columns:
        fig, ax = plt.subplots()
        sns.barplot(data=df, x='Order_Region', y='Transportation_Delay_Days', ax=ax)
        ax.set_title("Transportation Delay by Region")
        save_plot(fig, "delayregion.png")
        pdf.image("delayregion.png", w=180)
    
    # Graph 9: Shipping Mode Usage
    if 'Shipping_Mode' in df.columns:
        fig, ax = plt.subplots()
        df['Shipping_Mode'].value_counts().plot.pie(autopct='%1.1f%%', ax=ax)
        ax.set_title("Shipping Mode Usage")
        save_plot(fig, "shipmode.png")
        pdf.image("shipmode.png", w=140)
    
    # --- VI. SALES & PROFITABILITY ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "VI. Sales & Profitability", ln=True)
    pdf.set_font("Arial", size=10)
    
    total_sales = df['Total_Sales'].sum() if 'Total_Sales' in df.columns else 0
    total_profit = df['Profit'].sum() if 'Profit' in df.columns else 0
    avg_price = df['Product_Price'].mean() if 'Product_Price' in df.columns else 0
    avg_discount = df['Discount_Rate'].mean() if 'Discount_Rate' in df.columns else 0
    
    pdf.cell(0, 8, f"Total Sales: Rs.{total_sales:,.2f}", ln=True)
    pdf.cell(0, 8, f"Total Profit: Rs.{total_profit:,.2f}", ln=True)
    pdf.cell(0, 8, f"Avg Product Price: Rs.{avg_price:,.2f}", ln=True)
    pdf.cell(0, 8, f"Avg Discount Rate: {avg_discount}%", ln=True)
    
    # Graph 10: Profit vs Discount Rate
    if 'Discount_Rate' in df.columns and 'Profit' in df.columns:
        fig, ax = plt.subplots()
        sns.scatterplot(data=df, x='Discount_Rate', y='Profit', ax=ax)
        ax.set_title("Profit vs Discount Rate")
        save_plot(fig, "profitdisc.png")
        pdf.image("profitdisc.png", w=180)
    
    # Graph 11: Sales by Category
    if 'Category' in df.columns and 'Total_Sales' in df.columns:
        fig, ax = plt.subplots()
        df.groupby("Category")['Total_Sales'].sum().plot(kind='bar', ax=ax)
        ax.set_title("Sales by Category")
        ax.tick_params(axis='x', rotation=45)
        save_plot(fig, "salescat.png")
        pdf.image("salescat.png", w=180)
    
    # --- VII. SPACE UTILIZATION ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "VII. Space & Resource Utilization", ln=True)
    pdf.set_font("Arial", size=10)
    
    if 'Space_Utilization (%)' in df.columns:
        avg_space = df['Space_Utilization (%)'].mean()
        pdf.cell(0, 8, f"Space Utilization (%): {avg_space:.2f}%", ln=True)
        
        # Graph 12: Space Utilization Trend
        fig, ax = plt.subplots()
        df['Space_Utilization (%)'].plot(ax=ax)
        ax.set_title("Space Utilization Trend")
        save_plot(fig, "spacetrend.png")
        pdf.image("spacetrend.png", w=180)
    
    # --- VIII. REGIONAL INSIGHTS ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "VIII. Regional & Customer Segment Insights", ln=True)
    
    # Graph 13: Orders by Region
    if 'Order_Region' in df.columns:
        fig, ax = plt.subplots()
        df.groupby('Order_Region')['Order ID'].count().plot(kind='bar', ax=ax)
        ax.set_title("Orders by Region")
        save_plot(fig, "orders_region.png")
        pdf.image("orders_region.png", w=180)
    
    # Graph 14: Customer Segment Analysis
    if 'Customer_Segment' in df.columns and 'Total_Sales' in df.columns:
        fig, ax = plt.subplots()
        df.groupby('Customer_Segment')['Total_Sales'].sum().plot(kind='bar', ax=ax)
        ax.set_title("Customer Segment vs Order Value")
        save_plot(fig, "segment_value.png")
        pdf.image("segment_value.png", w=180)
    
    # --- INSIGHTS SECTION ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "IX. GenAI Insights", ln=True)
    
    warehouse_insights = [
        "Warehouses with optimized pick paths show 15% better efficiency",
        "Peak order processing occurs during mid-week periods",
        "Inventory accuracy directly correlates with fulfillment speed",
        "Regional shipping preferences impact delivery performance"
    ]
    add_insight_section(pdf, warehouse_insights)
    
    # Output PDF and cleanup
    pdf.output(output_path)
    
    # Clean up temporary files
    temp_files = ["fulfill.png", "daily_orders.png", "status.png", "inv_forecast.png", 
                  "fillrate.png", "pickdept.png", "laboreff.png", "delayregion.png", 
                  "shipmode.png", "profitdisc.png", "salescat.png", "spacetrend.png", 
                  "orders_region.png", "segment_value.png"]
    
    for f in temp_files:
        if os.path.exists(f):
            os.remove(f)
    
    return output_path

# ---------- Store Manager Weekly Report ----------
def generate_store_report(df, output_path="store_weekly_report.pdf"):
    """Generate comprehensive store manager weekly performance report"""
    pdf = PDF()
    pdf.add_page()
    
    store_id = df['Store ID'].iloc[0] if 'Store ID' in df.columns else 'N/A'
    region = df['Region'].iloc[0] if 'Region' in df.columns else 'N/A'
    today = datetime.today().strftime('%Y-%m-%d')
    
    # Header Information
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"Prepared by: Store Manager", ln=True)
    pdf.cell(0, 10, f"Store ID: {store_id}", ln=True)
    pdf.cell(0, 10, f"Region: {region}", ln=True)
    pdf.cell(0, 10, f"Date: {today}", ln=True)
    pdf.ln(5)
    
    # I. Executive Summary
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "I. Executive Summary", ln=True)
    pdf.set_font("Arial", size=10)
    
    summary_metrics = {
        "Total Purchase Orders Processed": df['PO ID'].nunique() if 'PO ID' in df.columns else 0,
        "Overall On-Time Delivery Rate": f"{(df['On Time Delivery'].mean() * 100):.2f}%" if 'On Time Delivery' in df.columns else "N/A",
        "Inventory Health Score": round(df['Inventory Health Score'].mean(), 2) if 'Inventory Health Score' in df.columns else 0,
        "Key Highlights": "Supplier performance improved, inventory optimization achieved"
    }
    
    for k, v in summary_metrics.items():
        pdf.cell(0, 10, f"{k}: {v}", ln=True)
    
    # II. Purchase Order Analysis
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "II. Purchase Order Analysis", ln=True)
    pdf.set_font("Arial", size=10)
    
    if 'PO ID' in df.columns:
        po_stats = {
            "Total PO Issued": df['PO ID'].nunique(),
            "Total Units Ordered": df['Units Ordered'].sum() if 'Units Ordered' in df.columns else 0,
            "Total Units Received": df['Units Received'].sum() if 'Units Received' in df.columns else 0,
            "PO Aging Avg (Days)": round(df['PO Aging (Days)'].mean(), 2) if 'PO Aging (Days)' in df.columns else 0,
            "Avg Lead Time": round(df['Lead Time (Days)'].mean(), 2) if 'Lead Time (Days)' in df.columns else 0
        }
        
        for k, v in po_stats.items():
            pdf.cell(0, 10, f"{k}: {v}", ln=True)
    
    # Graph: PO Aging vs Lead Time
    if 'Supplier Name' in df.columns and 'PO Aging (Days)' in df.columns and 'Lead Time (Days)' in df.columns:
        fig, ax = plt.subplots()
        lead_po = df.groupby('Supplier Name')[['PO Aging (Days)', 'Lead Time (Days)']].mean().reset_index()
        lead_po.plot(x='Supplier Name', kind='bar', ax=ax)
        ax.set_title("PO Aging vs Lead Time by Supplier")
        ax.set_ylabel("Days")
        ax.tick_params(axis='x', rotation=45)
        save_plot(fig, "po_aging.png")
        pdf.image("po_aging.png", w=180)
    
    # III. Inventory Performance
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "III. Inventory Performance", ln=True)
    pdf.set_font("Arial", size=10)
    
    inventory_metrics = {
        "Beginning Stock": df['Stock Before'].sum() if 'Stock Before' in df.columns else 0,
        "Ending Stock": df['Stock After'].sum() if 'Stock After' in df.columns else 0,
        "Stockouts Count": df[df['Stockout Flag'] == 1].shape[0] if 'Stockout Flag' in df.columns else 0,
        "Inventory Health Score": round(df['Inventory Health Score'].mean(), 2) if 'Inventory Health Score' in df.columns else 0
    }
    
    for k, v in inventory_metrics.items():
        pdf.cell(0, 10, f"{k}: {v}", ln=True)
    
    # IV. Forecasting & Replenishment
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "IV. Forecasting & Replenishment", ln=True)
    pdf.set_font("Arial", size=10)
    
    if 'Forecast Demand (30d)' in df.columns and 'Suggested Replenishment' in df.columns:
        forecast = df['Forecast Demand (30d)'].sum()
        replenish = df['Suggested Replenishment'].sum()
        
        pdf.cell(0, 10, f"Forecasted Demand (30d): {forecast}", ln=True)
        pdf.cell(0, 10, f"Suggested Replenishment: {replenish}", ln=True)
        
        # Graph: Forecast vs Replenishment by Category
        if 'Category' in df.columns:
            fig, ax = plt.subplots()
            agg = df.groupby('Category')[['Forecast Demand (30d)', 'Suggested Replenishment']].sum().reset_index()
            agg.plot(x='Category', kind='bar', ax=ax)
            ax.set_title("Forecast vs Replenishment by Category")
            ax.tick_params(axis='x', rotation=45)
            save_plot(fig, "forecast_vs_replenish.png")
            pdf.image("forecast_vs_replenish.png", w=180)
    
    # V. Supplier & Delivery Performance
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "V. Supplier & Delivery Performance", ln=True)
    pdf.set_font("Arial", size=10)
    
    if 'On Time Delivery' in df.columns:
        on_time_rate = (df['On Time Delivery'].mean() * 100)
        pdf.cell(0, 10, f"Overall On-Time Delivery Rate: {on_time_rate:.2f}%", ln=True)
        
        # Late suppliers analysis
        if 'Supplier Name' in df.columns and 'PO Aging (Days)' in df.columns:
            late_suppliers = df[df['On Time Delivery'] < 1].groupby('Supplier Name')['PO Aging (Days)'].mean().nlargest(5)
            for supplier, days in late_suppliers.items():
                pdf.cell(0, 10, f"{supplier}: {days:.2f} days late", ln=True)
    
    # Graph: On-Time Delivery by Supplier
    if 'Supplier Name' in df.columns and 'On Time Delivery' in df.columns:
        fig, ax = plt.subplots()
        delivery = df.groupby('Supplier Name')['On Time Delivery'].mean().sort_values().tail(10)
        delivery.plot(kind='barh', ax=ax)
        ax.set_title("On-Time Delivery Rate by Supplier")
        save_plot(fig, "ontime.png")
        pdf.image("ontime.png", w=180)
    
    # VI. Cost & Variance Analysis
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "VI. Cost & Variance Analysis", ln=True)
    pdf.set_font("Arial", size=10)
    
    cost_metrics = {
        "Total Cost": f"Rs.{df['Total Cost'].sum():,.2f}" if 'Total Cost' in df.columns else "N/A",
        "Avg Unit Cost": f"Rs.{df['Unit Cost'].mean():.2f}" if 'Unit Cost' in df.columns else "N/A",
        "Target Unit Cost": f"Rs.{df['Target Unit Cost'].mean():.2f}" if 'Target Unit Cost' in df.columns else "N/A",
        "Cost Variance": f"Rs.{df['Cost Variance'].sum():.2f}" if 'Cost Variance' in df.columns else "N/A"
    }
    
    for k, v in cost_metrics.items():
        pdf.cell(0, 10, f"{k}: {v}", ln=True)
    
    # Graph: Cost Variance by Category
    if 'Category' in df.columns and 'Cost Variance' in df.columns:
        fig, ax = plt.subplots()
        df.groupby('Category')['Cost Variance'].sum().plot(kind='bar', ax=ax)
        ax.set_title("Cost Variance by Category")
        ax.tick_params(axis='x', rotation=45)
        save_plot(fig, "cost_var.png")
        pdf.image("cost_var.png", w=180)
    
    # VII. Quality Issues
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "VII. Quality Issues (Returns & Damages)", ln=True)
    pdf.set_font("Arial", size=10)
    
    quality_metrics = {
        "Total Returns": df['Returns Units'].sum() if 'Returns Units' in df.columns else 0,
        "Return Rate": f"{df['Return Rate (%)'].mean():.2f}%" if 'Return Rate (%)' in df.columns else "N/A",
        "Damages Units": df['Damages Units'].sum() if 'Damages Units' in df.columns else 0,
        "Damage Rate": f"{df['Damage Rate (%)'].mean():.2f}%" if 'Damage Rate (%)' in df.columns else "N/A"
    }
    
    for k, v in quality_metrics.items():
        pdf.cell(0, 10, f"{k}: {v}", ln=True)
    
    # VIII. Recommendations
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "VIII. Recommendations & Alerts", ln=True)
    pdf.set_font("Arial", size=10)
    
    recommendations = [
        "Review supplier contracts for low-rated vendors",
        "Implement cost control measures for high-variance products",
        "Prioritize replenishment for stockout-prone items",
        "Consider alternative suppliers for poor delivery performance"
    ]
    
    for rec in recommendations:
        pdf.multi_cell(0, 8, f"- {rec}")
    
    # IX. Appendix
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "IX. Appendix (Sample Data)", ln=True)
    
    # Sample PO data
    if 'PO ID' in df.columns:
        sample_cols = ['PO ID', 'Supplier Name', 'Total Cost'] if all(col in df.columns for col in ['PO ID', 'Supplier Name', 'Total Cost']) else df.columns[:3]
        draw_table(pdf, "Sample Purchase Orders", df[sample_cols].head(10))
    
    # Output PDF and cleanup
    pdf.output(output_path)
    
    # Clean up temporary files
    temp_files = ["po_aging.png", "forecast_vs_replenish.png", "ontime.png", "cost_var.png"]
    for f in temp_files:
        if os.path.exists(f):
            os.remove(f)
    
    return output_path

# ---------- Executive Leadership Report ----------
def generate_exec_report(df, prepared_by="Executive Team", output_path="executive_report_walmart.pdf"):
    """Generate comprehensive executive leadership weekly insight report"""
    pdf = PDF()
    pdf.add_page()
    
    # Auto-generate header information
    week_ending = datetime.today().strftime("%Y-%m-%d")
    business_units = ", ".join(sorted(df["Business Unit"].dropna().unique())) if "Business Unit" in df.columns else "N/A"
    regions = ", ".join(sorted(df["Region"].dropna().unique())) if "Region" in df.columns else "N/A"
    
    # Title and header info
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Prepared by: {prepared_by}", ln=True)
    pdf.cell(0, 10, f"Week Ending: {week_ending}", ln=True)
    pdf.cell(0, 10, f"Business Unit(s): {business_units}", ln=True)
    pdf.cell(0, 10, f"Region(s) Covered: {regions}", ln=True)
    pdf.cell(0, 10, "Report Audience: Executive Leadership Team", ln=True)
    pdf.ln(5)
    
    # I. Executive Summary
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "I. Executive Summary", ln=True)
    pdf.set_font("Arial", size=11)
    
    # Calculate key metrics
    net_profit = df['Net Profit'].sum() if 'Net Profit' in df.columns else 0
    roi_avg = df["ROI (%)"].mean() if "ROI (%)" in df.columns else 0
    
    # Strategic initiatives summary
    if "Strategic Initiative" in df.columns:
        top_initiatives = df.groupby("Strategic Initiative").agg({
            "Initiative Impact Score": "mean",
            "Projected Growth (%)": "mean"
        }).sort_values("Initiative Impact Score", ascending=False).head(3)
        top_initiative_names = ", ".join(top_initiatives.index)
    else:
        top_initiative_names = "N/A"
    
    # Risk analysis
    high_risk_regions = df[df["Risk Score"] > 80]["Region"].unique() if "Risk Score" in df.columns and "Region" in df.columns else []
    poor_fulfillment = df[df["Order Fulfillment Rate (%)"] < 75]["Region"].unique() if "Order Fulfillment Rate (%)" in df.columns and "Region" in df.columns else []
    
    exec_summary_text = (
        f"Net Profit: ${net_profit:,.2f}\n"
        f"Average ROI across business units: {roi_avg:.2f}%\n"
        f"Top strategic initiatives: {top_initiative_names}\n"
        f"High-risk regions: {', '.join(high_risk_regions) if len(high_risk_regions) > 0 else 'None'}\n"
        f"Regions with fulfillment issues: {', '.join(poor_fulfillment) if len(poor_fulfillment) > 0 else 'None'}\n"
        f"Key achievements include automation successes and sustainability milestones."
    )
    
    pdf.multi_cell(0, 10, exec_summary_text)
    pdf.ln(5)
    
    # II. Financial Overview
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "II. Financial Overview", ln=True)
    pdf.set_font("Arial", size=11)
    
    financial_metrics = {
        "Total Revenue": f"${df['Revenue'].sum():,.2f}" if 'Revenue' in df.columns else "N/A",
        "Total Expenses": f"${df['Expenses'].sum():,.2f}" if 'Expenses' in df.columns else "N/A",
        "Net Profit": f"${net_profit:,.2f}",
        "ROI (%)": f"{roi_avg:.2f}%",
        "Cost per Unit": f"${df['Cost per Unit'].mean():,.2f}" if 'Cost per Unit' in df.columns else "N/A"
    }
    
    for k, v in financial_metrics.items():
        pdf.cell(0, 10, f"{k}: {v}", ln=True)
    pdf.ln(3)
    
    # Graph 1: Revenue vs Expenses by Business Unit
    if "Business Unit" in df.columns and "Revenue" in df.columns and "Expenses" in df.columns:
        fig, ax = plt.subplots(figsize=(10, 6))
        rev_exp = df.groupby("Business Unit")[["Revenue", "Expenses"]].sum().reset_index()
        rev_exp.plot(x="Business Unit", kind="bar", ax=ax)
        ax.set_title("Revenue vs Expenses by Business Unit")
        ax.set_ylabel("Amount ($)")
        ax.tick_params(axis='x', rotation=45)
        save_plot(fig, "graph_rev_exp.png")
        pdf.image("graph_rev_exp.png", w=180)
        pdf.ln(5)
    
    # Graph 2: ROI Analysis
    if "ROI (%)" in df.columns and "Region" in df.columns:
        fig, ax = plt.subplots(figsize=(10, 6))
        roi_by_region = df.groupby("Region")["ROI (%)"].mean().reset_index()
        sns.barplot(data=roi_by_region, x="Region", y="ROI (%)", ax=ax)
        ax.set_title("ROI by Region")
        ax.tick_params(axis='x', rotation=45)
        save_plot(fig, "graph_roi_region.png")
        pdf.image("graph_roi_region.png", w=180)
        pdf.ln(5)
    
    # III. Operational Efficiency
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "III. Operational Efficiency", ln=True)
    pdf.set_font("Arial", size=11)
    
    operational_metrics = {
        "Total Inventory Units": f"{int(df['Inventory Units'].sum()):,}" if 'Inventory Units' in df.columns else "N/A",
        "Logistics Spend": f"${df['Logistics Spend'].sum():,.2f}" if 'Logistics Spend' in df.columns else "N/A",
        "Order Fulfillment Rate": f"{df['Order Fulfillment Rate (%)'].mean():.2f}%" if 'Order Fulfillment Rate (%)' in df.columns else "N/A",
        "Network Efficiency Score": f"{df['Network Efficiency Score'].mean():.2f}" if 'Network Efficiency Score' in df.columns else "N/A"
    }
    
    for k, v in operational_metrics.items():
        pdf.cell(0, 10, f"{k}: {v}", ln=True)
    pdf.ln(3)
    
    # IV. Risk Management
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "IV. Risk Management", ln=True)
    pdf.set_font("Arial", size=11)
    
    if "Risk Score" in df.columns:
        avg_risk_score = df["Risk Score"].mean()
        high_risk_count = df[df["Risk Score"] > 80].shape[0]
        
        pdf.cell(0, 10, f"Average Risk Score: {avg_risk_score:.2f}", ln=True)
        pdf.cell(0, 10, f"High Risk Items: {high_risk_count}", ln=True)
        
        # Graph: Risk Score by Region
        if "Region" in df.columns:
            fig, ax = plt.subplots(figsize=(10, 6))
            risk_by_region = df.groupby("Region")["Risk Score"].mean().reset_index()
            sns.barplot(data=risk_by_region, x="Region", y="Risk Score", ax=ax)
            ax.set_title("Average Risk Score by Region")
            ax.tick_params(axis='x', rotation=45)
            save_plot(fig, "graph_risk_region.png")
            pdf.image("graph_risk_region.png", w=180)
            pdf.ln(5)
    
    # V. Sustainability Metrics
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "V. Sustainability & ESG Metrics", ln=True)
    pdf.set_font("Arial", size=11)
    
    sustainability_metrics = {
        "Carbon Emission (kg)": f"{df['Carbon Emission (kg)'].sum():,.2f}" if 'Carbon Emission (kg)' in df.columns else "N/A",
        "Renewable Energy Usage": f"{df['Renewable Energy Usage (%)'].mean():.2f}%" if 'Renewable Energy Usage (%)' in df.columns else "N/A",
        "Waste Reduction": f"{df['Waste Reduction (%)'].mean():.2f}%" if 'Waste Reduction (%)' in df.columns else "N/A"
    }
    
    for k, v in sustainability_metrics.items():
        pdf.cell(0, 10, f"{k}: {v}", ln=True)
    pdf.ln(3)
    
    # VI. Strategic Recommendations
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "VI. Strategic Recommendations", ln=True)
    pdf.set_font("Arial", size=11)
    
    recommendations = [
        "Focus investments in high ROI automation zones",
        "Implement risk mitigation strategies in high-risk regions",
        "Scale sustainability practices across all business units",
        "Optimize fulfillment logistics in underperforming areas"
    ]
    
    for rec in recommendations:
        pdf.multi_cell(0, 8, f"- {rec}")
    
    # VII. Appendix
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "VII. Appendix", ln=True)
    
    # Sample data table
    if len(df.columns) > 0:
        sample_cols = df.columns[:5]  # First 5 columns
        draw_table(pdf, "Sample Strategic Data", df[sample_cols].head(10))
    
    # Output PDF and cleanup
    pdf.output(output_path)
    
    # Clean up temporary files
    temp_files = ["graph_rev_exp.png", "graph_roi_region.png", "graph_risk_region.png"]
    for f in temp_files:
        if os.path.exists(f):
            os.remove(f)
    
    print(f"Executive Leadership Report generated: {output_path}")
    return output_path

# ---------- Main Test Function ----------
def main():
    """Main function to test all report generators"""
    # Create sample data for testing
    import numpy as np
    
    # Sample warehouse data
    warehouse_data = {
        'Order ID': range(1, 101),
        'Warehouse ID': ['WH001'] * 100,
        'Pick Duration (min)': np.random.normal(15, 3, 100),
        'Fill_Rate_pct': np.random.normal(85, 5, 100),
        'Order_Fulfillment (Days)': np.random.normal(3, 1, 100),
        'Inventory_Turnover': np.random.normal(12, 2, 100),
        'Inventory_Accuracy (%)': np.random.normal(95, 2, 100),
        'Picking_Accuracy (%)': np.random.normal(98, 1, 100),
        'Items_Picked': np.random.randint(10, 100, 100),
        'Labor_Hours': np.random.normal(8, 1, 100),
        'Travel_Distance (m)': np.random.normal(500, 100, 100),
        'Total_Sales': np.random.normal(10000, 2000, 100),
        'Profit': np.random.normal(2000, 500, 100)
    }
    
    df_warehouse = pd.DataFrame(warehouse_data)
    
    # Generate reports
    try:
        warehouse_report = generate_warehouse_report(df_warehouse)
        print(f"Warehouse report generated: {warehouse_report}")
    except Exception as e:
        print(f"Error generating warehouse report: {e}")

if __name__ == "__main__":
    main()
