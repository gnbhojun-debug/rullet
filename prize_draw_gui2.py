# -*- coding: utf-8 -*-
"""
경품 추첨 가챠 룰렛

실행 방법
1. Python 3 설치
2. pygame 설치: python -m pip install pygame
3. 실행: python prize_draw_gui.py

pygame이 설치되어 있지 않으면 위 설치 명령을 먼저 실행하세요.
외부 이미지 파일 없이 코드 내부의 도형, 텍스트, 픽셀아트만 사용합니다.

경품명을 바꾸고 싶다면 아래 PRIZE_NAMES 리스트만 수정하면 됩니다.
"""

from __future__ import annotations

import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import pygame
except ImportError:
    print("pygame이 설치되어 있지 않습니다.")
    print("설치 명령: python -m pip install pygame")
    sys.exit(1)


SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

PRIZE_NAMES = [
    "1등 경품",
    "2등 경품",
    "3등 경품",
    "4등 경품",
    "5등 경품",
]

STATE_IDLE = "IDLE"
STATE_SPINNING_TENS = "SPINNING_TENS"
STATE_TENS_REVEALED = "TENS_REVEALED"
STATE_SPINNING_ONES = "SPINNING_ONES"
STATE_BULK_REVEALING = "BULK_REVEALING"
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
PANEL = (16, 18, 20)
PANEL_LIGHT = (27, 30, 33)
PANEL_EDGE = (73, 78, 82)
WHITE = (248, 249, 247)
INK = (15, 17, 18)
GOLD = LOGO_ORANGE
PINK = LOGO_ORANGE_LIGHT
MINT = LOGO_TEAL
CYAN = LOGO_TEAL_LIGHT
VIOLET = LOGO_GRAY
PEACH = LOGO_ORANGE_DARK

LOGO_IMAGE_CANDIDATES = [
    Path(__file__).resolve().parent / "그림1.png",
    Path(__file__).resolve().parent.parent / "그림1.png",
    Path(r"c:/Users/gnbho/OneDrive/바탕 화면/그림1.png"),
]

ROULETTE_Y_OFFSET = -36
RAINBOW_COLORS = [
    (255, 64, 64),
    (255, 148, 48),
    (255, 226, 64),
    (86, 226, 91),
    (64, 205, 255),
    (90, 120, 255),
    (190, 90, 255),
]


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def ease_out_cubic(t: float) -> float:
    t = clamp(t, 0.0, 1.0)
    return 1.0 - pow(1.0 - t, 3)


def ease_out_back(t: float) -> float:
    t = clamp(t, 0.0, 1.0)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)


def ease_in_out_sine(t: float) -> float:
    t = clamp(t, 0.0, 1.0)
    return -(math.cos(math.pi * t) - 1) / 2


def make_font(size: int, bold: bool = False) -> pygame.font.Font:
    """한글 표시가 가능한 시스템 폰트를 우선 사용합니다."""
    candidates = [
        "malgungothic",
        "malgun gothic",
        "맑은 고딕",
        "nanumgothic",
        "nanum gothic",
        "notosanscjkk",
        "noto sans cjk kr",
        "applesdgothicneo",
        "applegothic",
        "arialunicode",
        "arial",
    ]

    for name in candidates:
        path = pygame.font.match_font(name, bold=bold)
        if path:
            font = pygame.font.Font(path, size)
            font.set_bold(bold)
            return font

    font = pygame.font.SysFont(None, size, bold=bold)
    font.set_bold(bold)
    return font


def draw_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    pos: tuple[int, int],
    anchor: str = "center",
    shadow: bool = True,
    shadow_color: tuple[int, int, int] = (0, 0, 0),
    pixel: bool = False,
) -> pygame.Rect:
    """텍스트를 그림자와 함께 그립니다."""
    image = font.render(text, not pixel, color)
    rect = image.get_rect()
    setattr(rect, anchor, pos)

    if shadow:
        shadow_image = font.render(text, not pixel, shadow_color)
        shadow_rect = shadow_image.get_rect()
        setattr(shadow_rect, anchor, (pos[0] + 3, pos[1] + 3))
        surface.blit(shadow_image, shadow_rect)

    surface.blit(image, rect)
    return rect


def draw_text_fit(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    pos: tuple[int, int],
    max_width: int,
    anchor: str = "center",
    shadow: bool = False,
    shadow_color: tuple[int, int, int] = (0, 0, 0),
    pixel: bool = False,
) -> pygame.Rect:
    """텍스트가 정해진 너비를 넘으면 비율을 줄여 그립니다."""
    image = font.render(text, not pixel, color)
    shadow_image = font.render(text, not pixel, shadow_color) if shadow else None

    if image.get_width() > max_width:
        scale = max_width / image.get_width()
        new_size = (max(1, int(image.get_width() * scale)), max(1, int(image.get_height() * scale)))
        image = pygame.transform.scale(image, new_size)
        if shadow_image is not None:
            shadow_image = pygame.transform.scale(shadow_image, new_size)

    rect = image.get_rect()
    setattr(rect, anchor, pos)

    if shadow_image is not None:
        shadow_rect = shadow_image.get_rect()
        setattr(shadow_rect, anchor, (pos[0] + 3, pos[1] + 3))
        surface.blit(shadow_image, shadow_rect)

    surface.blit(image, rect)
    return rect


def draw_pixel_star(
    surface: pygame.Surface,
    x: float,
    y: float,
    unit: int,
    color: tuple[int, int, int],
) -> None:
    """작은 도트 별을 그립니다."""
    unit = max(1, unit)
    pattern = [
        (0, -2),
        (0, -1),
        (-2, 0),
        (-1, 0),
        (0, 0),
        (1, 0),
        (2, 0),
        (0, 1),
        (0, 2),
    ]
    for px, py in pattern:
        pygame.draw.rect(
            surface,
            color,
            pygame.Rect(int(x + px * unit), int(y + py * unit), unit, unit),
        )


def draw_pixel_heart(
    surface: pygame.Surface,
    x: float,
    y: float,
    unit: int,
    color: tuple[int, int, int],
) -> None:
    """작은 도트 하트를 그립니다."""
    unit = max(1, unit)
    rows = [
        "01100110",
        "11111111",
        "11111111",
        "01111110",
        "00111100",
        "00011000",
    ]
    for row_i, row in enumerate(rows):
        for col_i, cell in enumerate(row):
            if cell == "1":
                pygame.draw.rect(
                    surface,
                    color,
                    pygame.Rect(
                        int(x + (col_i - 4) * unit),
                        int(y + (row_i - 3) * unit),
                        unit,
                        unit,
                    ),
                )


def draw_pixel_circle(
    surface: pygame.Surface,
    x: float,
    y: float,
    unit: int,
    color: tuple[int, int, int],
) -> None:
    """도트 느낌의 작은 원형 파티클을 그립니다."""
    unit = max(1, unit)
    pattern = [
        "0110",
        "1111",
        "1111",
        "0110",
    ]
    for row_i, row in enumerate(pattern):
        for col_i, cell in enumerate(row):
            if cell == "1":
                pygame.draw.rect(
                    surface,
                    color,
                    pygame.Rect(
                        int(x + (col_i - 2) * unit),
                        int(y + (row_i - 2) * unit),
                        unit,
                        unit,
                    ),
                )


@dataclass
class Particle:
    """축하 효과에 쓰이는 별, 하트, 작은 원형 파티클입니다."""

    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    size: int
    color: tuple[int, int, int]
    kind: str
    gravity: float = 160.0

    def update(self, dt: float) -> bool:
        self.life -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        return self.life > 0

    def draw(self, surface: pygame.Surface) -> None:
        alpha = int(255 * clamp(self.life / self.max_life, 0.0, 1.0))
        unit = self.size
        box = max(24, unit * 12)
        temp = pygame.Surface((box, box), pygame.SRCALPHA)
        color = (*self.color, alpha)
        center = box // 2

        if self.kind == "heart":
            draw_pixel_heart(temp, center, center, unit, color)
        elif self.kind == "circle":
            draw_pixel_circle(temp, center, center, unit, color)
        else:
            draw_pixel_star(temp, center, center, unit, color)

        surface.blit(temp, (int(self.x - box / 2), int(self.y - box / 2)))


@dataclass
class ShootingStar:
    """배경을 가로질러 떨어지는 별똥별입니다."""

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
        return self.life > 0 and self.x < SCREEN_WIDTH + 120 and self.y < SCREEN_HEIGHT + 120

    def draw(self, surface: pygame.Surface) -> None:
        alpha = int(255 * clamp(self.life / self.max_life, 0.0, 1.0))
        length = 190
        speed = max(1.0, math.hypot(self.vx, self.vy))
        tail_x = self.x - self.vx / speed * length
        tail_y = self.y - self.vy / speed * length

        temp = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.line(
            temp,
            (*self.color, max(0, alpha - 125)),
            (int(tail_x), int(tail_y)),
            (int(self.x), int(self.y)),
            10,
        )
        pygame.draw.line(
            temp,
            (*self.color, alpha),
            (int(tail_x), int(tail_y)),
            (int(self.x), int(self.y)),
            6,
        )
        pygame.draw.line(
            temp,
            (*LOGO_GRAY_LIGHT, max(0, alpha - 35)),
            (int((tail_x + self.x) / 2), int((tail_y + self.y) / 2)),
            (int(self.x), int(self.y)),
            3,
        )
        pygame.draw.circle(temp, (*self.color, max(0, alpha - 30)), (int(self.x), int(self.y)), 9)
        draw_pixel_star(temp, self.x, self.y, 3, (*self.color, alpha))
        surface.blit(temp, (0, 0))


class Button:
    """도트풍 버튼입니다."""

    def __init__(
        self,
        rect: pygame.Rect,
        text: str,
        font: pygame.font.Font,
        accent: tuple[int, int, int],
        text_shadow: bool = True,
    ):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.accent = accent
        self.text_shadow = text_shadow
        self.enabled = True
        self.hovered = False
        self.pressed = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.enabled:
            self.pressed = False
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
                return False

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was_pressed = self.pressed
            self.pressed = False
            return was_pressed and self.rect.collidepoint(event.pos)

        return False

    def update(self, mouse_pos: tuple[int, int]) -> None:
        self.hovered = self.enabled and self.rect.collidepoint(mouse_pos)

    def draw(self, surface: pygame.Surface) -> None:
        shadow = self.rect.move(5, 6)
        pygame.draw.rect(surface, (0, 0, 0), shadow, border_radius=8)

        offset = 2 if self.pressed else 0
        rect = self.rect.move(0, offset)
        fill = self.accent if self.enabled else LOGO_GRAY_DARK
        if self.hovered and self.enabled:
            fill = tuple(min(255, c + 22) for c in fill)

        pygame.draw.rect(surface, fill, rect, border_radius=8)
        pygame.draw.rect(surface, LOGO_GRAY_LIGHT, rect.inflate(-8, -8), 2, border_radius=5)
        pygame.draw.rect(surface, INK, rect, 3, border_radius=8)

        label_color = INK if self.enabled else (190, 198, 216)
        draw_text(
            surface,
            self.text,
            self.font,
            label_color,
            rect.center,
            shadow=self.text_shadow,
            shadow_color=(255, 232, 186),
            pixel=False,
        )


class TextInput:
    """추첨 번호 범위를 직접 입력하는 간단한 텍스트 박스입니다."""

    def __init__(
        self,
        rect: pygame.Rect,
        text: str,
        font: pygame.font.Font,
        placeholder: str = "1-50",
        allowed: str = "0123456789,-~ ",
        max_length: int = 80,
    ):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.placeholder = placeholder
        self.allowed = allowed
        self.max_length = max_length
        self.active = False
        self.hovered = False
        self.cursor_visible = True
        self.cursor_timer = 0.0

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)
            return False

        if not self.active or event.type != pygame.KEYDOWN:
            return False

        if event.key == pygame.K_RETURN:
            return True
        if event.key == pygame.K_ESCAPE:
            self.active = False
            return False
        if event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
            return False

        if event.unicode and event.unicode in self.allowed and len(self.text) < self.max_length:
            self.text += event.unicode

        return False

    def update(self, dt: float, mouse_pos: tuple[int, int]) -> None:
        self.hovered = self.rect.collidepoint(mouse_pos)
        self.cursor_timer += dt
        if self.cursor_timer >= 0.5:
            self.cursor_timer = 0.0
            self.cursor_visible = not self.cursor_visible

    def draw(self, surface: pygame.Surface) -> None:
        shadow = self.rect.move(4, 5)
        pygame.draw.rect(surface, (0, 0, 0), shadow, border_radius=8)
        fill = (238, 236, 226) if self.active else (218, 222, 220)
        if self.hovered and not self.active:
            fill = (231, 229, 220)
        pygame.draw.rect(surface, fill, self.rect, border_radius=8)
        border = LOGO_ORANGE if self.active else LOGO_TEAL
        pygame.draw.rect(surface, border, self.rect, 3, border_radius=8)

        text = self.text if self.text else self.placeholder
        image = self.font.render(text, True, INK)
        if image.get_width() > self.rect.width - 22:
            scale = (self.rect.width - 22) / image.get_width()
            image = pygame.transform.scale(
                image,
                (max(1, int(image.get_width() * scale)), max(1, int(image.get_height() * scale))),
            )
        text_rect = image.get_rect(midleft=(self.rect.x + 12, self.rect.centery))
        surface.blit(image, text_rect)

        if self.active and self.cursor_visible:
            cursor_x = min(text_rect.right + 4, self.rect.right - 12)
            pygame.draw.line(
                surface,
                INK,
                (cursor_x, self.rect.y + 9),
                (cursor_x, self.rect.bottom - 9),
                2,
            )


class PrizeCard:
    """오른쪽 경품 카드입니다. 클릭하면 현재 추첨 경품으로 선택됩니다."""

    ACCENTS = [LOGO_ORANGE, LOGO_TEAL, LOGO_GRAY, LOGO_ORANGE_DARK, LOGO_TEAL_LIGHT]

    def __init__(
        self,
        rank: int,
        name: str,
        rect: pygame.Rect,
        fonts: dict[str, pygame.font.Font],
    ):
        self.rank = rank
        self.name = name
        self.rect = pygame.Rect(rect)
        self.fonts = fonts
        self.accent = self.ACCENTS[(rank - 1) % len(self.ACCENTS)]
        self.offset_x = 0.0
        self.hovered = False
        self.pulse = random.random() * 10

    def current_rect(self) -> pygame.Rect:
        return self.rect.move(int(self.offset_x), 0)

    def update(
        self,
        dt: float,
        selected: bool,
        inserted: bool,
        mouse_pos: tuple[int, int],
    ) -> None:
        self.hovered = self.current_rect().collidepoint(mouse_pos)
        target_offset = 0
        if selected:
            target_offset = -18
        if inserted:
            target_offset = -40

        self.offset_x += (target_offset - self.offset_x) * min(1.0, dt * 12)
        self.pulse += dt

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            return self.current_rect().collidepoint(event.pos)
        return False

    def draw(self, surface: pygame.Surface, selected: bool) -> None:
        rect = self.current_rect()
        shadow = rect.move(7, 7)
        pygame.draw.rect(surface, (0, 0, 0), shadow, border_radius=8)

        if selected:
            glow = pygame.Surface((rect.width + 28, rect.height + 28), pygame.SRCALPHA)
            pulse = int(50 + 40 * math.sin(self.pulse * 5))
            pygame.draw.rect(
                glow,
                (*self.accent, 90 + pulse),
                glow.get_rect(),
                border_radius=12,
            )
            surface.blit(glow, (rect.x - 14, rect.y - 14))

        bg = (247, 242, 232) if selected else (226, 229, 228)
        if self.hovered and not selected:
            bg = (240, 236, 226)

        pygame.draw.rect(surface, bg, rect, border_radius=8)
        pygame.draw.rect(surface, self.accent, (rect.x, rect.y, 12, rect.height), border_radius=6)
        pygame.draw.rect(surface, (38, 42, 43), rect, 3, border_radius=8)

        icon_center = (rect.x + 38, rect.y + rect.height // 2)
        pygame.draw.circle(surface, self.accent, icon_center, 19)
        pygame.draw.circle(surface, LOGO_GRAY_LIGHT, icon_center, 13)
        draw_pixel_star(surface, icon_center[0], icon_center[1], 3, self.accent)

        draw_text(
            surface,
            f"{self.rank}등",
            self.fonts["small_bold"],
            (43, 47, 48),
            (rect.x + 70, rect.y + 24),
            anchor="midleft",
            shadow=False,
        )
        draw_text_fit(
            surface,
            self.name,
            self.fonts["card"],
            INK,
            (rect.x + 70, rect.y + 56),
            rect.width - 88,
            anchor="midleft",
            shadow=False,
        )

        if selected:
            draw_text(
                surface,
                "SELECTED",
                self.fonts["tiny"],
                (43, 47, 48),
                (rect.right - 16, rect.y + 20),
                anchor="midright",
                shadow=False,
                pixel=True,
            )


class RouletteDigit:
    """십의자리와 일의자리 슬롯 하나를 담당합니다."""

    def __init__(
        self,
        rect: pygame.Rect,
        digits: list[int],
        font: pygame.font.Font,
        label_font: pygame.font.Font,
        label: str,
        accent: tuple[int, int, int],
    ):
        self.rect = pygame.Rect(rect)
        self.digits = digits
        self.font = font
        self.label_font = label_font
        self.label = label
        self.accent = accent
        self.value: int | None = None
        self.target = 0
        self.current_digit = random.choice(self.digits)
        self.previous_digit = self.current_digit
        self.spinning = False
        self.start_time = 0
        self.duration = 2200
        self.switch_start = 0
        self.switch_interval = 35
        self.next_switch_time = 0
        self.bounce_start = -9999

    def reset(self) -> None:
        self.value = None
        self.current_digit = random.choice(self.digits)
        self.previous_digit = self.current_digit
        self.spinning = False
        self.bounce_start = -9999

    def set_value(self, value: int, now_ms: int, bounce: bool = True) -> None:
        self.value = value
        self.target = value
        self.current_digit = value
        self.previous_digit = value
        self.spinning = False
        self.bounce_start = now_ms if bounce else -9999

    def start_spin(self, target: int, duration_ms: int, now_ms: int) -> None:
        self.target = target
        self.duration = duration_ms
        self.start_time = now_ms
        self.switch_start = now_ms
        self.switch_interval = 32
        self.next_switch_time = now_ms + self.switch_interval
        self.previous_digit = self.current_digit
        self.current_digit = random.choice(self.digits)
        self.value = None
        self.spinning = True

    def update(self, now_ms: int) -> bool:
        """회전이 끝난 프레임에 True를 반환합니다."""
        if not self.spinning:
            return False

        progress = clamp((now_ms - self.start_time) / self.duration, 0.0, 1.0)
        if progress >= 1.0:
            self.spinning = False
            self.value = self.target
            self.previous_digit = self.current_digit
            self.current_digit = self.target
            self.bounce_start = now_ms
            return True

        slow = ease_out_cubic(progress)
        self.switch_interval = int(30 + slow * 190)

        while now_ms >= self.next_switch_time:
            self.previous_digit = self.current_digit
            next_digit = random.choice(self.digits)
            if len(self.digits) > 1:
                while next_digit == self.current_digit:
                    next_digit = random.choice(self.digits)
            self.current_digit = next_digit
            self.switch_start = self.next_switch_time
            self.next_switch_time += self.switch_interval

        return False

    def draw_digit_text(
        self,
        surface: pygame.Surface,
        text: str,
        center: tuple[int, int],
        scale: float,
        color: tuple[int, int, int],
    ) -> None:
        image = self.font.render(text, False, color)
        if abs(scale - 1.0) > 0.01:
            w = max(1, int(image.get_width() * scale))
            h = max(1, int(image.get_height() * scale))
            image = pygame.transform.scale(image, (w, h))
        rect = image.get_rect(center=center)
        shadow = self.font.render(text, False, LOGO_GRAY_LIGHT)
        if abs(scale - 1.0) > 0.01:
            shadow = pygame.transform.scale(shadow, image.get_size())
        shadow_rect = shadow.get_rect(center=(center[0] + 4, center[1] + 4))
        surface.blit(shadow, shadow_rect)
        surface.blit(image, rect)

    def draw(self, surface: pygame.Surface, now_ms: int, external_scale: float = 1.0) -> None:
        rect = self.rect
        pygame.draw.rect(surface, (0, 0, 0), rect.move(0, 8), border_radius=10)
        pygame.draw.rect(surface, LOGO_ORANGE, rect.inflate(18, 18), border_radius=12)
        pygame.draw.rect(surface, (236, 232, 222), rect, border_radius=8)
        pygame.draw.rect(surface, (36, 40, 41), rect.inflate(18, 18), 4, border_radius=12)

        for i in range(8):
            y = rect.y + 14 + i * 22
            pygame.draw.line(surface, (203, 199, 190), (rect.x + 14, y), (rect.right - 14, y), 1)

        draw_text(
            surface,
            self.label,
            self.label_font,
            LOGO_GRAY_LIGHT,
            (rect.centerx, rect.y - 20),
            shadow=False,
            pixel=True,
        )

        clip_rect = rect.inflate(-16, -18)
        previous_clip = surface.get_clip()
        surface.set_clip(clip_rect)

        center_x = rect.centerx
        center_y = rect.centery + 4
        slot_h = rect.height
        scale = external_scale

        bounce_t = clamp((now_ms - self.bounce_start) / 520, 0.0, 1.0)
        if 0 < bounce_t < 1:
            bounce = math.sin(bounce_t * math.pi) * (1 - bounce_t)
            center_y -= int(18 * bounce)
            scale *= 1.0 + 0.18 * bounce

        if self.spinning:
            local = clamp((now_ms - self.switch_start) / max(1, self.switch_interval), 0.0, 1.0)
            fall = ease_out_cubic(local) * slot_h
            self.draw_digit_text(
                surface,
                str(self.previous_digit),
                (center_x, int(center_y + fall)),
                1.0,
                LOGO_GRAY_DARK,
            )
            self.draw_digit_text(
                surface,
                str(self.current_digit),
                (center_x, int(center_y - slot_h + fall)),
                1.0,
                INK,
            )
        else:
            text = "?" if self.value is None else str(self.value)
            self.draw_digit_text(surface, text, (center_x, center_y), scale, INK)

        surface.set_clip(previous_clip)

        pygame.draw.rect(surface, self.accent, (rect.x, rect.y, rect.width, 10), border_radius=6)
        pygame.draw.rect(surface, WHITE, (rect.x + 18, rect.y + 18, rect.width - 36, 6))


class GachaLotteryApp:
    """경품 카드 선택, 두 단계 룰렛, 당첨 기록을 관리하는 메인 앱입니다."""

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("경품 추첨 가챠 룰렛")
        self.fullscreen = False
        self.windowed_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
        self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.running = True

        self.fonts = {
            "title": make_font(38, True),
            "subtitle": make_font(22, True),
            "status": make_font(24, True),
            "button": make_font(26, True),
            "card": make_font(22, True),
            "small": make_font(17),
            "small_bold": make_font(18, True),
            "tiny": make_font(12, True),
            "digit": make_font(136, True),
            "digit_label": make_font(16, True),
            "congrats": make_font(58, True),
            "result": make_font(46, True),
        }

        self.state = STATE_IDLE
        self.number_pool: list[int] = list(range(1, 51))
        self.history: list[tuple[int, str, int]] = []
        self.rank_results: dict[int, list[int]] = {rank: [] for rank in range(1, 6)}
        self.selected_prize: int | None = None
        self.target_number: int | None = None
        self.last_draw_numbers: list[int] = []
        self.last_draw_is_bulk = False
        self.bulk_pending_numbers: list[int] = []
        self.bulk_reveal_index = 0
        self.bulk_next_reveal_at = 0
        self.last_winner_rank: int | None = None
        self.show_unwon_list = False
        self.result_modal_rank: int | None = None

        self.message = "경품 카드를 선택하고 Start를 눌러주세요."
        self.message_until = 0
        self.celebration_start = -9999
        self.shake_until = 0
        self.card_insert_until = 0
        self.device_pulse_until = 0

        self.particles: list[Particle] = []
        self.background_twinkles: list[Particle] = []
        self.shooting_stars: list[ShootingStar] = []
        self.next_twinkle_at = 0
        self.next_shooting_star_at = 0
        self.background_stars = self.make_background_stars()
        self.logo_image = self.load_logo_image()

        self.tens_digit = RouletteDigit(
            pygame.Rect(354, 238 + ROULETTE_Y_OFFSET, 152, 188),
            list(range(0, 10)),
            self.fonts["digit"],
            self.fonts["digit_label"],
            "TENS",
            CYAN,
        )
        self.ones_digit = RouletteDigit(
            pygame.Rect(538, 238 + ROULETTE_Y_OFFSET, 152, 188),
            list(range(0, 10)),
            self.fonts["digit"],
            self.fonts["digit_label"],
            "ONES",
            PINK,
        )

        self.start_button = Button(
            pygame.Rect(424, 636, 228, 58),
            "Start",
            self.fonts["button"],
            GOLD,
        )
        self.reset_button = Button(
            pygame.Rect(678, 636, 148, 58),
            "Reset",
            self.fonts["button"],
            PEACH,
        )
        self.close_modal_button = Button(
            pygame.Rect(742, 154, 86, 38),
            "Close",
            self.fonts["small_bold"],
            LOGO_ORANGE,
        )
        self.rank1_results_button = Button(
            pygame.Rect(38, 268, 206, 38),
            "1등 당첨 번호",
            self.fonts["small_bold"],
            LOGO_ORANGE_LIGHT,
            text_shadow=False,
        )
        self.rank2_results_button = Button(
            pygame.Rect(38, 312, 206, 38),
            "2등 당첨 번호",
            self.fonts["small_bold"],
            LOGO_TEAL_LIGHT,
            text_shadow=False,
        )
        self.rank3_results_button = Button(
            pygame.Rect(38, 356, 206, 38),
            "3등 당첨 번호",
            self.fonts["small_bold"],
            LOGO_GRAY,
            text_shadow=False,
        )
        self.rank4_results_button = Button(
            pygame.Rect(38, 400, 206, 38),
            "4등 당첨 번호",
            self.fonts["small_bold"],
            LOGO_ORANGE,
            text_shadow=False,
        )
        self.rank5_results_button = Button(
            pygame.Rect(38, 444, 206, 38),
            "5등 당첨 번호",
            self.fonts["small_bold"],
            LOGO_TEAL,
            text_shadow=False,
        )
        self.unwon_button = Button(
            pygame.Rect(38, 488, 206, 38),
            "미당첨 리스트",
            self.fonts["small_bold"],
            LOGO_TEAL_DARK,
            text_shadow=False,
        )
        self.number_input = TextInput(
            pygame.Rect(626, 38, 170, 38),
            "1-50",
            self.fonts["small_bold"],
        )
        self.bulk_count_input = TextInput(
            pygame.Rect(1136, 650, 82, 36),
            "1",
            self.fonts["small_bold"],
            placeholder="개수",
            allowed="0123456789",
            max_length=3,
        )
        self.apply_numbers_button = Button(
            pygame.Rect(808, 38, 88, 38),
            "Apply",
            self.fonts["small_bold"],
            LOGO_TEAL,
        )

        self.prize_cards = []
        panel_x = 1000
        for index, name in enumerate(PRIZE_NAMES):
            rect = pygame.Rect(panel_x, 118 + index * 104, 238, 82)
            self.prize_cards.append(PrizeCard(index + 1, name, rect, self.fonts))

    def make_background_stars(self) -> list[tuple[int, int, int, float, tuple[int, int, int]]]:
        random.seed(20260527)
        stars = []
        colors = [LOGO_ORANGE, LOGO_ORANGE_LIGHT, LOGO_TEAL, LOGO_TEAL_LIGHT, LOGO_GRAY_LIGHT]
        for _ in range(170):
            stars.append(
                (
                    random.randint(0, SCREEN_WIDTH - 1),
                    random.randint(0, SCREEN_HEIGHT - 1),
                    random.choice([1, 1, 2, 2, 3]),
                    random.uniform(1.2, 3.6),
                    random.choice(colors),
                )
            )
        random.seed()
        return stars

    def load_logo_image(self) -> pygame.Surface | None:
        """제공된 로고 파일이 있으면 사용하고, 없으면 코드로 그린 로고를 사용합니다."""
        for path in LOGO_IMAGE_CANDIDATES:
            if not path.exists():
                continue
            try:
                image = pygame.image.load(str(path)).convert_alpha()
                return pygame.transform.smoothscale(image, (82, 82))
            except pygame.error:
                continue
        return None

    def set_message(self, text: str, duration_ms: int = 2600) -> None:
        self.message = text
        self.message_until = pygame.time.get_ticks() + duration_ms

    def current_selected_name(self) -> str:
        if self.selected_prize is None:
            return "선택된 경품 없음"
        return PRIZE_NAMES[self.selected_prize]

    def selected_rank(self) -> int | None:
        if self.selected_prize is None:
            return None
        return self.selected_prize + 1

    def is_bulk_prize_selected(self) -> bool:
        return self.selected_rank() in {4, 5}

    def is_spinning(self) -> bool:
        return self.state in {STATE_SPINNING_TENS, STATE_SPINNING_ONES, STATE_BULK_REVEALING}

    def is_list_modal_open(self) -> bool:
        return self.show_unwon_list or self.result_modal_rank is not None

    def clear_current_draw(self) -> None:
        self.target_number = None
        self.last_draw_numbers = []
        self.last_draw_is_bulk = False
        self.bulk_pending_numbers = []
        self.bulk_reveal_index = 0
        self.bulk_next_reveal_at = 0
        self.last_winner_rank = None

    def reveal_number_immediately(self, number: int, now: int, bounce: bool = False) -> None:
        self.target_number = number
        self.tens_digit.set_value(number // 10, now, bounce=bounce)
        self.ones_digit.set_value(number % 10, now, bounce=bounce)

    def parse_bulk_count(self) -> tuple[int | None, str | None]:
        text = self.bulk_count_input.text.strip()
        if not text:
            return None, "동시에 추첨할 개수를 입력하세요."
        if not text.isdigit():
            return None, "동시 추첨 개수는 숫자만 입력하세요."
        count = int(text)
        if count <= 0:
            return None, "동시 추첨 개수는 1개 이상이어야 합니다."
        return count, None

    def drawn_numbers(self) -> set[int]:
        return {number for numbers in self.rank_results.values() for number in numbers}

    def unwon_numbers(self) -> list[int]:
        drawn = self.drawn_numbers()
        return [number for number in self.number_pool if number not in drawn]

    def parse_number_pool(self, text: str) -> tuple[list[int], str | None]:
        """'1-50' 또는 '1, 3, 7-12' 형태의 입력을 추첨 번호 목록으로 바꿉니다."""
        cleaned = text.replace("~", "-").replace(";", ",").replace("/", ",")
        cleaned = cleaned.replace(" -", "-").replace("- ", "-")
        tokens = [token.strip() for token in cleaned.replace(" ", ",").split(",") if token.strip()]
        if not tokens:
            return [], "추첨 번호를 입력하세요."

        numbers: set[int] = set()
        for token in tokens:
            if "-" in token:
                parts = [part.strip() for part in token.split("-", 1)]
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
            return [], "두 자리 슬롯에 맞게 1~99 사이 번호만 사용할 수 있습니다."

        return sorted(numbers), None

    def apply_number_pool(self) -> None:
        if self.is_spinning():
            self.set_message("추첨이 끝난 뒤 번호를 변경하세요.", 2200)
            return

        numbers, error = self.parse_number_pool(self.number_input.text)
        if error:
            self.set_message(error, 3000)
            return

        self.number_pool = numbers
        self.history.clear()
        self.rank_results = {rank: [] for rank in range(1, 6)}
        self.target_number = None
        self.last_draw_numbers = []
        self.last_draw_is_bulk = False
        self.bulk_pending_numbers = []
        self.bulk_reveal_index = 0
        self.bulk_next_reveal_at = 0
        self.last_winner_rank = None
        self.show_unwon_list = False
        self.result_modal_rank = None
        self.state = STATE_IDLE
        self.tens_digit.reset()
        self.ones_digit.reset()
        self.particles.clear()
        self.set_message(f"추첨 번호 {len(numbers)}개가 적용되었습니다.", 2600)

    def available_numbers(self) -> list[int]:
        return list(self.number_pool)

    def update_button_state(self) -> None:
        self.start_button.enabled = self.state in {
            STATE_IDLE,
            STATE_TENS_REVEALED,
            STATE_FINAL_REVEALED,
        }
        self.apply_numbers_button.enabled = not self.is_spinning()
        self.rank1_results_button.enabled = not self.is_spinning()
        self.rank2_results_button.enabled = not self.is_spinning()
        self.rank3_results_button.enabled = not self.is_spinning()
        self.rank4_results_button.enabled = not self.is_spinning()
        self.rank5_results_button.enabled = not self.is_spinning()
        self.unwon_button.enabled = not self.is_spinning()
        self.close_modal_button.enabled = self.is_list_modal_open()

        if self.state == STATE_IDLE:
            self.start_button.text = "Start"
        elif self.state == STATE_TENS_REVEALED:
            self.start_button.text = "Reveal Ones"
        elif self.state == STATE_FINAL_REVEALED:
            self.start_button.text = "Next Draw"
        elif self.state == STATE_BULK_REVEALING:
            self.start_button.text = "Revealing..."
        else:
            self.start_button.text = "Spinning..."

    def handle_start(self) -> None:
        now = pygame.time.get_ticks()

        if self.state == STATE_FINAL_REVEALED:
            self.prepare_next_draw()
            return

        if not self.available_numbers():
            self.set_message("추첨 번호를 먼저 설정하세요.", 2600)
            return

        if self.selected_prize is None:
            self.set_message("먼저 오른쪽 경품 카드를 선택하세요.", 2600)
            return

        if self.is_bulk_prize_selected():
            if self.state != STATE_IDLE:
                self.set_message("진행 중인 추첨을 마친 뒤 동시 추첨을 시작하세요.", 2600)
                return
            self.handle_bulk_draw(now)
            return

        if self.state == STATE_IDLE:
            self.target_number = random.choice(self.available_numbers())
            tens = self.target_number // 10
            self.tens_digit.start_spin(tens, 2300, now)
            self.ones_digit.reset()
            self.state = STATE_SPINNING_TENS
            self.card_insert_until = now + 2200
            self.device_pulse_until = now + 2600
            self.set_message("십의자리 룰렛 회전 중...", 1800)
            self.spawn_start_particles()
            return

        if self.state == STATE_TENS_REVEALED and self.target_number is not None:
            ones = self.target_number % 10
            self.ones_digit.start_spin(ones, 2450, now)
            self.state = STATE_SPINNING_ONES
            self.card_insert_until = now + 1700
            self.device_pulse_until = now + 2500
            self.set_message("일의자리 룰렛 회전 중...", 1800)
            self.spawn_start_particles()

    def handle_bulk_draw(self, now: int) -> None:
        count, error = self.parse_bulk_count()
        if error:
            self.set_message(error, 2800)
            self.bulk_count_input.active = True
            return

        candidates = self.available_numbers()
        if not candidates:
            self.set_message("추첨 번호를 먼저 설정하세요.", 2800)
            return
        if count is None:
            return

        winners = [random.choice(candidates) for _ in range(count)]
        self.start_bulk_reveal(winners, now)

    def start_bulk_reveal(self, numbers: list[int], now: int) -> None:
        if self.selected_prize is None or not numbers:
            return

        self.bulk_pending_numbers = numbers[:]
        self.bulk_reveal_index = 0
        self.bulk_next_reveal_at = 0
        self.last_draw_numbers = []
        self.last_draw_is_bulk = True
        self.last_winner_rank = self.selected_prize + 1
        self.state = STATE_BULK_REVEALING
        self.card_insert_until = now + 900
        self.device_pulse_until = now + 900
        self.particles.clear()
        self.set_message(f"{PRIZE_NAMES[self.selected_prize]} 번호를 하나씩 공개합니다.", 2200)
        self.reveal_next_bulk_number(now)

    def reveal_next_bulk_number(self, now: int) -> None:
        if self.selected_prize is None or self.bulk_reveal_index >= len(self.bulk_pending_numbers):
            return

        number = self.bulk_pending_numbers[self.bulk_reveal_index]
        rank = self.selected_prize + 1
        prize_name = PRIZE_NAMES[self.selected_prize]

        self.reveal_number_immediately(number, now, bounce=True)
        self.last_draw_numbers.append(number)
        self.history.insert(0, (rank, prize_name, number))
        self.history = self.history[:8]
        if rank in self.rank_results:
            self.rank_results[rank].append(number)

        self.celebration_start = now
        self.device_pulse_until = now + 900
        self.spawn_bulk_reveal_particles()
        self.bulk_reveal_index += 1

        total = len(self.bulk_pending_numbers)
        if self.bulk_reveal_index >= total:
            self.state = STATE_FINAL_REVEALED
            self.bulk_next_reveal_at = 0
            self.set_message(f"{prize_name} {total}개 번호 공개 완료", 4200)
        else:
            self.bulk_next_reveal_at = now + 1000
            self.set_message(f"{self.bulk_reveal_index}/{total} 공개, 다음 번호 대기 중...", 1200)

    def prepare_next_draw(self) -> None:
        self.state = STATE_IDLE
        self.target_number = None
        self.last_draw_numbers = []
        self.last_draw_is_bulk = False
        self.bulk_pending_numbers = []
        self.bulk_reveal_index = 0
        self.bulk_next_reveal_at = 0
        self.tens_digit.reset()
        self.ones_digit.reset()
        self.celebration_start = -9999
        self.set_message("다음 추첨을 준비했습니다.", 1800)

    def handle_reset(self) -> None:
        self.state = STATE_IDLE
        self.history.clear()
        self.rank_results = {rank: [] for rank in range(1, 6)}
        self.selected_prize = None
        self.target_number = None
        self.last_draw_numbers = []
        self.last_draw_is_bulk = False
        self.bulk_pending_numbers = []
        self.bulk_reveal_index = 0
        self.bulk_next_reveal_at = 0
        self.last_winner_rank = None
        self.show_unwon_list = False
        self.result_modal_rank = None
        self.tens_digit.reset()
        self.ones_digit.reset()
        self.particles.clear()
        self.celebration_start = -9999
        self.shake_until = 0
        self.card_insert_until = 0
        self.device_pulse_until = 0
        self.set_message("초기화되었습니다. 경품 카드를 선택하세요.", 2400)

    def finalize_winner(self) -> None:
        if self.target_number is None or self.selected_prize is None:
            return

        number = self.target_number
        rank = self.selected_prize + 1
        prize_name = PRIZE_NAMES[self.selected_prize]
        self.last_winner_rank = rank
        self.last_draw_numbers = [number]
        self.last_draw_is_bulk = False

        self.history.insert(0, (rank, prize_name, number))
        self.history = self.history[:8]
        if rank in self.rank_results:
            self.rank_results[rank].append(number)
        self.state = STATE_FINAL_REVEALED

        now = pygame.time.get_ticks()
        self.celebration_start = now
        self.shake_until = now + (980 if rank == 1 else 620)
        self.device_pulse_until = now + (2600 if rank == 1 else 1500)
        self.set_message(f"{prize_name} 당첨 번호: {number}번", 4200)
        self.spawn_celebration_particles()

    def spawn_start_particles(self) -> None:
        center = (522, 232 + ROULETTE_Y_OFFSET)
        colors = [GOLD, PINK, CYAN, MINT, VIOLET]
        for _ in range(26):
            angle = random.uniform(-math.pi, 0)
            speed = random.uniform(80, 220)
            self.particles.append(
                Particle(
                    center[0] + random.uniform(-80, 80),
                    center[1] + random.uniform(-20, 60),
                    math.cos(angle) * speed,
                    math.sin(angle) * speed,
                    random.uniform(0.45, 0.9),
                    0.9,
                    random.choice([2, 3]),
                    random.choice(colors),
                    random.choice(["star", "circle"]),
                    gravity=240,
                )
            )

    def spawn_small_reveal_particles(self) -> None:
        colors = [GOLD, CYAN, PINK]
        for _ in range(36):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(80, 260)
            self.particles.append(
                Particle(
                    430,
                    335 + ROULETTE_Y_OFFSET,
                    math.cos(angle) * speed,
                    math.sin(angle) * speed,
                    random.uniform(0.7, 1.1),
                    1.1,
                    random.choice([2, 3]),
                    random.choice(colors),
                    random.choice(["star", "circle"]),
                    gravity=120,
                )
            )

    def spawn_bulk_reveal_particles(self) -> None:
        centers = [
            (430, 335 + ROULETTE_Y_OFFSET),
            (614, 335 + ROULETTE_Y_OFFSET),
        ]
        colors = [GOLD, CYAN, PINK, LOGO_ORANGE_LIGHT, LOGO_TEAL_LIGHT]
        for center_x, center_y in centers:
            for _ in range(26):
                angle = random.uniform(0, math.tau)
                speed = random.uniform(110, 320)
                self.particles.append(
                    Particle(
                        center_x + random.uniform(-16, 16),
                        center_y + random.uniform(-18, 18),
                        math.cos(angle) * speed,
                        math.sin(angle) * speed - random.uniform(20, 90),
                        random.uniform(0.65, 1.1),
                        1.1,
                        random.choice([2, 3, 4]),
                        random.choice(colors),
                        random.choice(["star", "circle"]),
                        gravity=150,
                    )
                )

    def spawn_celebration_particles(self) -> None:
        if self.last_winner_rank == 1:
            self.spawn_rainbow_fireworks()

        colors = [GOLD, PINK, CYAN, MINT, VIOLET, PEACH]
        origins = [
            (432, 330 + ROULETTE_Y_OFFSET),
            (615, 330 + ROULETTE_Y_OFFSET),
            (522, 210 + ROULETTE_Y_OFFSET),
            (522, 440 + ROULETTE_Y_OFFSET),
        ]
        count = 210 if self.last_winner_rank == 1 else 150
        for _ in range(count):
            ox, oy = random.choice(origins)
            angle = random.uniform(0, math.tau)
            speed = random.uniform(150, 620) if self.last_winner_rank == 1 else random.uniform(120, 520)
            self.particles.append(
                Particle(
                    ox + random.uniform(-30, 30),
                    oy + random.uniform(-25, 25),
                    math.cos(angle) * speed,
                    math.sin(angle) * speed - random.uniform(40, 160),
                    random.uniform(0.9, 1.8),
                    1.8,
                    random.choice([2, 3, 4, 5]) if self.last_winner_rank == 1 else random.choice([2, 3, 4]),
                    random.choice(RAINBOW_COLORS if self.last_winner_rank == 1 else colors),
                    random.choice(["star", "heart", "circle"]),
                    gravity=random.uniform(130, 260),
                )
            )

    def spawn_rainbow_fireworks(self) -> None:
        """1등 경품 전용 무지개 폭죽입니다."""
        burst_centers = [
            (300, 190),
            (455, 145),
            (620, 165),
            (760, 245),
            (360, 385),
            (690, 390),
        ]
        for burst_index, (cx, cy) in enumerate(burst_centers):
            for color_index, color in enumerate(RAINBOW_COLORS):
                for step in range(9):
                    angle = (step / 9) * math.tau + color_index * 0.08 + burst_index * 0.2
                    speed = 230 + color_index * 34 + random.uniform(-20, 40)
                    self.particles.append(
                        Particle(
                            cx + random.uniform(-8, 8),
                            cy + random.uniform(-8, 8),
                            math.cos(angle) * speed,
                            math.sin(angle) * speed,
                            random.uniform(1.15, 2.05),
                            2.05,
                            random.choice([3, 4, 5]),
                            color,
                            random.choice(["star", "heart", "circle"]),
                            gravity=random.uniform(70, 150),
                        )
                    )

        for _ in range(120):
            self.particles.append(
                Particle(
                    random.uniform(120, 850),
                    random.uniform(20, 90),
                    random.uniform(-80, 80),
                    random.uniform(140, 330),
                    random.uniform(1.6, 2.6),
                    2.6,
                    random.choice([2, 3, 4]),
                    random.choice(RAINBOW_COLORS),
                    random.choice(["star", "circle"]),
                    gravity=random.uniform(40, 90),
                )
            )

    def spawn_background_effects(self, now: int) -> None:
        if now >= self.next_twinkle_at:
            self.next_twinkle_at = now + random.randint(110, 280)
            colors = [LOGO_ORANGE, LOGO_ORANGE_LIGHT, LOGO_TEAL, LOGO_TEAL_LIGHT, LOGO_GRAY_LIGHT]
            for _ in range(random.randint(4, 8)):
                self.background_twinkles.append(
                    Particle(
                        random.uniform(10, 940),
                        random.uniform(12, 520),
                        0,
                        0,
                        random.uniform(0.55, 1.15),
                        1.15,
                        random.choice([2, 3, 4]),
                        random.choice(colors),
                        "star",
                        gravity=0,
                    )
                )

        if now >= self.next_shooting_star_at:
            self.next_shooting_star_at = now + random.randint(1100, 2800)
            color = random.choice([LOGO_ORANGE_LIGHT, LOGO_TEAL_LIGHT, LOGO_GRAY_LIGHT])
            self.shooting_stars.append(
                ShootingStar(
                    random.uniform(-80, 780),
                    random.uniform(-20, 180),
                    random.uniform(360, 560),
                    random.uniform(180, 310),
                    random.uniform(0.85, 1.25),
                    1.25,
                    color,
                )
            )

    def scene_transform(self) -> tuple[float, int, int, int, int]:
        """현재 창 크기에서 1280x720 화면이 들어갈 위치와 배율을 계산합니다."""
        window_w, window_h = self.screen.get_size()
        scale = min(window_w / SCREEN_WIDTH, window_h / SCREEN_HEIGHT)
        if scale <= 0:
            scale = 1.0
        scaled_w = max(1, int(SCREEN_WIDTH * scale))
        scaled_h = max(1, int(SCREEN_HEIGHT * scale))
        offset_x = (window_w - scaled_w) // 2
        offset_y = (window_h - scaled_h) // 2
        return scale, offset_x, offset_y, scaled_w, scaled_h

    def screen_to_scene_pos(self, pos: tuple[int, int]) -> tuple[int, int]:
        """실제 창 좌표를 내부 1280x720 좌표로 변환합니다."""
        scale, offset_x, offset_y, scaled_w, scaled_h = self.scene_transform()
        if not (offset_x <= pos[0] <= offset_x + scaled_w and offset_y <= pos[1] <= offset_y + scaled_h):
            return (-10000, -10000)
        return (
            int((pos[0] - offset_x) / scale),
            int((pos[1] - offset_y) / scale),
        )

    def event_to_scene(self, event: pygame.event.Event) -> pygame.event.Event:
        """마우스 이벤트 좌표를 내부 좌표로 변환한 새 이벤트를 만듭니다."""
        if "pos" not in event.dict:
            return event
        data = event.dict.copy()
        data["pos"] = self.screen_to_scene_pos(event.pos)
        return pygame.event.Event(event.type, data)

    def toggle_fullscreen(self) -> None:
        """F11 또는 Alt+Enter로 전체화면과 창모드를 전환합니다."""
        if self.fullscreen:
            self.fullscreen = False
            self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        else:
            self.fullscreen = True
            self.windowed_size = self.screen.get_size()
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

    def select_prize(self, index: int) -> None:
        if self.state == STATE_TENS_REVEALED and self.selected_prize != index:
            self.state = STATE_IDLE
            self.target_number = None
            self.last_draw_numbers = []
            self.last_draw_is_bulk = False
            self.tens_digit.reset()
            self.ones_digit.reset()

        self.selected_prize = index
        if not self.is_bulk_prize_selected():
            self.bulk_count_input.active = False

        message = f"{PRIZE_NAMES[index]} 카드가 장착되었습니다."
        if self.is_bulk_prize_selected():
            message += " 동시 추첨 개수를 입력하세요."
        self.set_message(message, 2400)

    def handle_events(self) -> None:
        for raw_event in pygame.event.get():
            if raw_event.type == pygame.QUIT:
                self.running = False

            if raw_event.type == pygame.VIDEORESIZE and not self.fullscreen:
                self.windowed_size = (max(640, raw_event.w), max(360, raw_event.h))
                self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)

            if raw_event.type == pygame.KEYDOWN:
                alt_enter = raw_event.key == pygame.K_RETURN and (pygame.key.get_mods() & pygame.KMOD_ALT)
                if raw_event.key == pygame.K_F11 or alt_enter:
                    self.toggle_fullscreen()
                    continue
                if raw_event.key == pygame.K_ESCAPE:
                    if self.fullscreen:
                        self.toggle_fullscreen()
                    elif self.is_list_modal_open():
                        self.show_unwon_list = False
                        self.result_modal_rank = None
                    else:
                        self.running = False
                    continue

            event = self.event_to_scene(raw_event)

            if self.is_list_modal_open():
                if self.close_modal_button.handle_event(event):
                    self.show_unwon_list = False
                    self.result_modal_rank = None
                continue

            if not self.is_spinning() and self.number_input.handle_event(event):
                self.apply_number_pool()

            if (
                self.is_bulk_prize_selected()
                and not self.is_spinning()
                and self.bulk_count_input.handle_event(event)
            ):
                self.handle_start()

            if self.start_button.handle_event(event):
                self.handle_start()

            if self.reset_button.handle_event(event):
                self.handle_reset()

            if self.apply_numbers_button.handle_event(event):
                self.apply_number_pool()

            if self.rank1_results_button.handle_event(event):
                self.result_modal_rank = 1
                self.show_unwon_list = False

            if self.rank2_results_button.handle_event(event):
                self.result_modal_rank = 2
                self.show_unwon_list = False

            if self.rank3_results_button.handle_event(event):
                self.result_modal_rank = 3
                self.show_unwon_list = False

            if self.rank4_results_button.handle_event(event):
                self.result_modal_rank = 4
                self.show_unwon_list = False

            if self.rank5_results_button.handle_event(event):
                self.result_modal_rank = 5
                self.show_unwon_list = False

            if self.unwon_button.handle_event(event):
                self.show_unwon_list = not self.show_unwon_list
                self.result_modal_rank = None

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if not self.is_spinning():
                    for index, card in enumerate(self.prize_cards):
                        if card.handle_event(event):
                            self.select_prize(index)
                            break

    def update(self, dt: float, now: int) -> None:
        mouse_pos = self.screen_to_scene_pos(pygame.mouse.get_pos())
        self.update_button_state()
        self.start_button.update(mouse_pos)
        self.reset_button.update(mouse_pos)
        self.apply_numbers_button.update(mouse_pos)
        self.rank1_results_button.update(mouse_pos)
        self.rank2_results_button.update(mouse_pos)
        self.rank3_results_button.update(mouse_pos)
        self.rank4_results_button.update(mouse_pos)
        self.rank5_results_button.update(mouse_pos)
        self.unwon_button.update(mouse_pos)
        self.close_modal_button.update(mouse_pos)
        self.number_input.update(dt, mouse_pos)
        if self.is_bulk_prize_selected() and not self.is_spinning():
            self.bulk_count_input.update(dt, mouse_pos)
        else:
            self.bulk_count_input.active = False
        self.spawn_background_effects(now)

        inserted = now < self.card_insert_until
        for index, card in enumerate(self.prize_cards):
            card.update(
                dt,
                selected=self.selected_prize == index,
                inserted=inserted and self.selected_prize == index,
                mouse_pos=mouse_pos,
            )

        tens_finished = self.tens_digit.update(now)
        ones_finished = self.ones_digit.update(now)

        if tens_finished and self.state == STATE_SPINNING_TENS:
            self.state = STATE_TENS_REVEALED
            self.set_message("십의자리 공개! 한 번 더 누르세요.", 3200)
            self.spawn_small_reveal_particles()

        if ones_finished and self.state == STATE_SPINNING_ONES:
            self.finalize_winner()

        if (
            self.state == STATE_BULK_REVEALING
            and self.bulk_next_reveal_at
            and now >= self.bulk_next_reveal_at
        ):
            self.reveal_next_bulk_number(now)

        self.particles = [particle for particle in self.particles if particle.update(dt)]
        self.background_twinkles = [
            particle for particle in self.background_twinkles if particle.update(dt)
        ]
        self.shooting_stars = [star for star in self.shooting_stars if star.update(dt)]

    def draw_background(self, surface: pygame.Surface, now: int) -> None:
        surface.fill(BG_DEEP)
        pygame.draw.rect(surface, BG_DARK, pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))

        title_clear_rect = pygame.Rect(20, 14, 575, 58)
        for x, y, size, speed, color in self.background_stars:
            if title_clear_rect.collidepoint(x, y):
                continue
            twinkle = 1.0 + 0.72 * math.sin(now * 0.0014 * speed + x * 0.01)
            if random.random() < 0.0016:
                twinkle = 2.0
            star_color = tuple(min(255, int(c * twinkle)) for c in color)
            if size <= 2:
                pygame.draw.rect(surface, star_color, pygame.Rect(x, y, size, size))
                if twinkle > 1.45:
                    pygame.draw.line(surface, star_color, (x - 3, y), (x + size + 3, y), 1)
                    pygame.draw.line(surface, star_color, (x, y - 3), (x, y + size + 3), 1)
            else:
                draw_pixel_star(surface, x, y, 2 if twinkle > 1.45 else 1, star_color)

        for shooting_star in self.shooting_stars:
            shooting_star.draw(surface)
        for sparkle in self.background_twinkles:
            if title_clear_rect.collidepoint(sparkle.x, sparkle.y):
                continue
            sparkle.draw(surface)

        for i in range(9):
            y = 560 + i * 24
            color = (9 + i * 3, 11 + i * 3, 12 + i * 3)
            pygame.draw.rect(surface, color, pygame.Rect(0, y, SCREEN_WIDTH, 24))
            if i % 2 == 0:
                line_color = LOGO_TEAL_DARK if i % 4 == 0 else LOGO_ORANGE_DARK
                pygame.draw.line(surface, line_color, (0, y), (SCREEN_WIDTH, y), 1)

        moon_rect = pygame.Rect(62, 82, 86, 86)
        pygame.draw.circle(surface, LOGO_ORANGE, moon_rect.center, 43)
        pygame.draw.circle(surface, LOGO_TEAL, (moon_rect.centerx - 12, moon_rect.centery + 12), 18)
        pygame.draw.circle(surface, BG_DARK, (moon_rect.centerx + 18, moon_rect.centery - 8), 38)

    def draw_title_area(self, surface: pygame.Surface) -> None:
        now = pygame.time.get_ticks()
        title_text = "2026 APRIL HOMECOMING"
        title_pos = (300, 42)
        title_glow = pygame.Surface((600, 78), pygame.SRCALPHA)
        for i, color in enumerate([LOGO_ORANGE, LOGO_TEAL, LOGO_GRAY_LIGHT]):
            alpha = 52 - i * 12
            pygame.draw.rect(
                title_glow,
                (*color, alpha),
                pygame.Rect(14 + i * 8, 13 + i * 5, 520 - i * 18, 44),
                border_radius=8,
            )
        surface.blit(title_glow, (14, 8))

        draw_text(
            surface,
            title_text,
            self.fonts["title"],
            LOGO_TEAL,
            (title_pos[0] + 3, title_pos[1] + 3),
            shadow=False,
        )
        draw_text(
            surface,
            title_text,
            self.fonts["title"],
            LOGO_GRAY_LIGHT,
            (title_pos[0] - 2, title_pos[1] - 2),
            shadow=False,
        )
        draw_text(
            surface,
            title_text,
            self.fonts["title"],
            LOGO_ORANGE_LIGHT,
            title_pos,
            shadow=True,
            shadow_color=(0, 0, 0),
        )
        for i in range(10):
            x = 44 + i * 50
            color = LOGO_ORANGE if i % 2 == 0 else LOGO_TEAL
            pygame.draw.rect(surface, color, pygame.Rect(x, 64, 30, 4))

        draw_text(
            surface,
            "추첨 번호",
            self.fonts["small_bold"],
            LOGO_GRAY_LIGHT,
            (626, 28),
            anchor="midleft",
            shadow=True,
            shadow_color=(0, 0, 0),
        )

        self.number_input.draw(surface)
        self.apply_numbers_button.draw(surface)

    def draw_device_glow(self, surface: pygame.Surface, now: int) -> None:
        pulse_active = now < self.device_pulse_until or self.state in {
            STATE_SPINNING_TENS,
            STATE_SPINNING_ONES,
        }
        pulse = 0.35 + 0.25 * math.sin(now * 0.012)
        strength = 0.25 + (0.75 * pulse if pulse_active else 0)

        glow = pygame.Surface((620, 470), pygame.SRCALPHA)
        center = (310, 235)
        for i, radius in enumerate([230, 190, 150]):
            alpha = int((70 - i * 12) * strength)
            pygame.draw.circle(glow, (*LOGO_ORANGE, alpha), center, radius, width=10)
        for i in range(18):
            angle = now * 0.0015 + i * math.tau / 18
            inner = 118
            outer = 245 + 20 * math.sin(now * 0.004 + i)
            start = (center[0] + math.cos(angle) * inner, center[1] + math.sin(angle) * inner)
            end = (center[0] + math.cos(angle) * outer, center[1] + math.sin(angle) * outer)
            ray_color = LOGO_TEAL if i % 2 else LOGO_ORANGE
            pygame.draw.line(glow, (*ray_color, int(60 * strength)), start, end, 4)
        surface.blit(glow, (214, 100 + ROULETTE_Y_OFFSET))

    def draw_selected_prize_banner(
        self,
        surface: pygame.Surface,
        banner: pygame.Rect,
        now: int,
    ) -> None:
        """장치 하단 슬롯에 현재 선택된 경품을 강조해서 표시합니다."""
        pulse = 0.5 + 0.5 * math.sin(now * 0.008)
        accent = LOGO_GRAY if self.selected_prize is None else self.prize_cards[self.selected_prize].accent
        glow = pygame.Surface((banner.width + 26, banner.height + 26), pygame.SRCALPHA)
        pygame.draw.rect(
            glow,
            (*accent, 68 + int(75 * pulse)),
            glow.get_rect(),
            border_radius=13,
        )
        surface.blit(glow, (banner.x - 13, banner.y - 13))

        pygame.draw.rect(surface, (0, 0, 0), banner.move(0, 9), border_radius=10)
        pygame.draw.rect(surface, PANEL_LIGHT, banner, border_radius=10)
        pygame.draw.rect(surface, accent, banner, 4, border_radius=10)

        for x in range(banner.x + 14, banner.right - 14, 34):
            stripe_color = LOGO_ORANGE if (x + now // 90) % 68 < 34 else LOGO_TEAL
            pygame.draw.rect(surface, stripe_color, pygame.Rect(x, banner.y + 6, 13, 4))
            pygame.draw.rect(surface, stripe_color, pygame.Rect(x, banner.bottom - 10, 13, 4))

        if self.selected_prize is None:
            banner_text = "경품 카드를 선택하세요"
        else:
            rank = self.selected_prize + 1
            banner_text = f"{rank}등 상품 장착!  {PRIZE_NAMES[self.selected_prize]}"
            draw_pixel_star(surface, banner.x + 26, banner.centery, 3, accent)
            draw_pixel_star(surface, banner.right - 26, banner.centery, 3, accent)

        draw_text_fit(
            surface,
            banner_text,
            self.fonts["subtitle"],
            WHITE,
            banner.center,
            banner.width - 64,
            shadow=True,
            shadow_color=(0, 0, 0),
        )

    def draw_gacha_device(self, surface: pygame.Surface, now: int) -> None:
        self.draw_device_glow(surface, now)

        base = pygame.Rect(282, 178 + ROULETTE_Y_OFFSET, 488, 380)
        pygame.draw.rect(surface, (0, 0, 0), base.move(0, 12), border_radius=18)
        pygame.draw.rect(surface, LOGO_ORANGE, base, border_radius=18)
        pygame.draw.rect(surface, PANEL_LIGHT, base.inflate(-18, -18), border_radius=14)
        pygame.draw.rect(surface, (38, 42, 43), base, 5, border_radius=18)

        crystal = [
            (526, 106 + ROULETTE_Y_OFFSET),
            (594, 164 + ROULETTE_Y_OFFSET),
            (556, 214 + ROULETTE_Y_OFFSET),
            (496, 214 + ROULETTE_Y_OFFSET),
            (458, 164 + ROULETTE_Y_OFFSET),
        ]
        pygame.draw.polygon(surface, LOGO_TEAL, crystal)
        pygame.draw.polygon(
            surface,
            LOGO_ORANGE_LIGHT,
            [crystal[0], crystal[1], crystal[2], (526, 178 + ROULETTE_Y_OFFSET)],
        )
        pygame.draw.polygon(
            surface,
            LOGO_GRAY_LIGHT,
            [crystal[0], (526, 178 + ROULETTE_Y_OFFSET), crystal[3], crystal[4]],
        )
        pygame.draw.polygon(surface, INK, crystal, 4)
        draw_pixel_star(surface, 526, 156 + ROULETTE_Y_OFFSET, 4, WHITE)

        frame = pygame.Rect(326, 208 + ROULETTE_Y_OFFSET, 392, 252)
        pygame.draw.rect(surface, (0, 0, 0), frame.move(0, 8), border_radius=12)
        pygame.draw.rect(surface, LOGO_TEAL, frame, border_radius=12)
        pygame.draw.rect(surface, (36, 40, 41), frame, 5, border_radius=12)

        bulb_colors = [LOGO_ORANGE, LOGO_ORANGE_LIGHT, LOGO_TEAL, LOGO_GRAY_LIGHT]
        for i in range(16):
            if i < 8:
                x = frame.x + 28 + i * 48
                y = frame.y + 18
            else:
                x = frame.x + 28 + (i - 8) * 48
                y = frame.bottom - 18
            color = bulb_colors[(i + now // 180) % len(bulb_colors)]
            pygame.draw.rect(surface, color, pygame.Rect(x - 5, y - 5, 10, 10))

        pedestal = pygame.Rect(354, 478 + ROULETTE_Y_OFFSET, 346, 62)
        self.draw_selected_prize_banner(surface, pedestal, now)

    def draw_digits(self, surface: pygame.Surface, now: int) -> None:
        scale = 1.0
        reveal_t = (now - self.celebration_start) / 780
        if (
            self.state == STATE_FINAL_REVEALED
            and not self.last_draw_is_bulk
            and 0.0 <= reveal_t <= 1.0
        ):
            scale = 1.0 + 0.2 * math.sin(reveal_t * math.pi) * (1 - reveal_t * 0.35)

        self.tens_digit.draw(surface, now, external_scale=scale)
        self.ones_digit.draw(surface, now, external_scale=scale)

    def draw_mascot(self, surface: pygame.Surface, now: int) -> None:
        """선택된 경품 카드 옆에 매달린 픽셀 마스코트를 그립니다."""
        if self.selected_prize is None:
            return

        card_rect = self.prize_cards[self.selected_prize].current_rect()
        t = (now - self.celebration_start) / 1400
        cheer = 0 <= t <= 1
        bob = math.sin(now * 0.008) * 4
        x = int(card_rect.x - 24 + math.sin(now * 0.005) * 3)
        y = int(card_rect.y + 66 + bob)
        u = 4

        hook = (card_rect.x + 16, card_rect.y + 10)
        hand_l = (x - 5 * u, y - 5 * u)
        hand_r = (x + 5 * u, y - 5 * u)
        pygame.draw.line(surface, LOGO_ORANGE_LIGHT, hook, hand_l, 3)
        pygame.draw.line(surface, LOGO_TEAL_LIGHT, hook, hand_r, 3)
        pygame.draw.circle(surface, LOGO_GRAY_LIGHT, hook, 5)

        colors = {
            "body": LOGO_TEAL,
            "body_dark": LOGO_TEAL_DARK,
            "face": LOGO_GRAY_LIGHT,
            "cheek": LOGO_ORANGE_LIGHT,
            "line": INK,
        }

        def block(dx: int, dy: int, w: int, h: int, color: tuple[int, int, int]) -> None:
            pygame.draw.rect(surface, color, pygame.Rect(x + dx * u, y + dy * u, w * u, h * u))

        block(-4, -8, 8, 2, colors["body"])
        block(-5, -6, 10, 8, colors["body"])
        block(-4, -5, 8, 5, colors["face"])
        block(-5, -6, 10, 8, colors["line"])
        block(-4, -5, 8, 5, colors["face"])
        block(-2, -3, 1, 1, colors["line"])
        block(2, -3, 1, 1, colors["line"])
        block(-3, -1, 1, 1, colors["cheek"])
        block(3, -1, 1, 1, colors["cheek"])
        block(-1, 0, 2, 1, colors["line"])
        block(-3, 2, 6, 5, colors["body"])
        block(-3, 6, 2, 2, colors["body_dark"])
        block(1, 6, 2, 2, colors["body_dark"])
        if cheer:
            block(-7, -7, 2, 3, colors["body"])
            block(5, -7, 2, 3, colors["body"])
        else:
            block(-7, -5, 2, 2, colors["body"])
            block(5, -5, 2, 2, colors["body"])
        block(-1, -11, 2, 3, colors["body_dark"])
        draw_pixel_star(surface, x, y - 52, 2, GOLD)

    def draw_history(self, surface: pygame.Surface) -> None:
        self.rank1_results_button.draw(surface)
        self.rank2_results_button.draw(surface)
        self.rank3_results_button.draw(surface)
        self.rank4_results_button.draw(surface)
        self.rank5_results_button.draw(surface)
        self.unwon_button.draw(surface)

        panel = pygame.Rect(38, 536, 348, 160)
        pygame.draw.rect(surface, (0, 0, 0), panel.move(5, 6), border_radius=8)
        pygame.draw.rect(surface, PANEL_LIGHT, panel, border_radius=8)
        pygame.draw.rect(surface, PANEL_EDGE, panel, 2, border_radius=8)

        draw_text(
            surface,
            "최근 당첨",
            self.fonts["small_bold"],
            GOLD,
            (panel.x + 18, panel.y + 22),
            anchor="midleft",
            shadow=False,
        )

        if not self.history:
            draw_text(
                surface,
                "아직 당첨 기록 없음",
                self.fonts["small"],
                LOGO_GRAY_LIGHT,
                (panel.x + 18, panel.y + 70),
                anchor="midleft",
                shadow=False,
            )
            return

        for i, (rank, prize_name, number) in enumerate(self.history[:5]):
            y = panel.y + 54 + i * 21
            color = WHITE if i == 0 else LOGO_GRAY_LIGHT
            draw_text(
                surface,
                f"{prize_name} - {number}번",
                self.fonts["small"],
                color,
                (panel.x + 18, y),
                anchor="midleft",
                shadow=False,
            )

    def draw_status(self, surface: pygame.Surface) -> None:
        panel = pygame.Rect(408, 574, 448, 42)
        pygame.draw.rect(surface, (0, 0, 0), panel.move(4, 5), border_radius=8)
        pygame.draw.rect(surface, PANEL_LIGHT, panel, border_radius=8)
        pygame.draw.rect(surface, LOGO_TEAL, panel, 2, border_radius=8)

        text = self.message
        if self.message_until and pygame.time.get_ticks() > self.message_until:
            if self.state == STATE_IDLE:
                if self.is_bulk_prize_selected():
                    text = "동시 추첨 개수를 입력한 뒤 Start를 누르세요."
                else:
                    text = "Start를 누르면 십의자리가 먼저 공개됩니다."
            elif self.state == STATE_TENS_REVEALED:
                text = "한 번 더 누르면 일의자리가 공개됩니다."
            elif self.state == STATE_BULK_REVEALING:
                total = len(self.bulk_pending_numbers)
                shown = len(self.last_draw_numbers)
                text = f"{shown}/{total} 공개 중..."

        draw_text_fit(
            surface,
            text,
            self.fonts["small_bold"],
            WHITE,
            panel.center,
            panel.width - 24,
            shadow=False,
        )

    def draw_number_grid(
        self,
        surface: pygame.Surface,
        numbers: list[int],
        list_rect: pygame.Rect,
        empty_text: str,
    ) -> None:
        if not numbers:
            draw_text(
                surface,
                empty_text,
                self.fonts["small_bold"],
                WHITE,
                list_rect.center,
                shadow=False,
            )
            return

        cell_w = 58
        cell_h = 34
        cols = max(1, list_rect.width // cell_w)
        max_rows = max(1, list_rect.height // cell_h)
        max_items = cols * max_rows

        for index, number in enumerate(numbers[:max_items]):
            col = index % cols
            row = index // cols
            x = list_rect.x + 12 + col * cell_w
            y = list_rect.y + 12 + row * cell_h
            rect = pygame.Rect(x, y, 44, 24)
            pygame.draw.rect(surface, (228, 231, 226), rect, border_radius=5)
            pygame.draw.rect(surface, LOGO_TEAL, rect, 2, border_radius=5)
            draw_text(
                surface,
                str(number),
                self.fonts["small_bold"],
                INK,
                rect.center,
                shadow=False,
            )

        if len(numbers) > max_items:
            draw_text(
                surface,
                f"+ {len(numbers) - max_items}개 더 있음",
                self.fonts["small"],
                LOGO_GRAY_LIGHT,
                (list_rect.centerx, list_rect.bottom - 14),
                shadow=False,
            )

    def draw_rank_results_modal(self, surface: pygame.Surface, rank: int) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 135))
        surface.blit(overlay, (0, 0))

        panel = pygame.Rect(336, 132, 520, 456)
        pygame.draw.rect(surface, (0, 0, 0), panel.move(8, 10), border_radius=10)
        pygame.draw.rect(surface, PANEL_LIGHT, panel, border_radius=10)
        pygame.draw.rect(surface, LOGO_ORANGE, panel, 4, border_radius=10)
        pygame.draw.rect(surface, LOGO_TEAL, panel.inflate(-14, -14), 2, border_radius=8)

        results = self.rank_results.get(rank, [])[:]
        draw_text(
            surface,
            f"{rank}등 당첨 번호",
            self.fonts["subtitle"],
            LOGO_ORANGE_LIGHT,
            (panel.x + 24, panel.y + 30),
            anchor="midleft",
            shadow=True,
            shadow_color=(0, 0, 0),
        )
        draw_text(
            surface,
            f"누적 당첨 번호 {len(results)}개",
            self.fonts["small_bold"],
            LOGO_GRAY_LIGHT,
            (panel.x + 24, panel.y + 62),
            anchor="midleft",
            shadow=False,
        )
        self.close_modal_button.draw(surface)

        list_rect = pygame.Rect(panel.x + 24, panel.y + 92, panel.width - 48, panel.height - 122)
        pygame.draw.rect(surface, (9, 11, 12), list_rect, border_radius=8)
        pygame.draw.rect(surface, PANEL_EDGE, list_rect, 2, border_radius=8)
        self.draw_number_grid(surface, results, list_rect, f"아직 {rank}등 당첨 번호가 없습니다.")

    def draw_unwon_modal(self, surface: pygame.Surface) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 135))
        surface.blit(overlay, (0, 0))

        panel = pygame.Rect(336, 132, 520, 456)
        pygame.draw.rect(surface, (0, 0, 0), panel.move(8, 10), border_radius=10)
        pygame.draw.rect(surface, PANEL_LIGHT, panel, border_radius=10)
        pygame.draw.rect(surface, LOGO_ORANGE, panel, 4, border_radius=10)
        pygame.draw.rect(surface, LOGO_TEAL, panel.inflate(-14, -14), 2, border_radius=8)

        unwon = self.unwon_numbers()
        draw_text(
            surface,
            "미당첨 리스트",
            self.fonts["subtitle"],
            LOGO_ORANGE_LIGHT,
            (panel.x + 24, panel.y + 30),
            anchor="midleft",
            shadow=True,
            shadow_color=(0, 0, 0),
        )
        draw_text(
            surface,
            f"아직 공개되지 않은 번호 {len(unwon)} / {len(self.number_pool)}",
            self.fonts["small_bold"],
            LOGO_GRAY_LIGHT,
            (panel.x + 24, panel.y + 62),
            anchor="midleft",
            shadow=False,
        )
        self.close_modal_button.draw(surface)

        list_rect = pygame.Rect(panel.x + 24, panel.y + 92, panel.width - 48, panel.height - 122)
        pygame.draw.rect(surface, (9, 11, 12), list_rect, border_radius=8)
        pygame.draw.rect(surface, PANEL_EDGE, list_rect, 2, border_radius=8)
        self.draw_number_grid(surface, unwon, list_rect, "모든 번호가 한 번 이상 공개되었습니다.")

    def draw_result_modal(self, surface: pygame.Surface) -> None:
        if self.result_modal_rank is not None:
            self.draw_rank_results_modal(surface, self.result_modal_rank)
        elif self.show_unwon_list:
            self.draw_unwon_modal(surface)

    def draw_vector_logo(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """로고 파일을 찾지 못했을 때 쓰는 코드 내장형 로고입니다."""

        def point(x: float, y: float) -> tuple[int, int]:
            scale = rect.width / 110
            return (int(rect.x + x * scale), int(rect.y + y * scale))

        def poly(points: list[tuple[float, float]], color: tuple[int, int, int]) -> None:
            pygame.draw.polygon(surface, color, [point(x, y) for x, y in points])
            pygame.draw.polygon(surface, INK, [point(x, y) for x, y in points], max(1, rect.width // 40))

        poly([(8, 24), (49, 7), (92, 24), (50, 43)], LOGO_ORANGE_LIGHT)
        poly([(50, 43), (92, 24), (108, 33), (67, 52)], LOGO_TEAL)
        poly([(8, 24), (29, 35), (29, 84), (8, 72)], LOGO_ORANGE)
        poly([(29, 84), (45, 93), (59, 86), (40, 77)], LOGO_ORANGE_DARK)
        poly([(50, 43), (70, 52), (70, 100), (50, 91)], LOGO_ORANGE_LIGHT)
        poly([(70, 52), (88, 43), (88, 89), (70, 100)], LOGO_ORANGE)
        poly([(67, 52), (108, 33), (108, 62), (67, 82)], LOGO_TEAL)
        poly([(67, 82), (108, 62), (108, 84), (82, 96), (67, 89)], LOGO_GRAY)

        pygame.draw.polygon(surface, BG_DEEP, [point(32, 23), point(45, 17), point(58, 23), point(45, 29)])
        pygame.draw.polygon(surface, BG_DEEP, [point(75, 27), point(88, 22), point(101, 29), point(88, 35)])
        pygame.draw.polygon(surface, LOGO_GRAY, [point(18, 44), point(25, 48), point(25, 70), point(18, 66)])
        pygame.draw.polygon(surface, BG_DEEP, [point(34, 68), point(48, 75), point(48, 88), point(34, 80)])

    def draw_corner_logo(self, surface: pygame.Surface) -> None:
        rect = pygame.Rect(1162, 18, 84, 84)
        pygame.draw.rect(surface, (0, 0, 0), rect.inflate(14, 14), border_radius=8)
        pygame.draw.rect(surface, PANEL_LIGHT, rect.inflate(10, 10), border_radius=8)
        pygame.draw.rect(surface, LOGO_ORANGE, rect.inflate(10, 10), 2, border_radius=8)

        if self.logo_image is not None:
            image_rect = self.logo_image.get_rect(center=rect.center)
            surface.blit(self.logo_image, image_rect)
        else:
            self.draw_vector_logo(surface, rect)

    def draw_bulk_count_panel(self, surface: pygame.Surface) -> None:
        panel = pygame.Rect(986, 626, 252, 72)
        rank = self.selected_rank()
        accent = LOGO_ORANGE if rank == 4 else LOGO_TEAL

        pygame.draw.rect(surface, (0, 0, 0), panel.move(5, 6), border_radius=8)
        pygame.draw.rect(surface, PANEL_LIGHT, panel, border_radius=8)
        pygame.draw.rect(surface, accent, panel, 3, border_radius=8)

        draw_text(
            surface,
            "동시 추첨 개수",
            self.fonts["small_bold"],
            WHITE,
            (panel.x + 16, panel.y + 24),
            anchor="midleft",
            shadow=False,
        )
        draw_text(
            surface,
            "1초 간격 공개",
            self.fonts["tiny"],
            LOGO_GRAY_LIGHT,
            (panel.x + 16, panel.y + 52),
            anchor="midleft",
            shadow=False,
            pixel=True,
        )
        self.bulk_count_input.draw(surface)

    def draw_prize_panel(self, surface: pygame.Surface, now: int) -> None:
        panel = pygame.Rect(960, 0, 320, SCREEN_HEIGHT)
        pygame.draw.rect(surface, PANEL, panel)
        pygame.draw.line(surface, LOGO_ORANGE_DARK, (panel.x, 0), (panel.x, SCREEN_HEIGHT), 3)

        draw_text(
            surface,
            "경품 카드",
            self.fonts["subtitle"],
            WHITE,
            (panel.x + 40, 48),
            anchor="midleft",
            shadow=True,
            shadow_color=(0, 0, 0),
        )
        self.draw_corner_logo(surface)

        for index, card in enumerate(self.prize_cards):
            card.draw(surface, selected=self.selected_prize == index)
        if self.is_bulk_prize_selected():
            self.draw_bulk_count_panel(surface)
        self.draw_mascot(surface, now)

    def draw_bulk_congratulations(self, surface: pygame.Surface) -> None:
        numbers = self.last_draw_numbers
        if not numbers:
            return

        rank = self.last_winner_rank or 0
        total = len(self.bulk_pending_numbers) if self.state == STATE_BULK_REVEALING else len(numbers)
        count_text = f"{len(numbers)}/{total} 공개" if self.state == STATE_BULK_REVEALING else f"{len(numbers)}개 번호 공개"
        draw_text(
            surface,
            "동시 당첨",
            self.fonts["congrats"],
            GOLD,
            (522, 108),
            shadow=True,
            shadow_color=(0, 0, 0),
        )
        draw_text(
            surface,
            f"{rank}등 {count_text}",
            self.fonts["subtitle"],
            LOGO_GRAY_LIGHT,
            (522, 156),
            shadow=True,
            shadow_color=(0, 0, 0),
            pixel=True,
        )

        list_rect = pygame.Rect(304, 454, 436, 100)
        pygame.draw.rect(surface, (0, 0, 0), list_rect.move(5, 6), border_radius=8)
        pygame.draw.rect(surface, PANEL_LIGHT, list_rect, border_radius=8)
        pygame.draw.rect(surface, LOGO_TEAL, list_rect, 2, border_radius=8)
        self.draw_number_grid(surface, numbers, list_rect, "")

    def draw_congratulations(self, surface: pygame.Surface, now: int) -> None:
        if self.state not in {STATE_FINAL_REVEALED, STATE_BULK_REVEALING} or self.target_number is None:
            return

        if self.last_draw_is_bulk:
            self.draw_bulk_congratulations(surface)
            return

        t = clamp((now - self.celebration_start) / 700, 0.0, 1.0)
        pop = ease_out_back(t)
        y = int(108 - (1 - t) * 26)
        if self.last_winner_rank == 1:
            center = (522, y + 6)
            for i, color in enumerate(RAINBOW_COLORS):
                angle = now * 0.004 + i * math.tau / len(RAINBOW_COLORS)
                draw_pixel_star(
                    surface,
                    center[0] + math.cos(angle) * 170,
                    center[1] + math.sin(angle) * 44,
                    4,
                    color,
                )
                pygame.draw.circle(
                    surface,
                    color,
                    (
                        int(center[0] + math.cos(angle + 0.8) * 112),
                        int(center[1] + math.sin(angle + 0.8) * 30),
                    ),
                    5,
                )

        text_color = random.choice(RAINBOW_COLORS) if self.last_winner_rank == 1 else GOLD
        text_surface = self.fonts["congrats"].render("당첨!", True, text_color)
        text_surface = pygame.transform.scale(
            text_surface,
            (
                max(1, int(text_surface.get_width() * pop)),
                max(1, int(text_surface.get_height() * pop)),
            ),
        )
        rect = text_surface.get_rect(center=(522, y))
        shadow = pygame.Surface(text_surface.get_size(), pygame.SRCALPHA)
        shadow.blit(text_surface, (0, 0))
        shadow.fill((0, 0, 0, 180), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(shadow, rect.move(5, 6))
        surface.blit(text_surface, rect)

        draw_text(
            surface,
            "1등 RAINBOW JACKPOT!" if self.last_winner_rank == 1 else "CONGRATULATIONS!",
            self.fonts["subtitle"],
            random.choice(RAINBOW_COLORS) if self.last_winner_rank == 1 else LOGO_GRAY_LIGHT,
            (522, 156),
            shadow=True,
            shadow_color=(0, 0, 0),
            pixel=True,
        )
        draw_text(
            surface,
            f"{self.target_number}번",
            self.fonts["result"],
            WHITE,
            (522, 512),
            shadow=True,
            shadow_color=(0, 0, 0),
        )

    def draw_particles(self, surface: pygame.Surface) -> None:
        for particle in self.particles:
            particle.draw(surface)

    def draw_flash_overlay(self, surface: pygame.Surface, now: int) -> None:
        if self.state != STATE_FINAL_REVEALED or self.last_draw_is_bulk:
            return

        elapsed = now - self.celebration_start
        if elapsed < 0 or elapsed > 1200:
            return

        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        if elapsed < 260:
            dark_alpha = int(120 * (1 - elapsed / 260))
            overlay.fill((0, 0, 0, dark_alpha))
            surface.blit(overlay, (0, 0))

        if 90 <= elapsed <= 430:
            flash_t = 1 - abs(elapsed - 210) / 170
            flash_alpha = int((220 if self.last_winner_rank == 1 else 170) * clamp(flash_t, 0.0, 1.0))
            flash_color = random.choice(RAINBOW_COLORS) if self.last_winner_rank == 1 else LOGO_ORANGE
            overlay.fill((*flash_color, flash_alpha))
            surface.blit(overlay, (0, 0))

    def blit_scene_to_screen(self, scene: pygame.Surface, shake_x: int, shake_y: int) -> None:
        """내부 1280x720 장면을 현재 창 크기에 맞게 비율 유지 스케일링합니다."""
        scale, offset_x, offset_y, scaled_w, scaled_h = self.scene_transform()
        if scaled_w == SCREEN_WIDTH and scaled_h == SCREEN_HEIGHT:
            scaled_scene = scene
        else:
            scaled_scene = pygame.transform.smoothscale(scene, (scaled_w, scaled_h))

        self.screen.blit(
            scaled_scene,
            (
                offset_x + int(shake_x * scale),
                offset_y + int(shake_y * scale),
            ),
        )

    def draw(self, now: int) -> None:
        scene = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)).convert()
        self.draw_background(scene, now)
        self.draw_title_area(scene)
        self.draw_gacha_device(scene, now)
        self.draw_digits(scene, now)
        self.draw_history(scene)
        self.draw_status(scene)
        self.start_button.draw(scene)
        self.reset_button.draw(scene)
        self.draw_prize_panel(scene, now)
        self.draw_congratulations(scene, now)
        self.draw_particles(scene)
        self.draw_result_modal(scene)

        self.screen.fill(BG_DEEP)
        shake_x = 0
        shake_y = 0
        if now < self.shake_until:
            remaining = clamp((self.shake_until - now) / 620, 0.0, 1.0)
            power = max(2, int(12 * remaining))
            shake_x = random.randint(-power, power)
            shake_y = random.randint(-power, power)
        self.blit_scene_to_screen(scene, shake_x, shake_y)
        self.draw_flash_overlay(self.screen, now)
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            now = pygame.time.get_ticks()
            self.handle_events()
            self.update(dt, now)
            self.draw(now)

        pygame.quit()


def main() -> None:
    app = GachaLotteryApp()
    app.run()


if __name__ == "__main__":
    main()
