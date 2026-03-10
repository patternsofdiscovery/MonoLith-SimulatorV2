import copy

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from model.results import run_model
from model.scenarios import SCENARIOS

st.set_page_config(page_title="MONOLiTH Simulator v2", layout="wide")

st.title("MONOLiTH Simulator v2")
st.caption("Physics-informed early-stage lithium refining model")

mode = st.radio("Mode", ["Investor", "Engineering"], horizontal=True)

scenario_name = st.selectbox("Scenario", list(SCENARIOS.keys()))
inputs = SCENARIOS[scenario_name]()

with st.sidebar:
    st.header("Core Inputs")

    inputs.feed_flow_m3h = st.number_input("Feed flow (m³/h)", value=float(inputs.feed_flow_m3h))
    inputs.feed_li_gL = st.number_input("Feed Li (g/L)", value=float(inputs.feed_li_gL))
    inputs.feed_mg_gL = st.number_input("Feed Mg (g/L)", value=float(inputs.feed_mg_gL))
    inputs.current_density_A_m2 = st.number_input("Current density (A/m²)", value=float(inputs.current_density_A_m2))
    inputs.electrode_area_m2_per_stack = st.number_input("Electrode area / stack (m²)", value=float(inputs.electrode_area_m2_per_stack))
    inputs.installed_stacks = st.number_input("Installed stacks", value=int(inputs.installed_stacks), step=1)
    inputs.active_stack_fraction = st.slider("Active stack fraction", 0.1, 1.0, float(inputs.active_stack_fraction))
    inputs.faradaic_efficiency = st.slider("Faradaic efficiency", 0.5, 1.0, float(inputs.faradaic_efficiency))
    inputs.electricity_price_per_MWh = st.number_input("Electricity ($/MWh)", value=float(inputs.electricity_price_per_MWh))

    if mode == "Engineering":
        st.header("Engineering Inputs")
        inputs.feed_na_gL = st.number_input("Feed Na (g/L)", value=float(inputs.feed_na_gL))
        inputs.feed_k_gL = st.number_input("Feed K (g/L)", value=float(inputs.feed_k_gL))
        inputs.feed_ca_gL = st.number_input("Feed Ca (g/L)", value=float(inputs.feed_ca_gL))
        inputs.stack_recovery = st.slider("Stack recovery", 0.5, 1.0, float(inputs.stack_recovery))
        inputs.polishing_recovery = st.slider("Polishing recovery", 0.5, 1.0, float(inputs.polishing_recovery))
        inputs.pretreatment_recovery = st.slider("Pretreatment recovery", 0.5, 1.0, float(inputs.pretreatment_recovery))
        inputs.product_recovery = st.slider("Product recovery", 0.5, 1.0, float(inputs.product_recovery))
        inputs.thermodynamic_voltage_V = st.number_input("Thermodynamic voltage (V)", value=float(inputs.thermodynamic_voltage_V))
        inputs.area_specific_resistance_ohm_m2 = st.number_input(
            "ASR (ohm·m²)",
            value=float(inputs.area_specific_resistance_ohm_m2),
            format="%.5f",
        )
        inputs.limiting_current_density_A_m2 = st.number_input(
            "Limiting current density (A/m²)",
            value=float(inputs.limiting_current_density_A_m2),
        )
        inputs.activation_coeff_V = st.number_input(
            "Activation coeff (V)",
            value=float(inputs.activation_coeff_V),
            format="%.4f",
        )
        inputs.years_on_stream = st.number_input("Years on stream", value=float(inputs.years_on_stream))
        inputs.uptime_fraction = st.slider("Uptime fraction", 0.5, 1.0, float(inputs.uptime_fraction))
        inputs.purge_fraction = st.slider("Purge fraction", 0.0, 0.5, float(inputs.purge_fraction))

results = run_model(inputs)

st.subheader("Core Plant KPIs")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Annual Production", f"{results['annual_tpy']:,.0f} t/y")
k2.metric("SEC", f"{results['sec_kwh_per_kg']:.2f} kWh/kg")
k3.metric("OPEX", f"${results['opex_usd_per_ton']:,.0f}/t")
k4.metric("CAPEX", f"${results['capex_usd'] / 1e6:,.1f}M")

k5, k6, k7, k8 = st.columns(4)
k5.metric("Active Stacks", f"{results['active_stacks']}")
k6.metric("Total Power", f"{results['power_kW']:,.0f} kW")
k7.metric("Overall Recovery", f"{results['overall_recovery'] * 100:.1f}%")
k8.metric("Cell Voltage", f"{results['cell_voltage_V']:.2f} V")

st.subheader("Engineering Sizing KPIs")
e1, e2, e3, e4 = st.columns(4)
e1.metric("Current / Stack", f"{results['stack_current_A']:,.0f} A")
e2.metric("Power / Stack", f"{results['power_per_stack_kW']:,.1f} kW")
e3.metric("Flow / Active Stack", f"{results['flow_per_active_stack_m3h']:,.2f} m³/h")
e4.metric("Brine / Ton Product", f"{results['brine_m3_per_ton_product']:,.0f} m³/t")

e5, e6 = st.columns(2)
e5.metric("Total Electrode Area", f"{results['total_electrode_area_m2']:,.0f} m²")
e6.metric("Annual Electricity Spend", f"${results['electricity_cost_usd_per_year'] / 1e6:,.2f}M/yr")

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

st.subheader("Economics and Lithium Pathways")
col1, col2 = st.columns(2)

with col1:
    cost_df = pd.DataFrame(
        {
            "Category": ["Electricity", "Stack Replacement", "Fixed OPEX"],
            "USD per ton": [
                results["electricity_cost_per_ton"],
                results["replacement_cost_per_ton"],
                results["fixed_opex_per_ton"],
            ],
        }
    )

    fig_cost, ax_cost = plt.subplots(figsize=(6, 2.8))
    ax_cost.barh(cost_df["Category"], cost_df["USD per ton"])
    ax_cost.set_xlabel("USD per ton LiOH·H₂O")
    ax_cost.set_title("OPEX Breakdown")
    st.pyplot(fig_cost)

with col2:
    li_df = pd.DataFrame(
        {
            "Pathway": [
                "Product Li",
                "Recycle Li",
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

    fig_li, ax_li = plt.subplots(figsize=(6, 2.8))
    ax_li.barh(li_df["Pathway"], li_df["Li kg/h"])
    ax_li.set_xlabel("Li mass (kg/h)")
    ax_li.set_title("Lithium Pathway Breakdown")
    st.pyplot(fig_li)

st.subheader("Stream Table")
stream_df = pd.DataFrame(results["stream_table"])
stream_df = stream_df.rename(
    columns={
        "name": "Stream",
        "flow_m3h": "Flow (m3/h)",
        "Li_kgph": "Li (kg/h)",
        "Mg_kgph": "Mg (kg/h)",
        "Na_kgph": "Na (kg/h)",
        "K_kgph": "K (kg/h)",
        "Ca_kgph": "Ca (kg/h)",
        "water_kgph": "Water (kg/h)",
    }
)
st.dataframe(stream_df, use_container_width=True)

stream_csv = stream_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download stream table CSV",
    data=stream_csv,
    file_name="monolith_stream_table.csv",
    mime="text/csv",
)

st.subheader("Assumptions Table")
assumptions_df = pd.DataFrame(results["assumptions_table"])
st.dataframe(assumptions_df, use_container_width=True)

assumptions_csv = assumptions_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download assumptions CSV",
    data=assumptions_csv,
    file_name="monolith_assumptions.csv",
    mime="text/csv",
)

st.subheader("Sensitivity Analysis")
s1, s2 = st.columns(2)

with s1:
    j_values = np.linspace(50, max(60, inputs.limiting_current_density_A_m2 * 0.95), 20)
    sec_vals = []
    prod_vals = []

    for j in j_values:
        test_inputs = copy.deepcopy(inputs)
        test_inputs.current_density_A_m2 = float(j)
        r = run_model(test_inputs)
        sec_vals.append(r["sec_kwh_per_kg"])
        prod_vals.append(r["annual_tpy"])

    fig_sec, ax_sec = plt.subplots(figsize=(6, 3.0))
    ax_sec.plot(j_values, sec_vals)
    ax_sec.set_xlabel("Current Density (A/m²)")
    ax_sec.set_ylabel("SEC (kWh/kg)")
    ax_sec.set_title("SEC vs Current Density")
    st.pyplot(fig_sec)

    fig_prod, ax_prod = plt.subplots(figsize=(6, 3.0))
    ax_prod.plot(j_values, prod_vals)
    ax_prod.set_xlabel("Current Density (A/m²)")
    ax_prod.set_ylabel("Annual Production (t/y)")
    ax_prod.set_title("Production vs Current Density")
    st.pyplot(fig_prod)

with s2:
    power_values = np.linspace(10, 120, 20)
    opex_vals = []

    for p in power_values:
        test_inputs = copy.deepcopy(inputs)
        test_inputs.electricity_price_per_MWh = float(p)
        r = run_model(test_inputs)
        opex_vals.append(r["opex_usd_per_ton"])

    fig_opex, ax_opex = plt.subplots(figsize=(6, 3.0))
    ax_opex.plot(power_values, opex_vals)
    ax_opex.set_xlabel("Electricity Price ($/MWh)")
    ax_opex.set_ylabel("OPEX ($/t)")
    ax_opex.set_title("OPEX vs Electricity Price")
    st.pyplot(fig_opex)

    stack_values = np.arange(
        max(10, int(inputs.installed_stacks * 0.4)),
        int(inputs.installed_stacks * 1.4) + 1,
        max(1, int(inputs.installed_stacks / 12)),
    )
    annual_prod_vals = []

    for n_stacks in stack_values:
        test_inputs = copy.deepcopy(inputs)
        test_inputs.installed_stacks = int(n_stacks)
        r = run_model(test_inputs)
        annual_prod_vals.append(r["annual_tpy"])

    fig_stack, ax_stack = plt.subplots(figsize=(6, 3.0))
    ax_stack.plot(stack_values, annual_prod_vals)
    ax_stack.set_xlabel("Installed Stacks")
    ax_stack.set_ylabel("Annual Production (t/y)")
    ax_stack.set_title("Production vs Installed Stacks")
    st.pyplot(fig_stack)
