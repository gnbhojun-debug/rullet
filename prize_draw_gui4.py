# -*- coding: utf-8 -*-
"""
경품 추첨 가챠 룰렛

실행 방법
1. Python 3 설치
2. pygame 설치: python -m pip install pygame
3. 실행: python prize_draw_gui.py

pygame이 설치되어 있지 않으면 위 설치 명령을 먼저 실행하세요.
외부 이미지 파일 없이 코드 내부의 도형, 텍스트, 픽셀아트만 사용합니다.

추첨 번호 범위와 추첨 인원을 조정해 당첨자를 뽑을 수 있습니다.
"""

from __future__ import annotations

import math
import random
import sys
from dataclasses import dataclass

try:
    import pygame
except ImportError:
    print("pygame이 설치되어 있지 않습니다.")
    print("설치 명령: python -m pip install pygame")
    sys.exit(1)


SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

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
PINK = LOGO_ORANGE_LIGHT
MINT = LOGO_TEAL
CYAN = LOGO_TEAL_LIGHT
VIOLET = LOGO_GRAY
PEACH = LOGO_ORANGE_DARK

ROULETTE_X_OFFSET = 114
ROULETTE_Y_OFFSET = -36

def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def ease_out_cubic(t: float) -> float:
    t = clamp(t, 0.0, 1.0)
    return 1.0 - pow(1.0 - t, 3)


def ease_out_back(t: float) -> float:
    t = clamp(t, 0.0, 1.0)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)


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
    ):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.accent = accent
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
            shadow=True,
            shadow_color=(255, 232, 186),
            pixel=False,
        )


class TextInput:
    """추첨 번호 범위와 추첨 인원을 직접 입력하는 간단한 텍스트 박스입니다."""

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
            "button": make_font(26, True),
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
        self.won_numbers: set[int] = set()
        self.history: list[int] = []
        self.latest_batch: list[int] = []
        self.batch_draw_numbers: list[int] = []
        self.batch_draw_index = 0
        self.batch_next_at = 0
        self.target_number: int | None = None
        self.show_unwon_list = False
        self.auto_tens_at = 0
        self.auto_ones_at = 0

        self.message = "Start를 누르면 당첨 번호가 자동 추첨됩니다."
        self.message_until = 0
        self.celebration_start = -9999
        self.shake_until = 0
        self.device_pulse_until = 0

        self.particles: list[Particle] = []
        self.background_twinkles: list[Particle] = []
        self.shooting_stars: list[ShootingStar] = []
        self.next_twinkle_at = 0
        self.next_shooting_star_at = 0
        self.background_stars = self.make_background_stars()

        self.tens_digit = RouletteDigit(
            pygame.Rect(354 + ROULETTE_X_OFFSET, 238 + ROULETTE_Y_OFFSET, 152, 188),
            list(range(0, 10)),
            self.fonts["digit"],
            self.fonts["digit_label"],
            "TENS",
            CYAN,
        )
        self.ones_digit = RouletteDigit(
            pygame.Rect(538 + ROULETTE_X_OFFSET, 238 + ROULETTE_Y_OFFSET, 152, 188),
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
        self.draw_count_input = TextInput(
            pygame.Rect(846, 636, 72, 58),
            "1",
            self.fonts["button"],
            placeholder="",
            allowed="0123456789",
            max_length=2,
        )
        self.unwon_button = Button(
            pygame.Rect(38, 488, 206, 38),
            "미 당첨자 리스트",
            self.fonts["small_bold"],
            LOGO_TEAL,
        )
        self.close_unwon_button = Button(
            pygame.Rect(742, 154, 86, 38),
            "Close",
            self.fonts["small_bold"],
            LOGO_ORANGE,
        )
        self.number_input = TextInput(
            pygame.Rect(1044, 38, 140, 38),
            "1-50",
            self.fonts["small_bold"],
        )
        self.apply_numbers_button = Button(
            pygame.Rect(1192, 38, 72, 38),
            "Apply",
            self.fonts["small_bold"],
            LOGO_TEAL,
        )

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

    def set_message(self, text: str, duration_ms: int = 2600) -> None:
        self.message = text
        self.message_until = pygame.time.get_ticks() + duration_ms

    def parse_draw_count(self) -> tuple[int, str | None]:
        text = self.draw_count_input.text.strip()
        if not text:
            return 0, "추첨 인원을 입력하세요."
        if not text.isdigit():
            return 0, "추첨 인원은 숫자만 입력하세요."

        count = int(text)
        if count < 1:
            return 0, "추첨 인원은 1명 이상이어야 합니다."
        return count, None

    def format_numbers(self, numbers: list[int], limit: int = 10) -> str:
        shown = ", ".join(f"{number}번" for number in numbers[:limit])
        if len(numbers) > limit:
            shown += f" 외 {len(numbers) - limit}명"
        return shown

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
        if self.state in {
            STATE_SPINNING_TENS,
            STATE_TENS_REVEALED,
            STATE_SPINNING_ONES,
            STATE_BATCH_REVEAL,
        }:
            self.set_message("룰렛이 멈춘 뒤 번호를 변경하세요.", 2200)
            return

        numbers, error = self.parse_number_pool(self.number_input.text)
        if error:
            self.set_message(error, 3000)
            return

        self.number_pool = numbers
        self.won_numbers.clear()
        self.history.clear()
        self.latest_batch.clear()
        self.batch_draw_numbers.clear()
        self.batch_draw_index = 0
        self.batch_next_at = 0
        self.target_number = None
        self.auto_tens_at = 0
        self.auto_ones_at = 0
        self.show_unwon_list = False
        self.state = STATE_IDLE
        self.tens_digit.reset()
        self.ones_digit.reset()
        self.particles.clear()
        self.set_message(f"추첨 번호 {len(numbers)}개가 적용되었습니다.", 2600)

    def unwon_numbers(self) -> list[int]:
        return [number for number in self.number_pool if number not in self.won_numbers]

    def draw_numbers_evenly(self, count: int) -> list[int]:
        return random.choices(self.number_pool, k=count)

    def update_button_state(self) -> None:
        self.start_button.enabled = self.state in {
            STATE_IDLE,
            STATE_FINAL_REVEALED,
        }
        active_draw_states = {
            STATE_SPINNING_TENS,
            STATE_TENS_REVEALED,
            STATE_SPINNING_ONES,
            STATE_BATCH_REVEAL,
        }
        self.apply_numbers_button.enabled = self.state not in active_draw_states
        self.unwon_button.enabled = self.state not in active_draw_states
        self.close_unwon_button.enabled = self.show_unwon_list

        if self.state == STATE_IDLE:
            self.start_button.text = "Start"
        elif self.state == STATE_FINAL_REVEALED:
            self.start_button.text = "Next Draw"
        else:
            self.start_button.text = "Spinning..."

    def handle_start(self) -> None:
        now = pygame.time.get_ticks()

        if self.state == STATE_FINAL_REVEALED:
            self.prepare_next_draw()
            return

        if not self.number_pool:
            self.set_message("추첨 번호를 먼저 설정하세요.", 2600)
            return

        draw_count, error = self.parse_draw_count()
        if error:
            self.set_message(error, 2600)
            return

        if self.state == STATE_IDLE:
            selected_numbers = self.draw_numbers_evenly(draw_count)
            self.auto_tens_at = 0
            self.auto_ones_at = 0
            self.tens_digit.reset()
            self.ones_digit.reset()

            if draw_count > 1:
                self.start_batch_reveal(selected_numbers, now)
                return

            self.target_number = selected_numbers[0]
            self.latest_batch.clear()
            self.device_pulse_until = now + 2400
            self.start_tens_spin(now)
            return

    def display_number_on_slots(self, number: int, now: int) -> None:
        self.target_number = number
        tens = number // 10
        ones = number % 10
        for digit, value in ((self.tens_digit, tens), (self.ones_digit, ones)):
            digit.value = value
            digit.target = value
            digit.current_digit = value
            digit.previous_digit = value
            digit.spinning = False
            digit.bounce_start = now

    def start_batch_reveal(self, numbers: list[int], now: int) -> None:
        self.batch_draw_numbers = list(numbers)
        self.batch_draw_index = 0
        self.latest_batch.clear()
        self.state = STATE_BATCH_REVEAL
        self.device_pulse_until = now + 1000
        self.show_batch_number(now)

    def show_batch_number(self, now: int) -> None:
        if self.batch_draw_index >= len(self.batch_draw_numbers):
            self.finish_draw(self.batch_draw_numbers)
            return

        number = self.batch_draw_numbers[self.batch_draw_index]
        self.display_number_on_slots(number, now)
        self.batch_next_at = now + 1000
        self.device_pulse_until = now + 1000
        self.shake_until = now + 240
        self.set_message(
            f"{self.batch_draw_index + 1}/{len(self.batch_draw_numbers)}번째 당첨 번호: {number}번",
            1200,
        )
        self.spawn_number_reveal_particles()

    def start_tens_spin(self, now: int) -> None:
        if self.target_number is None:
            return
        tens_duration = 2300
        tens = self.target_number // 10
        self.tens_digit.start_spin(tens, tens_duration, now)
        self.ones_digit.reset()
        self.state = STATE_SPINNING_TENS
        self.device_pulse_until = now + tens_duration + 300
        self.set_message("십의자리 룰렛 회전 중...", 1800)
        self.spawn_start_particles()

    def start_ones_spin(self, now: int) -> None:
        if self.target_number is None:
            return
        ones_duration = 2450
        ones = self.target_number % 10
        self.ones_digit.start_spin(ones, ones_duration, now)
        self.state = STATE_SPINNING_ONES
        self.device_pulse_until = now + ones_duration + 300
        self.set_message("일의자리 룰렛 회전 중...", 1800)
        self.spawn_start_particles()

    def prepare_next_draw(self) -> None:
        self.state = STATE_IDLE
        self.target_number = None
        self.latest_batch.clear()
        self.batch_draw_numbers.clear()
        self.batch_draw_index = 0
        self.batch_next_at = 0
        self.auto_tens_at = 0
        self.auto_ones_at = 0
        self.tens_digit.reset()
        self.ones_digit.reset()
        self.celebration_start = -9999
        self.set_message("다음 추첨을 준비했습니다.", 1800)

    def handle_reset(self) -> None:
        self.state = STATE_IDLE
        self.won_numbers.clear()
        self.history.clear()
        self.latest_batch.clear()
        self.batch_draw_numbers.clear()
        self.batch_draw_index = 0
        self.batch_next_at = 0
        self.target_number = None
        self.auto_tens_at = 0
        self.auto_ones_at = 0
        self.show_unwon_list = False
        self.tens_digit.reset()
        self.ones_digit.reset()
        self.particles.clear()
        self.celebration_start = -9999
        self.shake_until = 0
        self.device_pulse_until = 0
        self.set_message("초기화되었습니다. Start를 눌러 추첨하세요.", 2400)

    def finalize_winner(self) -> None:
        if self.target_number is None:
            return

        self.finish_draw([self.target_number])

    def finish_draw(self, numbers: list[int]) -> None:
        if not numbers:
            return

        self.latest_batch = list(numbers)
        self.history = self.latest_batch + self.history
        self.history = self.history[:20]
        self.won_numbers.update(self.latest_batch)
        self.batch_draw_numbers.clear()
        self.batch_draw_index = 0
        self.batch_next_at = 0
        self.state = STATE_FINAL_REVEALED

        now = pygame.time.get_ticks()
        self.celebration_start = now
        self.shake_until = now + 620
        self.device_pulse_until = now + 1500
        if len(self.latest_batch) == 1:
            self.set_message(f"당첨 번호: {self.latest_batch[0]}번", 4200)
        else:
            self.set_message(f"{len(self.latest_batch)}명 당첨: {self.format_numbers(self.latest_batch)}", 5200)
        self.spawn_celebration_particles()

    def spawn_start_particles(self) -> None:
        center = (522 + ROULETTE_X_OFFSET, 232 + ROULETTE_Y_OFFSET)
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
                    430 + ROULETTE_X_OFFSET,
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

    def spawn_number_reveal_particles(self) -> None:
        colors = [GOLD, CYAN, PINK, MINT, PEACH]
        origins = [
            self.tens_digit.rect.center,
            self.ones_digit.rect.center,
            (
                (self.tens_digit.rect.centerx + self.ones_digit.rect.centerx) // 2,
                self.tens_digit.rect.centery - 62,
            ),
        ]
        for _ in range(58):
            ox, oy = random.choice(origins)
            angle = random.uniform(0, math.tau)
            speed = random.uniform(90, 340)
            self.particles.append(
                Particle(
                    ox + random.uniform(-28, 28),
                    oy + random.uniform(-20, 20),
                    math.cos(angle) * speed,
                    math.sin(angle) * speed - random.uniform(40, 120),
                    random.uniform(0.65, 1.15),
                    1.15,
                    random.choice([2, 3]),
                    random.choice(colors),
                    random.choice(["star", "circle", "heart"]),
                    gravity=random.uniform(110, 210),
                )
            )

    def spawn_celebration_particles(self) -> None:
        colors = [GOLD, PINK, CYAN, MINT, VIOLET, PEACH]
        origins = [
            (432 + ROULETTE_X_OFFSET, 330 + ROULETTE_Y_OFFSET),
            (615 + ROULETTE_X_OFFSET, 330 + ROULETTE_Y_OFFSET),
            (522 + ROULETTE_X_OFFSET, 210 + ROULETTE_Y_OFFSET),
            (522 + ROULETTE_X_OFFSET, 440 + ROULETTE_Y_OFFSET),
        ]
        count = 180 if len(self.latest_batch) > 1 else 140
        for _ in range(count):
            ox, oy = random.choice(origins)
            angle = random.uniform(0, math.tau)
            speed = random.uniform(120, 520)
            self.particles.append(
                Particle(
                    ox + random.uniform(-30, 30),
                    oy + random.uniform(-25, 25),
                    math.cos(angle) * speed,
                    math.sin(angle) * speed - random.uniform(40, 160),
                    random.uniform(0.9, 1.8),
                    1.8,
                    random.choice([2, 3, 4]),
                    random.choice(colors),
                    random.choice(["star", "heart", "circle"]),
                    gravity=random.uniform(130, 260),
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
                    elif self.show_unwon_list:
                        self.show_unwon_list = False
                    else:
                        self.running = False
                    continue

            event = self.event_to_scene(raw_event)

            if self.show_unwon_list:
                if self.close_unwon_button.handle_event(event):
                    self.show_unwon_list = False
                continue

            if self.number_input.handle_event(event):
                self.apply_number_pool()

            if self.draw_count_input.handle_event(event):
                self.handle_start()

            if self.start_button.handle_event(event):
                self.handle_start()

            if self.reset_button.handle_event(event):
                self.handle_reset()

            if self.apply_numbers_button.handle_event(event):
                self.apply_number_pool()

            if self.unwon_button.handle_event(event):
                self.show_unwon_list = not self.show_unwon_list

    def update(self, dt: float, now: int) -> None:
        mouse_pos = self.screen_to_scene_pos(pygame.mouse.get_pos())
        self.update_button_state()
        self.start_button.update(mouse_pos)
        self.reset_button.update(mouse_pos)
        self.apply_numbers_button.update(mouse_pos)
        self.unwon_button.update(mouse_pos)
        self.close_unwon_button.update(mouse_pos)
        self.number_input.update(dt, mouse_pos)
        self.draw_count_input.update(dt, mouse_pos)
        self.spawn_background_effects(now)

        tens_finished = self.tens_digit.update(now)
        ones_finished = self.ones_digit.update(now)

        if tens_finished and self.state == STATE_SPINNING_TENS:
            self.state = STATE_TENS_REVEALED
            self.set_message("십의자리 공개! 일의자리 룰렛 준비 중...", 2600)
            self.auto_ones_at = now + 520
            self.spawn_small_reveal_particles()

        if self.state == STATE_TENS_REVEALED and self.auto_ones_at and now >= self.auto_ones_at:
            self.auto_ones_at = 0
            self.start_ones_spin(now)

        if ones_finished and self.state == STATE_SPINNING_ONES:
            self.finalize_winner()

        if self.state == STATE_BATCH_REVEAL and self.batch_next_at and now >= self.batch_next_at:
            self.batch_draw_index += 1
            self.show_batch_number(now)

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
            (1044, 28),
            anchor="midleft",
            shadow=True,
            shadow_color=(0, 0, 0),
        )

        self.number_input.draw(surface)
        self.apply_numbers_button.draw(surface)

    def draw_device_glow(self, surface: pygame.Surface, now: int) -> None:
        pulse_active = now < self.device_pulse_until or self.state in {
            STATE_SPINNING_TENS,
            STATE_TENS_REVEALED,
            STATE_SPINNING_ONES,
            STATE_BATCH_REVEAL,
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
        surface.blit(glow, (214 + ROULETTE_X_OFFSET, 100 + ROULETTE_Y_OFFSET))

    def draw_draw_banner(
        self,
        surface: pygame.Surface,
        banner: pygame.Rect,
        now: int,
    ) -> None:
        """장치 하단 슬롯에 현재 추첨 상태를 표시합니다."""
        pulse = 0.5 + 0.5 * math.sin(now * 0.008)
        active = self.state in {STATE_SPINNING_TENS, STATE_TENS_REVEALED, STATE_SPINNING_ONES, STATE_BATCH_REVEAL}
        accent = LOGO_TEAL if active else LOGO_GRAY
        glow = pygame.Surface((banner.width + 26, banner.height + 26), pygame.SRCALPHA)
        pygame.draw.rect(
            glow,
            (*accent, (68 + int(75 * pulse)) if active else 38),
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

        if self.state == STATE_FINAL_REVEALED and self.latest_batch:
            banner_text = f"{len(self.latest_batch)}명 당첨 완료"
        elif self.state == STATE_BATCH_REVEAL and self.batch_draw_numbers:
            banner_text = f"{self.batch_draw_index + 1}/{len(self.batch_draw_numbers)}번째 번호 표시 중"
        elif active:
            banner_text = "번호 룰렛 작동 중"
        else:
            count, error = self.parse_draw_count()
            banner_text = "이번 추첨 인원 확인 필요" if error else f"이번 추첨: {count}명"

        draw_pixel_star(surface, banner.x + 26, banner.centery, 3, LOGO_ORANGE_LIGHT)
        draw_pixel_star(surface, banner.right - 26, banner.centery, 3, LOGO_TEAL_LIGHT)

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

        base = pygame.Rect(282 + ROULETTE_X_OFFSET, 178 + ROULETTE_Y_OFFSET, 488, 380)
        pygame.draw.rect(surface, (0, 0, 0), base.move(0, 12), border_radius=18)
        pygame.draw.rect(surface, LOGO_ORANGE, base, border_radius=18)
        pygame.draw.rect(surface, PANEL_LIGHT, base.inflate(-18, -18), border_radius=14)
        pygame.draw.rect(surface, (38, 42, 43), base, 5, border_radius=18)

        top_plate = pygame.Rect(436 + ROULETTE_X_OFFSET, 124 + ROULETTE_Y_OFFSET, 180, 54)
        pygame.draw.rect(surface, (0, 0, 0), top_plate.move(0, 7), border_radius=10)
        pygame.draw.rect(surface, PANEL_LIGHT, top_plate, border_radius=10)
        pygame.draw.rect(surface, LOGO_GRAY_LIGHT, top_plate, 2, border_radius=10)
        draw_text(
            surface,
            "NUMBER DRAW",
            self.fonts["small_bold"],
            LOGO_ORANGE_LIGHT,
            top_plate.center,
            shadow=False,
            pixel=True,
        )

        frame = pygame.Rect(326 + ROULETTE_X_OFFSET, 208 + ROULETTE_Y_OFFSET, 392, 252)
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

        pedestal = pygame.Rect(354 + ROULETTE_X_OFFSET, 478 + ROULETTE_Y_OFFSET, 346, 62)
        self.draw_draw_banner(surface, pedestal, now)

    def draw_digits(self, surface: pygame.Surface, now: int) -> None:
        scale = 1.0
        reveal_t = (now - self.celebration_start) / 780
        if self.state == STATE_FINAL_REVEALED and 0.0 <= reveal_t <= 1.0:
            scale = 1.0 + 0.2 * math.sin(reveal_t * math.pi) * (1 - reveal_t * 0.35)

        self.tens_digit.draw(surface, now, external_scale=scale)
        self.ones_digit.draw(surface, now, external_scale=scale)

    def draw_history(self, surface: pygame.Surface) -> None:
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

        for i, number in enumerate(self.history[:5]):
            y = panel.y + 54 + i * 21
            color = WHITE if i == 0 else LOGO_GRAY_LIGHT
            draw_text(
                surface,
                f"{number}번",
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
                text = "Start를 누르면 당첨 번호가 자동 추첨됩니다."
            elif self.state == STATE_TENS_REVEALED:
                text = "일의자리 룰렛 준비 중..."
            elif self.state == STATE_BATCH_REVEAL:
                text = "당첨 번호를 순서대로 표시 중..."

        draw_text_fit(
            surface,
            text,
            self.fonts["small_bold"],
            WHITE,
            panel.center,
            panel.width - 24,
            shadow=False,
        )

    def draw_unwon_modal(self, surface: pygame.Surface) -> None:
        if not self.show_unwon_list:
            return

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
            "미 당첨자 리스트",
            self.fonts["subtitle"],
            LOGO_ORANGE_LIGHT,
            (panel.x + 24, panel.y + 30),
            anchor="midleft",
            shadow=True,
            shadow_color=(0, 0, 0),
        )
        draw_text(
            surface,
            f"남은 미당첨 번호 {len(unwon)} / {len(self.number_pool)}",
            self.fonts["small_bold"],
            LOGO_GRAY_LIGHT,
            (panel.x + 24, panel.y + 62),
            anchor="midleft",
            shadow=False,
        )
        self.close_unwon_button.draw(surface)

        list_rect = pygame.Rect(panel.x + 24, panel.y + 92, panel.width - 48, panel.height - 122)
        pygame.draw.rect(surface, (9, 11, 12), list_rect, border_radius=8)
        pygame.draw.rect(surface, PANEL_EDGE, list_rect, 2, border_radius=8)

        if not unwon:
            draw_text(
                surface,
                "모든 번호가 한 번 이상 당첨되었습니다.",
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

        for index, number in enumerate(unwon[:max_items]):
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

        if len(unwon) > max_items:
            draw_text(
                surface,
                f"+ {len(unwon) - max_items}개 더 있음",
                self.fonts["small"],
                LOGO_GRAY_LIGHT,
                (list_rect.centerx, list_rect.bottom - 14),
                shadow=False,
            )

    def draw_congratulations(self, surface: pygame.Surface, now: int) -> None:
        if self.state != STATE_FINAL_REVEALED or not self.latest_batch:
            return

        t = clamp((now - self.celebration_start) / 700, 0.0, 1.0)
        pop = ease_out_back(t)
        left_center = (220, 310)
        right_center = (1080, 320)
        text_surface = self.fonts["congrats"].render("당첨!", True, GOLD)
        text_surface = pygame.transform.scale(
            text_surface,
            (
                max(1, int(text_surface.get_width() * pop)),
                max(1, int(text_surface.get_height() * pop)),
            ),
        )
        rect = text_surface.get_rect(center=left_center)
        shadow = pygame.Surface(text_surface.get_size(), pygame.SRCALPHA)
        shadow.blit(text_surface, (0, 0))
        shadow.fill((0, 0, 0, 180), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(shadow, rect.move(5, 6))
        surface.blit(text_surface, rect)

        draw_text(
            surface,
            "CONGRATULATIONS!",
            self.fonts["subtitle"],
            LOGO_GRAY_LIGHT,
            (left_center[0], left_center[1] + 62),
            shadow=True,
            shadow_color=(0, 0, 0),
            pixel=True,
        )

        number_panel = pygame.Rect(right_center[0] - 150, right_center[1] - 104, 300, 188)
        pygame.draw.rect(surface, (0, 0, 0), number_panel.move(8, 10), 3, border_radius=12)
        pygame.draw.rect(surface, LOGO_TEAL, number_panel, 4, border_radius=12)
        draw_text(
            surface,
            "당첨 번호" if len(self.latest_batch) == 1 else f"당첨 번호 {len(self.latest_batch)}명",
            self.fonts["subtitle"],
            LOGO_GRAY_LIGHT,
            (right_center[0], number_panel.y + 34),
            shadow=False,
        )
        if len(self.latest_batch) == 1:
            draw_text(
                surface,
                f"{self.latest_batch[0]}번",
                self.fonts["result"],
                WHITE,
                right_center,
                shadow=True,
                shadow_color=(0, 0, 0),
            )
            return

        cell_w = 56
        cell_h = 30
        cols = 5
        start_x = number_panel.x + 18
        start_y = number_panel.y + 64
        max_items = 15
        for index, number in enumerate(self.latest_batch[:max_items]):
            col = index % cols
            row = index // cols
            rect = pygame.Rect(start_x + col * cell_w, start_y + row * cell_h, 46, 23)
            pygame.draw.rect(surface, (228, 231, 226), rect, border_radius=5)
            pygame.draw.rect(surface, LOGO_ORANGE, rect, 2, border_radius=5)
            draw_text(
                surface,
                str(number),
                self.fonts["small_bold"],
                INK,
                rect.center,
                shadow=False,
            )

        if len(self.latest_batch) > max_items:
            draw_text(
                surface,
                f"+ {len(self.latest_batch) - max_items}명",
                self.fonts["small_bold"],
                LOGO_GRAY_LIGHT,
                (right_center[0], number_panel.bottom - 20),
                shadow=False,
            )

    def draw_particles(self, surface: pygame.Surface) -> None:
        for particle in self.particles:
            particle.draw(surface)

    def draw_flash_overlay(self, surface: pygame.Surface, now: int) -> None:
        if self.state != STATE_FINAL_REVEALED:
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
            flash_alpha = int(170 * clamp(flash_t, 0.0, 1.0))
            overlay.fill((*LOGO_ORANGE, flash_alpha))
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
        draw_text(
            scene,
            "추첨 인원",
            self.fonts["tiny"],
            LOGO_GRAY_LIGHT,
            (846, 626),
            anchor="midleft",
            shadow=False,
            pixel=True,
        )
        self.draw_count_input.draw(scene)
        draw_text(
            scene,
            "명",
            self.fonts["button"],
            LOGO_GRAY_LIGHT,
            (928, 665),
            anchor="midleft",
            shadow=True,
            shadow_color=(0, 0, 0),
        )
        self.draw_congratulations(scene, now)
        self.draw_particles(scene)
        self.draw_unwon_modal(scene)

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
