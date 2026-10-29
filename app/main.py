import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from engine.data_loader import load_twin_data, get_supabase
from engine.model import LeontiefTwin
from engine.report import generate_pdf
from engine.live_data import fetch_live_budgets
from engine.optimizer import find_optimal_policy

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
st.caption("Macro-Fiscal + Microsimulation + Agent-Based Firm Dynamics")

@st.cache_resource
def init_engine():
    A, va, sectors = load_twin_data()
    return LeontiefTwin(A, va, sectors)

twin = init_engine()

# --- AUTOPILOT SECTION ---
st.markdown("### 🤖 AI Autopilot")
st.markdown("Set your macroeconomic targets below, and the AI will search for the optimal combination of taxes and spending to achieve them.")
col_auto1, col_auto2, col_auto3 = st.columns(3)
with col_auto1:
    target_poverty = st.number_input("Target Poverty Rate (%)", min_value=10.0, max_value=50.0, value=28.0, step=1.0)
with col_auto2:
    max_debt = st.number_input("Max Debt-to-GDP (%)", min_value=60.0, max_value=100.0, value=75.0, step=1.0)
with col_auto3:
    st.write("")
    st.write("")
    run_auto = st.button("🚀 Run Autopilot Optimization", use_container_width=True)

if run_auto:
    with st.spinner("Running 50 simulations to find the optimal policy..."):
        base_budgets_default = fetch_live_budgets()
        best_policy = find_optimal_policy(twin, base_budgets_default, sum(base_budgets_default.values()), target_poverty, max_debt)
        
        # Save optimal settings to session state so they override the sliders
        st.session_state.opt_vat = int(best_policy['vat'])
        st.session_state.opt_cit = int(best_policy['cit'])
        st.session_state.opt_pit = int(best_policy['pit'])
        st.session_state.pw_scale = best_policy['pw_scale']
        st.session_state.edu_scale = best_policy['edu_scale']
        st.success(f"Optimization Complete! Found policy to achieve {best_policy['resulting_poverty']:.1f}% poverty and {best_policy['resulting_debt']:.1f}% debt.")

st.divider()

# --- SIDEBAR CONTROLS ---
st.sidebar.header("🏦 Data Source")
if "base_budgets" not in st.session_state:
    st.session_state.base_budgets = fetch_live_budgets()
if st.sidebar.button("🔄 Refresh Treasury Data"):
    st.session_state.base_budgets = fetch_live_budgets()
    st.rerun()

base_budgets = st.session_state.base_budgets

st.sidebar.header("⚙️ Fiscal Rules")
envelope = st.sidebar.number_input("Base Envelope (R mn)", value=sum(base_budgets.values()), step=10000)
allow_deficit = st.sidebar.toggle("Allow Deficit Spending", value=True)

st.sidebar.subheader("💰 Tax Levers")
# Use session state defaults if autopilot ran
default_vat = st.session_state.get('opt_vat', 15)
default_cit = st.session_state.get('opt_cit', 27)
default_pit = st.session_state.get('opt_pit', 30)

vat_rate = st.sidebar.slider("VAT Rate (%)", 10, 25, default_vat)
cit_rate = st.sidebar.slider("Corporate Tax (%)", 15, 40, default_cit)
pit_rate = st.sidebar.slider("Personal Income Tax (%)", 15, 45, default_pit)

st.sidebar.subheader("🏭 Industrial & Trade Policy")
bbbee_share = st.sidebar.slider("B-BBEE SME Redirect (%)", 0, 50, 10)
tariff_shock = st.sidebar.slider("Avg Tariff Change (%)", -20, 20, 0)
markup_reduction = st.sidebar.slider("Competition Markup Reduction (%)", 0, 20, 0)
localization = st.sidebar.slider("Localization / Import Substitution (%)", 0, 50, 0)

st.subheader("📊 5-Year Budget Allocation (R mn)")
st.markdown(f"*Baseline loaded from Treasury data. Total Envelope: R {sum(base_budgets.values()):,.0f} mn*")

years = [f"Year {i}" for i in range(1, 6)]

# Apply autopilot budget scaling if it ran
if 'pw_scale' in st.session_state:
    base_budgets['Public Works'] = int(base_budgets['Public Works'] * st.session_state.pw_scale)
    base_budgets['Education'] = int(base_budgets['Education'] * st.session_state.edu_scale)

budget_df = pd.DataFrame([base_budgets for _ in range(5)], index=years)

edited_budget_df = st.data_editor(
    budget_df, use_container_width=True, num_rows="fixed",
    column_config={col: st.column_config.NumberColumn(format="%d") for col in budget_df.columns}
)

df_scenario = twin.simulate_5_years(edited_budget_df, base_budgets, envelope, allow_deficit, vat_rate, cit_rate, pit_rate, tariff_shock, bbbee_share, markup_reduction, localization)
baseline_df = pd.DataFrame([base_budgets for _ in range(5)], index=years)
df_baseline = twin.simulate_5_years(baseline_df, base_budgets, sum(base_budgets.values()), allow_deficit, 15, 27, 30, 0, 0, 0, 0)

st.divider()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Year 5 GDP", f"R {df_scenario.iloc[-1]['GDP']:.2f} T", delta=f"{(df_scenario.iloc[-1]['GDP'] - df_baseline.iloc[-1]['GDP']):.2f} T vs Baseline")
col2.metric("Year 5 Debt-to-GDP", f"{df_scenario.iloc[-1]['Debt_to_GDP']:.1f} %", delta=f"{(df_scenario.iloc[-1]['Debt_to_GDP'] - df_baseline.iloc[-1]['Debt_to_GDP']):.1f} % vs Baseline", delta_color="inverse")
col3.metric("Year 5 Employment", f"{df_scenario.iloc[-1]['Total_Employment']:,.0f}", delta=f"{(df_scenario.iloc[-1]['Total_Employment'] - df_baseline.iloc[-1]['Total_Employment']):,.0f} vs Baseline")
col4.metric("Year 5 Gini", f"{df_scenario.iloc[-1]['Gini']:.3f}", delta=f"{(df_scenario.iloc[-1]['Gini'] - df_baseline.iloc[-1]['Gini']):.3f} vs Baseline", delta_color="inverse")

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
st.subheader("🏢 Firm Dynamics & Market Concentration")
col_firm1, col_firm2 = st.columns(2)
with col_firm1:
    active_firms_df = pd.DataFrame([f.to_dict() for f in twin.firm_market.firms if f.active])
    fig_firms = px.scatter(active_firms_df, x="productivity", y="employees", size="market_share", color="sector", 
                           title="Active Firms: Productivity vs Employment Size", template="plotly_white")
    st.plotly_chart(fig_firms, use_container_width=True)

with col_firm2:
    fig_hhi = go.Figure()
    fig_hhi.add_trace(go.Scatter(x=df_baseline["Year"], y=df_baseline["HHI"], mode='lines', name='Baseline HHI', line=dict(dash='dot', color='gray')))
    fig_hhi.add_trace(go.Scatter(x=df_scenario["Year"], y=df_scenario["HHI"], mode='lines+markers', name='Scenario HHI', line=dict(color='#9b59b6', width=4)))
    fig_hhi.add_hline(y=1500, line_dash="dash", line_color="green", annotation_text="Competitive Threshold")
    fig_hhi.update_layout(title="Market Concentration (HHI)", template="plotly_white")
    st.plotly_chart(fig_hhi, use_container_width=True)

st.divider()
st.subheader("🏘️ Household Income Distribution")
income_df = twin.microsim.households[['current_income']]
fig_dist = px.histogram(income_df, x="current_income", nbins=100, title="Simulated Household Income Distribution", labels={'current_income': 'Annual Household Income (R)'}, color_discrete_sequence=['#3498db'])
fig_dist.add_vline(x=twin.microsim.poverty_line, line_dash="dash", line_color="red", annotation_text="Poverty Line")
st.plotly_chart(fig_dist, use_container_width=True)

st.divider()
with st.expander("💾 Save this Scenario to the Database"):
    scenario_name = st.text_input("Scenario Name", "Optimized Scenario")
    if st.button("Save to Supabase"):
        supabase = get_supabase()
        if supabase:
            payload = {
                "scenario_name": scenario_name,
                "levers": {"envelope": envelope, "vat": vat_rate, "cit": cit_rate, "pit": pit_rate, "tariff": tariff_shock, "bbbee": bbbee_share, "markup": markup_reduction, "localization": localization},
                "outputs": df_scenario.to_dict(orient="records")
            }
            try:
                supabase.table("scenario_runs").insert(payload).execute()
                st.success(f"Scenario '{scenario_name}' saved successfully!")
            except Exception as e:
                st.error(f"Failed to save: {e}")

st.divider()
st.subheader("🧠 AI Economic Advisor")

if "messages" not in st.session_state:
    st.session_state.messages = []

for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            levers_dict = {"vat": vat_rate, "cit": cit_rate, "pit": pit_rate, "bbbee": bbbee_share, "tariff": tariff_shock, "localization": localization}
            pdf_bytes = generate_pdf(message["content"], df_scenario, df_baseline, levers_dict)
            st.download_button(
                label="📄 Download Full Cabinet Report (PDF)", data=pdf_bytes,
                file_name=f"Cabinet_Memorandum_{i}.pdf", mime="application/pdf", key=f"download_hist_{i}"
            )

if prompt := st.chat_input("Ask about firm dynamics, inequality, or debt..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing scenario..."):
            ai_response = twin.ask_ai_advisor(prompt, df_scenario)
            st.markdown(ai_response)
            
            levers_dict = {"vat": vat_rate, "cit": cit_rate, "pit": pit_rate, "bbbee": bbbee_share, "tariff": tariff_shock, "localization": localization}
            pdf_bytes = generate_pdf(ai_response, df_scenario, df_baseline, levers_dict)
            
            st.download_button(
                label="📄 Download Full Cabinet Report (PDF)", data=pdf_bytes,
                file_name="Cabinet_Memorandum.pdf", mime="application/pdf", key="download_new"
            )
            
    st.session_state.messages.append({"role": "assistant", "content": ai_response})
