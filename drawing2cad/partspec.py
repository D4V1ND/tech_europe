from pydantic import BaseModel
from typing import Literal


class Point(BaseModel):
    """A 2D point on the profile, measured from the bottom-left of the bounding box."""
    x: float
    y: float


class Hole(BaseModel):
    x: float                      # center X, mm, from profile origin (bottom-left)
    y: float                      # center Y, mm
    diameter: float
    through: bool = True
    depth: float | None = None    # for blind holes


class RectCut(BaseModel):
    """An axis-aligned rectangular block subtracted from the part. Models L-steps,
    slots, notches, pockets. Coords share the part frame: origin at the bottom-left-front
    corner, X along width, Y along height, Z along thickness."""
    x: float                      # min corner X (along width)
    y: float                      # min corner Y (along height)
    z: float                      # min corner Z (along thickness)
    dx: float                     # cut size along X
    dy: float                     # cut size along Y
    dz: float                     # cut size along Z


class Dimension(BaseModel):
    name: str
    nominal: float
    tol_plus: float = 0.5
    tol_minus: float = 0.5


class PartSpec(BaseModel):
    units: Literal["mm", "in"] = "mm"
    profile_kind: Literal["rectangle", "circle", "polygon"] = "rectangle"
    width: float | None = None        # rectangle
    height: float | None = None       # rectangle
    diameter: float | None = None     # circle
    profile_points: list[Point] = []  # polygon: ordered outline, bottom-left of bbox at (0,0)
    thickness: float
    holes: list[Hole] = []
    cuts: list[RectCut] = []
    fillets: list[float] = []
    chamfers: list[float] = []
    dimensions: list[Dimension] = []
    notes: str | None = None

    def bbox(self) -> tuple[float, float]:
        """Profile bounding-box (width, height) in the spec's units. A circle's box is
        diameter x diameter; a polygon's spans its points. Used by the checks below and
        the generator."""
        if self.profile_kind == "circle":
            d = self.diameter or 0.0
            return d, d
        if self.profile_kind == "polygon":
            if not self.profile_points:
                return 0.0, 0.0
            xs = [p.x for p in self.profile_points]
            ys = [p.y for p in self.profile_points]
            return max(xs) - min(xs), max(ys) - min(ys)
        return self.width or 0.0, self.height or 0.0

    def sanity_check(self) -> list[str]:
        """Plausibility checks on the spec itself, run BEFORE code generation.
        Catches bad extractions that would otherwise build a 'valid' wrong part."""
        errs: list[str] = []
        if self.profile_kind == "circle":
            if not self.diameter:
                errs.append("circle profile missing diameter")
                return errs
        elif self.profile_kind == "polygon":
            if len(self.profile_points) < 3:
                errs.append("polygon profile needs at least 3 points")
                return errs
        elif not self.width or not self.height:
            errs.append("rectangle profile missing width/height")
            return errs                          # nothing else is checkable
        bw, bh = self.bbox()
        for i, h in enumerate(self.holes):
            if not (0 < h.x < bw and 0 < h.y < bh):
                errs.append(f"hole{i} center ({h.x},{h.y}) outside profile")
            if h.diameter >= min(bw, bh):
                errs.append(f"hole{i} diameter {h.diameter} >= part size")
        for r in self.fillets:
            if r >= min(bw, bh) / 2:
                errs.append(f"fillet r={r} too large for profile")
        return errs
