import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from model.scenarios import SCENARIOS
from model.results import run_model

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
        inputs.area_specific_resistance_ohm_m2 = st.number_input("ASR (ohm·m²)", value=float(inputs.area_specific_resistance_ohm_m2), format="%.5f")
        inputs.limiting_current_density_A_m2 = st.number_input("Limiting current density (A/m²)", value=float(inputs.limiting_current_density_A_m2))
        inputs.activation_coeff_V = st.number_input("Activation coeff (V)", value=float(inputs.activation_coeff_V), format="%.4f")
        inputs.years_on_stream = st.number_input("Years on stream", value=float(inputs.years_on_stream))
        inputs.uptime_fraction = st.slider("Uptime fraction", 0.5, 1.0, float(inputs.uptime_fraction))
        inputs.purge_fraction = st.slider("Purge fraction", 0.0, 0.5, float(inputs.purge_fraction))

results = run_model(inputs)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Annual Production", f"{results['annual_tpy']:,.0f} t/y")
c2.metric("SEC", f"{results['sec_kwh_per_kg']:.2f} kWh/kg")
c3.metric("Cell Voltage", f"{results['cell_voltage_V']:.2f} V")
c4.metric("OPEX", f"${results['opex_usd_per_ton']:,.0f}/t")

c5, c6, c7, c8 = st.columns(4)
c5.metric("Active Stacks", f"{results['active_stacks']}")
c6.metric("Total Power", f"{results['power_kW']:,.0f} kW")
c7.metric("Overall Recovery", f"{results['overall_recovery']*100:.1f}%")
c8.metric("CAPEX", f"${results['capex_usd']/1e6:,.1f}M")

if results["warnings"]:
    st.warning("Engineering warnings:\n\n- " + "\n- ".join(results["warnings"]))

st.subheader("Voltage Breakdown")
voltage_df = pd.DataFrame({
    "Component": ["Ohmic", "Activation", "Concentration"],
    "Voltage (V)": [
        results["voltage_parts"]["v_ohmic"],
        results["voltage_parts"]["v_activation"],
        results["voltage_parts"]["v_concentration"],
    ]
})

fig, ax = plt.subplots(figsize=(7, 4))
ax.bar(voltage_df["Component"], voltage_df["Voltage (V)"])
ax.set_ylabel("Voltage (V)")
ax.set_title("Cell Voltage Contributions")
st.pyplot(fig)

st.subheader("Mass Balance Snapshot")
mb_df = pd.DataFrame([
    {
        "Stream": "Feed",
        "Li (kg/h)": results["feed"]["Li_kgph"],
        "Mg (kg/h)": results["feed"]["Mg_kgph"],
        "Na (kg/h)": results["feed"]["Na_kgph"],
        "Ca (kg/h)": results["feed"]["Ca_kgph"],
    },
    {
        "Stream": "Pretreated",
        "Li (kg/h)": results["pretreated"]["Li_kgph"],
        "Mg (kg/h)": results["pretreated"]["Mg_kgph"],
        "Na (kg/h)": results["pretreated"]["Na_kgph"],
        "Ca (kg/h)": results["pretreated"]["Ca_kgph"],
    },
    {
        "Stream": "Product Path",
        "Li (kg/h)": results["product"]["Li_kgph_product"],
        "Mg (kg/h)": results["product"]["Mg_kgph_polished"],
        "Na (kg/h)": None,
        "Ca (kg/h)": None,
    },
])
st.dataframe(mb_df, use_container_width=True)

csv = mb_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download mass balance CSV",
    data=csv,
    file_name="monolith_mass_balance.csv",
    mime="text/csv",
)
