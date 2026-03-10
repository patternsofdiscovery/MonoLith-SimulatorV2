from dataclasses import dataclass, asdict


@dataclass
class Stream:
    name: str
    flow_m3h: float
    Li_kgph: float = 0.0
    Mg_kgph: float = 0.0
    Na_kgph: float = 0.0
    K_kgph: float = 0.0
    Ca_kgph: float = 0.0
    water_kgph: float = 0.0

    def copy(self, name: str | None = None):
        data = asdict(self)
        if name is not None:
            data["name"] = name
        return Stream(**data)

    def to_dict(self) -> dict:
        return asdict(self)
