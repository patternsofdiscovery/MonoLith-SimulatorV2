import math

FARADAY_CONST = 96485.3329  # C/mol
MW_LIOH_H2O = 41.96  # g/mol


def active_stacks(installed_stacks: int, active_stack_fraction: float) -> int:
    return max(1, int(round(installed_stacks * active_stack_fraction)))


def current_per_stack(current_density_A_m2: float, electrode_area_m2_per_stack: float) -> float:
    return current_density_A_m2 * electrode_area_m2_per_stack


def total_current_A(
    current_density_A_m2: float,
    electrode_area_m2_per_stack: float,
    installed_stacks: int,
    active_stack_fraction: float,
) -> float:
    n_active = active_stacks(installed_stacks, active_stack_fraction)
    return current_per_stack(current_density_A_m2, electrode_area_m2_per_stack) * n_active


def degraded_asr(initial_asr: float, years_on_stream: float, asr_growth_per_year: float) -> float:
    return initial_asr * (1.0 + years_on_stream * asr_growth_per_year)


def degraded_faradaic_efficiency(initial_fe: float, years_on_stream: float, fe_fade_per_year: float) -> float:
    return max(0.50, initial_fe * (1.0 - years_on_stream * fe_fade_per_year))


def cell_voltage_V(
    current_density_A_m2: float,
    limiting_current_density_A_m2: float,
    thermodynamic_voltage_V: float,
    activation_coeff_V: float,
    total_current_A: float,
    area_specific_resistance_ohm_m2: float,
    electrode_area_m2_per_stack: float,
) -> dict:
    j = max(current_density_A_m2, 1e-9)
    j_lim = max(limiting_current_density_A_m2, 1e-9)
    area = max(electrode_area_m2_per_stack, 1e-9)

    v_ohmic = total_current_A * area_specific_resistance_ohm_m2 / area
    v_activation = activation_coeff_V * math.log(max(j, 1.0))

    frac = min(j / j_lim, 0.95)
    v_concentration = 0.05 / max(1.0 - frac, 0.05)

    v_cell = thermodynamic_voltage_V + v_ohmic + v_activation + v_concentration

    return {
        "v_ohmic": v_ohmic,
        "v_activation": v_activation,
        "v_concentration": v_concentration,
        "v_cell": v_cell,
    }


def li_mol_per_s(total_current_A: float, faradaic_efficiency: float) -> float:
    return (total_current_A * faradaic_efficiency) / FARADAY_CONST


def lioh_monohydrate_kg_per_h(total_current_A: float, faradaic_efficiency: float) -> float:
    mol_s = li_mol_per_s(total_current_A, faradaic_efficiency)
    return mol_s * MW_LIOH_H2O * 3600.0 / 1000.0


def power_kW(total_current_A: float, cell_voltage_V: float) -> float:
    return total_current_A * cell_voltage_V / 1000.0


def annual_operating_hours(uptime_fraction: float) -> float:
    return 8760.0 * uptime_fraction
