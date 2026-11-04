"""Scene graph schema v0: the single source of truth for scene JSON.

Conventions (PROJECT_MATERIALS Appendix B): meters; +Y up; floor at y = 0. Room x in
[0, width] runs west -> east and z in [0, depth] runs north -> south, so the frame is
right-handed like three.js. An object's front faces +Z: rot_y_deg = 0 faces south, and
positive angles turn counterclockwise seen from above (90 = east, 180 = north, 270 = west).

This module checks structure only: ids, references, and openings that fit their walls.
Geometry rules (room bounds, collisions, door clearance) belong to the verifier.
"""

from __future__ import annotations

from enum import StrEnum
from itertools import pairwise
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SCHEMA_VERSION = "0.1"

# Length tolerance in meters, so floating-point noise doesn't fail an exact fit.
EPS = 1e-6

Id = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*$", max_length=64)]
HexColor = Annotated[str, Field(pattern=r"^#[0-9A-Fa-f]{6}$")]


class Wall(StrEnum):
    NORTH = "north"  # z = 0
    SOUTH = "south"  # z = depth
    WEST = "west"  # x = 0
    EAST = "east"  # x = width


WALL_IDS = frozenset(f"wall_{wall}" for wall in Wall)
ROOM_ID = "room"
RESERVED_IDS = WALL_IDS | {ROOM_ID}


class RoomType(StrEnum):
    LIVING_ROOM = "living_room"
    BEDROOM = "bedroom"
    DINING_ROOM = "dining_room"


class RelationType(StrEnum):
    AGAINST_WALL = "against_wall"
    FACING = "facing"
    NEXT_TO = "next_to"
    IN_FRONT_OF = "in_front_of"
    NEAR_OPENING = "near_opening"
    CENTERED_IN = "centered_in"
    ON_TOP_OF = "on_top_of"
    ALIGNED_WITH = "aligned_with"


# Which kinds of thing each relation may point at. The subject is always an object.
RELATION_TARGETS: dict[RelationType, frozenset[str]] = {
    RelationType.AGAINST_WALL: frozenset({"wall"}),
    RelationType.FACING: frozenset({"object", "opening"}),
    RelationType.NEXT_TO: frozenset({"object"}),
    RelationType.IN_FRONT_OF: frozenset({"object"}),
    RelationType.NEAR_OPENING: frozenset({"opening"}),
    RelationType.CENTERED_IN: frozenset({"zone", "room"}),
    RelationType.ON_TOP_OF: frozenset({"object"}),
    RelationType.ALIGNED_WITH: frozenset({"object"}),
}

_KIND_LABEL = {
    "object": "an object",
    "opening": "an opening",
    "wall": "a wall",
    "zone": "a zone",
    "room": "the room",
}


def _drop_field_titles(schema: dict[str, Any]) -> None:
    # Pydantic titles every field ("Offset M"); code generators turn each title into a type
    # alias. Field names and descriptions say enough.
    for prop in schema.get("properties", {}).values():
        prop.pop("title", None)


class _Model(BaseModel):
    # extra="forbid": a typo such as "rot_deg" fails loudly instead of being dropped.
    # json_schema_serialization_defaults_required: in the exported (serialization) schema,
    # fields with defaults are required, because the backend always emits them.
    model_config = ConfigDict(
        extra="forbid",
        json_schema_serialization_defaults_required=True,
        json_schema_extra=_drop_field_titles,
    )


class RoomSize(_Model):
    width: float = Field(ge=1.0, le=20.0, description="Extent along x (west -> east), meters.")
    depth: float = Field(ge=1.0, le=20.0, description="Extent along z (north -> south), meters.")
    height: float = Field(default=2.7, ge=2.0, le=6.0, description="Ceiling height, meters.")

    def wall_length(self, wall: Wall) -> float:
        return self.width if wall in (Wall.NORTH, Wall.SOUTH) else self.depth


class DoorOpening(_Model):
    id: Id
    type: Literal["door"]
    wall: Wall
    offset_m: float = Field(
        ge=0, description="From the wall's low-coordinate end to the door's near edge."
    )
    width_m: float = Field(gt=0, le=3.0)
    height_m: float = Field(default=2.1, gt=0)

    @property
    def bottom_m(self) -> float:
        return 0.0


class WindowOpening(_Model):
    id: Id
    type: Literal["window"]
    wall: Wall
    offset_m: float = Field(
        ge=0, description="From the wall's low-coordinate end to the window's near edge."
    )
    width_m: float = Field(gt=0, le=6.0)
    sill_m: float = Field(default=0.9, ge=0, description="Height of the bottom edge.")
    height_m: float = Field(default=1.2, gt=0)

    @property
    def bottom_m(self) -> float:
        return self.sill_m


# A tagged union: the "type" field decides which model parses the opening.
Opening = Annotated[DoorOpening | WindowOpening, Field(discriminator="type")]


class Room(_Model):
    type: RoomType
    size_m: RoomSize
    openings: list[Opening] = Field(default_factory=list)

    @model_validator(mode="after")
    def _openings_fit_walls(self) -> Self:
        by_wall: dict[Wall, list[DoorOpening | WindowOpening]] = {}
        for opening in self.openings:
            length = self.size_m.wall_length(opening.wall)
            if opening.offset_m + opening.width_m > length + EPS:
                raise ValueError(
                    f"opening '{opening.id}' runs off wall_{opening.wall}: offset "
                    f"{opening.offset_m:g} + width {opening.width_m:g} > wall length {length:g} m"
                )
            top = opening.bottom_m + opening.height_m
            if top > self.size_m.height + EPS:
                raise ValueError(
                    f"opening '{opening.id}' reaches {top:g} m, "
                    f"above the {self.size_m.height:g} m ceiling"
                )
            by_wall.setdefault(opening.wall, []).append(opening)

        for wall, openings in by_wall.items():
            openings.sort(key=lambda o: o.offset_m)
            for a, b in pairwise(openings):
                if b.offset_m < a.offset_m + a.width_m - EPS:
                    raise ValueError(f"openings '{a.id}' and '{b.id}' overlap on wall_{wall}")
        return self


class Pose(_Model):
    x: float = Field(description="Pivot (bottom center) along x, meters.")
    z: float = Field(description="Pivot (bottom center) along z, meters.")
    y: float = Field(
        default=0.0, ge=0, description="Pivot height; above 0 only for objects resting on others."
    )
    rot_y_deg: float = Field(
        default=0.0,
        description="Yaw in degrees, normalized to [0, 360). 0 faces south, 90 east.",
    )

    @field_validator("rot_y_deg")
    @classmethod
    def _normalize_rotation(cls, value: float) -> float:
        angle = value % 360.0
        # Tiny negative inputs (e.g. -1e-20) round up to exactly 360.0.
        return 0.0 if angle >= 360.0 else angle


class MaterialSpec(_Model):
    color: HexColor | None = None
    preset: Id | None = Field(default=None, description="Material preset name, e.g. 'oak'.")

    @model_validator(mode="after")
    def _color_or_preset(self) -> Self:
        if self.color is None and self.preset is None:
            raise ValueError("a material needs a color or a preset")
        return self


class SceneObject(_Model):
    id: Id
    name: str = Field(min_length=1, max_length=80, description="e.g. 'grey three-seat sofa'.")
    category: Id = Field(description="Catalog category, e.g. 'coffee_table'.")
    asset_id: Id = Field(description="Id of the record in assets/catalog.json.")
    pose: Pose
    materials: dict[str, MaterialSpec] = Field(
        default_factory=dict, description="Overrides per material slot."
    )


class Zone(_Model):
    id: Id
    label: str = Field(min_length=1, max_length=80, description="e.g. 'seating area'.")
    objects: list[Id] = Field(default_factory=list)


class Relation(_Model):
    type: RelationType
    subject: Id
    target: Id = Field(description="An object, opening, wall, zone, or 'room', by relation type.")


class Scene(_Model):
    schema_version: Literal["0.1"]
    room: Room
    zones: list[Zone] = Field(default_factory=list)
    objects: list[SceneObject] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_references(self) -> Self:
        # One id namespace for openings, zones, and objects, so a relation target is unambiguous.
        kinds: dict[str, str] = {}
        named = [
            *((o.id, "opening") for o in self.room.openings),
            *((z.id, "zone") for z in self.zones),
            *((o.id, "object") for o in self.objects),
        ]
        for item_id, kind in named:
            if item_id in RESERVED_IDS:
                raise ValueError(f"id '{item_id}' is reserved")
            if item_id in kinds:
                raise ValueError(f"duplicate id '{item_id}'")
            kinds[item_id] = kind

        zone_of: dict[str, str] = {}
        for zone in self.zones:
            for object_id in zone.objects:
                if kinds.get(object_id) != "object":
                    raise ValueError(f"zone '{zone.id}' lists unknown object '{object_id}'")
                if object_id in zone_of:
                    raise ValueError(
                        f"object '{object_id}' is in two zones: '{zone_of[object_id]}' "
                        f"and '{zone.id}'"
                    )
                zone_of[object_id] = zone.id

        kinds.update({wall_id: "wall" for wall_id in WALL_IDS})
        kinds[ROOM_ID] = "room"
        for rel in self.relations:
            where = f"relation {rel.type} from '{rel.subject}'"
            if kinds.get(rel.subject) != "object":
                raise ValueError(f"{where}: subject '{rel.subject}' is not an object in the scene")
            if rel.target == rel.subject:
                raise ValueError(f"{where}: relates '{rel.subject}' to itself")
            target_kind = kinds.get(rel.target)
            if target_kind is None:
                raise ValueError(f"{where}: target '{rel.target}' does not exist")
            allowed = RELATION_TARGETS[rel.type]
            if target_kind not in allowed:
                expected = " or ".join(_KIND_LABEL[k] for k in sorted(allowed))
                raise ValueError(
                    f"{where}: target '{rel.target}' is {_KIND_LABEL[target_kind]}; "
                    f"expected {expected}"
                )
        return self
