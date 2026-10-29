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

st.set_page_config(page_title="SA Macro Twin", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    div[data-testid="stSidebar"] { background-color: #f1f3f5; }
</style>
""", unsafe_allow_html=True)

st.title("🇿🇦 South Africa Macroeconomic Twin")

@st.cache_resource
def init_engine():
    A, va, sectors = load_twin_data()
    return LeontiefTwin(A, va, sectors)

twin = init_engine()

if "base_budgets" not in st.session_state:
    st.session_state.base_budgets = fetch_live_budgets()
base_budgets = st.session_state.base_budgets

# --- SIDEBAR LEVERS ---
st.sidebar.header("⚙️ Fiscal Rules")
levers = {}
levers['allow_deficit'] = st.sidebar.toggle("Allow Deficit Spending", value=True)

with st.sidebar.expander("💰 National Taxes", expanded=True):
    levers['vat'] = st.slider("VAT Rate (%)", 10, 25, 15)
    levers['cit'] = st.slider("Corporate Tax (%)", 15, 40, 27)
    levers['pit'] = st.slider("Personal Income Tax (%)", 15, 45, 30)
    levers['fuel_levy'] = st.slider("Fuel Levy Multiplier", 0.5, 2.0, 1.0, step=0.1)
    levers['sin_tax'] = st.slider("Sin Tax Multiplier", 0.5, 2.0, 1.0, step=0.1)

with st.sidebar.expander("👥 Social & Labour"):
    levers['grant_uplift'] = st.slider("Social Grant Uplift", 1.0, 1.5, 1.0, step=0.1)
    levers['min_wage'] = st.slider("Minimum Wage Multiplier", 1.0, 1.5, 1.0, step=0.1)
    levers['eti'] = st.slider("Employment Tax Incentive (ETI)", 0, 100, 0, step=10)

with st.sidebar.expander("🏦 Monetary Policy"):
    levers['repo_rate'] = st.slider("Repo Rate (%)", 5.0, 15.0, 8.25, step=0.25)

with st.sidebar.expander("🏭 Trade & Industrial"):
    levers['bbbee'] = st.slider("B-BBEE SME Redirect (%)", 0, 50, 10)
    levers['tariff'] = st.slider("Avg Tariff Change (%)", -20, 20, 0)
    levers['localization'] = st.slider("Localization (%)", 0, 50, 0)
    levers['markup_cap'] = st.slider("Competition Markup Cap (%)", 0, 20, 0)

# --- MAIN UI ---
st.subheader("📊 Budget Allocation by Sphere (R mn)")
sphere_select = st.radio("Select Sphere to Edit", ["National", "Provincial", "Local"], horizontal=True)

if sphere_select == "National":
    budget_df = pd.DataFrame(list(base_budgets['national'].items()), columns=["Department", "Year 1"])
    for i in range(2, 6): budget_df[f"Year {i}"] = budget_df["Year 1"]
    budget_df.set_index("Department", inplace=True)
    edited_df = st.data_editor(budget_df, use_container_width=True, num_rows="fixed")
    base_budgets['national'] = edited_df["Year 1"].to_dict()
    st.session_state.base_budgets = base_budgets

elif sphere_select == "Provincial":
    province = st.selectbox("Select Province", list(base_budgets['provincial'].keys()))
    budget_df = pd.DataFrame(list(base_budgets['provincial'][province].items()), columns=["Department", "Year 1"])
    for i in range(2, 6): budget_df[f"Year {i}"] = budget_df["Year 1"]
    budget_df.set_index("Department", inplace=True)
    edited_df = st.data_editor(budget_df, use_container_width=True, num_rows="fixed")
    base_budgets['provincial'][province] = edited_df["Year 1"].to_dict()
    st.session_state.base_budgets = base_budgets

else: # Local
    budget_df = pd.DataFrame(list(base_budgets['local'].items()), columns=["Function", "Year 1"])
    for i in range(2, 6): budget_df[f"Year {i}"] = budget_df["Year 1"]
    budget_df.set_index("Function", inplace=True)
    edited_df = st.data_editor(budget_df, use_container_width=True, num_rows="fixed")
    base_budgets['local'] = edited_df["Year 1"].to_dict()
    st.session_state.base_budgets = base_budgets

# Run Simulation
df_scenario = twin.simulate_5_years(base_budgets, st.session_state.base_budgets, levers)
df_baseline = twin.simulate_5_years(base_budgets, st.session_state.base_budgets, {**levers, 'vat': 15, 'cit': 27, 'pit': 30, 'fuel_levy': 1.0, 'sin_tax': 1.0, 'grant_uplift': 1.0, 'min_wage': 1.0, 'eti': 0, 'repo_rate': 8.25, 'bbbee': 10, 'tariff': 0, 'localization': 0, 'markup_cap': 0})

# Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Year 5 GDP", f"R {df_scenario.iloc[-1]['GDP']:.2f} T", delta=f"{(df_scenario.iloc[-1]['GDP'] - df_baseline.iloc[-1]['GDP']):.2f} T")
col2.metric("Year 5 Debt", f"{df_scenario.iloc[-1]['Debt_to_GDP']:.1f} %", delta=f"{(df_scenario.iloc[-1]['Debt_to_GDP'] - df_baseline.iloc[-1]['Debt_to_GDP']):.1f} %", delta_color="inverse")
col3.metric("Year 5 Employment", f"{df_scenario.iloc[-1]['Total_Employment']:,.0f}", delta=f"{(df_scenario.iloc[-1]['Total_Employment'] - df_baseline.iloc[-1]['Total_Employment']):,.0f}")
col4.metric("Year 5 Gini", f"{df_scenario.iloc[-1]['Gini']:.3f}", delta=f"{(df_scenario.iloc[-1]['Gini'] - df_baseline.iloc[-1]['Gini']):.3f}", delta_color="inverse")

st.divider()

# TABS
tab1, tab2, tab3 = st.tabs(["📈 Macro", "🏢 Firms", "🏘️ Households"])

with tab1:
    fig_gdp = go.Figure()
    fig_gdp.add_trace(go.Scatter(x=df_baseline["Year"], y=df_baseline["GDP"], name='Baseline', line=dict(dash='dot')))
    fig_gdp.add_trace(go.Scatter(x=df_scenario["Year"], y=df_scenario["GDP"], name='Scenario', line=dict(color='#2ecc71', width=4)))
    fig_gdp.update_layout(title="GDP Projection", template="plotly_white")
    st.plotly_chart(fig_gdp, use_container_width=True)

with tab2:
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        active_firms = pd.DataFrame([f.to_dict() for f in twin.firm_market.firms if f.active])
        st.plotly_chart(px.scatter(active_firms, x="productivity", y="employees", color="sector", title="Firm Survival"), use_container_width=True)
    with col_f2:
        st.plotly_chart(px.line(df_scenario, x="Year", y="HHI", title="Market Concentration (HHI)"), use_container_width=True)

with tab3:
    st.plotly_chart(px.histogram(twin.microsim.households, x="current_income", nbins=100, title="Income Distribution"), use_container_width=True)
