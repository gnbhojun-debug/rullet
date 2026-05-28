# -*- coding: utf-8 -*-
"""
Kivy version of the prize draw roulette.

This file is ready to be packaged with Buildozer/python-for-android.
The old pygame version has been preserved as prize_draw_gui5_pygame_backup.py.
"""

from __future__ import annotations

import math
import os
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from kivy.config import Config

Config.set("graphics", "width", "1280")
Config.set("graphics", "height", "720")
Config.set("graphics", "resizable", "1")

from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.utils import platform
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.stencilview import StencilView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget


SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 30

STATE_IDLE = "IDLE"
STATE_SPINNING_TENS = "SPINNING_TENS"
STATE_TENS_REVEALED = "TENS_REVEALED"
STATE_SPINNING_ONES = "SPINNING_ONES"
STATE_BATCH_REVEAL = "BATCH_REVEAL"
STATE_FINAL_REVEALED = "FINAL_REVEALED"

LOGO_ORANGE = (238, 141, 38)
LOGO_ORANGE_LIGHT = (248, 151, 48)
LOGO_ORANGE_DARK = (198, 115, 23)
LOGO_TEAL = (32, 170, 154)
LOGO_TEAL_LIGHT = (48, 198, 180)
LOGO_TEAL_DARK = (25, 130, 120)
LOGO_GRAY = (179, 179, 179)
LOGO_GRAY_LIGHT = (222, 222, 222)
LOGO_GRAY_DARK = (102, 102, 102)

BG_DARK = (7, 8, 10)
BG_DEEP = (0, 0, 0)
PANEL_LIGHT = (27, 30, 33)
PANEL_EDGE = (73, 78, 82)
WHITE = (248, 249, 247)
INK = (15, 17, 18)
GOLD = LOGO_ORANGE
MINT = LOGO_TEAL
CYAN = LOGO_TEAL_LIGHT
PEACH = LOGO_ORANGE_DARK


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def ease_out_cubic(t: float) -> float:
    t = clamp(t, 0.0, 1.0)
    return 1.0 - pow(1.0 - t, 3)


def rgba(color: tuple[int, int, int], alpha: float = 1.0) -> tuple[float, float, float, float]:
    return (color[0] / 255.0, color[1] / 255.0, color[2] / 255.0, alpha)


def shade(color: tuple[int, int, int], amount: int) -> tuple[int, int, int]:
    return tuple(int(clamp(channel + amount, 0, 255)) for channel in color)


def register_korean_font() -> str:
    """Register a Korean-capable font when one is available on desktop or Android."""
    windir = Path(os.environ.get("WINDIR", "C:/Windows"))
    candidates = [
        (
            Path("assets/NotoSansKR-Regular.ttf"),
            Path("assets/NotoSansKR-Bold.ttf"),
        ),
        (
            windir / "Fonts" / "malgun.ttf",
            windir / "Fonts" / "malgunbd.ttf",
        ),
        (
            Path("/system/fonts/NotoSansCJK-Regular.ttc"),
            Path("/system/fonts/NotoSansCJK-Bold.ttc"),
        ),
        (
            Path("/system/fonts/NotoSansKR-Regular.otf"),
            Path("/system/fonts/NotoSansKR-Bold.otf"),
        ),
        (
            Path("/system/fonts/NotoSans-Regular.ttf"),
            Path("/system/fonts/NotoSans-Bold.ttf"),
        ),
        (
            Path("/system/fonts/DroidSansFallback.ttf"),
            Path("/system/fonts/DroidSansFallback.ttf"),
        ),
    ]

    for regular_path, bold_path in candidates:
        try:
            if regular_path.exists():
                LabelBase.register(
                    name="KoreanFont",
                    fn_regular=str(regular_path),
                    fn_bold=str(bold_path if bold_path.exists() else regular_path),
                )
                return "KoreanFont"
        except Exception:
            continue

    return "Roboto"


FONT_NAME = register_korean_font()


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    size: float
    color: tuple[int, int, int]
    kind: str
    gravity: float = 180.0

    def update(self, dt: float) -> bool:
        self.life -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        return self.life > 0


@dataclass
class ShootingStar:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    color: tuple[int, int, int]

    def update(self, dt: float) -> bool:
        self.life -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        return self.life > 0 and self.x < SCREEN_WIDTH + 180 and self.y < SCREEN_HEIGHT + 180


class RouletteButton(Button):
    def __init__(
        self,
        *,
        accent: tuple[int, int, int] = LOGO_ORANGE,
        base_font_size: int = 22,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.accent = accent
        self.base_font_size = base_font_size
        self.font_name = FONT_NAME
        self.bold = True
        self.halign = "center"
        self.valign = "middle"
        self.outline_width = 1
        self.outline_color = rgba((255, 236, 190), 0.65)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.color = rgba(INK)
        self.bind(pos=self._redraw, size=self._redraw, state=self._redraw, disabled=self._redraw)
        Clock.schedule_once(lambda _dt: self._redraw(), 0)

    def _redraw(self, *_args) -> None:
        self.canvas.before.clear()
        x, y = self.pos
        w, h = self.size
        if w <= 0 or h <= 0:
            return

        self.text_size = (w, h)
        fill = LOGO_GRAY_DARK if self.disabled else self.accent
        if self.state == "down" and not self.disabled:
            fill = shade(fill, -24)
        elif not self.disabled:
            fill = shade(fill, 8)

        self.color = rgba((194, 201, 208) if self.disabled else INK)

        with self.canvas.before:
            Color(0, 0, 0, 0.55)
            RoundedRectangle(pos=(x + 4, y - 5), size=(w, h), radius=[8])
            Color(*rgba(fill))
            RoundedRectangle(pos=(x, y), size=(w, h), radius=[8])
            Color(*rgba(LOGO_GRAY_LIGHT, 0.8))
            Line(rectangle=(x + 5, y + 5, max(1, w - 10), max(1, h - 10)), width=1.2)
            Color(*rgba(INK, 0.95))
            Line(rectangle=(x, y, w, h), width=1.5)


class NumberChip(Label):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.font_name = FONT_NAME
        self.bold = True
        self.color = rgba(INK)
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_args) -> None:
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*rgba((230, 234, 230)))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[6])
            Color(*rgba(LOGO_TEAL))
            Line(rectangle=(*self.pos, *self.size), width=1.3)


class DigitSlot(FloatLayout):
    def __init__(self, label_text: str, accent: tuple[int, int, int], **kwargs) -> None:
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.label_text = label_text
        self.accent = accent
        self.digits = list(range(10))
        self.current_value = "?"
        self.target = 0
        self.spinning = False
        self._elapsed = 0.0
        self._duration = 0.0
        self._switch_elapsed = 0.0
        self._switch_interval = 0.04
        self._spin_event: Any | None = None
        self._on_done: Callable[[], None] | None = None
        self._scale = 1.0
        self._normal_label_y = 0.0
        self._clip_h = 1.0

        self.caption = Label(
            text=label_text,
            size_hint=(None, None),
            font_name=FONT_NAME,
            bold=True,
            color=rgba(WHITE),
            halign="center",
            valign="middle",
        )
        self.caption.outline_width = 1
        self.caption.outline_color = rgba(LOGO_TEAL_DARK, 0.85)
        self.clip_area = StencilView(size_hint=(None, None))
        self.previous_label = Label(
            text="?",
            size_hint=(None, None),
            font_name=FONT_NAME,
            bold=True,
            color=rgba(LOGO_GRAY_DARK),
            halign="center",
            valign="middle",
            opacity=0,
        )
        self.digit_label = Label(
            text="?",
            size_hint=(None, None),
            font_name=FONT_NAME,
            bold=True,
            color=rgba(INK),
            halign="center",
            valign="middle",
        )
        for digit_label in (self.previous_label, self.digit_label):
            digit_label.outline_width = 1
            digit_label.outline_color = rgba(LOGO_GRAY_LIGHT, 0.85)

        self.add_widget(self.caption)
        self.add_widget(self.clip_area)
        self.clip_area.add_widget(self.previous_label)
        self.clip_area.add_widget(self.digit_label)
        self.bind(pos=self._layout_children, size=self._layout_children)

    def place(self, owner: "LotteryRoot", x: float, y: float, w: float, h: float) -> None:
        self._scale = owner.scene_scale
        px, py, pw, ph = owner.scene_rect(x, y, w, h)
        self.pos = (px, py)
        self.size = (pw, ph)
        self._layout_children()

    def reset(self) -> None:
        self.stop()
        self.current_value = "?"
        self.previous_label.opacity = 0
        self.digit_label.text = "?"
        self.digit_label.color = rgba(INK)
        self._position_digit_labels(0.0)

    def set_value(self, value: int | str) -> None:
        self.stop()
        self.current_value = str(value)
        self.previous_label.opacity = 0
        self.digit_label.text = str(value)
        self.digit_label.color = rgba(INK)
        self._position_digit_labels(0.0)

    def start_spin(self, target: int, duration: float, on_done: Callable[[], None]) -> None:
        self.stop()
        self.target = target
        self._duration = max(0.1, duration)
        self._elapsed = 0.0
        self._switch_elapsed = 0.0
        self._switch_interval = 0.035
        self._on_done = on_done
        self.spinning = True
        self.previous_label.text = str(random.choice(self.digits))
        self.previous_label.opacity = 1
        self.digit_label.text = str(random.choice(self.digits))
        self.digit_label.color = rgba(LOGO_ORANGE_DARK)
        self._position_digit_labels(0.0)
        self._spin_event = Clock.schedule_interval(self._spin_tick, 1 / 60.0)

    def stop(self) -> None:
        if self._spin_event is not None:
            self._spin_event.cancel()
            self._spin_event = None
        self.spinning = False

    def _spin_tick(self, dt: float) -> bool:
        self._elapsed += dt
        progress = clamp(self._elapsed / self._duration, 0.0, 1.0)

        if progress >= 1.0:
            self.stop()
            self.current_value = str(self.target)
            self.previous_label.opacity = 0
            self.digit_label.text = str(self.target)
            self.digit_label.color = rgba(INK)
            self._position_digit_labels(0.0)
            if self._on_done is not None:
                callback = self._on_done
                self._on_done = None
                callback()
            return False

        slow = ease_out_cubic(progress)
        self._switch_interval = 0.035 + slow * 0.17
        self._switch_elapsed += dt
        if self._switch_elapsed >= self._switch_interval:
            self._switch_elapsed = 0.0
            self.previous_label.text = self.digit_label.text
            self.previous_label.opacity = 1
            next_digit = random.choice(self.digits)
            if str(next_digit) == self.digit_label.text:
                next_digit = (next_digit + random.randint(1, 9)) % 10
            self.digit_label.text = str(next_digit)

        local = clamp(self._switch_elapsed / max(0.001, self._switch_interval), 0.0, 1.0)
        self._position_digit_labels(ease_out_cubic(local))
        pulse = 0.55 + 0.45 * math.sin(self._elapsed * 18.0)
        self.digit_label.color = rgba(shade(LOGO_ORANGE_DARK, int(35 * pulse)))
        return True

    def _layout_children(self, *_args) -> None:
        self._redraw()
        x, y = self.pos
        w, h = self.size
        s = self._scale
        caption_h = max(16, 22 * s)
        self.caption.pos = (x, y + h + 3 * s)
        self.caption.size = (w, caption_h)
        self.caption.font_size = max(10, 17 * s)
        self.caption.text_size = self.caption.size

        clip_x = x + 16 * s
        clip_y = y + 18 * s
        clip_w = w - 32 * s
        clip_h = h - 42 * s
        self.clip_area.pos = (clip_x, clip_y)
        self.clip_area.size = (clip_w, clip_h)
        self._normal_label_y = clip_y
        self._clip_h = max(1, clip_h)

        for label in (self.previous_label, self.digit_label):
            label.size = (clip_w, clip_h)
            label.font_size = max(34, 116 * s)
            label.text_size = label.size
        self._position_digit_labels(0.0)

    def _position_digit_labels(self, fall_progress: float) -> None:
        fall = self._clip_h * clamp(fall_progress, 0.0, 1.0)
        base_x = self.clip_area.x
        self.previous_label.pos = (base_x, self._normal_label_y - fall)
        self.digit_label.pos = (
            base_x,
            self._normal_label_y + (self._clip_h - fall if self.spinning else 0),
        )

    def _redraw(self) -> None:
        self.canvas.before.clear()
        x, y = self.pos
        w, h = self.size
        s = self._scale
        if w <= 0 or h <= 0:
            return

        with self.canvas.before:
            Color(0, 0, 0, 0.75)
            RoundedRectangle(pos=(x, y - 8 * s), size=(w, h), radius=[10 * s])
            Color(*rgba(LOGO_ORANGE))
            RoundedRectangle(pos=(x - 8 * s, y - 8 * s), size=(w + 16 * s, h + 16 * s), radius=[12 * s])
            Color(*rgba((236, 232, 222)))
            RoundedRectangle(pos=(x, y), size=(w, h), radius=[8 * s])
            Color(*rgba((36, 40, 41)))
            Line(rectangle=(x - 8 * s, y - 8 * s, w + 16 * s, h + 16 * s), width=max(1, 3 * s))
            Color(*rgba(self.accent))
            Rectangle(pos=(x, y + h - 9 * s), size=(w, 9 * s))
            Color(*rgba((203, 199, 190), 0.45))
            for index in range(7):
                yy = y + 20 * s + index * 22 * s
                Line(points=(x + 16 * s, yy, x + w - 16 * s, yy), width=max(1, s))


class SceneCanvas(Widget):
    def __init__(self, owner: "LotteryRoot", **kwargs) -> None:
        super().__init__(**kwargs)
        self.owner = owner
        rng = random.Random(20260527)
        star_colors = [LOGO_ORANGE, LOGO_ORANGE_LIGHT, LOGO_TEAL, LOGO_TEAL_LIGHT, LOGO_GRAY_LIGHT]
        self.stars = [
            (
                rng.randint(0, SCREEN_WIDTH - 1),
                rng.randint(0, SCREEN_HEIGHT - 1),
                rng.choice([1, 1, 2, 2, 3]),
                rng.uniform(1.2, 3.8),
                rng.uniform(0, math.tau),
                rng.choice(star_colors),
            )
            for _ in range(155)
        ]
        self.elapsed = 0.0
        self.background_twinkles: list[Particle] = []
        self.next_twinkle_at = 0.15
        self.shooting_stars: list[ShootingStar] = []
        self.next_shooting_star_at = random.uniform(1.0, 2.8)
        self.bind(pos=lambda *_: self.redraw(), size=lambda *_: self.redraw())

    def update(self, dt: float) -> None:
        self.elapsed += dt
        self.next_twinkle_at -= dt
        if self.next_twinkle_at <= 0:
            self.next_twinkle_at = random.uniform(0.11, 0.28)
            for _ in range(random.randint(4, 8)):
                life = random.uniform(0.55, 1.15)
                self.background_twinkles.append(
                    Particle(
                        random.uniform(10, 940),
                        random.uniform(12, 520),
                        0,
                        0,
                        life,
                        life,
                        random.choice([2, 3, 4]),
                        random.choice([LOGO_ORANGE, LOGO_ORANGE_LIGHT, LOGO_TEAL, LOGO_TEAL_LIGHT, LOGO_GRAY_LIGHT]),
                        "star",
                        gravity=0,
                    )
                )
        self.next_shooting_star_at -= dt
        if self.next_shooting_star_at <= 0:
            self.next_shooting_star_at = random.uniform(1.3, 3.6)
            self.shooting_stars.append(
                ShootingStar(
                    random.uniform(-80, 760),
                    random.uniform(-10, 220),
                    random.uniform(360, 560),
                    random.uniform(160, 310),
                    random.uniform(0.8, 1.25),
                    1.25,
                    random.choice([LOGO_ORANGE_LIGHT, LOGO_TEAL_LIGHT, LOGO_GRAY_LIGHT]),
                )
            )
        self.background_twinkles = [sparkle for sparkle in self.background_twinkles if sparkle.update(dt)]
        self.shooting_stars = [star for star in self.shooting_stars if star.update(dt)]
        self.redraw()

    def drect(self, x: float, y: float, w: float, h: float) -> tuple[float, float, float, float]:
        return self.owner.scene_rect(x, y, w, h)

    def dpoint(self, x: float, y: float) -> tuple[float, float]:
        return self.owner.scene_point(x, y)

    def rounded(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        color: tuple[int, int, int],
        radius: float = 8,
        alpha: float = 1.0,
    ) -> None:
        px, py, pw, ph = self.drect(x, y, w, h)
        s = self.owner.scene_scale
        Color(*rgba(color, alpha))
        RoundedRectangle(pos=(px, py), size=(pw, ph), radius=[max(1, radius * s)])

    def outline(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        color: tuple[int, int, int],
        width: float = 2,
        alpha: float = 1.0,
    ) -> None:
        px, py, pw, ph = self.drect(x, y, w, h)
        Color(*rgba(color, alpha))
        Line(rectangle=(px, py, pw, ph), width=max(1, width * self.owner.scene_scale))

    def redraw(self) -> None:
        s = self.owner.scene_scale
        ox, oy = self.owner.scene_offset
        scene_w = SCREEN_WIDTH * s
        scene_h = SCREEN_HEIGHT * s
        now = self.elapsed

        self.canvas.clear()
        with self.canvas:
            Color(*rgba(BG_DEEP))
            Rectangle(pos=self.pos, size=self.size)
            Color(*rgba(BG_DARK))
            Rectangle(pos=(ox, oy), size=(scene_w, scene_h))

            for x, y, size, speed, phase, color in self.stars:
                twinkle = 0.35 + 0.55 * (0.5 + 0.5 * math.sin(now * speed + phase))
                px, py, pw, ph = self.drect(x, y, size, size)
                Color(*rgba(color, twinkle))
                Rectangle(pos=(px, py), size=(max(1, pw), max(1, ph)))
                if size >= 2:
                    Color(*rgba(color, twinkle * 0.45))
                    Line(points=(px - 3 * s, py + ph / 2, px + pw + 3 * s, py + ph / 2), width=max(1, s))
                    Line(points=(px + pw / 2, py - 3 * s, px + pw / 2, py + ph + 3 * s), width=max(1, s))

            for star in self.shooting_stars:
                alpha = clamp(star.life / star.max_life, 0.0, 1.0)
                head = self.dpoint(star.x, star.y)
                speed = max(1.0, math.hypot(star.vx, star.vy))
                tail = self.dpoint(star.x - star.vx / speed * 170, star.y - star.vy / speed * 170)
                Color(*rgba(star.color, 0.7 * alpha))
                Line(points=(tail[0], tail[1], head[0], head[1]), width=max(2, 5 * s))
                Color(*rgba(WHITE, 0.85 * alpha))
                Ellipse(pos=(head[0] - 5 * s, head[1] - 5 * s), size=(10 * s, 10 * s))

            for sparkle in self.background_twinkles:
                alpha = clamp(sparkle.life / sparkle.max_life, 0.0, 1.0)
                px, py = self.dpoint(sparkle.x, sparkle.y)
                unit = max(1.0, sparkle.size * s)
                Color(*rgba(sparkle.color, alpha))
                Rectangle(pos=(px - unit / 2, py - unit * 2), size=(unit, unit * 4))
                Rectangle(pos=(px - unit * 2, py - unit / 2), size=(unit * 4, unit))

            for index in range(9):
                y = 560 + index * 24
                color = (9 + index * 3, 11 + index * 3, 12 + index * 3)
                self.rounded(0, y, SCREEN_WIDTH, 24, color, 0, 1.0)
                if index % 2 == 0:
                    line_color = LOGO_TEAL_DARK if index % 4 == 0 else LOGO_ORANGE_DARK
                    px, py = self.dpoint(0, y)
                    Color(*rgba(line_color))
                    Line(points=(px, py, px + SCREEN_WIDTH * s, py), width=max(1, s))

            moon_x, moon_y = self.dpoint(105, 125)
            Color(*rgba(LOGO_ORANGE, 0.96))
            Ellipse(pos=(moon_x - 46 * s, moon_y - 46 * s), size=(92 * s, 92 * s))
            Color(*rgba(BG_DARK))
            Ellipse(pos=(moon_x - 16 * s, moon_y - 29 * s), size=(98 * s, 98 * s))
            Color(*rgba(LOGO_TEAL, 0.72))
            Ellipse(pos=(moon_x - 30 * s, moon_y - 23 * s), size=(34 * s, 34 * s))

            # Main screen shapes follow the original pygame coordinate map.
            self.rounded(14, 32, 520, 44, LOGO_ORANGE, 8, 0.2)
            self.rounded(20, 38, 506, 34, PANEL_LIGHT, 7, 0.96)
            for index in range(10):
                color = LOGO_ORANGE if index % 2 == 0 else LOGO_TEAL
                px, py, pw, ph = self.drect(44 + index * 50, 74, 30, 4)
                Color(*rgba(color))
                Rectangle(pos=(px, py), size=(pw, ph))

            self.rounded(38, 536, 348, 160, PANEL_LIGHT, 8, 0.96)
            self.outline(38, 536, 348, 160, PANEL_EDGE, 2, 0.9)

            pulse = 0.4 + 0.35 * math.sin(now * 4.5)
            active = self.owner.state in {
                STATE_SPINNING_TENS,
                STATE_TENS_REVEALED,
                STATE_SPINNING_ONES,
                STATE_BATCH_REVEAL,
            }
            glow_alpha = 0.14 + (0.2 * pulse if active else 0.03)
            cx, cy = self.dpoint(640, 330)
            for radius, color in ((230, LOGO_ORANGE), (190, LOGO_TEAL), (150, LOGO_ORANGE_LIGHT)):
                Color(*rgba(color, glow_alpha))
                Line(circle=(cx, cy, radius * s), width=max(4, 8 * s))
            for index in range(18):
                angle = now * 1.5 + index * math.tau / 18
                inner = 118
                outer = 245 + 20 * math.sin(now * 4.0 + index)
                start = self.dpoint(640 + math.cos(angle) * inner, 330 + math.sin(angle) * inner)
                end = self.dpoint(640 + math.cos(angle) * outer, 330 + math.sin(angle) * outer)
                ray_color = LOGO_TEAL if index % 2 else LOGO_ORANGE
                Color(*rgba(ray_color, 0.24 if active else 0.08))
                Line(points=(start[0], start[1], end[0], end[1]), width=max(1.5, 4 * s))

            self.rounded(396, 142, 488, 380, LOGO_ORANGE, 18)
            self.rounded(405, 151, 470, 362, PANEL_LIGHT, 14)
            self.outline(396, 142, 488, 380, (38, 42, 43), 4)
            self.rounded(550, 88, 180, 54, PANEL_LIGHT, 10)
            self.outline(550, 88, 180, 54, LOGO_GRAY_LIGHT, 1.5)
            self.rounded(440, 172, 392, 252, LOGO_TEAL, 12)
            self.outline(440, 172, 392, 252, (36, 40, 41), 4)

            bulb_colors = [LOGO_ORANGE, LOGO_ORANGE_LIGHT, LOGO_TEAL, LOGO_GRAY_LIGHT]
            for index in range(18):
                row = 0 if index < 9 else 1
                col = index if row == 0 else index - 9
                x = 468 + col * 48
                y = 190 if row == 0 else 406
                color = bulb_colors[(index + int(now * 5)) % len(bulb_colors)]
                px, py = self.dpoint(x, y)
                Color(*rgba(color))
                Rectangle(pos=(px - 5 * s, py - 5 * s), size=(10 * s, 10 * s))

            banner_color = LOGO_TEAL if active else LOGO_GRAY
            self.rounded(468, 442, 346, 62, PANEL_LIGHT, 10)
            self.outline(468, 442, 346, 62, banner_color, 3)
            for x in range(482, 790, 34):
                color = LOGO_ORANGE if (x + int(now * 80)) % 68 < 34 else LOGO_TEAL
                px1, py1, pw1, ph1 = self.drect(x, 452, 14, 4)
                px2, py2, pw2, ph2 = self.drect(x, 492, 14, 4)
                Color(*rgba(color))
                Rectangle(pos=(px1, py1), size=(pw1, ph1))
                Rectangle(pos=(px2, py2), size=(pw2, ph2))

            self.rounded(408, 574, 448, 42, PANEL_LIGHT, 8)
            self.outline(408, 574, 448, 42, LOGO_TEAL, 1.5)

            if self.owner.state == STATE_FINAL_REVEALED and self.owner.latest_batch:
                if len(self.owner.latest_batch) == 1:
                    self.rounded(950, 226, 260, 170, BG_DARK, 12, 0.72)
                    self.outline(950, 226, 260, 170, LOGO_TEAL, 3)
                else:
                    self.rounded(930, 196, 300, 260, BG_DARK, 12, 0.72)
                    self.outline(930, 196, 300, 260, LOGO_TEAL, 3)


class ParticleLayer(Widget):
    def __init__(self, owner: "LotteryRoot", **kwargs) -> None:
        super().__init__(**kwargs)
        self.owner = owner
        self.particles: list[Particle] = []

    def spawn_burst(
        self,
        origin: tuple[float, float],
        count: int,
        *,
        colors: list[tuple[int, int, int]] | None = None,
        kinds: list[str] | None = None,
        speed_range: tuple[float, float] = (80, 360),
        life_range: tuple[float, float] = (0.75, 1.5),
    ) -> None:
        colors = colors or [GOLD, LOGO_ORANGE_LIGHT, CYAN, MINT, PEACH]
        kinds = kinds or ["star", "circle", "heart"]
        ox, oy = origin
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(*speed_range)
            life = random.uniform(*life_range)
            self.particles.append(
                Particle(
                    ox + random.uniform(-24, 24),
                    oy + random.uniform(-20, 20),
                    math.cos(angle) * speed,
                    math.sin(angle) * speed - random.uniform(30, 120),
                    life,
                    life,
                    random.choice([2.5, 3.5, 4.5]),
                    random.choice(colors),
                    random.choice(kinds),
                    gravity=random.uniform(120, 240),
                )
            )
        if len(self.particles) > 360:
            self.particles = self.particles[-360:]

    def update(self, dt: float) -> None:
        self.particles = [particle for particle in self.particles if particle.update(dt)]
        self.redraw()

    def redraw(self) -> None:
        self.canvas.clear()
        s = self.owner.scene_scale
        with self.canvas:
            for particle in self.particles:
                alpha = clamp(particle.life / particle.max_life, 0.0, 1.0)
                px, py = self.owner.scene_point(particle.x, particle.y)
                unit = max(2.0, particle.size * s)
                Color(*rgba(particle.color, alpha))
                if particle.kind == "heart":
                    for dx, dy in ((-1, 0), (1, 0), (-2, 1), (0, 1), (2, 1), (-1, 2), (1, 2), (0, 3)):
                        Rectangle(pos=(px + dx * unit, py - dy * unit), size=(unit, unit))
                elif particle.kind == "circle":
                    Ellipse(pos=(px - unit * 1.6, py - unit * 1.6), size=(unit * 3.2, unit * 3.2))
                else:
                    Rectangle(pos=(px - unit / 2, py - unit * 2.2), size=(unit, unit * 4.4))
                    Rectangle(pos=(px - unit * 2.2, py - unit / 2), size=(unit * 4.4, unit))

            if self.owner.flash_elapsed is not None:
                elapsed = self.owner.flash_elapsed
                if 0 <= elapsed <= self.owner.flash_duration:
                    if elapsed < 0.18:
                        Color(0, 0, 0, 0.38 * (1 - elapsed / 0.18))
                        Rectangle(pos=self.pos, size=self.size)
                    if 0.05 <= elapsed <= 0.24:
                        flash_t = 1 - abs(elapsed - 0.135) / 0.095
                        Color(*rgba(LOGO_ORANGE, 0.42 * clamp(flash_t, 0.0, 1.0)))
                        Rectangle(pos=self.pos, size=self.size)


class LotteryRoot(FloatLayout):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        Window.clearcolor = rgba(BG_DEEP)
        self.scene_scale = 1.0
        self.scene_offset = (0.0, 0.0)
        self.shake_x = 0.0
        self.shake_y = 0.0

        self.state = STATE_IDLE
        self.number_pool = list(range(1, 51))
        self.won_numbers: set[int] = set()
        self.draw_total = 0
        self.history: list[int] = []
        self.latest_batch: list[int] = []
        self.batch_draw_numbers: list[int] = []
        self.batch_draw_index = 0
        self.target_number: int | None = None
        self.draw_events: list[Any] = []
        self.message_event: Any | None = None
        self.flash_elapsed: float | None = None
        self.flash_duration = 0.62
        self.shake_elapsed: float | None = None
        self.shake_duration = 0.56
        self.success_sound = self.load_sound("assets/success.mp3")
        self.roulette_sound = self.load_sound("assets/roulette_spin.mp3")
        self.roulette_sound_active = False

        self.scene = SceneCanvas(self)
        self.add_widget(self.scene)

        self.title_shadow_deep = self.make_label("2026 APRIL HOMECOMING", 39, INK, "left", True)
        self.title_shadow_teal = self.make_label("2026 APRIL HOMECOMING", 39, LOGO_TEAL, "left", True)
        self.title_shadow_light = self.make_label("2026 APRIL HOMECOMING", 39, LOGO_GRAY_LIGHT, "left", True)
        self.title_label = self.make_label("2026 APRIL HOMECOMING", 39, LOGO_ORANGE_LIGHT, "left", True)
        self.event_label = self.make_label("", 1, LOGO_TEAL_LIGHT, "left", True)
        for title_layer in (
            self.title_shadow_deep,
            self.title_shadow_teal,
            self.title_shadow_light,
            self.title_label,
        ):
            title_layer.outline_width = 1
            title_layer.outline_color = rgba((0, 0, 0), 0.95)
        self.range_caption = self.make_label("추첨 번호", 18, LOGO_GRAY_LIGHT, "left", True)
        self.status_label = self.make_label(self.default_message(), 18, WHITE, "center", True)
        self.banner_label = self.make_label("번호 추첨 대기", 24, WHITE, "center", True)

        self.number_input = TextInput(
            text="1-50",
            size_hint=(None, None),
            multiline=False,
            font_name=FONT_NAME,
            foreground_color=rgba(INK),
            background_color=rgba((232, 234, 229)),
            cursor_color=rgba(LOGO_ORANGE),
            write_tab=False,
        )
        self.number_input.base_font_size = 19
        self.draw_count_input = TextInput(
            text="1",
            size_hint=(None, None),
            multiline=False,
            input_filter="int",
            font_name=FONT_NAME,
            foreground_color=rgba(INK),
            background_color=rgba((232, 234, 229)),
            cursor_color=rgba(LOGO_ORANGE),
            write_tab=False,
            halign="center",
        )
        self.draw_count_input.base_font_size = 22

        self.apply_button = RouletteButton(
            text="Apply",
            size_hint=(None, None),
            accent=LOGO_TEAL,
            base_font_size=17,
        )
        self.unwon_button = RouletteButton(
            text="미당첨 번호",
            size_hint=(None, None),
            accent=LOGO_TEAL,
            base_font_size=19,
        )
        self.start_button = RouletteButton(
            text="Start",
            size_hint=(None, None),
            accent=LOGO_ORANGE,
            base_font_size=27,
        )
        self.reset_button = RouletteButton(
            text="Reset",
            size_hint=(None, None),
            accent=LOGO_ORANGE_DARK,
            base_font_size=22,
        )

        self.stats_caption_labels: list[Label] = []
        self.stats_value_labels: list[Label] = []
        for caption in ("전체", "당첨", "남음"):
            self.stats_caption_labels.append(self.make_label(caption, 14, LOGO_GRAY_LIGHT, "center", True))
            self.stats_value_labels.append(self.make_label("0", 28, WHITE, "center", True))

        self.history_title = self.make_label("최근 당첨", 21, GOLD, "left", True)
        self.history_labels = [self.make_label("", 18, LOGO_GRAY_LIGHT, "left", False) for _ in range(8)]

        self.machine_title = self.make_label("NUMBER DRAW", 17, LOGO_ORANGE_LIGHT, "center", True)
        self.tens_digit = DigitSlot("TENS", LOGO_TEAL)
        self.ones_digit = DigitSlot("ONES", LOGO_ORANGE)

        self.draw_count_caption = self.make_label("추첨 인원", 17, LOGO_GRAY_LIGHT, "left", True)
        self.person_label = self.make_label("명", 22, LOGO_GRAY_LIGHT, "left", True)

        self.result_title = self.make_label("결과", 22, LOGO_ORANGE_LIGHT, "center", True)
        self.result_number = self.make_label("--", 66, WHITE, "center", True)
        self.result_list = self.make_label("추첨 결과가 여기에 표시됩니다.", 18, LOGO_GRAY_LIGHT, "center", False)
        self.congrats_label = self.make_label("CONGRATULATIONS!", 20, LOGO_GRAY_LIGHT, "center", True)
        self.result_scroll = ScrollView(
            size_hint=(None, None),
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=4,
            opacity=0,
            disabled=True,
        )
        self.result_grid = GridLayout(cols=5, spacing=4, size_hint_y=None)
        self.result_grid.bind(minimum_height=self.result_grid.setter("height"))
        self.result_scroll.add_widget(self.result_grid)

        for widget in (
            self.title_shadow_deep,
            self.title_shadow_teal,
            self.title_shadow_light,
            self.title_label,
            self.event_label,
            self.range_caption,
            self.number_input,
            self.apply_button,
            self.unwon_button,
            *self.stats_caption_labels,
            *self.stats_value_labels,
            self.history_title,
            *self.history_labels,
            self.machine_title,
            self.tens_digit,
            self.ones_digit,
            self.banner_label,
            self.status_label,
            self.draw_count_caption,
            self.draw_count_input,
            self.person_label,
            self.result_title,
            self.result_number,
            self.result_list,
            self.result_scroll,
            self.congrats_label,
            self.start_button,
            self.reset_button,
        ):
            self.add_widget(widget)

        self.particles = ParticleLayer(self)
        self.add_widget(self.particles)

        self.apply_button.bind(on_release=lambda _button: self.apply_number_pool())
        self.start_button.bind(on_release=lambda _button: self.handle_start())
        self.reset_button.bind(on_release=lambda _button: self.handle_reset())
        self.unwon_button.bind(on_release=lambda _button: self.open_unwon_popup())
        self.number_input.bind(on_text_validate=lambda _input: self.apply_number_pool())
        self.draw_count_input.bind(on_text_validate=lambda _input: self.handle_start())

        self.bind(pos=self.layout_scene, size=self.layout_scene)
        Clock.schedule_once(self.layout_scene, 0)
        Clock.schedule_interval(self.tick, 1 / FPS)
        self.update_ui()

    def make_label(
        self,
        text: str,
        font_size: int,
        color: tuple[int, int, int],
        halign: str,
        bold: bool = False,
    ) -> Label:
        label = Label(
            text=text,
            size_hint=(None, None),
            font_name=FONT_NAME,
            font_size=font_size,
            color=rgba(color),
            halign=halign,
            valign="middle",
            bold=bold,
            shorten=False,
        )
        if bold:
            label.outline_width = 1
            label.outline_color = rgba((0, 0, 0), 0.85)
        label.base_font_size = font_size
        return label

    def scene_rect(self, x: float, y: float, w: float, h: float) -> tuple[float, float, float, float]:
        sx, sy = self.scene_offset
        s = self.scene_scale
        return sx + (x + self.shake_x) * s, sy + (SCREEN_HEIGHT - y - h + self.shake_y) * s, w * s, h * s

    def scene_point(self, x: float, y: float) -> tuple[float, float]:
        sx, sy = self.scene_offset
        s = self.scene_scale
        return sx + (x + self.shake_x) * s, sy + (SCREEN_HEIGHT - y + self.shake_y) * s

    def place(self, widget: Widget, x: float, y: float, w: float, h: float) -> None:
        widget.size_hint = (None, None)
        px, py, pw, ph = self.scene_rect(x, y, w, h)
        widget.pos = (px, py)
        widget.size = (pw, ph)
        if hasattr(widget, "base_font_size"):
            widget.font_size = max(10, widget.base_font_size * self.scene_scale)
        if hasattr(widget, "text_size"):
            widget.text_size = (pw, ph)
        if isinstance(widget, TextInput):
            font_size = max(12, widget.base_font_size * self.scene_scale)
            widget.font_size = font_size
            pad_x = max(8, 12 * self.scene_scale)
            pad_y = max(2, (ph - font_size * 1.35) / 2)
            widget.padding = [pad_x, pad_y, pad_x, pad_y]

    def place_unshaken(self, widget: Widget, x: float, y: float, w: float, h: float) -> None:
        old_x, old_y = self.shake_x, self.shake_y
        self.shake_x = 0.0
        self.shake_y = 0.0
        self.place(widget, x, y, w, h)
        self.shake_x, self.shake_y = old_x, old_y

    def layout_scene(self, *_args) -> None:
        width, height = max(1, self.width), max(1, self.height)
        self.scene_scale = min(width / SCREEN_WIDTH, height / SCREEN_HEIGHT)
        self.scene_offset = (
            self.x + (width - SCREEN_WIDTH * self.scene_scale) / 2,
            self.y + (height - SCREEN_HEIGHT * self.scene_scale) / 2,
        )
        self.scene.pos = self.pos
        self.scene.size = self.size
        self.particles.pos = self.pos
        self.particles.size = self.size

        self.place(self.title_shadow_deep, 43, 39, 520, 42)
        self.place(self.title_shadow_teal, 41, 37, 520, 42)
        self.place(self.title_shadow_light, 36, 32, 520, 42)
        self.place(self.title_label, 38, 34, 520, 42)
        self.place(self.event_label, 0, 0, 1, 1)
        self.place(self.range_caption, 1030, 8, 150, 24)
        self.place(self.number_input, 1044, 42, 140, 38)
        self.place(self.apply_button, 1192, 38, 72, 38)

        self.place(self.unwon_button, 38, 488, 206, 38)
        stat_x = [450, 450, 450]
        for index, x in enumerate(stat_x):
            self.place(self.stats_caption_labels[index], x, 705, 1, 1)
            self.place(self.stats_value_labels[index], x, 705, 1, 1)
            self.stats_caption_labels[index].opacity = 0
            self.stats_value_labels[index].opacity = 0

        self.place(self.history_title, 56, 550, 180, 30)
        for index, label in enumerate(self.history_labels):
            self.place(label, 58, 596 + index * 19, 278, 20)

        self.place(self.machine_title, 550, 100, 180, 30)
        self.tens_digit.place(self, 468, 202, 152, 188)
        self.ones_digit.place(self, 652, 202, 152, 188)
        self.place(self.banner_label, 486, 454, 310, 38)
        self.place(self.status_label, 420, 579, 422, 30)

        self.place(self.draw_count_caption, 846, 608, 100, 22)
        self.place(self.draw_count_input, 846, 636, 72, 58)
        self.place(self.person_label, 928, 654, 48, 34)
        self.place(self.start_button, 424, 636, 228, 58)
        self.place(self.reset_button, 678, 636, 148, 58)

        self.place(self.congrats_label, 70, 250, 300, 100)
        if len(self.latest_batch) == 1:
            self.place(self.result_title, 954, 236, 252, 30)
            self.place(self.result_number, 954, 270, 252, 70)
            self.place(self.result_list, 954, 344, 252, 26)
            self.place(self.result_scroll, 954, 372, 252, 1)
        else:
            self.place(self.result_title, 954, 218, 252, 32)
            self.place(self.result_number, 954, 256, 252, 76)
            self.place(self.result_list, 954, 334, 252, 26)
            self.place(self.result_scroll, 948, 366, 264, 72)
        self.refresh_result_grid()

        self.scene.redraw()
        self.particles.redraw()

    def refresh_result_grid(self) -> None:
        self.result_grid.clear_widgets()
        if len(self.latest_batch) <= 1:
            self.result_scroll.opacity = 0
            self.result_scroll.disabled = True
            return

        self.result_scroll.opacity = 1
        self.result_scroll.disabled = False
        s = self.scene_scale
        cols = 5 if len(self.latest_batch) <= 30 else 6
        spacing = max(3, 5 * s)
        chip_h = max(22, 28 * s)
        chip_w = max(34, (max(1, self.result_scroll.width) - spacing * (cols - 1)) / cols)
        self.result_grid.cols = cols
        self.result_grid.spacing = (spacing, spacing)
        self.result_grid.padding = [0, 0, 0, 0]
        self.result_grid.width = self.result_scroll.width

        for number in self.latest_batch:
            chip = NumberChip(
                text=str(number),
                size_hint=(None, None),
                size=(chip_w, chip_h),
                font_size=max(12, 16 * s),
            )
            self.result_grid.add_widget(chip)

    def tick(self, dt: float) -> None:
        shaking = False
        if self.shake_elapsed is not None:
            self.shake_elapsed += dt
            if self.shake_elapsed > self.shake_duration:
                self.shake_elapsed = None
                self.shake_x = 0.0
                self.shake_y = 0.0
            else:
                remaining = clamp((self.shake_duration - self.shake_elapsed) / self.shake_duration, 0.0, 1.0)
                power = max(1.0, 11.0 * remaining)
                self.shake_x = random.uniform(-power, power)
                self.shake_y = random.uniform(-power * 0.6, power * 0.6)
            shaking = True

        if shaking:
            self.layout_scene()

        if self.flash_elapsed is not None:
            self.flash_elapsed += dt
            if self.flash_elapsed > self.flash_duration:
                self.flash_elapsed = None
        self.scene.update(dt)
        self.particles.update(dt)

    def default_message(self) -> str:
        if self.state == STATE_IDLE:
            return "Start를 누르면 당첨 번호가 자동 추첨됩니다."
        if self.state == STATE_TENS_REVEALED:
            return "일의 자리 룰렛 준비 중..."
        if self.state == STATE_BATCH_REVEAL:
            return "당첨 번호를 순서대로 표시 중..."
        if self.state == STATE_FINAL_REVEALED:
            return "다음 추첨을 준비할 수 있습니다."
        return "번호 룰렛 작동 중..."

    def set_message(self, text: str, duration: float = 2.6) -> None:
        self.status_label.text = text
        if self.message_event is not None:
            self.message_event.cancel()
        self.message_event = Clock.schedule_once(lambda _dt: self.restore_default_message(), duration)

    def restore_default_message(self) -> None:
        self.status_label.text = self.default_message()

    def load_sound(self, relative_path: str):
        sound_path = Path(__file__).resolve().parent / relative_path
        if not sound_path.exists():
            return None
        return SoundLoader.load(str(sound_path))

    def restart_sound(self, sound) -> None:
        if sound is None:
            return
        try:
            sound.stop()
            sound.seek(0)
            sound.play()
        except Exception:
            return

    def play_success_sound(self) -> None:
        self.restart_sound(self.success_sound)

    def start_roulette_sound(self) -> None:
        if self.roulette_sound is None:
            return
        self.roulette_sound_active = True
        self.restart_sound(self.roulette_sound)

    def stop_roulette_sound(self) -> None:
        if self.roulette_sound is None:
            return
        try:
            self.roulette_sound.stop()
        except Exception:
            pass
        self.roulette_sound_active = False

    def schedule_draw_event(self, callback: Callable[[], None], delay: float) -> Any:
        event: Any | None = None

        def wrapped(_dt: float) -> None:
            if event in self.draw_events:
                self.draw_events.remove(event)
            callback()

        event = Clock.schedule_once(wrapped, delay)
        self.draw_events.append(event)
        return event

    def clear_draw_events(self) -> None:
        for event in self.draw_events:
            event.cancel()
        self.draw_events.clear()
        self.tens_digit.stop()
        self.ones_digit.stop()
        self.stop_roulette_sound()

    def active_draw_in_progress(self) -> bool:
        return self.state in {
            STATE_SPINNING_TENS,
            STATE_TENS_REVEALED,
            STATE_SPINNING_ONES,
            STATE_BATCH_REVEAL,
        }

    def parse_draw_count(self) -> tuple[int, str | None]:
        text = self.draw_count_input.text.strip()
        if not text:
            return 0, "추첨 인원을 입력하세요."
        if not text.isdigit():
            return 0, "추첨 인원은 숫자만 입력하세요."
        count = int(text)
        if count < 1:
            return 0, "추첨 인원은 1명 이상이어야 합니다."
        if count > 999:
            return 0, "한 번에 추첨할 인원은 999명 이하로 입력하세요."
        return count, None

    def parse_number_pool(self, text: str) -> tuple[list[int], str | None]:
        cleaned = text.replace("~", "-").replace(";", ",").replace("/", ",")
        cleaned = re.sub(r"\s*-\s*", "-", cleaned)
        cleaned = re.sub(r"\s+", ",", cleaned)
        tokens = [token.strip() for token in cleaned.split(",") if token.strip()]
        if not tokens:
            return [], "추첨 번호를 입력하세요."

        numbers: set[int] = set()
        for token in tokens:
            if "-" in token:
                parts = token.split("-", 1)
                if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
                    return [], "번호 형식은 1-50 또는 1,3,7-12처럼 입력하세요."
                start, end = int(parts[0]), int(parts[1])
                if start > end:
                    start, end = end, start
                numbers.update(range(start, end + 1))
            else:
                if not token.isdigit():
                    return [], "숫자, 쉼표, 범위(-)만 사용할 수 있습니다."
                numbers.add(int(token))

        if any(number < 1 or number > 99 for number in numbers):
            return [], "두 자리 룰렛에 맞게 1~99 사이 번호만 사용할 수 있습니다."

        return sorted(numbers), None

    def apply_number_pool(self) -> None:
        if self.active_draw_in_progress():
            self.set_message("룰렛이 멈춘 뒤 번호를 변경해 주세요.", 2.2)
            return

        numbers, error = self.parse_number_pool(self.number_input.text)
        if error:
            self.set_message(error, 3.0)
            return

        self.clear_draw_events()
        self.number_pool = numbers
        self.won_numbers.clear()
        self.draw_total = 0
        self.history.clear()
        self.latest_batch.clear()
        self.batch_draw_numbers.clear()
        self.batch_draw_index = 0
        self.target_number = None
        self.state = STATE_IDLE
        self.tens_digit.reset()
        self.ones_digit.reset()
        self.particles.particles.clear()
        self.flash_elapsed = None
        self.shake_elapsed = None
        self.shake_x = 0.0
        self.shake_y = 0.0
        self.set_message(f"추첨 번호 {len(numbers)}개가 적용되었습니다.", 2.6)
        self.update_ui()

    def unwon_numbers(self) -> list[int]:
        return [number for number in self.number_pool if number not in self.won_numbers]

    def draw_numbers_evenly(self, count: int) -> list[int]:
        if count <= 0 or not self.number_pool:
            return []
        return random.choices(self.number_pool, k=count)

    def format_numbers(self, numbers: list[int], limit: int = 14) -> str:
        shown = ", ".join(f"{number}번" for number in numbers[:limit])
        if len(numbers) > limit:
            shown += f" 외 {len(numbers) - limit}명"
        return shown

    def handle_start(self) -> None:
        if self.state == STATE_FINAL_REVEALED:
            self.prepare_next_draw()
            return
        if self.state != STATE_IDLE:
            return
        if not self.number_pool:
            self.set_message("추첨 번호를 먼저 설정하세요.", 2.6)
            return

        count, error = self.parse_draw_count()
        if error:
            self.set_message(error, 2.6)
            return

        self.clear_draw_events()
        self.latest_batch.clear()
        self.batch_draw_numbers.clear()
        self.batch_draw_index = 0
        self.tens_digit.reset()
        self.ones_digit.reset()
        selected_numbers = self.draw_numbers_evenly(count)

        if count > 1:
            self.start_batch_reveal(selected_numbers)
            return

        self.target_number = selected_numbers[0]
        self.state = STATE_SPINNING_TENS
        self.set_message("십의 자리 룰렛 회전 중...", 1.8)
        self.particles.spawn_burst((640, 250), 32, kinds=["star", "circle"], speed_range=(60, 240))
        self.start_roulette_sound()
        self.tens_digit.start_spin(self.target_number // 10, 2.3, self.on_tens_finished)
        self.update_ui()

    def on_tens_finished(self) -> None:
        if self.state != STATE_SPINNING_TENS:
            return
        self.stop_roulette_sound()
        self.state = STATE_TENS_REVEALED
        self.set_message("십의 자리 공개! 일의 자리 룰렛 준비 중...", 2.0)
        self.particles.spawn_burst((548, 338), 42, colors=[GOLD, CYAN, LOGO_ORANGE_LIGHT], kinds=["star", "circle"])
        self.update_ui()
        self.schedule_draw_event(self.start_ones_spin, 0.52)

    def start_ones_spin(self) -> None:
        if self.target_number is None:
            return
        self.state = STATE_SPINNING_ONES
        self.set_message("일의 자리 룰렛 회전 중...", 1.8)
        self.particles.spawn_burst((732, 338), 32, kinds=["star", "circle"], speed_range=(60, 240))
        self.start_roulette_sound()
        self.ones_digit.start_spin(self.target_number % 10, 2.45, self.finalize_winner)
        self.update_ui()

    def start_batch_reveal(self, numbers: list[int]) -> None:
        self.batch_draw_numbers = list(numbers)
        self.batch_draw_index = 0
        self.latest_batch.clear()
        self.state = STATE_BATCH_REVEAL
        self.set_message(f"{len(numbers)}명 추첨을 시작합니다.", 1.6)
        self.update_ui()
        self.show_batch_number()

    def show_batch_number(self) -> None:
        if self.batch_draw_index >= len(self.batch_draw_numbers):
            self.finish_draw(self.batch_draw_numbers)
            return

        number = self.batch_draw_numbers[self.batch_draw_index]
        self.target_number = number
        self.tens_digit.set_value(number // 10)
        self.ones_digit.set_value(number % 10)
        self.set_message(
            f"{self.batch_draw_index + 1}/{len(self.batch_draw_numbers)}번째 당첨 번호: {number}번",
            1.1,
        )
        self.particles.spawn_burst((640, 338), 34, speed_range=(90, 330), life_range=(0.55, 1.0))
        self.play_success_sound()
        self.update_ui()

        delay = 0.65 if len(self.batch_draw_numbers) <= 25 else 0.08
        self.schedule_draw_event(self.advance_batch_number, delay)

    def advance_batch_number(self) -> None:
        self.batch_draw_index += 1
        self.show_batch_number()

    def finalize_winner(self) -> None:
        if self.target_number is not None:
            self.stop_roulette_sound()
            self.finish_draw([self.target_number])

    def finish_draw(self, numbers: list[int]) -> None:
        if not numbers:
            return
        self.clear_draw_events()
        self.latest_batch = list(numbers)
        self.history = (self.latest_batch + self.history)[:40]
        self.won_numbers.update(self.latest_batch)
        self.draw_total += len(self.latest_batch)
        self.batch_draw_numbers.clear()
        self.batch_draw_index = 0
        self.state = STATE_FINAL_REVEALED
        self.flash_elapsed = 0.0
        self.shake_elapsed = 0.0
        if len(numbers) == 1:
            self.play_success_sound()
        burst_count = 150 if len(numbers) == 1 else 220
        for origin in ((548, 330), (732, 330), (640, 250), (640, 454)):
            self.particles.spawn_burst(
                origin,
                burst_count // 4,
                colors=[GOLD, LOGO_ORANGE_LIGHT, CYAN, MINT, PEACH, LOGO_GRAY_LIGHT],
                kinds=["star", "heart", "circle"],
                speed_range=(130, 520),
                life_range=(1.0, 1.9),
            )
        if len(numbers) == 1:
            self.set_message(f"당첨 번호: {numbers[0]}번", 4.2)
        else:
            self.set_message(f"{len(numbers)}명 당첨 완료", 5.2)
        self.update_ui()

    def prepare_next_draw(self) -> None:
        self.clear_draw_events()
        self.state = STATE_IDLE
        self.target_number = None
        self.latest_batch.clear()
        self.batch_draw_numbers.clear()
        self.batch_draw_index = 0
        self.tens_digit.reset()
        self.ones_digit.reset()
        self.flash_elapsed = None
        self.shake_elapsed = None
        self.shake_x = 0.0
        self.shake_y = 0.0
        self.set_message("다음 추첨을 준비했습니다.", 1.8)
        self.update_ui()

    def handle_reset(self) -> None:
        self.clear_draw_events()
        self.state = STATE_IDLE
        self.won_numbers.clear()
        self.draw_total = 0
        self.history.clear()
        self.latest_batch.clear()
        self.batch_draw_numbers.clear()
        self.batch_draw_index = 0
        self.target_number = None
        self.tens_digit.reset()
        self.ones_digit.reset()
        self.particles.particles.clear()
        self.flash_elapsed = None
        self.shake_elapsed = None
        self.shake_x = 0.0
        self.shake_y = 0.0
        self.set_message("초기화되었습니다. Start를 눌러 추첨하세요.", 2.4)
        self.update_ui()

    def update_ui(self) -> None:
        active = self.active_draw_in_progress()
        self.start_button.disabled = active
        self.apply_button.disabled = active
        self.number_input.disabled = active
        self.draw_count_input.disabled = active
        self.unwon_button.disabled = active

        if self.state == STATE_FINAL_REVEALED:
            self.start_button.text = "Next Draw"
        elif active:
            self.start_button.text = "Spinning..."
        else:
            self.start_button.text = "Start"

        stats = [len(self.number_pool), self.draw_total, len(self.unwon_numbers())]
        for label, value in zip(self.stats_value_labels, stats):
            label.text = str(value)

        if not self.history:
            self.history_labels[0].text = "아직 당첨 기록 없음"
            self.history_labels[0].opacity = 1
            for label in self.history_labels[1:]:
                label.text = ""
                label.opacity = 0
        else:
            visible_history = self.history[:5]
            for index, label in enumerate(self.history_labels):
                if index < len(visible_history):
                    label.opacity = 1
                    label.text = f"{index + 1}. {visible_history[index]}번"
                    label.color = rgba(WHITE if index == 0 else LOGO_GRAY_LIGHT)
                else:
                    label.text = ""
                    label.opacity = 0

        self.banner_label.text = self.banner_text()
        self.status_label.text = self.status_label.text or self.default_message()
        self.update_result_panel()
        self.refresh_result_grid()
        self.scene.redraw()

    def banner_text(self) -> str:
        if self.state == STATE_FINAL_REVEALED and self.latest_batch:
            return "당첨 완료" if len(self.latest_batch) == 1 else f"{len(self.latest_batch)}명 당첨 완료"
        if self.state == STATE_BATCH_REVEAL and self.batch_draw_numbers:
            current = min(self.batch_draw_index + 1, len(self.batch_draw_numbers))
            return f"{current}/{len(self.batch_draw_numbers)}번째 번호 표시 중"
        if self.active_draw_in_progress():
            return "번호 룰렛 작동 중"
        count, error = self.parse_draw_count()
        return "추첨 인원 확인 필요" if error else f"이번 추첨: {count}명"

    def update_result_panel(self) -> None:
        if not self.latest_batch:
            for widget in (self.result_title, self.congrats_label, self.result_number, self.result_list):
                widget.opacity = 0
            self.result_scroll.opacity = 0
            self.result_scroll.disabled = True
            self.congrats_label.base_font_size = 20
            self.result_number.base_font_size = 66
            self.result_title.text = "결과"
            self.congrats_label.text = ""
            self.result_number.text = "--"
            self.result_list.text = "추첨 결과가 여기에 표시됩니다."
            self.result_number.font_size = max(34, 66 * self.scene_scale)
            return

        for widget in (self.result_title, self.congrats_label, self.result_number, self.result_list):
            widget.opacity = 1
        self.result_title.text = "당첨 번호"
        self.congrats_label.text = "당첨!"
        self.congrats_label.color = rgba(GOLD)
        self.congrats_label.base_font_size = 82
        self.congrats_label.font_size = max(48, 82 * self.scene_scale)
        if len(self.latest_batch) == 1:
            self.result_number.text = f"{self.latest_batch[0]}번"
            self.result_number.base_font_size = 72
            self.result_number.font_size = max(38, 72 * self.scene_scale)
            self.result_list.text = "축하합니다!"
            self.result_scroll.opacity = 0
            self.result_scroll.disabled = True
        else:
            self.result_number.text = f"{len(self.latest_batch)}명"
            self.result_number.base_font_size = 58
            self.result_number.font_size = max(36, 58 * self.scene_scale)
            self.result_list.text = "당첨 번호 목록"
            self.result_scroll.opacity = 1
            self.result_scroll.disabled = False

    def open_unwon_popup(self) -> None:
        if self.active_draw_in_progress():
            return

        unwon = self.unwon_numbers()
        content = BoxLayout(orientation="vertical", padding=14, spacing=10)
        summary = Label(
            text=f"아직 나오지 않은 번호 {len(unwon)} / {len(self.number_pool)}",
            font_name=FONT_NAME,
            font_size=18,
            bold=True,
            color=rgba(WHITE),
            size_hint_y=None,
            height=34,
        )
        content.add_widget(summary)

        scroll = ScrollView(do_scroll_x=False)
        cols = max(4, min(8, int(max(Window.width, 640) / 150)))
        grid = GridLayout(cols=cols, spacing=8, size_hint_y=None, padding=[2, 2, 2, 2])
        grid.bind(minimum_height=grid.setter("height"))

        if not unwon:
            empty = Label(
                text="모든 번호가 한 번 이상 당첨되었습니다.",
                font_name=FONT_NAME,
                font_size=18,
                color=rgba(WHITE),
                size_hint_y=None,
                height=48,
            )
            grid.add_widget(empty)
        else:
            for number in unwon:
                grid.add_widget(NumberChip(text=str(number), size_hint_y=None, height=36, font_size=17))

        scroll.add_widget(grid)
        content.add_widget(scroll)

        close_button = RouletteButton(text="Close", accent=LOGO_ORANGE, size_hint_y=None, height=48, base_font_size=18)
        content.add_widget(close_button)

        popup = Popup(
            title="미당첨 번호",
            title_font=FONT_NAME,
            title_size=20,
            content=content,
            size_hint=(0.82, 0.82),
            background_color=rgba((18, 20, 22), 0.96),
        )
        close_button.bind(on_release=popup.dismiss)
        popup.open()


class PrizeDrawApp(App):
    title = "경품 추첨 룰렛"

    def build(self) -> LotteryRoot:
        if platform not in {"android", "ios"}:
            Window.size = (SCREEN_WIDTH, SCREEN_HEIGHT)
        return LotteryRoot()


def main() -> None:
    PrizeDrawApp().run()


if __name__ == "__main__":
    main()
