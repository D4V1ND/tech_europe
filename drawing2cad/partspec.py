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
    profile_kind: Literal["rectangle"] = "rectangle"   # polygons out of scope
    width: float | None = None
    height: float | None = None
    thickness: float
    holes: list[Hole] = []
    fillets: list[float] = []
    chamfers: list[float] = []
    dimensions: list[Dimension] = []
    notes: str | None = None

    def sanity_check(self) -> list[str]:
        """Plausibility checks on the spec itself, run BEFORE code generation.
        Catches bad extractions that would otherwise build a 'valid' wrong part."""
        errs: list[str] = []
        if not self.width or not self.height:
            errs.append("rectangle profile missing width/height")
            return errs                          # nothing else is checkable
        for i, h in enumerate(self.holes):
            if not (0 < h.x < self.width and 0 < h.y < self.height):
                errs.append(f"hole{i} center ({h.x},{h.y}) outside profile")
            if h.diameter >= min(self.width, self.height):
                errs.append(f"hole{i} diameter {h.diameter} >= part size")
        for r in self.fillets:
            if r >= min(self.width, self.height) / 2:
                errs.append(f"fillet r={r} too large for profile")
        return errs
