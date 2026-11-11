#!/usr/bin/env python3
"""Draw the floor plan and sprites, then embed them in a Planimation AP."""

import argparse
import base64
from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


SOURCE = Path(__file__).resolve().parent
OUTPUT = SOURCE.parent / "symbolic_planning_AP.pddl"
SCALE = 2
INK = "#142d43"
WALL = "#354e65"
SLATE = "#46627a"
WHITE = "#ffffff"
TEAL = "#087e81"
ITEM_SIZE = 52
SLOT_STEP = 54
PASSAGE = 164


@dataclass(frozen=True)
class Room:
    name: str
    bounds: tuple[int, int, int, int]
    stop: tuple[int, int]
    floor: str
    grid: str
    accent: str
    # Room-local lower-left corners for loose items, table, cabinet, person.
    items: tuple[int, int]
    table: tuple[int, int]
    cabinet: tuple[int, int]
    person: tuple[int, int]


# Rooms share walls. The two columns use the same movement axis vertically.
# All paths between stops are straight through their illustrated thresholds.
ROOMS = (
    Room("Office", (0, 446, 416, 394), (274, 712), "#e9f2fa", "#d4e4f2", "#2c659c",
         (126, 144), (216, 14), (8, 15), (8, 238)),
    Room("Meeting", (0, 0, 416, 446), (274, 180), "#eeedf9", "#dfdcf1", "#6b58a0",
         (126, 281), (193, 14), (8, 16), (8, 251)),
    Room("Hallway", (416, 572, 424, 268), (688, 712), "#edf1f5", "#dde5ed", "#5b7087",
         (126, 31), (223, 14), (16, 15), (220, 130)),
    Room("Entrance", (416, 294, 424, 278), (688, 438), "#e9f5f1", "#d5eae3", "#127367",
         (126, 27), (222, 13), (17, 13), (220, 136)),
    Room("Lab", (416, 0, 424, 294), (688, 180), "#fbf2e6", "#eee3d3", "#91612a",
         (126, 32), (222, 13), (17, 16), (220, 148)),
)
CONNECTIONS = (
    ("Entrance", "Hallway"), ("Hallway", "Office"), ("Office", "Meeting"),
    ("Meeting", "Lab"), ("Lab", "Entrance"),
)


@lru_cache
def font(size, weight):
    face = ImageFont.truetype(str(SOURCE / "DM-Sans.ttf"), size * SCALE)
    face.set_variation_by_axes([14, weight])  # DM Sans optical size and weight.
    return face


class Drawing:
    def __init__(self, width, height, fill=None):
        self.size = (width, height)
        self.image = Image.new("RGBA", self.scale(self.size), fill)
        self.draw = ImageDraw.Draw(self.image)

    @staticmethod
    def scale(values):
        return tuple(round(value * SCALE) for value in values)

    def box(self, bounds, fill, outline=None, radius=0, width=1):
        if radius:
            self.draw.rounded_rectangle(
                self.scale(bounds), radius * SCALE, fill, outline, width * SCALE
            )
        else:
            self.draw.rectangle(self.scale(bounds), fill, outline, width * SCALE)

    def ellipse(self, bounds, fill, outline=None, width=1):
        self.draw.ellipse(self.scale(bounds), fill, outline, width * SCALE)

    def line(self, points, fill, width=1):
        self.draw.line(self.scale(points), fill, width * SCALE, joint="curve")

    def polygon(self, points, fill):
        self.draw.polygon(self.scale(points), fill)

    def text(self, point, label, size, fill=INK, weight=700, anchor="lm"):
        self.draw.text(self.scale(point), label, fill, font(size, weight), anchor)

    def png(self):
        buffer = BytesIO()
        self.image.save(buffer, format="PNG", optimize=True)
        return base64.b64encode(buffer.getvalue()).decode("ascii")


def room_art(room):
    x, y, width, height = room.bounds
    art = Drawing(width, height, room.floor)
    for grid_x in range(18, width, 20):
        for grid_y in range(18, height, 20):
            art.ellipse((grid_x, grid_y, grid_x + 1, grid_y + 1), room.grid)
    art.box((0, 0, width, height), None, WALL, width=4)

    stop_x, stop_y = room.stop
    local_x, local_y = stop_x - x, y + height - stop_y
    for first, second in CONNECTIONS:
        if room.name not in (first, second):
            continue
        other_name = second if room.name == first else first
        other_x, other_y = next(entry.stop for entry in ROOMS if entry.name == other_name)
        if other_x == stop_x:
            edge = 0 if other_y > stop_y else height
            art.box((local_x - PASSAGE // 2, max(edge - 5, 0),
                     local_x + PASSAGE // 2, min(edge + 5, height)), room.floor)
            for jamb in (local_x - PASSAGE // 2, local_x + PASSAGE // 2):
                art.line((jamb, edge, jamb, 13 if edge == 0 else height - 13), WALL, 4)
            for mark in range(min(edge, local_y) + 5, max(edge, local_y) - 4, 20):
                art.line((local_x, mark, local_x, mark + 8), room.accent, 2)
        else:
            edge = 0 if other_x < stop_x else width
            art.box((max(edge - 5, 0), local_y - PASSAGE // 2,
                     min(edge + 5, width), local_y + PASSAGE // 2), room.floor)
            for jamb in (local_y - PASSAGE // 2, local_y + PASSAGE // 2):
                art.line((edge, jamb, 13 if edge == 0 else width - 13, jamb), WALL, 4)
            for mark in range(min(edge, local_x) + 5, max(edge, local_x) - 4, 20):
                art.line((mark, local_y, mark + 8, local_y), room.accent, 2)

    art.ellipse((local_x - 12, local_y - 12, local_x + 12, local_y + 12),
                room.floor, room.accent, 2)
    # The label sits in a reserved corner. It moves and scales with the room.
    label_width = int(font(31, 760).getlength(room.name) / SCALE) + 29
    art.box((15, 9, 15 + label_width, 51), WHITE, radius=9)
    art.box((21, 20, 26, 41), room.accent, radius=2)
    art.text((34, 31), room.name, 31, weight=760)
    return art


def robot_art():
    art = Drawing(160, 132)
    art.ellipse((33, 105, 127, 127), "#b6cbd7")
    art.line((80, 14, 80, 30), WALL, 4)
    art.ellipse((73, 4, 87, 18), "#63e1d5", INK, 2)
    art.box((42, 82, 118, 117), INK, radius=16)
    art.box((51, 58, 109, 111), "#d9eaf1", INK, radius=16, width=3)
    art.box((38, 25, 122, 82), "#eff8fb", INK, radius=20, width=3)
    art.box((46, 34, 114, 70), "#152e48", radius=13)
    for eye_x in (62, 98):
        art.box((eye_x - 4, 43, eye_x + 4, 57), "#71eee4", radius=4)
    art.line((75, 59, 85, 59), "#9ed8df", 2)
    art.box((69, 88, 91, 95), "#269d9b", radius=3)
    for center, shoulder, side in ((28, 53, "L"), (132, 107, "R")):
        art.line((shoulder, 82, center, 86), INK, 12)
        art.line((shoulder, 80, center, 84), "#83b3c7", 5)
        art.ellipse((center - 16, 70, center + 16, 102), INK)
        art.ellipse((center - 11, 75, center + 11, 97), "#c1e9ed", SLATE, 2)
        art.ellipse((center - 10, 47, center + 10, 67), INK)
        art.text((center, 57), side, 13, WHITE, anchor="mm")
    return art


def item_art(kind):
    art = Drawing(ITEM_SIZE, ITEM_SIZE)
    accent, light = {
        "book": ("#6745ad", "#eee7fb"),
        "laptop": ("#087d75", "#dff7ef"),
        "cup": ("#a76116", "#fff0d8"),
        "item": ("#41657e", "#e7eff6"),
    }[kind]
    art.box((2, 4, 50, 51), "#afc1ce", radius=11)
    art.box((2, 1, 50, 48), light, accent, radius=11, width=2)
    if kind == "book":
        art.box((14, 9, 37, 40), accent, radius=4)
        art.box((18, 32, 36, 38), WHITE, radius=2)
        art.line((20, 15, 32, 15), WHITE, 2)
        art.line((20, 21, 29, 21), "#d8c7f1", 2)
    elif kind == "laptop":
        art.box((12, 11, 40, 32), accent, radius=4)
        art.box((16, 15, 36, 28), WHITE, radius=2)
        art.polygon((12, 31, 40, 31, 45, 38, 43, 40, 9, 40, 7, 38), accent)
        art.line((23, 36, 29, 36), WHITE, 2)
    elif kind == "cup":
        art.ellipse((26, 16, 40, 32), None, accent, 3)
        art.box((12, 12, 32, 37), accent, radius=5)
        art.line((17, 17, 17, 29), "#ffd896", 2)
    else:
        art.box((14, 12, 38, 37), accent, radius=4)
        art.line((17, 19, 35, 19), WHITE, 2)
    return art


def card(width, height, fill, border):
    art = Drawing(width, height)
    art.box((1, 4, width - 1, height - 1), "#b9cad6", radius=13)
    art.box((1, 1, width - 1, height - 5), fill, border, radius=13, width=2)
    return art


def tray_slots(art, y, outline, fill):
    for x in range(12, 173, SLOT_STEP):
        art.box((x, y, x + ITEM_SIZE, y + ITEM_SIZE), fill, outline, radius=7, width=2)


def table_art():
    art = card(184, 94, "#f7e9d3", "#896d4e")
    art.text((13, 18), "Table", 19)
    tray_slots(art, 33, "#bfa686", "#fff7ec")
    return art


def person_art(label):
    art = card(184, 120, "#edf4fa", "#6c8ba4")
    art.ellipse((12, 9, 55, 52), "#d9e9f6")
    art.box((19, 31, 48, 47), "#376079", radius=8)
    art.ellipse((25, 14, 42, 34), "#a96e4e")
    art.box((24, 12, 43, 22), "#302f3d", radius=5)
    art.line((27, 24, 40, 24), "#2c3647", 2)
    art.text((62, 22), label, 21)
    art.text((62, 41), "Delivery tray", 14, SLATE, weight=570)
    tray_slots(art, 59, "#9fb6c9", "#f8fbff")
    return art


def cabinet_art(is_open):
    art = card(184, 116, "#e6edf2", "#5c7288")
    art.text((12, 20), "Cabinet", 19)
    accent = TEAL if is_open else "#994637"
    art.box((113, 9, 172, 31), accent, radius=6)
    art.text((142, 20), "Open" if is_open else "Closed", 13, WHITE, anchor="mm")
    if is_open:
        art.box((8, 43, 176, 106), "#526c81", radius=7)
        # Clear the panel over the shelf. Empty slots show the room floor.
        art.box((11, 47, 173, 104), (0, 0, 0, 0))
        art.line((10, 105, 174, 105), "#8ea7b6", 2)
    else:
        art.box((8, 43, 176, 106), "#bacad6", "#8299ab", radius=7, width=2)
        art.line((92, 44, 92, 104), "#8299ab", 2)
        art.box((79, 67, 85, 87), SLATE, radius=3)
        art.box((99, 67, 105, 87), SLATE, radius=3)
    return art


def door_art(is_open):
    art = Drawing(184, 68)
    accent = TEAL if is_open else "#a64839"
    art.box((6, 29, 178, 41), "#e0ecef", SLATE, radius=3, width=2)
    art.box((6, 22, 16, 48), WALL, radius=3)
    art.box((168, 22, 178, 48), WALL, radius=3)
    if is_open:
        art.line((19, 35, 52, 58), accent, 7)
        for x in range(60, 165, 17):
            art.line((x, 35, x + 8, 35), accent, 2)
    else:
        art.box((15, 28, 169, 42), accent, radius=3)
        art.line((144, 34, 156, 34), "#ffd8c6", 3)
    art.box((45, 3, 139, 26), accent, radius=6)
    art.text((92, 14), "Door open" if is_open else "Door closed",
             14, WHITE, anchor="mm")
    return art


def visual(name, kind, objects=None, **properties):
    lines = [f"(:visual {name}", f"  :type {kind}"]
    if objects:
        lines.append(f"  :objects {objects}")
    lines.append("  :properties (")
    lines.extend(f"    ({key} {value})" for key, value in properties.items())
    lines.append("  )\n)")
    return "\n".join(lines)


def build_profile():
    sprites = {
        "img-none": Drawing(1, 1),
        "img-robot": robot_art(),
        "img-table": table_art(),
        "img-person": person_art("Person"),
        "img-professor": person_art("Professor"),
        "img-cabinet-closed": cabinet_art(False),
        "img-cabinet-open": cabinet_art(True),
        "img-door-closed": door_art(False),
        "img-door-open": door_art(True),
    }
    for item in ("item", "book", "laptop", "cup"):
        sprites[f"img-{item}"] = item_art(item)

    common = dict(showname="false", color="white")
    default = dict(prefabimage="img-none", x=0, y=0, width=ITEM_SIZE, height=ITEM_SIZE,
                   depth=5, slot=0, loosex=0, loosey=0, gripx=2,
                   itemimage="img-item", personimage="img-person")
    blocks = [
        visual("unplaced-object", "default", **(common | default)),
        visual("robot", "custom", "robot", **common, prefabimage="img-robot",
               x="null", y="null", width=160, height=132, depth=4),
    ]
    # Loose items have separate pickup positions. The tray slot is stable
    # across all furniture and independent of which gripper carries the item.
    for item, slot, loose_x, loose_y in (
        ("book", 0, 0, 0), ("laptop", SLOT_STEP, 230, 0), ("cup", 2 * SLOT_STEP, 0, 56),
    ):
        blocks.append(visual(f"item-{item}", "predefine", item,
                             **(common | default | dict(itemimage=f"img-{item}", slot=slot,
                                                        loosex=loose_x, loosey=loose_y))))
    for gripper, grip_x in (("left", 2), ("right", 106)):
        blocks.append(visual(f"gripper-{gripper}", "predefine", gripper,
                             **(common | default | dict(width=0, height=0, gripx=grip_x))))
    blocks.append(visual("professor-style", "predefine", "%professor",
                         **(common | default | dict(personimage="img-professor"))))

    for room in ROOMS:
        name = room.name.lower()
        image = f"img-room-{name}"
        sprites[image] = room_art(room)
        x, y, width, height = room.bounds
        stop_x, stop_y = room.stop
        blocks.append(visual(
            f"room-{name}", "predefine", name, **common, prefabimage=image,
            x=x, y=y, width=width, height=height, depth=0,
            robotx=stop_x - x, roboty=stop_y - y, doorx=stop_x // 2, doory=stop_y // 2,
            itemx=room.items[0], itemy=room.items[1],
            tablex=room.table[0], tabley=room.table[1],
            cabinetx=room.cabinet[0], cabinety=room.cabinet[1],
            personx=room.person[0], persony=room.person[1],
        ))

    return "\n".join([
        "(define (animation building)",
        "; Generated by source/build_profile.py from source/rules.pddl.in and sprite drawings.",
        "; AP coordinates use a lower-left origin. The PNG artwork uses a top-left origin.\n",
        (SOURCE / "rules.pddl.in").read_text(encoding="utf-8").rstrip(),
        "",
        "; Layers: floors 0, furniture 2, door 3, robot 4, items 5, cabinet front 6.",
        "\n\n".join(blocks),
        "",
        "; Embedded PNGs keep this profile self-contained.",
        "(:image",
        *(f"  ({name} {drawing.png()})" for name, drawing in sprites.items()),
        ")",
        ")",
        "",
    ])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check the committed AP is current")
    args = parser.parse_args()
    profile = build_profile()
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != profile:
            parser.exit(1, f"{OUTPUT.name} differs from the generated profile\n")
    else:
        OUTPUT.write_text(profile, encoding="utf-8")


if __name__ == "__main__":
    main()
