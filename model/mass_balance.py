def stream_mass_kg_per_h(flow_m3h: float, concentration_gL: float) -> float:
    # 1 m3 = 1000 L ; g/L * 1000 L = g ; /1000 = kg
    return flow_m3h * concentration_gL


def build_feed_stream(inputs) -> dict:
    return {
        "flow_m3h": inputs.feed_flow_m3h,
        "Li_kgph": stream_mass_kg_per_h(inputs.feed_flow_m3h, inputs.feed_li_gL),
        "Mg_kgph": stream_mass_kg_per_h(inputs.feed_flow_m3h, inputs.feed_mg_gL),
        "Na_kgph": stream_mass_kg_per_h(inputs.feed_flow_m3h, inputs.feed_na_gL),
        "K_kgph": stream_mass_kg_per_h(inputs.feed_flow_m3h, inputs.feed_k_gL),
        "Ca_kgph": stream_mass_kg_per_h(inputs.feed_flow_m3h, inputs.feed_ca_gL),
    }


def run_pretreatment(feed: dict, li_recovery: float = 0.98, mg_removal: float = 0.85, ca_removal: float = 0.80) -> dict:
    out = dict(feed)
    out["Li_kgph"] = feed["Li_kgph"] * li_recovery
    out["Mg_kgph"] = feed["Mg_kgph"] * (1.0 - mg_removal)
    out["Ca_kgph"] = feed["Ca_kgph"] * (1.0 - ca_removal)
    return out


def run_stack_section(pretreated: dict, stack_recovery: float) -> dict:
    out = dict(pretreated)
    li_to_product_path = pretreated["Li_kgph"] * stack_recovery
    li_to_recycle = pretreated["Li_kgph"] - li_to_product_path

    out["Li_kgph_to_product_path"] = li_to_product_path
    out["Li_kgph_to_recycle"] = li_to_recycle
    return out


def run_polishing(stack_out: dict, polishing_recovery: float, mg_polish_removal: float = 0.80) -> dict:
    out = dict(stack_out)
    out["Li_kgph_polished"] = stack_out["Li_kgph_to_product_path"] * polishing_recovery
    out["Mg_kgph_polished"] = stack_out["Mg_kgph"] * (1.0 - mg_polish_removal)
    return out


def run_product_step(polished: dict, product_recovery: float, purge_fraction: float) -> dict:
    out = dict(polished)
    out["Li_kgph_product"] = polished["Li_kgph_polished"] * product_recovery
    out["Li_kgph_purge_loss"] = polished["Li_kgph_to_recycle"] * purge_fraction
    out["Li_kgph_recycle"] = polished["Li_kgph_to_recycle"] * (1.0 - purge_fraction)
    return out


def overall_recovery(inputs) -> float:
    return (
        inputs.pretreatment_recovery
        * inputs.stack_recovery
        * inputs.polishing_recovery
        * inputs.product_recovery
    )
