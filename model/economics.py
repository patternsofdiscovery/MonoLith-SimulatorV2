def annual_production_tpy(product_kgph: float, uptime_fraction: float) -> float:
    return product_kgph * 8760.0 * uptime_fraction / 1000.0


def annual_electricity_cost_usd(power_kW: float, electricity_price_per_MWh: float, uptime_fraction: float) -> float:
    annual_MWh = power_kW * 8760.0 * uptime_fraction / 1000.0
    return annual_MWh * electricity_price_per_MWh


def annual_stack_replacement_cost_usd(
    installed_stacks: int,
    replacement_cost_per_stack_per_year: float,
) -> float:
    return installed_stacks * replacement_cost_per_stack_per_year


def scaled_capex_usd(base_usd: float, actual_tpy: float, ref_tpy: float, exponent: float) -> float:
    actual_tpy = max(actual_tpy, 1e-6)
    ref_tpy = max(ref_tpy, 1e-6)
    return base_usd * (actual_tpy / ref_tpy) ** exponent


def total_annual_opex_usd(
    electricity_cost_usd: float,
    stack_replacement_cost_usd: float,
    fixed_opex_per_year: float,
) -> float:
    return electricity_cost_usd + stack_replacement_cost_usd + fixed_opex_per_year


def opex_per_ton_usd(total_annual_opex_usd: float, annual_tpy: float) -> float:
    return total_annual_opex_usd / max(annual_tpy, 1e-6)
