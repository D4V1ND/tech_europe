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


class Body(BaseModel):
    """One sub-solid of a multi-body part: an axis-aligned box or a cylinder, placed in
    the shared part frame. operation 'add' unions it in, 'cut' subtracts it (use a cut
    cylinder for a hole/opening in any face -- pick its axis to match the face normal).

    box:      size (dx, dy, dz); (x, y, z) is the MIN corner.
    cylinder: diameter + length along `axis`; (x, y, z) is the CENTER of the base face."""

    shape: Literal["box", "cylinder"] = "box"
    operation: Literal["add", "cut"] = "add"
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    dx: float | None = None
    dy: float | None = None
    dz: float | None = None
    diameter: float | None = None
    length: float | None = None
    axis: Literal["x", "y", "z"] = "z"

    def aabb(self) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        """Axis-aligned (min_corner, max_corner) of this body in the part frame."""
        if self.shape == "box":
            dx, dy, dz = self.dx or 0.0, self.dy or 0.0, self.dz or 0.0
            return (self.x, self.y, self.z), (self.x + dx, self.y + dy, self.z + dz)
        r = (self.diameter or 0.0) / 2.0
        ln = self.length or 0.0
        if self.axis == "z":
            return (self.x - r, self.y - r, self.z), (self.x + r, self.y + r, self.z + ln)
        if self.axis == "y":
            return (self.x - r, self.y, self.z - r), (self.x + r, self.y + ln, self.z + r)
        return (self.x, self.y - r, self.z - r), (self.x + ln, self.y + r, self.z + r)


class MultiBodyGeometry(BaseModel):
    """A part assembled from several positioned boxes/cylinders unioned (and cut) into one
    solid. Approximates brackets, weldments, and bent sheet metal as oriented plates."""

    kind: Literal["multibody"] = "multibody"
    bodies: list[Body] = Field(default_factory=list)

    def bbox(self) -> tuple[float, float, float]:
        adds = [b for b in self.bodies if b.operation == "add"]
        if not adds:
            return 0.0, 0.0, 0.0
        mins = [b.aabb()[0] for b in adds]
        maxs = [b.aabb()[1] for b in adds]
        span = lambda i: max(m[i] for m in maxs) - min(m[i] for m in mins)
        return span(0), span(1), span(2)


class UnsupportedGeometry(BaseModel):
    kind: Literal["unsupported"] = "unsupported"
    reason: str
    visible_features: list[str] = Field(default_factory=list)
    # Best-effort overall bounding box (mm/in per spec.units). When provided, the part is
    # approximated as a solid block of this size for partial geometric credit instead of
    # producing nothing. Leave None only if no overall dimensions are readable at all.
    envelope_width: float | None = None
    envelope_height: float | None = None
    envelope_depth: float | None = None

    def has_envelope(self) -> bool:
        return bool(self.envelope_width and self.envelope_height and self.envelope_depth)

    def bbox(self) -> tuple[float, float, float]:
        return (
            self.envelope_width or 0.0,
            self.envelope_height or 0.0,
            self.envelope_depth or 0.0,
        )


Geometry = Annotated[
    ExtrudedGeometry | RevolvedGeometry | MultiBodyGeometry | UnsupportedGeometry,
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
        return self.geometry.bbox()

    def sanity_check(self) -> list[str]:
        """Reject incomplete or physically implausible extraction results."""
        errors: list[str] = []
        geometry = self.geometry

        if isinstance(geometry, UnsupportedGeometry):
            # Approximate as a bounding-block when an envelope is given; only truly fail
            # when there are no overall dimensions to approximate from.
            if not geometry.has_envelope():
                return [f"unsupported geometry (no envelope): {geometry.reason}"]
            return []          # build the envelope block; holes/cuts skipped downstream

        if isinstance(geometry, MultiBodyGeometry):
            # Multi-body manages its own features via its bodies; validate those and stop.
            adds = [b for b in geometry.bodies if b.operation == "add"]
            if not adds:
                return ["multibody needs at least one 'add' body"]
            for i, b in enumerate(geometry.bodies):
                if b.shape == "box" and not (b.dx and b.dy and b.dz):
                    errors.append(f"body{i} box missing positive dx/dy/dz")
                if b.shape == "cylinder" and not (b.diameter and b.length):
                    errors.append(f"body{i} cylinder missing positive diameter/length")
            return errors

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
        elif isinstance(geometry, RevolvedGeometry):
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
