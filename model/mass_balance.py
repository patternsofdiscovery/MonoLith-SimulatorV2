"""
Mass balance module for MONOLiTH simulator.

Defines major process streams and simplified unit operations:

Feed → Pretreatment → Electrochemical Stack → Polishing → Product

Tracks lithium, key impurities, recycle, and purge.
"""

from model.streams import Stream


WATER_DENSITY_KG_PER_M3 = 1000.0


def stream_mass_kg_per_h(flow_m3h: float, concentration_gL: float) -> float:
    """
    Convert concentration (g/L) and flow (m3/h) to kg/h.
    """
    return flow_m3h * concentration_gL


def estimate_water_kgph(flow_m3h: float) -> float:
    """
    Approximate bulk water mass flow from volumetric flow.
    """
    return flow_m3h * WATER_DENSITY_KG_PER_M3


def build_feed_stream(inputs) -> Stream:
    """
    Build the raw feed stream from user inputs.
    """
    return Stream(
        name="Feed",
        flow_m3h=inputs.feed_flow_m3h,
        Li_kgph=stream_mass_kg_per_h(inputs.feed_flow_m3h, inputs.feed_li_gL),
        Mg_kgph=stream_mass_kg_per_h(inputs.feed_flow_m3h, inputs.feed_mg_gL),
        Na_kgph=stream_mass_kg_per_h(inputs.feed_flow_m3h, inputs.feed_na_gL),
        K_kgph=stream_mass_kg_per_h(inputs.feed_flow_m3h, inputs.feed_k_gL),
        Ca_kgph=stream_mass_kg_per_h(inputs.feed_flow_m3h, inputs.feed_ca_gL),
        water_kgph=estimate_water_kgph(inputs.feed_flow_m3h),
    )


def run_pretreatment(
    feed: Stream,
    li_recovery: float = 0.98,
    mg_removal: float = 0.85,
    ca_removal: float = 0.80,
) -> tuple[Stream, dict]:
    """
    Pretreatment removes multivalent impurities and loses a small amount of lithium.
    """
    out = feed.copy(name="Pretreated")
    out.Li_kgph = feed.Li_kgph * li_recovery
    out.Mg_kgph = feed.Mg_kgph * (1.0 - mg_removal)
    out.Ca_kgph = feed.Ca_kgph * (1.0 - ca_removal)

    removed = {
        "Li_loss_kgph": max(feed.Li_kgph - out.Li_kgph, 0.0),
        "Mg_removed_kgph": max(feed.Mg_kgph - out.Mg_kgph, 0.0),
        "Ca_removed_kgph": max(feed.Ca_kgph - out.Ca_kgph, 0.0),
    }
    return out, removed


def run_stack_section(pretreated: Stream, stack_recovery: float) -> tuple[Stream, Stream]:
    """
    Split lithium into product-path and recycle-path streams.
    Non-lithium species are retained on the product-path stream for this simplified model.
    """
    product_path = pretreated.copy(name="Stack Product Path")
    recycle_path = pretreated.copy(name="Stack Recycle Path")

    li_to_product = pretreated.Li_kgph * stack_recovery
    li_to_recycle = pretreated.Li_kgph - li_to_product

    product_path.Li_kgph = li_to_product
    recycle_path.Li_kgph = li_to_recycle

    # Simplified flow split using recycle ratio assumption from Li split
    total_li = max(pretreated.Li_kgph, 1e-9)
    frac_product = li_to_product / total_li
    frac_recycle = li_to_recycle / total_li

    product_path.flow_m3h = pretreated.flow_m3h * frac_product
    recycle_path.flow_m3h = pretreated.flow_m3h * frac_recycle

    product_path.water_kgph = pretreated.water_kgph * frac_product
    recycle_path.water_kgph = pretreated.water_kgph * frac_recycle

    # In this simplified model impurities mostly remain with the product-path liquid,
    # while recycle stream is treated as lithium-rich recycle only.
    recycle_path.Mg_kgph = 0.0
    recycle_path.Na_kgph = 0.0
    recycle_path.K_kgph = 0.0
    recycle_path.Ca_kgph = 0.0

    return product_path, recycle_path


def run_polishing(
    stack_product_path: Stream,
    polishing_recovery: float,
    mg_polish_removal: float = 0.80,
) -> tuple[Stream, dict]:
    """
    Polishing removes remaining impurities and loses a small amount of lithium.
    """
    out = stack_product_path.copy(name="Polished")
    out.Li_kgph = stack_product_path.Li_kgph * polishing_recovery
    out.Mg_kgph = stack_product_path.Mg_kgph * (1.0 - mg_polish_removal)

    removed = {
        "Li_loss_kgph": max(stack_product_path.Li_kgph - out.Li_kgph, 0.0),
        "Mg_removed_kgph": max(stack_product_path.Mg_kgph - out.Mg_kgph, 0.0),
    }
    return out, removed


def run_product_step(
    polished: Stream,
    recycle_path: Stream,
    product_recovery: float,
    purge_fraction: float,
) -> tuple[Stream, Stream, Stream, dict]:
    """
    Final step forms product and defines recycle and purge streams.
    """
    product_stream = polished.copy(name="Final Product Path")
    recycle_stream = recycle_path.copy(name="Recycle")
    purge_stream = recycle_path.copy(name="Purge Loss")

    product_stream.Li_kgph = polished.Li_kgph * product_recovery
    recycle_stream.Li_kgph = recycle_path.Li_kgph * (1.0 - purge_fraction)
    purge_stream.Li_kgph = recycle_path.Li_kgph * purge_fraction

    # For clarity, product stream is represented as lithium-equivalent in the solution path.
    # Non-lithium species after polishing remain low but are retained here.
    product_stream.Mg_kgph = polished.Mg_kgph

    removed = {
        "Li_loss_kgph": max(polished.Li_kgph - product_stream.Li_kgph, 0.0),
        "Li_purge_loss_kgph": purge_stream.Li_kgph,
    }

    return product_stream, recycle_stream, purge_stream, removed


def overall_recovery(inputs) -> float:
    """
    Overall lithium recovery across all process steps.
    """
    return (
        inputs.pretreatment_recovery
        * inputs.stack_recovery
        * inputs.polishing_recovery
        * inputs.product_recovery
    )


def lithium_balance_summary(
    feed: Stream,
    product_stream: Stream,
    recycle_stream: Stream,
    purge_stream: Stream,
    pretreatment_losses: dict,
    polishing_losses: dict,
    product_losses: dict,
) -> dict:
    """
    Summarize lithium mass balance across the process.
    """
    li_in = feed.Li_kgph
    li_accounted = (
        product_stream.Li_kgph
        + recycle_stream.Li_kgph
        + purge_stream.Li_kgph
        + pretreatment_losses.get("Li_loss_kgph", 0.0)
        + polishing_losses.get("Li_loss_kgph", 0.0)
        + product_losses.get("Li_loss_kgph", 0.0)
    )
    error = li_in - li_accounted
    rel_error_pct = 100.0 * error / max(li_in, 1e-9)

    return {
        "li_in_kgph": li_in,
        "li_accounted_kgph": li_accounted,
        "li_balance_error_kgph": error,
        "li_balance_error_pct": rel_error_pct,
    }


def stream_table(streams: list[Stream]) -> list[dict]:
    """
    Convert streams to table-friendly dictionaries.
    """
    return [s.to_dict() for s in streams]
