import copy
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

from model.results import run_model
from model.scenarios import SCENARIOS


st.set_page_config(page_title="MONOLiTH Simulator", layout="wide")

st.title("MONOLiTH Lithium Refining Simulator")
st.caption("Electrochemical lithium hydroxide refining process model")

# ----------------------------
# SCENARIO
# ----------------------------

scenario_name = st.selectbox(
    "Scenario Preset",
    list(SCENARIOS.keys()),
)

inputs = SCENARIOS[scenario_name]()

# ----------------------------
# SIDEBAR INPUTS
# ----------------------------

with st.sidebar:

    st.header("Feed Brine")

    inputs.feed_flow_m3h = st.number_input(
        "Feed Flow (m³/h)",
        value=float(inputs.feed_flow_m3h),
    )

    inputs.feed_li_gL = st.number_input(
        "Lithium (g/L)",
        value=float(inputs.feed_li_gL),
    )

    inputs.feed_mg_gL = st.number_input(
        "Magnesium (g/L)",
        value=float(inputs.feed_mg_gL),
    )

    st.header("Electrochemical Stack")

    inputs.current_density_A_m2 = st.number_input(
        "Current Density (A/m²)",
        value=float(inputs.current_density_A_m2),
    )

    inputs.electrode_area_m2_per_stack = st.number_input(
        "Electrode Area per Stack (m²)",
        value=float(inputs.electrode_area_m2_per_stack),
    )

    inputs.installed_stacks = st.number_input(
        "Installed Stacks",
        value=int(inputs.installed_stacks),
        step=1,
    )

    inputs.active_stack_fraction = st.slider(
        "Active Stack Fraction",
        0.1,
        1.0,
        float(inputs.active_stack_fraction),
    )

    inputs.faradaic_efficiency = st.slider(
        "Faradaic Efficiency",
        0.5,
        1.0,
        float(inputs.faradaic_efficiency),
    )

    st.header("Economics")

    inputs.electricity_price_per_MWh = st.number_input(
        "Electricity Price ($/MWh)",
        value=float(inputs.electricity_price_per_MWh),
    )

# ----------------------------
# RUN MODEL
# ----------------------------

results = run_model(inputs)

# ----------------------------
# PROCESS COMPETITIVENESS KPIs
# ----------------------------

st.subheader("Process Competitiveness")

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Energy Intensity",
    f"{results['sec_kwh_per_kg']:.2f} kWh/kg LiOH",
)

k2.metric(
    "Lithium Recovery",
    f"{results['overall_recovery']*100:.1f} %",
)

k3.metric(
    "Operating Cost",
    f"${results['opex_usd_per_ton']:,.0f}/t",
)

k4.metric(
    "Annual Production",
    f"{results['annual_tpy']:,.0f} t/y",
)

# ----------------------------
# ENGINEERING KPIs
# ----------------------------

st.subheader("Engineering Metrics")

e1, e2, e3, e4 = st.columns(4)

e1.metric(
    "Current per Stack",
    f"{results['stack_current_A']:,.0f} A",
)

e2.metric(
    "Power per Stack",
    f"{results['power_per_stack_kW']:,.1f} kW",
)

e3.metric(
    "Flow per Active Stack",
    f"{results['flow_per_active_stack_m3h']:,.2f} m³/h",
)

e4.metric(
    "Brine Intensity",
    f"{results['brine_m3_per_ton_product']:,.0f} m³/t LiOH",
)

# ----------------------------
# PLANT DESIGN SUMMARY
# ----------------------------

st.subheader("Plant Design Summary")

d1, d2, d3, d4 = st.columns(4)

d1.metric(
    "Installed Stacks",
    f"{inputs.installed_stacks}"
)

d2.metric(
    "Total Electrode Area",
    f"{results['total_electrode_area_m2']:,.0f} m²"
)

d3.metric(
    "Total Plant Power",
    f"{results['power_kW']:,.0f} kW"
)

d4.metric(
    "Annual Brine Throughput",
    f"{inputs.feed_flow_m3h * 8760 * inputs.uptime_fraction:,.0f} m³/yr"
)

d5, d6 = st.columns(2)

d5.metric(
    "Electricity Cost / ton",
    f"${results['electricity_cost_per_ton']:,.0f}/t"
)

d6.metric(
    "Stack Replacement Cost / ton",
    f"${results['replacement_cost_per_ton']:,.0f}/t"
)

# ----------------------------
# PROCESS INSIGHT CHARTS
# ----------------------------

st.subheader("Process Insights")

col1, col2 = st.columns(2)

# OPEX breakdown

with col1:

    cost_df = pd.DataFrame(
        {
            "Category": [
                "Electricity",
                "Stack Replacement",
                "Fixed OPEX",
            ],
            "USD per ton": [
                results["electricity_cost_per_ton"],
                results["replacement_cost_per_ton"],
                results["fixed_opex_per_ton"],
            ],
        }
    )

    fig = px.bar(
        cost_df,
        x="USD per ton",
        y="Category",
        orientation="h",
        title="Operating Cost Breakdown",
    )

    st.plotly_chart(fig, use_container_width=True)


# Lithium pathway chart

with col2:

    li_df = pd.DataFrame(
        {
            "Pathway": [
                "Product",
                "Recycle",
                "Purge Loss",
                "Pretreatment Loss",
                "Polish/Product Loss",
            ],
            "Li kg/h": [
                results["li_product_kgph"],
                results["li_stack_to_recycle_kgph"] - results["li_purge_loss_kgph"],
                results["li_purge_loss_kgph"],
                results["li_pretreatment_loss_kgph"],
                results["li_polish_and_product_loss_kgph"],
            ],
        }
    )

    fig = px.bar(
        li_df,
        x="Li kg/h",
        y="Pathway",
        orientation="h",
        title="Lithium Mass Distribution",
    )

    st.plotly_chart(fig, use_container_width=True)

# ----------------------------
# SENSITIVITY ANALYSIS
# ----------------------------

st.subheader("Sensitivity Analysis")

col1, col2 = st.columns(2)

# Energy vs current density

with col1:

    j_values = np.linspace(
        50,
        inputs.limiting_current_density_A_m2 * 0.95,
        20,
    )

    sec_vals = []

    for j in j_values:

        test_inputs = copy.deepcopy(inputs)
        test_inputs.current_density_A_m2 = float(j)

        r = run_model(test_inputs)

        sec_vals.append(r["sec_kwh_per_kg"])

    df = pd.DataFrame(
        {
            "Current Density": j_values,
            "Energy Intensity": sec_vals,
        }
    )

    fig = px.line(
        df,
        x="Current Density",
        y="Energy Intensity",
        title="Energy Intensity vs Current Density",
    )

    st.plotly_chart(fig, use_container_width=True)


# Production vs stacks

with col2:

    stack_values = np.arange(
        max(10, int(inputs.installed_stacks * 0.5)),
        int(inputs.installed_stacks * 1.5),
        5,
    )

    prod_vals = []

    for s in stack_values:

        test_inputs = copy.deepcopy(inputs)
        test_inputs.installed_stacks = int(s)

        r = run_model(test_inputs)

        prod_vals.append(r["annual_tpy"])

    df = pd.DataFrame(
        {
            "Stacks": stack_values,
            "Production": prod_vals,
        }
    )

    fig = px.line(
        df,
        x="Stacks",
        y="Production",
        title="Production vs Installed Stacks",
    )

    st.plotly_chart(fig, use_container_width=True)

# ----------------------------
# OPERATING ENVELOPE HEATMAP
# ----------------------------

st.subheader("Process Operating Envelope")

j_range = np.linspace(
    50,
    inputs.limiting_current_density_A_m2 * 0.95,
    20,
)

stack_range = np.linspace(
    max(10, inputs.installed_stacks * 0.5),
    inputs.installed_stacks * 1.5,
    20,
)

heatmap_data = []

for j in j_range:

    row = []

    for s in stack_range:

        test_inputs = copy.deepcopy(inputs)

        test_inputs.current_density_A_m2 = float(j)
        test_inputs.installed_stacks = int(s)

        r = run_model(test_inputs)

        row.append(r["sec_kwh_per_kg"])

    heatmap_data.append(row)

heatmap_df = pd.DataFrame(
    heatmap_data,
    index=j_range,
    columns=stack_range,
)

fig = px.imshow(
    heatmap_df,
    labels=dict(
        x="Installed Stacks",
        y="Current Density (A/m²)",
        color="Energy Intensity (kWh/kg)",
    ),
    title="Operating Envelope (Energy Intensity)",
)

st.plotly_chart(fig, use_container_width=True)

# ----------------------------
# STREAM TABLE
# ----------------------------

st.subheader("Process Stream Table")

stream_df = pd.DataFrame(results["stream_table"])

st.dataframe(stream_df, use_container_width=True)

# ----------------------------
# ASSUMPTIONS TABLE
# ----------------------------

st.subheader("Model Assumptions")

assumptions_df = pd.DataFrame(results["assumptions_table"])

st.dataframe(assumptions_df, use_container_width=True)
