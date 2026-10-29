import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
from engine.data_loader import load_twin_data
from engine.model import LeontiefTwin

st.set_page_config(page_title="SA Fiscal Twin", layout="wide")
st.title("South Africa Fiscal–Economic Twin")

@st.cache_data
def init_engine():
    A, va, sectors = load_twin_data()
    return LeontiefTwin(A, va, sectors)

twin = init_engine()
base_budgets = {'Health': 250000, 'Education': 300000, 'Public Works': 40000, 
                'Trade and Industry': 10000, 'Small Business Development': 5000}
total_base = sum(base_budgets.values())

st.sidebar.header("1. Simulation Mode")
mode = st.sidebar.radio("Select Horizon", ["Single Year", "5-Year Projection"])

st.sidebar.header("2. Fiscal Rules")
envelope = st.sidebar.number_input("Base Envelope (R mn)", value=total_base, step=10000)
allow_deficit = st.sidebar.toggle("Allow Deficit Spending", value=True)
tax_rate = st.sidebar.slider("Average Tax Rate (%)", 15, 45, 25)

st.sidebar.header("3. Budget Levers")
new_budgets = {}
for dept, base in base_budgets.items():
    new_budgets[dept] = st.sidebar.slider(dept, float(base*0.5), float(base*2.0), float(base), 1000.0)

st.sidebar.header("4. Policy Levers")
bbbee_share = st.sidebar.slider("B-BBEE Redirect (%)", 0, 50, 10)
tariff_shock = st.sidebar.slider("Avg Tariff Change (%)", -20, 20, 0)

if mode == "Single Year":
    # Existing Single Year logic
    results, gdp_effect, revenue, jobs_effect, net_fiscal, actual_budgets, budget_scaled = twin.simulate(
        new_budgets, base_budgets, envelope, allow_deficit, tax_rate, tariff_shock, bbbee_share
    )
    
    if budget_scaled:
        st.warning("⚠️ Over Budget! Departments were scaled down to fit the envelope.")
        
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("GDP Effect (mn)", f"{gdp_effect:,.0f}")
    col2.metric("Jobs Created", f"{jobs_effect:,.0f}")
    col3.metric("Net Fiscal (mn)", f"{net_fiscal:,.0f}")
    col4.metric("Revenue (mn)", f"{revenue:,.0f}")
    
    st.plotly_chart(px.bar(results, x="sector", y="gross_output_zar_mn", color="gross_output_zar_mn", title="Sectoral Impact"), use_container_width=True)

else:
    # 5-Year Simulation Logic
    st.subheader("5-Year Macroeconomic Projection")
    st.markdown("Notice how persistent deficits accumulate debt, increasing interest payments and eventually crowding out your budget envelope.")
    
    df_history = twin.simulate_5_years(new_budgets, base_budgets, envelope, allow_deficit, tax_rate, tariff_shock, bbbee_share)
    
    # Line Charts
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        fig_gdp = px.line(df_history, x="Year", y="GDP", markers=True, title="Projected GDP (R Trillion)")
        st.plotly_chart(fig_gdp, use_container_width=True)
    with col_c2:
        fig_debt = px.line(df_history, x="Year", y="Debt_to_GDP", markers=True, title="Debt-to-GDP Ratio (%)", color_discrete_sequence=['red'])
        st.plotly_chart(fig_debt, use_container_width=True)
        
    st.divider()
    
    # Data Table
    st.markdown("### Year-by-Year Breakdown")
    st.dataframe(
        df_history[["Year", "Actual_Spend_mn", "Interest_Payment_mn", "Net_Fiscal_mn", "Debt", "Jobs_Created"]].style.format({
            "Actual_Spend_mn": "{:,.0f}",
            "Interest_Payment_mn": "{:,.0f}",
            "Net_Fiscal_mn": "{:,.0f}",
            "Debt": "R {:.2f} T",
            "Jobs_Created": "{:,.0f}"
        }),
        use_container_width=True
    )
