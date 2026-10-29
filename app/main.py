import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from engine.data_loader import load_twin_data, get_supabase
from engine.model import LeontiefTwin

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
st.markdown("Simulate fiscal, industrial, and trade policy in a dynamic 5-year horizon.")

@st.cache_resource
def init_engine():
    A, va, sectors = load_twin_data()
    return LeontiefTwin(A, va, sectors)

twin = init_engine()
base_budgets = {'Health': 250000, 'Education': 300000, 'Public Works': 40000, 
                'Trade and Industry': 10000, 'Small Business Development': 5000}

st.sidebar.header("⚙️ Fiscal & Policy Levers")
envelope = st.sidebar.number_input("Base Envelope (R mn)", value=sum(base_budgets.values()), step=10000)
allow_deficit = st.sidebar.toggle("Allow Deficit Spending", value=True)
tax_rate = st.sidebar.slider("Average Tax Rate (%)", 15, 45, 25)

st.sidebar.subheader("Industrial & Trade Policy")
bbbee_share = st.sidebar.slider("B-BBEE SME Redirect (%)", 0, 50, 10)
tariff_shock = st.sidebar.slider("Avg Tariff Change (%)", -20, 20, 0)
markup_reduction = st.sidebar.slider("Competition Markup Reduction (%)", 0, 20, 0)
localization = st.sidebar.slider("Localization / Import Substitution (%)", 0, 50, 0)

st.subheader("📊 5-Year Budget Allocation (R mn)")
years = [f"Year {i}" for i in range(1, 6)]
budget_df = pd.DataFrame([base_budgets for _ in range(5)], index=years)

edited_budget_df = st.data_editor(
    budget_df, use_container_width=True, num_rows="fixed",
    column_config={col: st.column_config.NumberColumn(format="%d") for col in budget_df.columns}
)

df_scenario = twin.simulate_5_years(edited_budget_df, base_budgets, envelope, allow_deficit, tax_rate, tariff_shock, bbbee_share, markup_reduction, localization)
baseline_df = pd.DataFrame([base_budgets for _ in range(5)], index=years)
df_baseline = twin.simulate_5_years(baseline_df, base_budgets, sum(base_budgets.values()), allow_deficit, tax_rate, 0, 0, 0, 0)

st.divider()

# Sum of jobs across all 5 years is better than just Year 5
total_jobs = df_scenario['Jobs_Created'].sum()

col1, col2, col3 = st.columns(3)
col1.metric("Year 5 GDP", f"R {df_scenario.iloc[-1]['GDP']:.2f} T", delta=f"{(df_scenario.iloc[-1]['GDP'] - df_baseline.iloc[-1]['GDP']):.2f} T vs Baseline")
col2.metric("Year 5 Debt-to-GDP", f"{df_scenario.iloc[-1]['Debt_to_GDP']:.1f} %", delta=f"{(df_scenario.iloc[-1]['Debt_to_GDP'] - df_baseline.iloc[-1]['Debt_to_GDP']):.1f} % vs Baseline", delta_color="inverse")
col3.metric("Total Jobs (5-Yr Sum)", f"{total_jobs:,.0f}")

col_chart1, col_chart2 = st.columns(2)
with col_chart1:
    fig_gdp = go.Figure()
    fig_gdp.add_trace(go.Scatter(x=df_baseline["Year"], y=df_baseline["GDP"], mode='lines', name='Baseline', line=dict(dash='dot', color='gray')))
    fig_gdp.add_trace(go.Scatter(x=df_scenario["Year"], y=df_scenario["GDP"], mode='lines+markers', name='Scenario', line=dict(color='#2ecc71', width=4)))
    fig_gdp.update_layout(title="Projected GDP (R Trillion)", template="plotly_white")
    st.plotly_chart(fig_gdp, use_container_width=True)

with col_chart2:
    fig_debt = go.Figure()
    fig_debt.add_trace(go.Scatter(x=df_baseline["Year"], y=df_baseline["Debt_to_GDP"], mode='lines', name='Baseline', line=dict(dash='dot', color='gray')))
    fig_debt.add_trace(go.Scatter(x=df_scenario["Year"], y=df_scenario["Debt_to_GDP"], mode='lines+markers', name='Scenario', line=dict(color='#e74c3c', width=4)))
    fig_debt.update_layout(title="Debt-to-GDP Ratio (%)", template="plotly_white")
    st.plotly_chart(fig_debt, use_container_width=True)

st.divider()
with st.expander("💾 Save this Scenario to the Database"):
    scenario_name = st.text_input("Scenario Name", "My Policy Proposal")
    if st.button("Save to Supabase"):
        supabase = get_supabase()
        if supabase:
            payload = {
                "scenario_name": scenario_name,
                "levers": {"envelope": envelope, "tax_rate": tax_rate, "tariff": tariff_shock, "bbbee": bbbee_share, "markup": markup_reduction, "localization": localization},
                "outputs": df_scenario.to_dict(orient="records")
            }
            try:
                supabase.table("scenario_runs").insert(payload).execute()
                st.success(f"Scenario '{scenario_name}' saved successfully!")
            except Exception as e:
                st.error(f"Failed to save: {e}")
        else:
            st.error("Supabase credentials not found.")

st.divider()
st.subheader("🧠 AI Economic Advisor")

if "messages" not in st.session_state:
    st.session_state.messages = []

# FIX: Added enumerate() to give each download button a unique key
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            st.download_button(
                label="📄 Download Memo",
                data=message["content"],
                file_name=f"Cabinet_Memorandum_{i}.txt",
                mime="text/plain",
                key=f"download_hist_{i}" # <--- UNIQUE KEY ADDED
            )

if prompt := st.chat_input("Ask for a briefing note, or ask about trade-offs..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing scenario (this may take up to 2 minutes)..."):
            ai_response = twin.ask_ai_advisor(prompt, df_scenario)
            st.markdown(ai_response)
            st.download_button(
                label="📄 Download Memo",
                data=ai_response,
                file_name="Cabinet_Memorandum.txt",
                mime="text/plain",
                key="download_new" # <--- UNIQUE KEY ADDED
            )
            
    st.session_state.messages.append({"role": "assistant", "content": ai_response})
