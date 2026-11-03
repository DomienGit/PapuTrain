"""Generuje ikony PWA (Etap 9). Uruchom: .venv/bin/python frontend/scripts/generate_icons.py

Prosty znak: ciemne tło + emeraldowy sztangielek. Ikona "maskable" ma mniejszy
rysunek — Android przycina ją do kształtu ekranu telefonu, więc ważny rysunek
musi siedzieć w bezpiecznym środku (ok. 80%).
"""

from pathlib import Path

from PIL import Image, ImageDraw

BG = (24, 24, 27, 255)  # zinc-900
FG = (16, 185, 129, 255)  # emerald-500
OUT = Path(__file__).parent.parent / "public" / "icons"


def draw_dumbbell(draw: ImageDraw.ImageDraw, cx: int, cy: int, width: int) -> None:
    """Sztangielek wyśrodkowany w (cx, cy); width = szerokość całego rysunku."""
    h = width  # wysokość rysunku
    bar_h = max(3, h // 14)  # gryf (poziomy pręt)
    bar_w = int(width * 0.62)
    plate_w = max(6, h // 7)  # szerokość jednego krążka
    plate_h_tall = int(h * 0.62)
    plate_h_short = int(plate_h_tall * 0.72)
    gap = int(width * 0.10)

    # gryf
    draw.rounded_rectangle(
        [cx - bar_w // 2, cy - bar_h // 2, cx + bar_w // 2, cy + bar_h // 2],
        radius=bar_h // 2,
        fill=FG,
    )
    # po dwie pary krążków z każdej strony (wysoki + niższy)
    for side in (-1, 1):
        x_in = cx + side * gap
        x_out = x_in + side * plate_w
        left, right = sorted((x_in, x_out))
        draw.rounded_rectangle(
            [left, cy - plate_h_short // 2, right, cy + plate_h_short // 2],
            radius=plate_w // 4,
            fill=FG,
        )
        x_in2 = x_out
        x_out2 = x_in2 + side * plate_w
        left2, right2 = sorted((x_in2, x_out2))
        draw.rounded_rectangle(
            [left2, cy - plate_h_tall // 2, right2, cy + plate_h_tall // 2],
            radius=plate_w // 4,
            fill=FG,
        )


def make_icon(size: int, glyph_scale: float, path: Path) -> None:
    img = Image.new("RGBA", (size, size), BG)
    draw = ImageDraw.Draw(img)
    draw_dumbbell(draw, size // 2, size // 2, int(size * glyph_scale))
    img.save(path)
    print(f"{path} ({size}x{size})")


OUT.mkdir(parents=True, exist_ok=True)
make_icon(192, 0.66, OUT / "icon-192.png")
make_icon(512, 0.66, OUT / "icon-512.png")
make_icon(512, 0.46, OUT / "icon-maskable-512.png")  # mniejszy rysunek = strefa bezpieczna
make_icon(180, 0.66, OUT / "apple-touch-icon.png")
