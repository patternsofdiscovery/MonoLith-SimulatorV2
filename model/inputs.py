from dataclasses import dataclass


@dataclass
class PlantInputs:
    # Feed
    feed_flow_m3h: float
    feed_li_gL: float
    feed_mg_gL: float
    feed_na_gL: float
    feed_k_gL: float
    feed_ca_gL: float

    # Electrochemistry
    current_density_A_m2: float
    electrode_area_m2_per_stack: float
    installed_stacks: int
    active_stack_fraction: float
    faradaic_efficiency: float
    stack_recovery: float
    polishing_recovery: float
    pretreatment_recovery: float
    product_recovery: float

    # Voltage model
    thermodynamic_voltage_V: float
    area_specific_resistance_ohm_m2: float
    limiting_current_density_A_m2: float
    activation_coeff_V: float

    # Operations
    uptime_fraction: float
    purge_fraction: float
    recycle_ratio: float

    # Degradation
    years_on_stream: float
    asr_growth_per_year: float
    fe_fade_per_year: float
    stack_replacement_interval_years: float

    # Economics
    electricity_price_per_MWh: float
    stack_replacement_cost_per_stack_per_year: float
    fixed_opex_per_year: float
    capex_base_usd: float
    capex_reference_tpy: float
    capex_scaling_exponent: float
