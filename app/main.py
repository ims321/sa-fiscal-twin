import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from engine.data_loader import load_twin_data, get_supabase
from engine.model import LeontiefTwin

st.set_page_config(page_title="SA Fiscal Twin", layout="wide")
st.title("South Africa Fiscal–Economic Twin")

@st.cache_resource
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
    total_proposed = sum(new_budgets.values())
    actual_budgets = new_budgets.copy()
    budget_scaled = False
    
    if total_proposed > envelope and not allow_deficit:
        scale_factor = envelope / total_proposed
        actual_budgets = {k: v * scale_factor for k, v in new_budgets.items()}
        budget_scaled = True

    if budget_scaled:
        st.warning("⚠️ Over Budget! Departments were scaled down to fit the envelope.")
        
    budget_change = sum(actual_budgets.values()) - total_base
    gdp_effect, revenue, jobs_effect, results = twin.simulate_year(
        actual_budgets, base_budgets, tax_rate, tariff_shock, bbbee_share
    )
    net_fiscal = revenue - budget_change
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("GDP Effect (mn)", f"{gdp_effect:,.0f}")
    col2.metric("Jobs Created", f"{jobs_effect:,.0f}")
    col3.metric("Net Fiscal (mn)", f"{net_fiscal:,.0f}")
    col4.metric("Revenue (mn)", f"{revenue:,.0f}")
    
    st.plotly_chart(px.bar(results, x="sector", y="gross_output_zar_mn", color="gross_output_zar_mn", title="Sectoral Impact"), use_container_width=True)

else:
    st.subheader("5-Year Macroeconomic Projection: Baseline vs. Scenario")
    
    # 1. Calculate Scenario
    df_scenario = twin.simulate_5_years(new_budgets, base_budgets, envelope, allow_deficit, tax_rate, tariff_shock, bbbee_share)
    
    # 2. Calculate Baseline (No changes, no tariffs, no BBBEE)
    df_baseline = twin.simulate_5_years(base_budgets, base_budgets, total_base, allow_deficit, tax_rate, 0, 0)
    
    col_c1, col_c2 = st.columns(2)
    
    # 3. Plot GDP
    with col_c1:
        fig_gdp = go.Figure()
        fig_gdp.add_trace(go.Scatter(x=df_baseline["Year"], y=df_baseline["GDP"], mode='lines+markers', name='Baseline', line=dict(dash='dash', color='gray')))
        fig_gdp.add_trace(go.Scatter(x=df_scenario["Year"], y=df_scenario["GDP"], mode='lines+markers', name='Scenario', line=dict(color='green', width=3)))
        fig_gdp.update_layout(title="Projected GDP (R Trillion)", yaxis_title="Trillions (R)")
        st.plotly_chart(fig_gdp, use_container_width=True)
        
    # 4. Plot Debt
    with col_c2:
        fig_debt = go.Figure()
        fig_debt.add_trace(go.Scatter(x=df_baseline["Year"], y=df_baseline["Debt_to_GDP"], mode='lines+markers', name='Baseline', line=dict(dash='dash', color='gray')))
        fig_debt.add_trace(go.Scatter(x=df_scenario["Year"], y=df_scenario["Debt_to_GDP"], mode='lines+markers', name='Scenario', line=dict(color='red', width=3)))
        fig_debt.update_layout(title="Debt-to-GDP Ratio (%)", yaxis_title="%")
        st.plotly_chart(fig_debt, use_container_width=True)
        
    st.divider()
    
    # 5. Save to Database
    st.subheader("Save this Scenario")
    scenario_name = st.text_input("Scenario Name", "My Policy Proposal")
    if st.button("Save to Supabase"):
        supabase = get_supabase()
        if supabase:
            payload = {
                "scenario_name": scenario_name,
                "levers": {"budgets": new_budgets, "envelope": envelope, "tax_rate": tax_rate, "tariff": tariff_shock, "bbbee": bbbee_share},
                "outputs": df_scenario.to_dict(orient="records")
            }
            try:
                supabase.table("scenario_runs").insert(payload).execute()
                st.success(f"Scenario '{scenario_name}' saved successfully!")
            except Exception as e:
                st.error(f"Failed to save: {e}")
        else:
            st.error("Supabase credentials not found.")
