import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from engine.data_loader import load_twin_data
from engine.model import LeontiefTwin

# --- UI CONFIGURATION & CUSTOM CSS ---
st.set_page_config(page_title="SA Macro Twin", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    div[data-testid="stSidebar"] { background-color: #f1f3f5; }
    h1 { font-weight: 700; color: #1a202c; }
    h3 { font-weight: 600; color: #2d3748; }
</style>
""", unsafe_allow_html=True)

st.title("🇿🇦 South Africa Macroeconomic Twin")
st.markdown("Simulate fiscal, industrial, and trade policy in a dynamic 5-year horizon.")

@st.cache_resource
def init_engine():
    A, va, sectors = load_twin_data()
    return LeontiefTwin(A, va, sectors)

twin = init_engine()
base_budgets = {'Health': 250000, 'Education': 300000, 'Public Works': 40000, 
                'Trade and Industry': 10000, 'Small Business Development': 5000}

# --- SIDEBAR CONTROLS ---
st.sidebar.header("⚙️ Fiscal & Policy Levers")
envelope = st.sidebar.number_input("Base Envelope (R mn)", value=sum(base_budgets.values()), step=10000)
allow_deficit = st.sidebar.toggle("Allow Deficit Spending", value=True)
tax_rate = st.sidebar.slider("Average Tax Rate (%)", 15, 45, 25)

st.sidebar.subheader("Industrial & Trade Policy")
bbbee_share = st.sidebar.slider("B-BBEE SME Redirect (%)", 0, 50, 10)
tariff_shock = st.sidebar.slider("Avg Tariff Change (%)", -20, 20, 0)
markup_reduction = st.sidebar.slider("Competition Markup Reduction (%)", 0, 20, 0, help="Lowering markups reduces prices and boosts real demand.")
localization = st.sidebar.slider("Localization / Import Substitution (%)", 0, 50, 0, help="Increases domestic inter-industry linkages.")

# --- MULTI-YEAR BUDGET MATRIX (Data Editor) ---
st.subheader("📊 5-Year Budget Allocation (R mn)")
st.markdown("Adjust the budget for each department per year. The engine will dynamically calculate debt and interest.")

# Create initial 5-year DataFrame
years = [f"Year {i}" for i in range(1, 6)]
budget_df = pd.DataFrame([base_budgets for _ in range(5)], index=years)

# Interactive Data Editor
edited_budget_df = st.data_editor(
    budget_df,
    use_container_width=True,
    num_rows="fixed",
    column_config={col: st.column_config.NumberColumn(format="%d") for col in budget_df.columns}
)

# --- EXECUTION & CHARTS ---
# 1. Calculate Scenario
df_scenario = twin.simulate_5_years(
    edited_budget_df, base_budgets, envelope, allow_deficit, tax_rate, tariff_shock, bbbee_share, markup_reduction, localization
)

# 2. Calculate Baseline (Static budgets, no shocks)
baseline_df = pd.DataFrame([base_budgets for _ in range(5)], index=years)
df_baseline = twin.simulate_5_years(
    baseline_df, base_budgets, sum(base_budgets.values()), allow_deficit, tax_rate, 0, 0, 0, 0
)

st.divider()

# Metric Cards
col1, col2, col3 = st.columns(3)
col1.metric("Year 5 GDP", f"R {df_scenario.iloc[-1]['GDP']:.2f} T", 
            delta=f"{(df_scenario.iloc[-1]['GDP'] - df_baseline.iloc[-1]['GDP']):.2f} T vs Baseline")
col2.metric("Year 5 Debt-to-GDP", f"{df_scenario.iloc[-1]['Debt_to_GDP']:.1f} %", 
            delta=f"{(df_scenario.iloc[-1]['Debt_to_GDP'] - df_baseline.iloc[-1]['Debt_to_GDP']):.1f} % vs Baseline", delta_color="inverse")
col3.metric("Total Jobs Created (Y5)", f"{df_scenario.iloc[-1]['Jobs_Created']:,.0f}")

# Charts
col_chart1, col_chart2 = st.columns(2)
with col_chart1:
    fig_gdp = go.Figure()
    fig_gdp.add_trace(go.Scatter(x=df_baseline["Year"], y=df_baseline["GDP"], mode='lines', name='Baseline', line=dict(dash='dot', color='gray')))
    fig_gdp.add_trace(go.Scatter(x=df_scenario["Year"], y=df_scenario["GDP"], mode='lines+markers', name='Scenario', line=dict(color='#2ecc71', width=4)))
    fig_gdp.update_layout(title="Projected GDP (R Trillion)", template="plotly_white", margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig_gdp, use_container_width=True)

with col_chart2:
    fig_debt = go.Figure()
    fig_debt.add_trace(go.Scatter(x=df_baseline["Year"], y=df_baseline["Debt_to_GDP"], mode='lines', name='Baseline', line=dict(dash='dot', color='gray')))
    fig_debt.add_trace(go.Scatter(x=df_scenario["Year"], y=df_scenario["Debt_to_GDP"], mode='lines+markers', name='Scenario', line=dict(color='#e74c3c', width=4)))
    fig_debt.update_layout(title="Debt-to-GDP Ratio (%)", template="plotly_white", margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig_debt, use_container_width=True)

# --- AI ADVISOR CHAT ---
st.divider()
st.subheader("🧠 AI Economic Advisor")
st.markdown("Ask the AI to analyze your current policy scenario, prepare a briefing note, or suggest trade-offs.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("e.g., 'Write a cabinet memo on the debt trajectory of this policy.'"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing scenario..."):
            ai_response = twin.ask_ai_advisor(prompt, df_scenario)
            st.markdown(ai_response)
            
    st.session_state.messages.append({"role": "assistant", "content": ai_response})
