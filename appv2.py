import copy
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

from model.results import run_model
from model.scenarios import SCENARIOS


st.set_page_config(page_title="MONOLiTH Simulator", layout="wide")

# ----------------------------
# PAGE STYLES
# ----------------------------

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    .kpi-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        padding: 18px 20px 16px 20px;
        min-height: 138px;
    }

    .kpi-label {
        font-size: 0.95rem;
        color: rgba(250,250,250,0.78);
        margin-bottom: 10px;
        line-height: 1.2;
    }

    .kpi-value {
        font-size: 2.1rem;
        font-weight: 700;
        line-height: 1.05;
        color: white;
        margin-bottom: 6px;
    }

    .kpi-subtext {
        font-size: 0.82rem;
        color: rgba(250,250,250,0.58);
        line-height: 1.25;
    }

    .section-spacer {
        padding-top: 0.35rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_kpi_card(label: str, value: str, subtext: str = ""):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-subtext">{subtext}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
        help="""
Fraction of installed electrochemical stacks actively operating.

Accounts for maintenance downtime, stack replacement, and operational availability.

Example:
120 installed stacks × 0.9 availability = 108 active stacks

Typical values:
0.85–0.95
""",
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
# PROCESS COMPETITIVENESS
# ----------------------------

st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
st.subheader("Process Competitiveness")

c1, c2, c3 = st.columns(3)

with c1:
    render_kpi_card(
        "Energy Intensity",
        f"{results['sec_kwh_per_kg']:.1f} kWh/kg",
        "Lower is better. This is one of the most important competitiveness metrics.",
    )

with c2:
    render_kpi_card(
        "Lithium Recovery",
        f"{results['overall_recovery'] * 100:.1f}%",
        "Overall lithium captured through pretreatment, stack, polishing, and product steps.",
    )

with c3:
    render_kpi_card(
        "Operating Cost",
        f"${results['opex_usd_per_ton']:,.0f}/t",
        "Variable + fixed annual operating cost normalized by annual LiOH output.",
    )

c4, c5 = st.columns([1.2, 1.8])

with c4:
    render_kpi_card(
        "Annual Production",
        f"{results['annual_tpy']:,.0f} t/y",
        "Nominal annual LiOH·H₂O production at current operating assumptions.",
    )

with c5:
    st.markdown("")
    st.markdown("")
    st.caption(
        "These four metrics summarize the core tradeoff of the process: "
        "energy use, lithium recovery, operating cost, and production scale."
    )

# ----------------------------
# ENGINEERING METRICS
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
    f"{inputs.installed_stacks}",
)

d2.metric(
    "Total Electrode Area",
    f"{results['total_electrode_area_m2']:,.0f} m²",
)

d3.metric(
    "Total Plant Power",
    f"{results['power_kW']:,.0f} kW",
)

d4.metric(
    "Annual Brine Throughput",
    f"{inputs.feed_flow_m3h * 8760 * inputs.uptime_fraction:,.0f} m³/yr",
)

d5, d6 = st.columns(2)

d5.metric(
    "Electricity Cost / ton",
    f"${results['electricity_cost_per_ton']:,.0f}/t",
)

d6.metric(
    "Stack Replacement Cost / ton",
    f"${results['replacement_cost_per_ton']:,.0f}/t",
)

if results["warnings"]:
    st.warning("Engineering warnings:\n\n- " + "\n- ".join(results["warnings"]))

if results["limiters"]:
    st.info("What is limiting production:\n\n- " + "\n- ".join(results["limiters"]))

balance = results["balance"]
st.subheader("Mass Balance Check")
b1, b2, b3, b4 = st.columns(4)
b1.metric("Li In", f"{balance['li_in_kgph']:,.3f} kg/h")
b2.metric("Li Accounted", f"{balance['li_accounted_kgph']:,.3f} kg/h")
b3.metric("Balance Error", f"{balance['li_balance_error_kgph']:,.4f} kg/h")
b4.metric("Balance Error %", f"{balance['li_balance_error_pct']:.3f}%")

# ----------------------------
# PROCESS INSIGHTS
# ----------------------------

st.subheader("Process Insights")

col1, col2 = st.columns(2)

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
    fig.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=45, b=10),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

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
    fig.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=45, b=10),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------
# SENSITIVITY ANALYSIS
# ----------------------------

st.subheader("Sensitivity Analysis")

col1, col2 = st.columns(2)

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
    fig.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=45, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

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
    fig.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=45, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------
# OPERATING ENVELOPE
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
    index=[round(v, 1) for v in j_range],
    columns=[int(v) for v in stack_range],
)

fig = px.imshow(
    heatmap_df,
    labels=dict(
        x="Installed Stacks",
        y="Current Density (A/m²)",
        color="Energy Intensity (kWh/kg)",
    ),
    title="Operating Envelope (Energy Intensity)",
    aspect="auto",
)
fig.update_layout(
    height=420,
    margin=dict(l=10, r=10, t=45, b=10),
)
st.plotly_chart(fig, use_container_width=True)

# ----------------------------
# STREAM TABLE
# ----------------------------

st.subheader("Process Stream Table")

stream_df = pd.DataFrame(results["stream_table"])
st.dataframe(stream_df, use_container_width=True)

stream_csv = stream_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download stream table CSV",
    data=stream_csv,
    file_name="monolith_stream_table.csv",
    mime="text/csv",
)

# ----------------------------
# ASSUMPTIONS TABLE
# ----------------------------

st.subheader("Model Assumptions")

assumptions_df = pd.DataFrame(results["assumptions_table"])
st.dataframe(assumptions_df, use_container_width=True)

assumptions_csv = assumptions_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download assumptions CSV",
    data=assumptions_csv,
    file_name="monolith_assumptions.csv",
    mime="text/csv",
)
