import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from engine.data_loader import load_twin_data, get_supabase
from engine.model import LeontiefTwin
from engine.live_data import fetch_live_budgets
from engine.report import generate_pdf

st.set_page_config(page_title="SA Macro Twin", layout="wide")

# Initialize
if "base_budgets" not in st.session_state:
    st.session_state.base_budgets = fetch_live_budgets()
    import copy
    st.session_state.scenario_budgets = copy.deepcopy(st.session_state.base_budgets)

base_budgets = st.session_state.base_budgets
scenario_budgets = st.session_state.scenario_budgets

@st.cache_resource
def init_engine():
    A, va, sectors = load_twin_data()
    return LeontiefTwin(A, va, sectors)
twin = init_engine()

# --- SIDEBAR LEVERS ---
st.sidebar.header("⚙️ National Fiscal & Macro Levers")
levers = {'allow_deficit': st.sidebar.toggle("Allow Deficit Spending", value=True)}
with st.sidebar.expander("💰 National Taxes"):
    levers['vat'] = st.slider("VAT (%)", 10, 25, 15)
    levers['cit'] = st.slider("Corporate Tax (%)", 15, 40, 27)
    levers['pit'] = st.slider("Personal Tax (%)", 15, 45, 30)
    levers['fuel_levy'] = st.slider("Fuel Levy (Mult)", 0.5, 2.0, 1.0)
    levers['sin_tax'] = st.slider("Sin Tax (Mult)", 0.5, 2.0, 1.0)
with st.sidebar.expander("🏦 Monetary Policy"):
    levers['repo_rate'] = st.slider("Repo Rate (%)", 5.0, 15.0, 8.25)
with st.sidebar.expander("🏭 Industrial & Trade"):
    levers['bbbee'] = st.slider("B-BBEE Redirect (%)", 0, 50, 10)
    levers['tariff'] = st.slider("Tariff Change (%)", -20, 20, 0)
    levers['localization'] = st.slider("Localization (%)", 0, 50, 0)
    levers['markup_cap'] = st.slider("Markup Cap (%)", 0, 20, 0)

# --- MUNICIPAL SCENARIO PLANNER ---
st.subheader("🏙️ Municipal Scenario Planner")
mun_select = st.selectbox("Select Municipality", list(scenario_budgets['local'].keys()))

if mun_select:
    mun_data = scenario_budgets['local'][mun_select]
    base_mun_data = base_budgets['local'][mun_select]
    
    # Municipal Levers
    st.markdown("### 📈 Adjust Municipal Levers")
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        tariff_increase = st.slider("Service Tariff Increase (%)", 0.0, 20.0, 5.0, step=0.5)
    with col_m2:
        rate_increase = st.slider("Property Rate Increase (%)", 0.0, 20.0, 5.0, step=0.5)
    with col_m3:
        collection_rate = st.slider("Collection Rate (%)", 70.0, 100.0, 90.0, step=1.0)
        
    # Apply levers to revenue
    for rev_item in mun_data['revenue']:
        if 'Service Charges' in rev_item or 'Fuel Levy' in rev_item:
            mun_data['revenue'][rev_item] = base_mun_data['revenue'][rev_item] * (1 + tariff_increase / 100)
        elif 'Property Rates' in rev_item:
            mun_data['revenue'][rev_item] = base_mun_data['revenue'][rev_item] * (1 + rate_increase / 100)
            
    # Apply collection rate (reduces actual revenue recognized)
    for rev_item in mun_data['revenue']:
        if rev_item not in ['Operating Grants & Subsidies']: # Grants are usually 100% collected
            mun_data['revenue'][rev_item] *= (collection_rate / 100)
            
    # Display Revenue vs Expenditure
    st.markdown("### 📊 Municipal Budget Summary (R millions)")
    col_rev, col_exp = st.columns(2)
    with col_rev:
        st.metric("Total Revenue", f"R {sum(mun_data['revenue'].values()):,.0f} mn")
        rev_df = pd.DataFrame(list(mun_data['revenue'].items()), columns=["Revenue Item", "Amount"])
        st.dataframe(rev_df, hide_index=True, use_container_width=True)
    with col_exp:
        st.metric("Total Expenditure", f"R {sum(mun_data['expenditure'].values()):,.0f} mn")
        exp_df = pd.DataFrame(list(mun_data['expenditure'].items()), columns=["Expenditure Item", "Amount"])
        st.dataframe(exp_df, hide_index=True, use_container_width=True)

    # Calculate Surplus/Deficit
    surplus = sum(mun_data['revenue'].values()) - sum(mun_data['expenditure'].values())
    st.metric("Operating Surplus / (Deficit)", f"R {surplus:,.0f} mn", delta_color="normal" if surplus > 0 else "inverse")

# Run Simulation
df_scenario = twin.simulate_5_years(scenario_budgets, base_budgets, levers)
df_baseline = twin.simulate_5_years(base_budgets, base_budgets, {**levers, 'vat': 15, 'cit': 27, 'pit': 30, 'fuel_levy': 1.0, 'sin_tax': 1.0, 'grant_uplift': 1.0, 'min_wage': 1.0, 'eti': 0, 'repo_rate': 8.25, 'bbbee': 10, 'tariff': 0, 'localization': 0, 'markup_cap': 0})

# Metrics & Tabs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Year 5 GDP", f"R {df_scenario.iloc[-1]['GDP']:.2f} T", delta=f"{(df_scenario.iloc[-1]['GDP'] - df_baseline.iloc[-1]['GDP']):.2f} T")
col2.metric("Year 5 Debt", f"{df_scenario.iloc[-1]['Debt_to_GDP']:.1f} %", delta=f"{(df_scenario.iloc[-1]['Debt_to_GDP'] - df_baseline.iloc[-1]['Debt_to_GDP']):.1f} %", delta_color="inverse")
col3.metric("Year 5 Employment", f"{df_scenario.iloc[-1]['Total_Employment']:,.0f}", delta=f"{(df_scenario.iloc[-1]['Total_Employment'] - df_baseline.iloc[-1]['Total_Employment']):,.0f}")
col4.metric("Year 5 Gini", f"{df_scenario.iloc[-1]['Gini']:.3f}", delta=f"{(df_scenario.iloc[-1]['Gini'] - df_baseline.iloc[-1]['Gini']):.3f}", delta_color="inverse")
