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
)
from model.economics import (
    annual_production_tpy,
    annual_electricity_cost_usd,
    annual_stack_replacement_cost_usd,
    scaled_capex_usd,
    total_annual_opex_usd,
    opex_per_ton_usd,
)


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
    pretreated = run_pretreatment(
        feed,
        li_recovery=inputs.pretreatment_recovery,
        mg_removal=0.85,
        ca_removal=0.80,
    )
    stack_out = run_stack_section(pretreated, inputs.stack_recovery)
    polished = run_polishing(stack_out, inputs.polishing_recovery)
    product = run_product_step(polished, inputs.product_recovery, inputs.purge_fraction)

    li_path_limited_product_kgph = product["Li_kgph_product"] * (41.96 / 6.94)
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

    li_feed_kgph = feed["Li_kgph"]
    li_after_pretreatment_kgph = pretreated["Li_kgph"]
    li_pretreatment_loss_kgph = max(li_feed_kgph - li_after_pretreatment_kgph, 0.0)
    li_stack_to_recycle_kgph = stack_out["Li_kgph_to_recycle"]
    li_purge_loss_kgph = product["Li_kgph_purge_loss"]
    li_product_kgph = product["Li_kgph_product"]
    li_polish_and_product_loss_kgph = max(
        stack_out["Li_kgph_to_product_path"] - li_product_kgph,
        0.0,
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
        "feed": feed,
        "pretreated": pretreated,
        "stack_out": stack_out,
        "polished": polished,
        "product": product,
        "warnings": warnings,
        "limiters": limiters,
    }
