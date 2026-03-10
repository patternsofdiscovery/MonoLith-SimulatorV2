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

    inputs.feed_flow_m3h = st.number_input(
        "Feed flow (m³/h)",
        value=float(inputs.feed_flow_m3h),
    )
    inputs.feed_li_gL = st.number_input(
        "Feed Li (g/L)",
        value=float(inputs.feed_li_gL),
    )
    inputs.feed_mg_gL = st.number_input(
        "Feed Mg (g/L)",
        value=float(inputs.feed_mg_gL),
    )
    inputs.current_density_A_m2 = st.number_input(
        "Current density (A/m²)",
        value=float(inputs.current_density_A_m2),
    )
    inputs.electrode_area_m2_per_stack = st.number_input(
        "Electrode area / stack (m²)",
        value=float(inputs.electrode_area_m2_per_stack),
    )
    inputs.installed_stacks = st.number_input(
        "Installed stacks",
        value=int(inputs.installed_stacks),
        step=1,
    )
    inputs.active_stack_fraction = st.slider(
        "Active stack fraction",
        0.1,
        1.0,
        float(inputs.active_stack_fraction),
    )
    inputs.faradaic_efficiency = st.slider(
        "Faradaic efficiency",
        0.5,
        1.0,
        float(inputs.faradaic_efficiency),
    )
    inputs.electricity_price_per_MWh = st.number_input(
        "Electricity ($/MWh)",
        value=float(inputs.electricity_price_per_MWh),
    )

    if mode == "Engineering":
        st.header("Engineering Inputs")
        inputs.feed_na_gL = st.number_input(
            "Feed Na (g/L)",
            value=float(inputs.feed_na_gL),
        )
        inputs.feed_k_gL = st.number_input(
            "Feed K (g/L)",
            value=float(inputs.feed_k_gL),
        )
        inputs.feed_ca_gL = st.number_input(
            "Feed Ca (g/L)",
            value=float(inputs.feed_ca_gL),
        )
        inputs.stack_recovery = st.slider(
            "Stack recovery",
            0.5,
            1.0,
            float(inputs.stack_recovery),
        )
        inputs.polishing_recovery = st.slider(
            "Polishing recovery",
            0.5,
            1.0,
            float(inputs.polishing_recovery),
        )
        inputs.pretreatment_recovery = st.slider(
            "Pretreatment recovery",
            0.5,
            1.0,
            float(inputs.pretreatment_recovery),
        )
        inputs.product_recovery = st.slider(
            "Product recovery",
            0.5,
            1.0,
            float(inputs.product_recovery),
        )
        inputs.thermodynamic_voltage_V = st.number_input(
            "Thermodynamic voltage (V)",
            value=float(inputs.thermodynamic_voltage_V),
        )
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
        inputs.years_on_stream = st.number_input(
            "Years on stream",
            value=float(inputs.years_on_stream),
        )
        inputs.uptime_fraction = st.slider(
            "Uptime fraction",
            0.5,
            1.0,
            float(inputs.uptime_fraction),
        )
        inputs.purge_fraction = st.slider(
            "Purge fraction",
            0.0,
            0.5,
            float(inputs.purge_fraction),
        )

results = run_model(inputs)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Annual Production", f"{results['annual_tpy']:,.0f} t/y")
c2.metric("SEC", f"{results['sec_kwh_per_kg']:.2f} kWh/kg")
c3.metric("Cell Voltage", f"{results['cell_voltage_V']:.2f} V")
c4.metric("OPEX", f"${results['opex_usd_per_ton']:,.0f}/t")

c5, c6, c7, c8 = st.columns(4)
c5.metric("Active Stacks", f"{results['active_stacks']}")
c6.metric("Total Power", f"{results['power_kW']:,.0f} kW")
c7.metric("Overall Recovery", f"{results['overall_recovery'] * 100:.1f}%")
c8.metric("CAPEX", f"${results['capex_usd'] / 1e6:,.1f}M")

if results["warnings"]:
    st.warning("Engineering warnings:\n\n- " + "\n- ".join(results["warnings"]))

if results["limiters"]:
    st.info("What is limiting production:\n\n- " + "\n- ".join(results["limiters"]))

st.subheader("Voltage Breakdown")
voltage_df = pd.DataFrame(
    {
        "Component": ["Ohmic", "Activation", "Concentration"],
        "Voltage (V)": [
            results["voltage_parts"]["v_ohmic"],
            results["voltage_parts"]["v_activation"],
            results["voltage_parts"]["v_concentration"],
        ],
    }
)

fig, ax = plt.subplots(figsize=(7, 4))
ax.bar(voltage_df["Component"], voltage_df["Voltage (V)"])
ax.set_ylabel("Voltage (V)")
ax.set_title("Cell Voltage Contributions")
st.pyplot(fig)

st.subheader("Mass Balance Snapshot")
mb_df = pd.DataFrame(
    [
        {
            "Stream": "Feed",
            "Flow (m3/h)": results["feed"].get("flow_m3h"),
            "Li (kg/h)": results["feed"].get("Li_kgph"),
            "Mg (kg/h)": results["feed"].get("Mg_kgph"),
            "Na (kg/h)": results["feed"].get("Na_kgph"),
            "K (kg/h)": results["feed"].get("K_kgph"),
            "Ca (kg/h)": results["feed"].get("Ca_kgph"),
        },
        {
            "Stream": "Pretreated",
            "Flow (m3/h)": results["pretreated"].get("flow_m3h"),
            "Li (kg/h)": results["pretreated"].get("Li_kgph"),
            "Mg (kg/h)": results["pretreated"].get("Mg_kgph"),
            "Na (kg/h)": results["pretreated"].get("Na_kgph"),
            "K (kg/h)": results["pretreated"].get("K_kgph"),
            "Ca (kg/h)": results["pretreated"].get("Ca_kgph"),
        },
        {
            "Stream": "Stack Product Path",
            "Flow (m3/h)": None,
            "Li (kg/h)": results["stack_out"].get("Li_kgph_to_product_path"),
            "Mg (kg/h)": results["stack_out"].get("Mg_kgph"),
            "Na (kg/h)": results["stack_out"].get("Na_kgph"),
            "K (kg/h)": results["stack_out"].get("K_kgph"),
            "Ca (kg/h)": results["stack_out"].get("Ca_kgph"),
        },
        {
            "Stream": "Recycle",
            "Flow (m3/h)": None,
            "Li (kg/h)": results["product"].get("Li_kgph_recycle"),
            "Mg (kg/h)": None,
            "Na (kg/h)": None,
            "K (kg/h)": None,
            "Ca (kg/h)": None,
        },
        {
            "Stream": "Purge Loss",
            "Flow (m3/h)": None,
            "Li (kg/h)": results["product"].get("Li_kgph_purge_loss"),
            "Mg (kg/h)": None,
            "Na (kg/h)": None,
            "K (kg/h)": None,
            "Ca (kg/h)": None,
        },
        {
            "Stream": "Final Product Path",
            "Flow (m3/h)": None,
            "Li (kg/h)": results["product"].get("Li_kgph_product"),
            "Mg (kg/h)": results["product"].get("Mg_kgph_polished"),
            "Na (kg/h)": None,
            "K (kg/h)": None,
            "Ca (kg/h)": None,
        },
    ]
)
st.dataframe(mb_df, use_container_width=True)

csv = mb_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download mass balance CSV",
    data=csv,
    file_name="monolith_mass_balance.csv",
    mime="text/csv",
)

st.subheader("Sensitivity Analysis")

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("**SEC and Production vs Current Density**")
    j_values = np.linspace(50, max(60, inputs.limiting_current_density_A_m2 * 0.95), 20)
    sec_vals = []
    prod_vals = []

    for j in j_values:
        test_inputs = copy.deepcopy(inputs)
        test_inputs.current_density_A_m2 = float(j)
        r = run_model(test_inputs)
        sec_vals.append(r["sec_kwh_per_kg"])
        prod_vals.append(r["annual_tpy"])

    fig1, ax1 = plt.subplots(figsize=(7, 4))
    ax1.plot(j_values, sec_vals)
    ax1.set_xlabel("Current Density (A/m²)")
    ax1.set_ylabel("SEC (kWh/kg)")
    ax1.set_title("SEC vs Current Density")
    st.pyplot(fig1)

    fig2, ax2 = plt.subplots(figsize=(7, 4))
    ax2.plot(j_values, prod_vals)
    ax2.set_xlabel("Current Density (A/m²)")
    ax2.set_ylabel("Annual Production (t/y)")
    ax2.set_title("Production vs Current Density")
    st.pyplot(fig2)

with col_b:
    st.markdown("**OPEX vs Electricity Price**")
    power_values = np.linspace(10, 120, 20)
    opex_vals = []

    for p in power_values:
        test_inputs = copy.deepcopy(inputs)
        test_inputs.electricity_price_per_MWh = float(p)
        r = run_model(test_inputs)
        opex_vals.append(r["opex_usd_per_ton"])

    fig3, ax3 = plt.subplots(figsize=(7, 4))
    ax3.plot(power_values, opex_vals)
    ax3.set_xlabel("Electricity Price ($/MWh)")
    ax3.set_ylabel("OPEX ($/t)")
    ax3.set_title("OPEX vs Electricity Price")
    st.pyplot(fig3)
