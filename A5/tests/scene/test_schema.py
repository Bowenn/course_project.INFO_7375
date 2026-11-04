"""Scene schema v0: structural validation. Geometry (bounds, collisions) is the verifier's job."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from server.scene.schema import RELATION_TARGETS, SCHEMA_VERSION, RelationType, Scene

EXAMPLE = Path(__file__).resolve().parents[2] / "server/scene/examples/living_room.json"


@pytest.fixture
def example() -> dict:
    return json.loads(EXAMPLE.read_text())


def set_at(data: dict, path: str, value) -> None:
    """Set a nested value by dotted path, e.g. "objects.1.id". An index equal to the list
    length appends."""
    *parents, last = path.split(".")
    for key in parents:
        data = data[int(key)] if key.isdigit() else data[key]
    if last.isdigit():
        index = int(last)
        if index == len(data):
            data.append(value)
        else:
            data[index] = value
    else:
        data[last] = value


def test_example_parses(example):
    scene = Scene.model_validate(example)

    assert scene.schema_version == SCHEMA_VERSION
    assert [o.id for o in scene.objects] == ["sofa_1", "coffee_table_1", "armchair_1"]
    assert scene.room.openings[1].sill_m == 0.8


def test_round_trip_through_json(example):
    scene = Scene.model_validate(example)

    assert Scene.model_validate_json(scene.model_dump_json()) == scene


def test_defaults_are_filled(example):
    scene = Scene.model_validate(example)

    assert scene.room.openings[0].height_m == 2.1  # door default
    assert scene.objects[0].pose.y == 0.0
    assert scene.objects[2].materials == {}


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(0, 0.0), (90, 90.0), (-90, 270.0), (360, 0.0), (450, 90.0), (-1e-20, 0.0)],
)
def test_rotation_is_normalized_to_0_360(example, raw, expected):
    set_at(example, "objects.0.pose.rot_y_deg", raw)

    assert Scene.model_validate(example).objects[0].pose.rot_y_deg == expected


def test_every_relation_type_has_target_rules():
    assert set(RELATION_TARGETS) == set(RelationType)


VALID_VARIANTS = [
    pytest.param("room.openings.1.offset_m", 2.4, id="opening-ends-exactly-at-wall-end"),
    pytest.param(
        "relations.3",
        {"type": "centered_in", "subject": "coffee_table_1", "target": "zone_seating"},
        id="centered-in-zone",
    ),
    pytest.param(
        "relations.3",
        {"type": "centered_in", "subject": "coffee_table_1", "target": "room"},
        id="centered-in-room",
    ),
    pytest.param(
        "relations.3",
        {"type": "near_opening", "subject": "armchair_1", "target": "window_1"},
        id="near-opening",
    ),
]


@pytest.mark.parametrize(("path", "value"), VALID_VARIANTS)
def test_accepts_valid_variants(example, path, value):
    set_at(example, path, value)

    Scene.model_validate(example)


INVALID_VARIANTS = [
    pytest.param("objects.1.id", "sofa_1", "duplicate id 'sofa_1'", id="duplicate-object-id"),
    pytest.param("objects.2.id", "door_1", "duplicate id 'door_1'", id="id-clashes-with-opening"),
    pytest.param("objects.2.id", "wall_north", "reserved", id="reserved-id"),
    pytest.param("objects.0.id", "Sofa 1", "should match pattern", id="bad-id-format"),
    pytest.param(
        "relations.1.target", "chair_9", "target 'chair_9' does not exist", id="dangling-target"
    ),
    pytest.param(
        "relations.0.subject", "lamp_1", "subject 'lamp_1' is not an object", id="dangling-subject"
    ),
    pytest.param("relations.0.type", "under", "relations.0.type", id="unknown-relation-type"),
    pytest.param("relations.0.target", "coffee_table_1", "expected a wall", id="wrong-target-kind"),
    pytest.param("relations.1.target", "coffee_table_1", "to itself", id="self-relation"),
    pytest.param("room.openings.1.offset_m", 3.0, "runs off wall_north", id="opening-off-wall"),
    pytest.param(
        "room.openings.1.sill_m", 2.0, "above the 2.7 m ceiling", id="opening-above-ceiling"
    ),
    pytest.param(
        "room.openings.2",
        {"id": "window_2", "type": "window", "wall": "north", "offset_m": 2.0, "width_m": 1.0},
        "overlap on wall_north",
        id="overlapping-openings",
    ),
    pytest.param(
        "zones.0.objects.3", "lamp_1", "unknown object 'lamp_1'", id="zone-lists-unknown-object"
    ),
    pytest.param(
        "zones.1",
        {"id": "zone_reading", "label": "reading corner", "objects": ["armchair_1"]},
        "in two zones",
        id="object-in-two-zones",
    ),
    pytest.param(
        "objects.0.pose.elevation", 0.3, "Extra inputs are not permitted", id="extra-field"
    ),
    pytest.param("schema_version", "0.2", "schema_version", id="wrong-schema-version"),
    pytest.param(
        "objects.0.materials.fabric.color", "grey", "should match pattern", id="bad-color"
    ),
    pytest.param("objects.0.materials.fabric", {}, "color or a preset", id="empty-material"),
    pytest.param("room.size_m.width", 0.5, "greater than or equal to 1", id="room-too-small"),
]


@pytest.mark.parametrize(("path", "value", "message"), INVALID_VARIANTS)
def test_rejects_invalid_scene(example, path, value, message):
    set_at(example, path, value)

    with pytest.raises(ValidationError, match=message):
        Scene.model_validate(example)
