from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator


class Point(BaseModel):
    """A 2D point measured from the bottom-left of a profile bounding box."""

    x: float
    y: float


class ExtrudedGeometry(BaseModel):
    kind: Literal["extruded"] = "extruded"
    profile_kind: Literal["rectangle", "circle", "polygon"] = "rectangle"
    width: float | None = None
    height: float | None = None
    diameter: float | None = None
    profile_points: list[Point] = Field(default_factory=list)
    thickness: float

    def bbox(self) -> tuple[float, float, float]:
        if self.profile_kind == "circle":
            d = self.diameter or 0.0
            return d, d, self.thickness
        if self.profile_kind == "polygon":
            if not self.profile_points:
                return 0.0, 0.0, self.thickness
            xs = [point.x for point in self.profile_points]
            ys = [point.y for point in self.profile_points]
            return max(xs) - min(xs), max(ys) - min(ys), self.thickness
        return self.width or 0.0, self.height or 0.0, self.thickness


class RevolvedSegment(BaseModel):
    """A constant-diameter axial interval in a stepped revolved part."""

    z_start: float
    z_end: float
    outer_diameter: float
    inner_diameter: float = 0.0


class RevolvedGeometry(BaseModel):
    kind: Literal["revolved"] = "revolved"
    axis: Literal["z"] = "z"
    segments: list[RevolvedSegment]

    def bbox(self) -> tuple[float, float, float]:
        if not self.segments:
            return 0.0, 0.0, 0.0
        diameter = max(segment.outer_diameter for segment in self.segments)
        z_min = min(segment.z_start for segment in self.segments)
        z_max = max(segment.z_end for segment in self.segments)
        return diameter, diameter, z_max - z_min


class UnsupportedGeometry(BaseModel):
    kind: Literal["unsupported"] = "unsupported"
    reason: str
    visible_features: list[str] = Field(default_factory=list)


Geometry = Annotated[
    ExtrudedGeometry | RevolvedGeometry | UnsupportedGeometry,
    Field(discriminator="kind"),
]


class Hole(BaseModel):
    """A cylindrical hole positioned in the part bounding-box coordinate frame."""

    id: str | None = None
    x: float
    y: float
    diameter: float
    hole_type: Literal[
        "through", "blind", "counterbore", "countersink", "threaded"
    ] = "through"
    depth: float | None = None
    counterbore_diameter: float | None = None
    counterbore_depth: float | None = None
    countersink_diameter: float | None = None
    countersink_angle: float | None = None
    thread: str | None = None

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_hole(cls, data):
        if not isinstance(data, dict) or "hole_type" in data:
            return data
        migrated = dict(data)
        migrated["hole_type"] = "through" if migrated.pop("through", True) else "blind"
        return migrated

    @property
    def through(self) -> bool:
        return self.hole_type == "through"


class RectCut(BaseModel):
    """An axis-aligned rectangular block subtracted from an extruded part.

    corner_radius rounds the four vertical (Z) corners of the removed block -- set it for
    pockets/trays whose inner corners are filleted (e.g. inner_corner_radius), so the wall
    stays continuous around the corner. 0 means sharp corners."""

    x: float
    y: float
    z: float
    dx: float
    dy: float
    dz: float
    corner_radius: float = 0.0


class Dimension(BaseModel):
    name: str
    nominal: float
    tol_plus: float = 0.5
    tol_minus: float = 0.5


class PartSpec(BaseModel):
    units: Literal["mm", "in"] = "mm"
    geometry: Geometry
    holes: list[Hole] = Field(default_factory=list)
    cuts: list[RectCut] = Field(default_factory=list)
    fillets: list[float] = Field(default_factory=list)
    chamfers: list[float] = Field(default_factory=list)
    dimensions: list[Dimension] = Field(default_factory=list)
    notes: str | None = None

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_geometry(cls, data):
        """Load JSON produced before the geometry discriminator was introduced."""
        if not isinstance(data, dict) or "geometry" in data:
            return data
        legacy = dict(data)
        legacy["geometry"] = {
            "kind": "extruded",
            "profile_kind": legacy.pop("profile_kind", "rectangle"),
            "width": legacy.pop("width", None),
            "height": legacy.pop("height", None),
            "diameter": legacy.pop("diameter", None),
            "profile_points": legacy.pop("profile_points", []),
            "thickness": legacy.pop("thickness"),
        }
        return legacy

    def bbox(self) -> tuple[float, float, float]:
        if isinstance(self.geometry, UnsupportedGeometry):
            return 0.0, 0.0, 0.0
        return self.geometry.bbox()

    def sanity_check(self) -> list[str]:
        """Reject incomplete or physically implausible extraction results."""
        errors: list[str] = []
        geometry = self.geometry

        if isinstance(geometry, UnsupportedGeometry):
            return [f"unsupported geometry: {geometry.reason}"]

        if isinstance(geometry, ExtrudedGeometry):
            if geometry.thickness <= 0:
                errors.append("extruded thickness must be positive")
            if geometry.profile_kind == "circle":
                if not geometry.diameter or geometry.diameter <= 0:
                    errors.append("circle profile missing positive diameter")
            elif geometry.profile_kind == "polygon":
                if len(geometry.profile_points) < 3:
                    errors.append("polygon profile needs at least 3 points")
            elif not geometry.width or not geometry.height:
                errors.append("rectangle profile missing width/height")
        else:
            if not geometry.segments:
                errors.append("revolved geometry needs at least one segment")
            elif min(segment.z_start for segment in geometry.segments) != 0:
                errors.append("revolved segments must start at z=0")
            for index, segment in enumerate(geometry.segments):
                if segment.z_end <= segment.z_start:
                    errors.append(f"segment{index} z_end must be greater than z_start")
                if segment.outer_diameter <= 0:
                    errors.append(f"segment{index} outer diameter must be positive")
                if not 0 <= segment.inner_diameter < segment.outer_diameter:
                    errors.append(f"segment{index} inner diameter must be smaller than outer")

        width, height, thickness = self.bbox()
        for index, hole in enumerate(self.holes):
            name = hole.id or f"hole{index}"
            if hole.diameter <= 0:
                errors.append(f"{name} diameter must be positive")
            if not (0 < hole.x < width and 0 < hole.y < height):
                errors.append(f"{name} center ({hole.x},{hole.y}) outside bounding box")
            if hole.hole_type == "blind" and (
                hole.depth is None or not 0 < hole.depth < thickness
            ):
                errors.append(f"{name} blind depth must be between 0 and part thickness")
            if hole.hole_type == "counterbore" and (
                hole.counterbore_diameter is None
                or hole.counterbore_diameter <= hole.diameter
                or hole.counterbore_depth is None
                or not 0 < hole.counterbore_depth < thickness
            ):
                errors.append(f"{name} has invalid counterbore dimensions")
            if hole.hole_type == "countersink" and (
                hole.countersink_diameter is None
                or hole.countersink_diameter <= hole.diameter
                or hole.countersink_angle is None
            ):
                errors.append(f"{name} has invalid countersink dimensions")

        if isinstance(geometry, RevolvedGeometry) and self.cuts:
            errors.append("rectangular cuts are only supported for extruded geometry")
        for radius in self.fillets:
            if radius <= 0 or radius >= min(width, height) / 2:
                errors.append(f"fillet r={radius} is invalid for the part bounding box")
        return errors
