/*
 * Generated from server/scene/scene.schema.json (Pydantic models in server/scene/schema.py).
 * Do not edit by hand: run `make schemas`.
 */

export type RoomType = "living_room" | "bedroom" | "dining_room";
export type Wall = "north" | "south" | "west" | "east";
export type RelationType =
  "against_wall" | "facing" | "next_to" | "in_front_of" | "near_opening" | "centered_in" | "on_top_of" | "aligned_with";

export interface Scene {
  schema_version: "0.1";
  room: Room;
  zones: Zone[];
  objects: SceneObject[];
  relations: Relation[];
}
export interface Room {
  type: RoomType;
  size_m: RoomSize;
  openings: (DoorOpening | WindowOpening)[];
}
export interface RoomSize {
  /**
   * Extent along x (west -> east), meters.
   */
  width: number;
  /**
   * Extent along z (north -> south), meters.
   */
  depth: number;
  /**
   * Ceiling height, meters.
   */
  height: number;
}
export interface DoorOpening {
  id: string;
  type: "door";
  wall: Wall;
  /**
   * From the wall's low-coordinate end to the door's near edge.
   */
  offset_m: number;
  width_m: number;
  height_m: number;
}
export interface WindowOpening {
  id: string;
  type: "window";
  wall: Wall;
  /**
   * From the wall's low-coordinate end to the window's near edge.
   */
  offset_m: number;
  width_m: number;
  /**
   * Height of the bottom edge.
   */
  sill_m: number;
  height_m: number;
}
export interface Zone {
  id: string;
  /**
   * e.g. 'seating area'.
   */
  label: string;
  objects: string[];
}
export interface SceneObject {
  id: string;
  /**
   * e.g. 'grey three-seat sofa'.
   */
  name: string;
  /**
   * Catalog category, e.g. 'coffee_table'.
   */
  category: string;
  /**
   * Id of the record in assets/catalog.json.
   */
  asset_id: string;
  pose: Pose;
  /**
   * Overrides per material slot.
   */
  materials: {
    [k: string]: MaterialSpec;
  };
}
export interface Pose {
  /**
   * Pivot (bottom center) along x, meters.
   */
  x: number;
  /**
   * Pivot (bottom center) along z, meters.
   */
  z: number;
  /**
   * Pivot height; above 0 only for objects resting on others.
   */
  y: number;
  /**
   * Yaw in degrees, normalized to [0, 360). 0 faces south, 90 east.
   */
  rot_y_deg: number;
}
export interface MaterialSpec {
  color: string | null;
  /**
   * Material preset name, e.g. 'oak'.
   */
  preset: string | null;
}
export interface Relation {
  type: RelationType;
  subject: string;
  /**
   * An object, opening, wall, zone, or 'room', by relation type.
   */
  target: string;
}
