from model.inputs import PlantInputs


def base_pilot() -> PlantInputs:
    return PlantInputs(
        feed_flow_m3h=15.0,
        feed_li_gL=1.5,
        feed_mg_gL=0.2,
        feed_na_gL=3.0,
        feed_k_gL=0.5,
        feed_ca_gL=0.1,
        current_density_A_m2=250.0,
        electrode_area_m2_per_stack=8.0,
        installed_stacks=120,
        active_stack_fraction=0.90,
        faradaic_efficiency=0.92,
        stack_recovery=0.93,
        polishing_recovery=0.97,
        pretreatment_recovery=0.98,
        product_recovery=0.985,
        thermodynamic_voltage_V=2.2,
        area_specific_resistance_ohm_m2=0.002,
        limiting_current_density_A_m2=500.0,
        activation_coeff_V=0.02,
        uptime_fraction=0.90,
        purge_fraction=0.05,
        recycle_ratio=0.30,
        years_on_stream=0.0,
        asr_growth_per_year=0.03,
        fe_fade_per_year=0.01,
        stack_replacement_interval_years=3.0,
        electricity_price_per_MWh=40.0,
        stack_replacement_cost_per_stack_per_year=2500.0,
        fixed_opex_per_year=1_500_000.0,
        capex_base_usd=18_000_000.0,
        capex_reference_tpy=2000.0,
        capex_scaling_exponent=0.68,
    )


def dirty_brine() -> PlantInputs:
    x = base_pilot()
    x.feed_mg_gL = 0.8
    x.feed_ca_gL = 0.3
    x.stack_recovery = 0.89
    return x


def degraded_stack_case() -> PlantInputs:
    x = base_pilot()
    x.years_on_stream = 2.0
    x.active_stack_fraction = 0.82
    return x


SCENARIOS = {
    "Base Pilot": base_pilot,
    "Dirty Brine": dirty_brine,
    "Degraded Stack": degraded_stack_case,
}
