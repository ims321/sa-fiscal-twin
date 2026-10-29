import streamlit as st
import pandas as pd
import plotly.express as px
from engine.data_loader import load_twin_data
from engine.model import LeontiefTwin

st.set_page_config(page_title="SA Fiscal Twin", layout="wide")
st.title("South Africa Fiscal–Economic Twin")
st.caption("Leontief I-O Engine with Strict Budget Envelope")

@st.cache_data
def init_engine():
    A, va, sectors = load_twin_data()
    return LeontiefTwin(A, va, sectors)

twin = init_engine()
base_budgets = {'Health': 250000, 'Education': 300000, 'Public Works': 40000, 
                'Trade and Industry': 10000, 'Small Business Development': 5000}
total_base = sum(base_budgets.values())

st.sidebar.header("1. Fiscal Rules")
envelope = st.sidebar.number_input("Total Budget Envelope (R mn)", value=total_base, step=10000)
allow_deficit = st.sidebar.toggle("Allow Deficit Spending", value=False, 
                                  help="If off, departments are scaled down proportionally to fit the envelope.")
tax_rate = st.sidebar.slider("Average Tax Rate (%)", 15, 45, 25)

st.sidebar.header("2. Budget Levers (R mn)")
new_budgets = {}
for dept, base in base_budgets.items():
    new_budgets[dept] = st.sidebar.slider(dept, float(base*0.5), float(base*2.0), float(base), 1000.0)

st.sidebar.header("3. Policy Levers")
bbbee_share = st.sidebar.slider("B-BBEE Procurement Redirect (%)", 0, 50, 10)
tariff_shock = st.sidebar.slider("Average Tariff Change (%)", -20, 20, 0)

# --- REAL-TIME EXECUTION ---
results, gdp_effect, revenue, jobs_effect, net_fiscal, actual_budgets, budget_scaled = twin.simulate(
    new_budgets, base_budgets, envelope, allow_deficit, tax_rate, tariff_shock, bbbee_share
)

# Warnings and Status
if budget_scaled:
    st.warning(f"⚠️ Over Budget! Your proposed spending was R{sum(new_budgets.values()):,.0f} mn. To fit the R{envelope:,.0f} mn envelope, all departments were scaled down by {(1 - (envelope / sum(new_budgets.values()))) * 100:.1f}%.")
elif allow_deficit and sum(new_budgets.values()) > envelope:
    st.info(f"📈 Deficit Spending Active: You are spending R{sum(new_budgets.values()) - envelope:,.0f} mn more than the envelope. This will increase government debt.")

# Top Metrics
col1, col2, col3, col4 = st.columns(4)
budget_change = sum(actual_budgets.values()) - total_base
col1.metric("Actual Budget Change", f"{budget_change:,.0f} mn")
col2.metric("GDP Effect", f"{gdp_effect:,.0f} mn", delta=f"{gdp_effect/1000:,.1f} bn")
col3.metric("Jobs Created", f"{jobs_effect:,.0f}")
col4.metric("Net Fiscal Balance", f"{net_fiscal:,.0f} mn", delta=f"{net_fiscal/1000:,.1f} bn", delta_color="normal")

st.divider()

col_chart1, col_chart2 = st.columns([2, 1])

with col_chart1:
    fig = px.bar(results, x="sector", y="gross_output_zar_mn", 
                 title="Sectoral Gross Output Effect (R million)",
                 labels={"gross_output_zar_mn": "Impact (R mn)"},
                 color="gross_output_zar_mn", color_continuous_scale="RdYlGn")
    st.plotly_chart(fig, use_container_width=True)

with col_chart2:
    # Use actual_budgets (post-scaling) for the pie chart so the UI reflects reality
    budget_df = pd.DataFrame(list(actual_budgets.items()), columns=['Department', 'Budget'])
    fig_pie = px.pie(budget_df, values='Budget', names='Department', title="Actual Budget Allocation (Post-Scaling)")
    st.plotly_chart(fig_pie, use_container_width=True)
