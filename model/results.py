from model.electrochem import (
    active_stacks,
    current_per_stack,
    total_current_A,
    degraded_asr,
    degraded_faradaic_efficiency,
    cell_voltage_V,
    lioh_monohydrate_kg_per_h,
    power_kW,
)
from model.mass_balance import (
    build_feed_stream,
    run_pretreatment,
    run_stack_section,
    run_polishing,
    run_product_step,
    overall_recovery,
    lithium_balance_summary,
    stream_table,
)
from model.economics import (
    annual_production_tpy,
    annual_electricity_cost_usd,
    annual_stack_replacement_cost_usd,
    scaled_capex_usd,
    total_annual_opex_usd,
    opex_per_ton_usd,
)


def build_assumptions_table(inputs) -> list[dict]:
    return [
        {"Parameter": "Feed flow", "Value": inputs.feed_flow_m3h, "Units": "m3/h"},
        {"Parameter": "Feed Li", "Value": inputs.feed_li_gL, "Units": "g/L"},
        {"Parameter": "Feed Mg", "Value": inputs.feed_mg_gL, "Units": "g/L"},
        {"Parameter": "Feed Na", "Value": inputs.feed_na_gL, "Units": "g/L"},
        {"Parameter": "Feed K", "Value": inputs.feed_k_gL, "Units": "g/L"},
        {"Parameter": "Feed Ca", "Value": inputs.feed_ca_gL, "Units": "g/L"},
        {"Parameter": "Current density", "Value": inputs.current_density_A_m2, "Units": "A/m2"},
        {"Parameter": "Electrode area per stack", "Value": inputs.electrode_area_m2_per_stack, "Units": "m2/stack"},
        {"Parameter": "Installed stacks", "Value": inputs.installed_stacks, "Units": "count"},
        {"Parameter": "Active stack fraction", "Value": inputs.active_stack_fraction, "Units": "fraction"},
        {"Parameter": "Faradaic efficiency", "Value": inputs.faradaic_efficiency, "Units": "fraction"},
        {"Parameter": "Pretreatment recovery", "Value": inputs.pretreatment_recovery, "Units": "fraction"},
        {"Parameter": "Stack recovery", "Value": inputs.stack_recovery, "Units": "fraction"},
        {"Parameter": "Polishing recovery", "Value": inputs.polishing_recovery, "Units": "fraction"},
        {"Parameter": "Product recovery", "Value": inputs.product_recovery, "Units": "fraction"},
        {"Parameter": "Thermodynamic voltage", "Value": inputs.thermodynamic_voltage_V, "Units": "V"},
        {"Parameter": "ASR", "Value": inputs.area_specific_resistance_ohm_m2, "Units": "ohm·m2"},
        {"Parameter": "Limiting current density", "Value": inputs.limiting_current_density_A_m2, "Units": "A/m2"},
        {"Parameter": "Activation coefficient", "Value": inputs.activation_coeff_V, "Units": "V"},
        {"Parameter": "Uptime", "Value": inputs.uptime_fraction, "Units": "fraction"},
        {"Parameter": "Purge fraction", "Value": inputs.purge_fraction, "Units": "fraction"},
        {"Parameter": "Years on stream", "Value": inputs.years_on_stream, "Units": "years"},
        {"Parameter": "ASR growth / year", "Value": inputs.asr_growth_per_year, "Units": "fraction/year"},
        {"Parameter": "FE fade / year", "Value": inputs.fe_fade_per_year, "Units": "fraction/year"},
        {"Parameter": "Electricity price", "Value": inputs.electricity_price_per_MWh, "Units": "$/MWh"},
        {"Parameter": "Stack replacement cost", "Value": inputs.stack_replacement_cost_per_stack_per_year, "Units": "$/stack-year"},
        {"Parameter": "Fixed OPEX", "Value": inputs.fixed_opex_per_year, "Units": "$/year"},
        {"Parameter": "Base CAPEX", "Value": inputs.capex_base_usd, "Units": "$"},
        {"Parameter": "Reference CAPEX capacity", "Value": inputs.capex_reference_tpy, "Units": "t/y"},
        {"Parameter": "CAPEX scaling exponent", "Value": inputs.capex_scaling_exponent, "Units": "-"},
    ]


def run_model(inputs):
    n_active = active_stacks(inputs.installed_stacks, inputs.active_stack_fraction)

    eff_asr = degraded_asr(
        inputs.area_specific_resistance_ohm_m2,
        inputs.years_on_stream,
        inputs.asr_growth_per_year,
    )
    eff_fe = degraded_faradaic_efficiency(
        inputs.faradaic_efficiency,
        inputs.years_on_stream,
        inputs.fe_fade_per_year,
    )

    stack_current_A = current_per_stack(
        inputs.current_density_A_m2,
        inputs.electrode_area_m2_per_stack,
    )

    total_current = total_current_A(
        inputs.current_density_A_m2,
        inputs.electrode_area_m2_per_stack,
        inputs.installed_stacks,
        inputs.active_stack_fraction,
    )

    voltage_parts = cell_voltage_V(
        current_density_A_m2=inputs.current_density_A_m2,
        limiting_current_density_A_m2=inputs.limiting_current_density_A_m2,
        thermodynamic_voltage_V=inputs.thermodynamic_voltage_V,
        activation_coeff_V=inputs.activation_coeff_V,
        total_current_A=total_current,
        area_specific_resistance_ohm_m2=eff_asr,
        electrode_area_m2_per_stack=inputs.electrode_area_m2_per_stack,
    )

    electrochem_product_kgph = lioh_monohydrate_kg_per_h(total_current, eff_fe)
    total_power_kW = power_kW(total_current, voltage_parts["v_cell"])
    power_per_stack_kW = total_power_kW / max(n_active, 1)

    feed = build_feed_stream(inputs)
    pretreated, pretreat_removed = run_pretreatment(
        feed,
        li_recovery=inputs.pretreatment_recovery,
        mg_removal=0.85,
        ca_removal=0.80,
    )
    stack_product_path, recycle_path = run_stack_section(pretreated, inputs.stack_recovery)
    polished, polish_removed = run_polishing(stack_product_path, inputs.polishing_recovery)
    product_stream, recycle_stream, purge_stream, product_removed = run_product_step(
        polished,
        recycle_path,
        inputs.product_recovery,
        inputs.purge_fraction,
    )

    li_path_limited_product_kgph = product_stream.Li_kgph * (41.96 / 6.94)
    final_product_kgph = min(electrochem_product_kgph, li_path_limited_product_kgph)

    annual_tpy = annual_production_tpy(final_product_kgph, inputs.uptime_fraction)
    electricity_cost = annual_electricity_cost_usd(
        total_power_kW,
        inputs.electricity_price_per_MWh,
        inputs.uptime_fraction,
    )
    replacement_cost = annual_stack_replacement_cost_usd(
        inputs.installed_stacks,
        inputs.stack_replacement_cost_per_stack_per_year,
    )
    annual_opex = total_annual_opex_usd(
        electricity_cost,
        replacement_cost,
        inputs.fixed_opex_per_year,
    )
    capex = scaled_capex_usd(
        inputs.capex_base_usd,
        annual_tpy,
        inputs.capex_reference_tpy,
        inputs.capex_scaling_exponent,
    )

    sec_kwh_per_kg = total_power_kW / max(final_product_kgph, 1e-6)
    opex_ton = opex_per_ton_usd(annual_opex, annual_tpy)
    electricity_cost_per_ton = electricity_cost / max(annual_tpy, 1e-6)
    replacement_cost_per_ton = replacement_cost / max(annual_tpy, 1e-6)
    fixed_opex_per_ton = inputs.fixed_opex_per_year / max(annual_tpy, 1e-6)

    flow_per_active_stack_m3h = inputs.feed_flow_m3h / max(n_active, 1)
    total_electrode_area_m2 = inputs.electrode_area_m2_per_stack * n_active
    brine_m3_per_ton_product = (
        inputs.feed_flow_m3h * 8760.0 * inputs.uptime_fraction / max(annual_tpy, 1e-6)
    )

    li_feed_kgph = feed.Li_kgph
    li_after_pretreatment_kgph = pretreated.Li_kgph
    li_pretreatment_loss_kgph = pretreat_removed["Li_loss_kgph"]
    li_stack_to_recycle_kgph = recycle_path.Li_kgph
    li_purge_loss_kgph = purge_stream.Li_kgph
    li_product_kgph = product_stream.Li_kgph
    li_polish_and_product_loss_kgph = (
        polish_removed["Li_loss_kgph"] + product_removed["Li_loss_kgph"]
    )

    balance = lithium_balance_summary(
        feed=feed,
        product_stream=product_stream,
        recycle_stream=recycle_stream,
        purge_stream=purge_stream,
        pretreatment_losses=pretreat_removed,
        polishing_losses=polish_removed,
        product_losses=product_removed,
    )

    warnings = []
    if inputs.current_density_A_m2 > 0.8 * inputs.limiting_current_density_A_m2:
        warnings.append("Current density is close to the limiting current density.")
    if voltage_parts["v_cell"] > 5.0:
        warnings.append("Cell voltage is high; energy consumption may be unrealistic.")
    if sec_kwh_per_kg > 20.0:
        warnings.append("Specific energy consumption is high.")
    if inputs.feed_mg_gL > 0.5:
        warnings.append("Feed magnesium is high; pretreatment/polishing burden may be significant.")
    if inputs.active_stack_fraction < 0.75:
        warnings.append("Low active stack fraction may create availability bottlenecks.")
    if inputs.feed_li_gL < 0.5:
        warnings.append("Feed lithium concentration is very low; economics may be unfavorable.")
    if inputs.purge_fraction > 0.15:
        warnings.append("High purge fraction may be causing unnecessary lithium loss.")
    if inputs.faradaic_efficiency < 0.80:
        warnings.append("Faradaic efficiency is low; stack performance may be poor.")
    if inputs.stack_recovery < 0.85:
        warnings.append("Stack recovery is low and may be constraining product output.")
    if inputs.uptime_fraction < 0.85:
        warnings.append("Plant uptime is low for a commercial-style operating target.")
    if abs(balance["li_balance_error_pct"]) > 0.5:
        warnings.append("Lithium mass-balance error exceeds 0.5%; review assumptions and stream logic.")

    limiters = []
    if abs(final_product_kgph - electrochem_product_kgph) < 1e-9:
        limiters.append("Electrochemical stack capacity is limiting production.")
    if abs(final_product_kgph - li_path_limited_product_kgph) < 1e-9:
        limiters.append("Lithium availability through the process path is limiting production.")
    if inputs.active_stack_fraction < 0.90:
        limiters.append("Stack availability is reducing practical plant output.")
    if inputs.uptime_fraction < 0.95:
        limiters.append("Plant uptime is reducing annual production.")
    if inputs.feed_li_gL < 1.0:
        limiters.append("Low feed lithium concentration may be constraining throughput and economics.")

    streams = [
        feed,
        pretreated,
        stack_product_path,
        recycle_path,
        polished,
        product_stream,
        recycle_stream,
        purge_stream,
    ]

    return {
        "active_stacks": n_active,
        "effective_asr": eff_asr,
        "effective_fe": eff_fe,
        "stack_current_A": stack_current_A,
        "total_current_A": total_current,
        "cell_voltage_V": voltage_parts["v_cell"],
        "voltage_parts": voltage_parts,
        "power_kW": total_power_kW,
        "power_per_stack_kW": power_per_stack_kW,
        "electrochem_product_kgph": electrochem_product_kgph,
        "li_path_limited_product_kgph": li_path_limited_product_kgph,
        "final_product_kgph": final_product_kgph,
        "annual_tpy": annual_tpy,
        "sec_kwh_per_kg": sec_kwh_per_kg,
        "electricity_cost_usd_per_year": electricity_cost,
        "replacement_cost_usd_per_year": replacement_cost,
        "annual_opex_usd": annual_opex,
        "opex_usd_per_ton": opex_ton,
        "electricity_cost_per_ton": electricity_cost_per_ton,
        "replacement_cost_per_ton": replacement_cost_per_ton,
        "fixed_opex_per_ton": fixed_opex_per_ton,
        "capex_usd": capex,
        "overall_recovery": overall_recovery(inputs),
        "flow_per_active_stack_m3h": flow_per_active_stack_m3h,
        "total_electrode_area_m2": total_electrode_area_m2,
        "brine_m3_per_ton_product": brine_m3_per_ton_product,
        "li_feed_kgph": li_feed_kgph,
        "li_after_pretreatment_kgph": li_after_pretreatment_kgph,
        "li_pretreatment_loss_kgph": li_pretreatment_loss_kgph,
        "li_stack_to_recycle_kgph": li_stack_to_recycle_kgph,
        "li_purge_loss_kgph": li_purge_loss_kgph,
        "li_product_kgph": li_product_kgph,
        "li_polish_and_product_loss_kgph": li_polish_and_product_loss_kgph,
        "feed": feed.to_dict(),
        "pretreated": pretreated.to_dict(),
        "stack_product_path": stack_product_path.to_dict(),
        "recycle_path": recycle_path.to_dict(),
        "polished": polished.to_dict(),
        "product_stream": product_stream.to_dict(),
        "recycle_stream": recycle_stream.to_dict(),
        "purge_stream": purge_stream.to_dict(),
        "stream_table": stream_table(streams),
        "balance": balance,
        "assumptions_table": build_assumptions_table(inputs),
        "warnings": warnings,
        "limiters": limiters,
    }
