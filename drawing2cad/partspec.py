from pydantic import BaseModel
from typing import Literal


class Hole(BaseModel):
    x: float                      # center X, mm, from profile origin (bottom-left)
    y: float                      # center Y, mm
    diameter: float
    through: bool = True
    depth: float | None = None    # for blind holes


class Dimension(BaseModel):
    name: str
    nominal: float
    tol_plus: float = 0.5
    tol_minus: float = 0.5


class PartSpec(BaseModel):
    units: Literal["mm", "in"] = "mm"
    profile_kind: Literal["rectangle", "polygon"] = "rectangle"
    width: float | None = None
    height: float | None = None
    polygon: list[tuple[float, float]] | None = None
    thickness: float
    holes: list[Hole] = []
    fillets: list[float] = []
    chamfers: list[float] = []
    dimensions: list[Dimension] = []
    notes: str | None = None
