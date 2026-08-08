import pygame
import sys
import subprocess
import math
import random
import json
import os

_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
_CORE_DIR = os.path.join(_ROOT_DIR, "core_v1")
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from core_v1.classes import Player, TextureFactory, INF, WRN, ERR, DEV, SUC
from colorama import init

pygame.init()
pygame.mixer.init()
init(autoreset=True)


# Оригінальне вікно розроблянося на 2к дисплеї, 
#  для менших або більших екранів, додано масштабування 
#   яке ніяк не впливає на логіку гри (оригінальні обрахунки на 1600x900).
BASE_WIDTH, BASE_HEIGHT = 1600, 900
WIDTH, HEIGHT = BASE_WIDTH, BASE_HEIGHT

info = pygame.display.Info()
window_w = max(1100, int(info.current_w * 0.75))
window_h = max(650, int(info.current_h * 0.75))
SCREEN_WIDTH, SCREEN_HEIGHT = min(1400, window_w), min(800, window_h)

FPS = 60

# Всі координати живуть в розмірі 1600x900.
#  А лише потім розтягується або стискається для користувача.
screen = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
display = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Gravity Shift - Головне Меню")
clock = pygame.time.Clock()

scale_x = SCREEN_WIDTH / BASE_WIDTH
scale_y = SCREEN_HEIGHT / BASE_HEIGHT


def to_virtual_mouse(mouse_pos):
    return (mouse_pos[0] / scale_x, mouse_pos[1] / scale_y)

BG_COLOR = (5, 5, 12)
CYAN = (0, 220, 255)
WHITE = (255, 255, 255)
GRAY = (180, 180, 180)
RED = (180, 20, 40)
DARK = (25, 25, 40)


# ====================== ШРИФТИ =======================================

title_font = pygame.font.SysFont("Consolas", 110, bold=True)
mega_font  = pygame.font.SysFont("Consolas", 60, bold=True)
big_font   = pygame.font.SysFont("Consolas", 32, bold=True)
mid_font   = pygame.font.SysFont("Consolas", 22, bold=True)
small_font = pygame.font.SysFont("Consolas", 18)

# ====================== ЛОГО ТА АВАРІЙНИЙ ФОЛЬБЕК ====================
logo_image = None
logo_path = os.path.join(_ROOT_DIR, "MARS_world", "Resources", "Picture", "Logo_menu.png")
if os.path.exists(logo_path):
    try:
        logo_image = pygame.image.load(logo_path).convert_alpha()
        # Зменшимо логотип до розміру, близького до текстового заголовка
        max_w = int(WIDTH * 2.4)
        max_h = int(title_font.get_height() * 2.6)
        w, h = logo_image.get_size()
        if w > max_w or h > max_h:
            scale = min(max_w / w, max_h / h)
            logo_image = pygame.transform.smoothscale(logo_image, (int(w * scale), int(h * scale)))
    except Exception as e:
        print(f"{ERR} Помилка завантаження логотипу {logo_path}: {e} \n")
        logo_image = None

# ====================== ДОВІДКОВІ ДАНІ ===============================

ADVICE = {
    1: "He забувай що гpa ніколи не закінчиться. Вона матиме купа доповнень, купу світів i купу нових механік. Просто насолоджуйся процесом.",
    2: "He зупиняйся! Проходь гpy!",
    3: "Світ як i жорстокий так i хороший, треба просто...   ...бути обережним.",
    4: "Режим розробника Dev Mode показує купу моїх старань, сделать користування зручним!",
    5: "He тільки портали можуть міняти тобі гравітацію. Просто вір y ce6e i все вийде...  А нуй це лише для розробників, нечесно було б давати таку силу гравцю)",
    6: "Гравець не тільки плавний, ай виразний, достатньо сіганути в прірву, гарантую шок)",
    7: "Текстури, напевно мій найсильніший ворог. Якби тільки не слабкий пк, я б мабуть не знав про оптимуізацію...",
    8: "Партікли дуже мені складні для розуміння, це ж буквально купа частинок, як вони не з'їдають процесор?",
    9: "Першим вибухом у розробці гри був Vector2, зараз це моя улюблена частина коду, я навіть не знаю як би я робив гру без нього...",
    10: "Якщо ти не куриш як тим всім керувати, чи забув. затисни Ctrl і отримаєш список всіх клавіш та їх роботу.",
    11: "ЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕ\nЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕ\nЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕеееееее\nееееее  СІКС СЕВЕН",
    12: "Are you sure?",
    13: "Обличчя повинно відображати дії! Навіть якщо це т_T",
    14: "Ви хоча б розумієте, наскільки запарно було робити стилі? Я почав цінувати як об'єкти створені...",
    15: "Що вставити в пораду дня цитую:\"хз хз, це нада думать, я так не вмію\" автор анонімий :Х",
    16: "Музика... Ці саунди обрані нашвидкоруч. Хз чи колись будуть кращі. О а ще було б норм звуки світові додати оооооооо~",
    17: "Мій друг гадає, що ця гра натхнена Geometry Dash. Так от це не правда. Гра побудована на гравітаціях і переродженна в пригоди!",
    18: "Оце з мене художник.. Дві текстурки і вже бомба. Так і в політику...",
    19: "Скін MKin не просто іменний, він має більшу увагу у мому коді. Просто крути пресети і маєш шанс на рідкісний варіант!",
    20: "Я робив скіни гравцю більш цікавішими, додавши власну текстуру і характер. Статичним маюнком не обійшлося)",
    21: "Streetfly раніше був фічою а ніж користю. Тупо упиняв всі рухи в сторони, круто ж він зараз реалізований)",
    22: "Ммм доречі, фільтри. КОли ти програєш або перемагаєш на фоні все стає не розбірливим, не знав?",
    23: "Вгадайде що саме більше жерло мій проц всі ці часи? Нетягну, інфо панелі що оновлювалися 60 разів на секунду(",
    24: "Я пишаюся як зробив конвеєр стилів, тільки скіни гравців соло стали вау ефектом)",
    25: "Рух кнопок і обєктів в головному меню, зроблемі однією формулою тому достатньо змінити координати чи розмір щоб воно було різним.",
    26: "Система збережень працює так, що видалить твій прогрем якщо ти грубо натисниш на X на вікні гри ;)",
    27: "Світло працює дуже цікаво. А для світла від сонця, щей з'являється засвіт на об'єктах.",
    28: "README.md - документ інструкція по грі. Якщо ти ще не читав його, то рекомендую, там є купа корисної інформації про гру, її механіки та навіть секрети!",
    29: "Анімація головного меню, плавність в кожному кадрі. І кожного разу я буду його модернізовувати. Як нарахунок зорепад?",
    30: "Рефакторинг коду. Коли я писав свій перший README.md, я заодне вз'явся за зміни, щоб модинг став блище до реальності."
}

# ====================== ФАЙЛОВА СИСТЕМА ТА ЗБЕРЕЖЕННЯ ================
save_file = os.path.join(_ROOT_DIR, "core_v1", "save.json")
save_data = {}

default_save = {
    "world_id": "objects.json",
    "player": {"x": None, "y": None, "campfires": 0, "gravity": [0, 1]},
    "settings": {"preset": "classic", "control_mode": "both", "is_fullscreen": False, "lighting_enabled": True, "white_light_active": True},
    "audio": {"volume": 0.1, "track_name": None, "track_pos": 0}}

try:
    if os.path.exists(save_file):
        with open(save_file, "r", encoding="utf-8") as f:
            save_data = json.load(f)
except Exception as e:
    print(f"{ERR} Помилка читання {save_file}: {e} \n")

settings_data = save_data.get("settings", {})
audio_data    = save_data.get("audio", {})

saved_preset  = settings_data.get("preset", "classic")
saved_control = settings_data.get("control_mode", "both")
saved_volume  = audio_data.get("volume", 0.1)

# ====================== АУДІО ========================================

pygame.mixer.music.load(os.path.join(_ROOT_DIR, "MARS_world", "Resources", "Music", "Clear Momentum.mp3")) 
pygame.mixer.music.set_volume(saved_volume)
pygame.mixer.music.play(-1)

# ====================== КЛАСИ ЯДРА (КАМЕРА ТА ГРАВЕЦЬ) ===============

class Camera:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.target_x = 0.0
        self.target_y = 0.0
        self.speed = 0.05

    def update(self):
        self.x += (self.target_x - self.x) * self.speed
        self.y += (self.target_y - self.y) * self.speed

    def move_to(self, state):
        if state == "MAIN":
            self.target_x, self.target_y = 0, 0
        elif state == "SETTINGS":
            self.target_x, self.target_y = WIDTH, 0
        elif state == "PLAY":
            self.target_x, self.target_y = 0, -HEIGHT

# --- ОПТИМІЗАЦІЯ: Глобальний фон із зірками (Starfield) ---
class Starfield:
    def __init__(self, w, h):
        self.layers = []
        # 3 шари паралаксу замість 500 окремих обчислень
        for parallax in [0.15, 0.3, 0.45]:
            surf = pygame.Surface((w * 2, h * 2), pygame.SRCALPHA)
            for _ in range(120): # Кількість зірок на шар
                x = random.randint(0, w * 2 - 1)
                y = random.randint(0, h * 2 - 1)
                r = random.randint(1, 3)
                pygame.draw.circle(surf, (200, 200, 255), (x, y), r)
            self.layers.append({"surf": surf.convert_alpha(), "p": parallax, "w": w * 2, "h": h * 2})

    def draw(self, surface, cam_x, cam_y):
        surface.fill(BG_COLOR)
        for layer in self.layers:
            # Створюємо ефект безкінечного прокручування
            offset_x = -(cam_x * layer["p"]) % layer["w"]
            offset_y = -(cam_y * layer["p"]) % layer["h"]
            
            surface.blit(layer["surf"], (offset_x, offset_y))
            surface.blit(layer["surf"], (offset_x - layer["w"], offset_y))
            surface.blit(layer["surf"], (offset_x, offset_y - layer["h"]))
            surface.blit(layer["surf"], (offset_x - layer["w"], offset_y - layer["h"]))

class MenuPlayer:
    active_drag = None 
    def __init__(self, x, y, bounds_rect, force_dir=None, is_main=False):
        self.is_main = is_main
        self.player_data = Player(x, y)
        self.player_data.current_preset = saved_preset
        self.player_data.control_mode = saved_control
        
        self.force_dir = force_dir
        if self.force_dir:
            self.player_data.gravity_vec = pygame.Vector2(self.force_dir)
            
        self.player_data.update_color()
        
        self.pos = pygame.Vector2(x, y)
        self.size = self.player_data.size
        
        # Налаштування індивідуальних параметрів швидкості та розміру
        if self.is_main:
            self.size = int(self.player_data.size * 1.5)  
            angle = random.uniform(0, 2 * math.pi)
            self.vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * 1.5  
        else:
            self.vel = pygame.Vector2(random.uniform(-2, 2), random.uniform(-2, 2))
            
        self.rect = pygame.Rect(x, y, self.size, self.size)
        self.is_dragged = False
        self.last_mouse_pos = pygame.Vector2(0, 0)
        self.bounds = bounds_rect

    def update(self, mouse_pos, mouse_pressed, cam_x, cam_y):
        world_mouse = pygame.Vector2(mouse_pos[0] + cam_x, mouse_pos[1] + cam_y)

        # Логіка захоплення (один раз)
        if mouse_pressed[0]:
            if not self.is_dragged and self.rect.collidepoint(world_mouse.x, world_mouse.y):
                if MenuPlayer.active_drag is None:
                    self.is_dragged = True
                    MenuPlayer.active_drag = self
        else:
            self.is_dragged = False
            if MenuPlayer.active_drag == self:
                MenuPlayer.active_drag = None

        # Фізика переміщення
        if self.is_dragged:
            self.vel = world_mouse - self.last_mouse_pos
            self.pos = world_mouse - pygame.Vector2(self.size / 2, self.size / 2)
        else:
            if self.is_main:
                speed = self.vel.length()
                if speed > 1.5:
                    # Плавне сповільнення до стабільної швидкості (зберігається інерція кидка)
                    self.vel *= 0.98
                    # Коли швидкість впала нижче ліміту, жорстко фіксується на 1.5
                    if self.vel.length() < 1.5:
                        self.vel = self.vel.normalize() * 1.5
                elif 0 < speed < 1.5:
                    self.vel = self.vel.normalize() * 1.5
                elif speed == 0:
                    angle = random.uniform(0, 2 * math.pi)
                    self.vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * 1.5
                    
                self.pos += self.vel
            else:
                # Міні-гравці підкоряються вектору сили тяжіння у свій бік
                if self.force_dir:
                    self.vel += pygame.Vector2(self.force_dir) * 0.25
                self.pos += self.vel
                self.vel *= 0.98  # Стабілізаційне тертя простору для міні-зони

            # Відбивання від заданих кордонів
            hit_wall = False
            if self.pos.x <= self.bounds.left:
                self.pos.x = self.bounds.left
                self.vel.x = abs(self.vel.x)
                if not self.is_main: self.vel.x *= 0.9  # Весела пружинистість для прев'ю
                hit_wall = True
            elif self.pos.x >= self.bounds.right - self.size:
                self.pos.x = self.bounds.right - self.size
                self.vel.x = -abs(self.vel.x)
                if not self.is_main: self.vel.x *= 0.9
                hit_wall = True
                
            if self.pos.y <= self.bounds.top:
                self.pos.y = self.bounds.top
                self.vel.y = abs(self.vel.y)
                if not self.is_main: self.vel.y *= 0.9
                hit_wall = True
            elif self.pos.y >= self.bounds.bottom - self.size:
                self.pos.y = self.bounds.bottom - self.size
                self.vel.y = -abs(self.vel.y)
                if not self.is_main: self.vel.y *= 0.9
                hit_wall = True

            # Хаотичний нелінійний відскок для головного великого гравця
            if hit_wall and self.is_main:
                # Випадковий розкид кута відскоку в межах +-15 градусів
                self.vel = self.vel.rotate(random.uniform(-15, 15))
                # Жорстке вирівнювання напрямку, щоб уникнути застрягання всередині колізії стіни
                if self.pos.x <= self.bounds.left: self.vel.x = abs(self.vel.x)
                if self.pos.x >= self.bounds.right - self.size: self.vel.x = -abs(self.vel.x)
                if self.pos.y <= self.bounds.top: self.vel.y = abs(self.vel.y)
                if self.pos.y >= self.bounds.bottom - self.size: self.vel.y = -abs(self.vel.y)

        self.last_mouse_pos = world_mouse
        self.rect.topleft = self.pos
        self.player_data.rect.topleft = self.pos

        # --- ЗАПИС ПОЗИЦІЙ ДЛЯ ШЛЕЙФУ ---
        if self.player_data.current_preset == "classic" and self.vel.length() > 0.5:
            current_img = self.player_data.image
            if self.is_main:
                current_img = pygame.transform.scale(current_img, (self.size, self.size))
            self.player_data.ghost_positions.append((self.pos.copy(), current_img))
            if len(self.player_data.ghost_positions) > self.player_data.max_ghosts:
                self.player_data.ghost_positions.pop(0)
        else:
            if self.player_data.ghost_positions:
                self.player_data.ghost_positions.pop(0)

    def draw(self, surface, cam_x, cam_y):
        # --- ДИНАМІЧНА КАДРОВКА АНІМАЦІЙ ---
        current_style = self.player_data.skin_styles.get(self.player_data.current_preset)

        if current_style == "matrix_flow": frame_limit = 30
        elif current_style == "liquid_lava": frame_limit = 10
        elif current_style == "noise_dust": frame_limit = 40
        else: frame_limit = 10 

        if current_style in ("matrix_flow", "liquid_lava", "noise_dust"):
            self.player_data.visual_tick += 1
            if self.player_data.visual_tick >= frame_limit:
                if self.force_dir: self.player_data.gravity_vec = pygame.Vector2(self.force_dir)
                self.player_data.update_color()
                self.player_data.visual_tick = 0
        else:
            # Одноразове застосування кольору для статичних міні-гравців
            if self.force_dir and self.player_data.visual_tick == 0:
                self.player_data.gravity_vec = pygame.Vector2(self.force_dir)
                self.player_data.update_color()
                self.player_data.visual_tick = 1
            
        draw_pos = self.pos - pygame.Vector2(cam_x, cam_y)

        # --- ВІДМАЛЬОВУВАННЯ ШЛЕЙФУ (CLASSIC) ---
        if self.player_data.current_preset == "classic":
            for i, (ghost_pos, ghost_img) in enumerate(self.player_data.ghost_positions):
                alpha = int((i + 1) * (180 / len(self.player_data.ghost_positions)))
                ghost_img.set_alpha(alpha)
                ghost_draw_pos = ghost_pos - pygame.Vector2(cam_x, cam_y)
                surface.blit(ghost_img, ghost_draw_pos)
                ghost_img.set_alpha(255)

        # --- ВІДМАЛЬОВУВАННЯ ГРАВЦЯ ---
        img = self.player_data.image
        if self.is_main:
            img = pygame.transform.scale(img, (self.size, self.size))
            
        surface.blit(img, draw_pos)
        self.draw_face(surface, cam_x, cam_y)

    def draw_face(self, surface, cam_x, cam_y):
        if not self.is_main: 
            return # Малюється обличчя ТІЛЬКИ для головного кубика
        
        t = pygame.time.get_ticks() / 1000.0
        # Координати центру гравця на екрані
        cx = self.pos.x - cam_x + self.size / 2
        cy = self.pos.y - cam_y + self.size / 2
        
        # Колір обличчя (затемнений основний колір скіна)
        dark_color = [int(c * 0.3) for c in self.player_data.color]
        # Коефіцієнт масштабу (у грі базовий розмір 50, а в меню він збільшений)
        scale_ratio = self.size / 50.0
        
        move_vel_x = self.vel.x
        move_vel_y = self.vel.y
        
        # Зсув обличчя в сторону руху (інерція/очікування удару)
        shift_x = max(-10, min(10, move_vel_x * 1.5)) * scale_ratio
        shift_y = max(-10, min(10, move_vel_y * 1.5)) * scale_ratio
        
        speed_factor = min(self.vel.length() / 20.0, 1.0)
        breath_e = math.sin(t * 3) * scale_ratio
        breath_m = math.sin((t - 0.07) * 3) * scale_ratio
        
        # Динамічне розтягування рота від швидкості
        dynamic_stretch = min(self.vel.length() * 0.4, 10) * scale_ratio
        
        # Розміри очей (збільшуються при великій швидкості)
        base_eye_s = 10 + int(4 * speed_factor)
        ew = eh = int(base_eye_s * scale_ratio)
        
        # Рот (звужується і розтягується)
        mouth_narrowness = max(0.4, 1.0 - (abs(self.vel.length()) / 25.0))
        mw = int(35 * mouth_narrowness * scale_ratio)
        mh = int((6 + dynamic_stretch) * scale_ratio)
        
        # Базові відстані
        eye_dist = 10 * scale_ratio

        # Очі "з'їжджаються" при русі вбік
        left_eye_dist = eye_dist
        right_eye_dist = eye_dist
        if move_vel_x > 1: left_eye_dist *= 0.6
        elif move_vel_x < -1: right_eye_dist *= 0.6
            
        eye_depth = -11 * scale_ratio
        mouth_depth = 6 * scale_ratio
        
        # Кінцеві позиції по Y
        e_y = cy + eye_depth + breath_e + shift_y
        m_y = cy + mouth_depth + breath_m + shift_y
        
        eyes_pos = [
            pygame.Rect(int(cx - left_eye_dist - ew / 2 + shift_x), int(e_y - eh / 2), ew, eh),
            pygame.Rect(int(cx + right_eye_dist - ew / 2 + shift_x), int(e_y - eh / 2), ew, eh)
        ]
        
        mouth_rect = pygame.Rect(int(cx - mw / 2 + shift_x), int(m_y - mh / 2), mw, mh)
        
        for eye in eyes_pos:
            pygame.draw.rect(surface, dark_color, eye)
        pygame.draw.rect(surface, dark_color, mouth_rect)

# ====================== КЛАСИ ІНТЕРФЕЙСУ (UI) ========================

class DriftingButton:
    def __init__(self, text, base_x, base_y, action, font_size=32, color_theme="default", shift_x_coeff=0.0, shift_y_coeff=0.0):
        self.text = text
        self.base_x = base_x
        self.base_y = base_y
        self.action = action
        self.shift_x_coeff = shift_x_coeff
        self.shift_y_coeff = shift_y_coeff
        
        # Створюємо унікальний шрифт для кнопки з урахуванням переданого розміру
        custom_font = pygame.font.SysFont("Consolas", font_size, bold=True)
        
        # Налаштування кольорових тем
        if color_theme == "red":
            self.base_color = (40, 20, 20)      # Темно-червоний фон
            self.hover_color = (70, 35, 35)     # Світліший при наведенні
            self.border_color = (255, 100, 100) # Яскраво-червона рамка
        elif color_theme == "green":
            self.base_color = (20, 40, 20)      # Темно-зелений фон
            self.hover_color = (35, 70, 35)     # Світліший при наведенні
            self.border_color = (100, 255, 100) # Яскраво-зелена рамка
        else: # "default" (Існуючий синій варіант)
            self.base_color = DARK
            self.hover_color = (40, 40, 60)
            self.border_color = WHITE
            
        self.surf_text = custom_font.render(text, True, WHITE)
        self.w = self.surf_text.get_width() + 60
        self.h = self.surf_text.get_height() + 40
        self.hovered = False
        self.time_offset = random.uniform(0, math.pi * 2)

        self.normal_surf = self._create_surf(self.base_color)
        self.hover_surf = self._create_surf(self.hover_color)

    def _create_surf(self, bg_color):
        btn_surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        pygame.draw.rect(btn_surf, bg_color, (0, 0, self.w, self.h), border_radius=10)
        pygame.draw.rect(btn_surf, self.border_color, (0, 0, self.w, self.h), 2, border_radius=10)
        txt_rect = self.surf_text.get_rect(center=(self.w//2, self.h//2))
        btn_surf.blit(self.surf_text, txt_rect)
        return btn_surf

    def get_current_transform(self, cam_x=0, cam_y=0):
        t = pygame.time.get_ticks() / 1000.0 + self.time_offset
        dx = math.sin(t * 0.8) * 20
        dy = math.cos(t * 1.2) * 15
        angle = math.sin(t * 0.5) * 3 
        return self.base_x + dx + cam_x * self.shift_x_coeff, self.base_y + dy + cam_y * self.shift_y_coeff, angle

    def update(self, mouse_pos, cam_x, cam_y):
        x, y, _ = self.get_current_transform(cam_x, cam_y)
        screen_x = x - cam_x
        screen_y = y - cam_y
        rect = pygame.Rect(screen_x - self.w//2, screen_y - self.h//2, self.w, self.h)
        self.hovered = rect.collidepoint(mouse_pos)
        return self.hovered

    def draw(self, surface, cam_x, cam_y):
        x, y, angle = self.get_current_transform(cam_x, cam_y)
        screen_x = x - cam_x
        screen_y = y - cam_y

        current_surf = self.hover_surf if self.hovered else self.normal_surf
        
        rotated_surf = pygame.transform.rotate(current_surf, angle)
        rot_rect = rotated_surf.get_rect(center=(screen_x, screen_y))
        
        surface.blit(rotated_surf, rot_rect)

class PlanetNode:
    def __init__(self, x, y, name, radius, image_path):
        self.x = x
        self.y = y
        self.name = name
        self.radius = radius
        self.hovered = False
        
        self.image = None
        if os.path.exists(image_path):
            try:
                self.image = pygame.image.load(image_path).convert_alpha()
                self.image = pygame.transform.scale(self.image, (radius * 2, radius * 2))
            except Exception as e:
                print(f"{ERR} Помилка завантаження текстури планети {image_path}: {e} \n")

    def update(self, mouse_pos, cam_x, cam_y):
        screen_x = self.x - cam_x
        screen_y = self.y - cam_y
        dist = math.hypot(mouse_pos[0] - screen_x, mouse_pos[1] - screen_y)
        self.hovered = dist <= self.radius

    def draw(self, surface, cam_x, cam_y):
        screen_x = self.x - cam_x
        screen_y = self.y - cam_y

        # Обведення при наведенні миші 
        if self.hovered:
            pygame.draw.circle(surface, WHITE, (int(screen_x), int(screen_y)), self.radius + 0, 2)
            lbl = big_font.render(self.name, True, WHITE)
            surface.blit(lbl, (screen_x - lbl.get_width()//2, screen_y + self.radius + 10))

        # Відображення картинки Марса
        if self.image:
            surface.blit(self.image, (int(screen_x - self.radius), int(screen_y - self.radius)))
        else:
            pygame.draw.circle(surface, (180, 60, 30), (int(screen_x), int(screen_y)), self.radius)
            pygame.draw.circle(surface, (0, 0, 0), (int(screen_x), int(screen_y)), self.radius, 3)

class DebrisNode:
    def __init__(self, text, x, y, w, h, action, drift_group=None):
        self.base_x = x
        self.base_y = y
        self.w = w
        self.h = h
        self.text = text
        self.action = action
        self.hovered = False
        self.drift_group = drift_group

    def update(self, mouse_pos, cam_x, cam_y):
        dx = self.drift_group.dx if self.drift_group else 0
        dy = self.drift_group.dy if self.drift_group else 0
        
        curr_x = self.base_x + dx
        curr_y = self.base_y + dy
        
        rect = pygame.Rect(curr_x - cam_x, curr_y - cam_y, self.w, self.h)
        self.hovered = rect.collidepoint(mouse_pos)
        return rect, curr_x, curr_y

    def draw(self, surface, cam_x, cam_y):
        dx = self.drift_group.dx if self.drift_group else 0
        dy = self.drift_group.dy if self.drift_group else 0
        
        screen_x = self.base_x + dx - cam_x
        screen_y = self.base_y + dy - cam_y
        
        color = (60, 70, 80) if not self.hovered else (80, 90, 100)
        
        rect = pygame.Rect(screen_x, screen_y, self.w, self.h)
        pygame.draw.rect(surface, color, rect, border_radius=5)
        pygame.draw.rect(surface, (100, 110, 120), rect, 2, border_radius=5)
        
        lbl = mid_font.render(self.text, True, WHITE)
        surface.blit(lbl, (screen_x + 15, screen_y + 15))

        val_txt = ""
        if self.action == "TOGGLE_SKIN": val_txt = menu_player.player_data.current_preset
        elif self.action == "TOGGLE_CTRL": val_txt = menu_player.player_data.control_mode
        
        if val_txt:
            val_surf = big_font.render(val_txt, True, CYAN)
            surface.blit(val_surf, (screen_x + 15, screen_y + 50))

class KeyCrossNode:
    def __init__(self, x, y, drift_group=None):
        self.x = x
        self.y = y
        self.drift_group = drift_group

    def draw(self, surface, cam_x, cam_y):
        dx = self.drift_group.dx if self.drift_group else 0
        dy = self.drift_group.dy if self.drift_group else 0
        
        screen_x = self.x + dx - cam_x
        screen_y = self.y + dy - cam_y
        size = 70
        mode = menu_player.player_data.control_mode

        if mode == "both": labels = ["W/↑", "A/←", "S/↓", "D/→"]
        elif mode == "wasd_only": labels = ["W", "A", "S", "D"]
        else: labels = ["↑", "←", "↓", "→"]

        positions = [
            (screen_x, screen_y - size),
            (screen_x - size, screen_y),
            (screen_x, screen_y),
            (screen_x + size, screen_y)
        ]

        for i, pos in enumerate(positions):
            r = pygame.Rect(pos[0], pos[1], 60, 60)
            pygame.draw.rect(surface, WHITE, r, 2, border_radius=8)
            txt = small_font.render(labels[i], True, WHITE)
            surface.blit(txt, (r.centerx - txt.get_width() // 2, r.centery - txt.get_height() // 2))

class AdviceNode:
    def __init__(self, x, y, w, h, drift_group=None):
        self.base_x = x
        self.base_y = y
        self.w = w
        self.h = h
        self.advice_id = random.randint(1, len(ADVICE))
        self.hovered = False
        self.drift_group = drift_group

    def update(self, mouse_pos, cam_x, cam_y):
        dx = self.drift_group.dx if self.drift_group else 0
        dy = self.drift_group.dy if self.drift_group else 0
        
        rect = pygame.Rect(self.base_x + dx - cam_x, self.base_y + dy - cam_y, self.w, self.h)
        self.hovered = rect.collidepoint(mouse_pos)

    def draw(self, surface, cam_x, cam_y):
        dx = self.drift_group.dx if self.drift_group else 0
        dy = self.drift_group.dy if self.drift_group else 0
        
        screen_x = self.base_x + dx - cam_x
        screen_y = self.base_y + dy - cam_y
        
        rect = pygame.Rect(screen_x, screen_y, self.w, self.h)
        color = DARK if not self.hovered else (40, 40, 60)
        pygame.draw.rect(surface, color, rect, border_radius=12)
        pygame.draw.rect(surface, CYAN, rect, 2, border_radius=12)
        
        title = big_font.render("Порада дня", True, CYAN)
        surface.blit(title, (screen_x + 20, screen_y - 35))

        text = ADVICE[self.advice_id]
        words = text.replace('\n', ' \n ').split(' ')
        
        lines = []
        current = ""
        for word in words:
            if word == '\n':
                lines.append(current)
                current = ""
                continue
            test = current + word + " "
            if mid_font.size(test)[0] < self.w - 40:
                current = test
            else:
                lines.append(current)
                current = word + " "
        lines.append(current)
        
        start_y = screen_y + 30
        for line in lines:
            txt = mid_font.render(line, True, WHITE)
            surface.blit(txt, (screen_x + 20, start_y))
            start_y += 35

class VolumeSliderNode:
    def __init__(self, x, y, w, h, drift_group=None):
        self.base_x = x
        self.base_y = y
        self.w = w
        self.h = h
        global saved_volume
        self.val = saved_volume
        self.is_dragging = False
        self.drift_group = drift_group

    def update(self, mouse_pos, mouse_pressed, cam_x, cam_y):
        dx = self.drift_group.dx if self.drift_group else 0
        dy = self.drift_group.dy if self.drift_group else 0
        
        screen_x = self.base_x + dx - cam_x
        screen_y = self.base_y + dy - cam_y
        rect = pygame.Rect(screen_x - 10, screen_y - 10, self.w + 20, self.h + 20)
        
        if mouse_pressed[0]:
            if rect.collidepoint(mouse_pos) or self.is_dragging:
                self.is_dragging = True
                rel = (mouse_pos[0] - screen_x) / self.w
                self.val = max(0.0, min(1.0, rel))
                pygame.mixer.music.set_volume(self.val)
                global saved_volume
                saved_volume = self.val
        else:
            self.is_dragging = False

    def draw(self, surface, cam_x, cam_y):
        dx = self.drift_group.dx if self.drift_group else 0
        dy = self.drift_group.dy if self.drift_group else 0
        
        screen_x = self.base_x + dx - cam_x
        screen_y = self.base_y + dy - cam_y
        
        title = mid_font.render("Гучність", True, CYAN)
        surface.blit(title, (screen_x, screen_y - 35))

        outer = pygame.Rect(screen_x, screen_y, self.w, self.h)
        pygame.draw.rect(surface, WHITE, outer, border_radius=8)
        inner = pygame.Rect(screen_x + 2, screen_y + 2, self.w - 4, self.h - 4)
        pygame.draw.rect(surface, (60, 60, 60), inner, border_radius=8)
        
        knob_x = screen_x + int(self.val * self.w)
        pygame.draw.circle(surface, WHITE, (int(knob_x), int(screen_y + self.h // 2)), 12)

class MenuLabDecoration:
    def __init__(self, x, y, w, h, obj_type="lab", drift_group=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.obj_type = obj_type
        self.image = TextureFactory.get_texture(obj_type, w, h)
        self.drift_group = drift_group 

    def draw(self, surface, cam_x, cam_y):
        dx = self.drift_group.dx if self.drift_group else 0
        dy = self.drift_group.dy if self.drift_group else 0

        screen_x = self.rect.x + dx - cam_x
        screen_y = self.rect.y + dy - cam_y
        surface.blit(self.image, (screen_x, screen_y))

class DriftGroup:
    def __init__(self, time_offset, amp_x=12, amp_y=8, speed=1.0):
        self.time_offset = time_offset # Для розсинхрону різних груп
        self.amp_x = amp_x
        self.amp_y = amp_y
        self.speed = speed
        self.dx = 0
        self.dy = 0

    def update(self):
        t = pygame.time.get_ticks() / 1000.0 * self.speed + self.time_offset
        self.dx = math.sin(t * 0.8) * self.amp_x
        self.dy = math.cos(t * 1.2) * self.amp_y

# ====================== СТВОРЕННЯ ОБ'ЄКТІВ ТА ІНСТАНЦІЙ ==============
camera = Camera()

# Групи левітації
group_controls = DriftGroup(time_offset=0)
group_skins    = DriftGroup(time_offset=2.5)
group_advice   = DriftGroup(time_offset=5.0)
group_volume   = DriftGroup(time_offset=7.5)

# Ініціалізація оптимізованого зоряного неба
stars_bg = Starfield(WIDTH, HEIGHT)

# Гравці
main_bounds = pygame.Rect(0, 0, WIDTH, HEIGHT)
menu_player = MenuPlayer(WIDTH // 2, HEIGHT // 2, main_bounds, is_main=True)

# Тестова рамка зі скінами
preview_bounds = pygame.Rect(WIDTH + 1050, 140, 400, 300)
physics_bounds = preview_bounds.inflate(-4, -4)

skin_previews = [
    MenuPlayer(WIDTH + 1150, 250, physics_bounds, force_dir=(0, 1),  is_main=False),  
    MenuPlayer(WIDTH + 1250, 250, physics_bounds, force_dir=(0, -1), is_main=False),  
    MenuPlayer(WIDTH + 1150, 350, physics_bounds, force_dir=(-1, 0), is_main=False),  
    MenuPlayer(WIDTH + 1250, 350, physics_bounds, force_dir=(1, 0),  is_main=False)]  

# ---===--- UI Елементи ---===---
# Кнопки навігації головного меню
main_buttons = [
    DriftingButton("ДО ПРИГОД",        WIDTH // 2,       HEIGHT // 2,       "GO_PLAY",     font_size=50, color_theme="green",   shift_x_coeff=-0.5, shift_y_coeff=-0.6),
    DriftingButton("НАЛАШТУНКИ",       WIDTH // 2 - 280, HEIGHT // 2 + 150, "GO_SETTINGS", font_size=40, color_theme="default", shift_x_coeff=-0.9, shift_y_coeff=-1.5),
    DriftingButton("ПОКИНУТИ ПРОСТІР", WIDTH // 2 + 280, HEIGHT // 2 + 170, "QUIT",        font_size=30, color_theme="red",     shift_x_coeff=-0.6, shift_y_coeff=-1.8)]

# Кнопки планети рівнів
levels = [
    PlanetNode(WIDTH // 2, -HEIGHT // 2, "Марс", 125, os.path.join(_ROOT_DIR, "MARS_world", "Resources", "Picture", "MARS_pik.png"))]

# Кнопки діалогу прогресу
confirm_buttons = [
    DriftingButton("НОВА ГРА",   WIDTH // 2 - 220, -HEIGHT // 2 + 30, "NEW_GAME", font_size=40, color_theme="red"),
    DriftingButton("ПРОДОВЖИТИ", WIDTH // 2 + 220, -HEIGHT // 2 + 30, "CONTINUE", font_size=40, color_theme="green")]

# Кнопки перемикачі
settings_debris = [
    DebrisNode("СКІН",      WIDTH + 830, HEIGHT//2 - 220, 180, 120, "TOGGLE_SKIN", drift_group=group_skins),
    DebrisNode("КЕРУВАННЯ", WIDTH + 200, HEIGHT//2 - 250, 300, 120, "TOGGLE_CTRL", drift_group=group_controls)]

# Креслення клавіш / Панель з порадами / Повзунок гучності
key_cross = KeyCrossNode(WIDTH + 340, HEIGHT//2 - 20, drift_group=group_controls)
advice_panel = AdviceNode(WIDTH + 890, HEIGHT - 350, 400, 250, drift_group=group_advice)
volume_slider = VolumeSliderNode(WIDTH + 370, HEIGHT - 160, 300, 10, drift_group=group_volume)

# Об'єкти лабораторії
lab_decorations_data = [
        # --- Фон та платформи лабораторії ---
    {"x": WIDTH + WIDTH // 2 - 650, "y": HEIGHT // 2 - 280, "w": 400, "h": 340, "type": "lab_bg", "group": group_controls},
    {"x": WIDTH + WIDTH // 2 - 720, "y": HEIGHT // 2 - 320, "w": 70,  "h": 340, "type": "lab",    "group": group_controls},
    {"x": WIDTH + WIDTH // 2 - 720, "y": HEIGHT // 2 - 350, "w": 500, "h": 70,  "type": "lab",    "group": group_controls},
    {"x": WIDTH + WIDTH // 2 - 20,  "y": HEIGHT // 2 - 340, "w": 700, "h": 360, "type": "lab_bg", "group": group_skins},
    {"x": WIDTH + WIDTH // 2 + 680, "y": HEIGHT // 2 - 340, "w": 70,  "h": 340, "type": "lab",    "group": group_skins},
    {"x": WIDTH + WIDTH // 2 + 10,  "y": HEIGHT // 2 - 410, "w": 740, "h": 70,  "type": "lab",    "group": group_skins},
    {"x": WIDTH + WIDTH // 2 + 60,  "y": HEIGHT // 2 + 50,  "w": 470, "h": 330, "type": "lab_bg", "group": group_advice},
    {"x": WIDTH + WIDTH // 2 + 530, "y": HEIGHT // 2 + 120, "w": 70, "h": 260, "type": "lab",     "group": group_advice},
    {"x": WIDTH + WIDTH // 2 + 20,  "y": HEIGHT // 2 + 380, "w": 580,"h": 60,  "type": "lab",     "group": group_advice},
    {"x": WIDTH + WIDTH // 2 - 460, "y": HEIGHT // 2 + 220, "w": 360, "h": 130, "type": "lab_bg", "group": group_volume},
    {"x": WIDTH + WIDTH // 2 - 480, "y": HEIGHT // 2 + 350, "w": 400, "h": 60,  "type": "lab",     "group": group_volume},
    {"x": WIDTH + WIDTH // 2 + 650, "y": HEIGHT // 2 + 80,  "w": 90,  "h": 60,  "type": "lab",     "group": group_volume},
    {"x": WIDTH + WIDTH // 2 - 670, "y": HEIGHT // 2 + 110, "w": 60,  "h": 150, "type": "lab",     "group": group_skins}]

# Генерація списку об'єктів класу
lab_decorations = [MenuLabDecoration(d["x"], d["y"], d["w"], d["h"], d["type"], drift_group=d["group"]) for d in lab_decorations_data]
# ====================== ДОПОМІЖНІ ФУНКЦІЇ ============================

def draw_static_back(surface, cam_x, cam_y, mouse_pos):
    if abs(cam_x) > 100 or abs(cam_y) > 100:
        rect = pygame.Rect(40, HEIGHT - 100, 200, 60)
        hovered = rect.collidepoint(mouse_pos)
        
        color = RED if not hovered else (220, 50, 70)
        pygame.draw.rect(surface, color, rect, border_radius=8)
        pygame.draw.rect(surface, WHITE, rect, 2, border_radius=8)
        
        lbl = mid_font.render("ПОВЕРНУТИСЯ", True, WHITE)
        surface.blit(lbl, (rect.centerx - lbl.get_width()//2, rect.centery - lbl.get_height()//2))
        return rect, hovered
    return None, False

def save_and_play():
    if "settings" not in save_data: save_data["settings"] = {}
    if "audio" not in save_data: save_data["audio"] = {}

    save_data["settings"]["preset"] = menu_player.player_data.current_preset
    save_data["settings"]["control_mode"] = menu_player.player_data.control_mode
    save_data["audio"]["volume"] = saved_volume

    with open(save_file, "w", encoding="utf-8") as f:
        json.dump(save_data, f, ensure_ascii=False, indent=4)
    
    subprocess.Popen([sys.executable, os.path.join(_ROOT_DIR, "MARS_world", "main.py")], cwd=os.path.join(_ROOT_DIR, "MARS_world"))
    pygame.quit()
    sys.exit()

def standart_progress():
    """Скидає абсолютно все до заводських налаштувань (викликається при закритті на хрестик)."""
    try:
        with open(save_file, "w", encoding="utf-8") as f:
            json.dump(default_save, f, ensure_ascii=False, indent=4)
        print(f"{WRN} Прогрес та налаштування повністю скинуто до звичайних. \n")
    except Exception as e:
        print(f"{ERR} Помилка при скиданні налаштувань: {e} \n")

def has_progress():
    """Перевіряє, чи є у гравця реальний прогрес у світі."""
    player_data = save_data.get("player", {})
    # Прогрес вважається наявним, якщо координати не None або збережено вогнища
    return player_data.get("x") is not None or player_data.get("campfires", 0) > 0

# ====================== ГОЛОВНИЙ ЦИКЛ ГРИ ============================
show_progress_dialog = False
running = True
current_state = "MAIN"

while running:
    mouse_pos = pygame.mouse.get_pos()
    mouse_pos = to_virtual_mouse(mouse_pos)
    mouse_pressed = pygame.mouse.get_pressed()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            standart_progress()
            running = False
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            back_rect, is_hovered = draw_static_back(screen, camera.x, camera.y, mouse_pos)
            if back_rect and is_hovered:
                current_state = "MAIN"
                camera.move_to(current_state)
                show_progress_dialog = False
                continue

            if current_state == "MAIN":
                for btn in main_buttons:
                    if btn.hovered:
                        if btn.action == "GO_PLAY":
                            current_state = "PLAY"
                            camera.move_to(current_state)
                        elif btn.action == "GO_SETTINGS":
                            current_state = "SETTINGS"
                            camera.move_to(current_state)
                        elif btn.action == "QUIT":
                            running = False
                            
            elif current_state == "PLAY":
                if show_progress_dialog:
                    for btn in confirm_buttons:
                        if btn.hovered:
                            if btn.action == "NEW_GAME":
                                save_data["player"] = default_save["player"].copy()
                                save_data["world_id"] = default_save["world_id"]
                                save_and_play()
                            elif btn.action == "CONTINUE":
                                save_and_play()
                else:
                    for lvl in levels:
                        if lvl.hovered:
                            if has_progress(): show_progress_dialog = True
                            else: save_and_play()
                        
            elif current_state == "SETTINGS":
                for deb in settings_debris:
                    if deb.hovered:
                        if deb.action == "TOGGLE_SKIN":
                            menu_player.player_data.switch_skin()
                            new_preset = menu_player.player_data.current_preset
                            for mp in skin_previews:
                                mp.player_data.current_preset = new_preset
                                mp.player_data.update_color()
                        elif deb.action == "TOGGLE_CTRL":
                            menu_player.player_data.switch_control_mode()
                if advice_panel.hovered:
                    advice_panel.advice_id += 1
                    if advice_panel.advice_id > len(ADVICE):
                        advice_panel.advice_id = 1

    # Оновлення логіки груп
    group_controls.update()
    group_skins.update()
    group_advice.update()
    group_volume.update()

    # Оновлення логіки
    camera.update()
    menu_player.update(mouse_pos, mouse_pressed, camera.x, camera.y)
    
    if current_state == "SETTINGS" or camera.x > 100:
        advice_panel.update(mouse_pos, camera.x, camera.y)
        volume_slider.update(mouse_pos, mouse_pressed, camera.x, camera.y)
        for mp in skin_previews:
            mp.update(mouse_pos, mouse_pressed, camera.x, camera.y)
    
    for btn in main_buttons:
        btn.update(mouse_pos, camera.x, camera.y)
        
    for lvl in levels:
        lvl.update(mouse_pos, camera.x, camera.y)
        
    if current_state == "PLAY" and show_progress_dialog:
        for btn in confirm_buttons:
            btn.update(mouse_pos, camera.x, camera.y)
        
    for deb in settings_debris:
        deb.update(mouse_pos, camera.x, camera.y)

    # Рендеринг
    stars_bg.draw(screen, camera.x, camera.y)

    # --- ДОДАНО: Відмальовування декорацій лабораторії ---
    for decor in lab_decorations:
        decor.draw(screen, camera.x, camera.y)

    menu_player.draw(screen, camera.x, camera.y)

    # СЕКЦІЯ: ГОЛОВНЕ МЕНЮ (0, 0)
    if not show_progress_dialog:
        if logo_image:
            img = logo_image
            t = pygame.time.get_ticks() / 1000.0
            dx = math.sin(t * 0.8) * 10
            dy = math.cos(t * 1.1) * 8
            angle = math.sin(t * 0.45) * 2.5
            rotated_img = pygame.transform.rotate(img, angle)
            img_x = WIDTH // 2 - rotated_img.get_width() // 2 - camera.x + dx
            img_y = camera.y * 0.9 + dy
            screen.blit(rotated_img, (img_x, img_y))
        else:
            title_x = WIDTH // 2 - title_font.size("GRAVITY SHIFT")[0] // 2 - camera.x
            title_y = 80 - camera.y * 0.8
            shadow = title_font.render("GRAVITY SHIFT", True, (25,25,25))
            txt    = title_font.render("GRAVITY SHIFT", True, CYAN)
            screen.blit(shadow, (title_x - 4, title_y + 5))
            screen.blit(txt, (title_x, title_y))

    for btn in main_buttons:
        btn.draw(screen, camera.x, camera.y)   

    # СЕКЦІЯ: НАЛАШТУВАННЯ (WIDTH, 0)
    for deb in settings_debris:
        deb.draw(screen, camera.x, camera.y)
    key_cross.draw(screen, camera.x, camera.y)
    advice_panel.draw(screen, camera.x, camera.y)
    volume_slider.draw(screen, camera.x, camera.y)
    
    # Малює зону прев'ю
    dx, dy = group_skins.dx, group_skins.dy
    
    # Левітація до рамки
    preview_rect = pygame.Rect(preview_bounds.x + dx - camera.x, preview_bounds.y + dy - camera.y, preview_bounds.w, preview_bounds.h)
    pygame.draw.rect(screen, DARK, preview_rect, border_radius=12)
    pygame.draw.rect(screen, (60, 70, 80), preview_rect, 2, border_radius=12)
    
    lbl_preview = small_font.render("Інтерактивна тестова зона", True, GRAY)
    screen.blit(lbl_preview, (preview_rect.x + 15, preview_rect.y - 20))
    
    # Малює міні-гравців, передаючи їм додаткове зміщення через камеру
    for mp in skin_previews:
        # Віднімає dx/dy від камери суто для малювання, щоб вони рухалися з рамкою
        mp.draw(screen, camera.x - dx, camera.y - dy)

    # СЕКЦІЯ: ГРАТИ (0, -HEIGHT)
    if not show_progress_dialog:
        story_lbl = mega_font.render("ВИБРАТИ НОВУ ІСТОРІЮ", True, WHITE)
        story_x = WIDTH // 2 - story_lbl.get_width() // 2 - camera.x
        story_y = 40 - HEIGHT - camera.y
        screen.blit(story_lbl, (story_x, story_y))

    if show_progress_dialog:
        lbl = mega_font.render("СХОЖЕ ВИ ВЖЕ МАЄТЕ ПРОГРЕС", True, WHITE)
        lbl_x =   WIDTH // 2 - lbl.get_width()  // 2 - camera.x
        lbl_y = (-HEIGHT // 2 - lbl.get_height() // 2 - camera.y) - 110
        screen.blit(lbl, (lbl_x, lbl_y))
        
        for btn in confirm_buttons:
            btn.draw(screen, camera.x, camera.y)
    else:
        for lvl in levels:
            lvl.draw(screen, camera.x, camera.y)

    # Static UI (кнопка назад)
    draw_static_back(screen, camera.x, camera.y, mouse_pos)

    scaled = pygame.transform.smoothscale(screen, (SCREEN_WIDTH, SCREEN_HEIGHT))
    display.blit(scaled, (0, 0))
    pygame.display.flip()
    clock.tick(FPS)
pygame.quit()


# M.
