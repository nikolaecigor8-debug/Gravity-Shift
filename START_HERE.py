import pygame
import sys
import subprocess
from classes import Player
import random
pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 1600, 900
FPS = 30

BG = (8, 10, 35)
GRID = (30, 50, 100)

CYAN = (0, 220, 255)
WHITE = (255, 255, 255)
GRAY = (180, 180, 180)
RED = (180, 20, 40)
DARK = (25, 25, 40)
BLUE = (0, 120, 220)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gravity Shift - Меню")
clock = pygame.time.Clock()

pygame.mixer.music.load("Music/Main_menu.mp3")
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)
# ====================== ШРИФТИ ===========================

title_font = pygame.font.SysFont("Consolas", 122, bold=True)
title_font_small = pygame.font.SysFont("Consolas", 102, bold=True)
big_font = pygame.font.SysFont("Consolas", 32, bold=True)
mid_font = pygame.font.SysFont("Consolas", 22, bold=True)
small_font = pygame.font.SysFont("Consolas", 18)

player = Player(0, 0)

# ====================== ПОРАДИ ==========================

ADVICE = {
    1: "He забувай що гpa ніколи не закінчиться. Вона матиме купа доповнень, купу світів i купу нових механік. Просто насолоджуйся процесом.",
    2: "He зупиняйся! Проходь гpy!",
    3: "Світ як i жорстокий так i хороший, треба просто...   ...бути обережним.",
    4: "Режим розробника Dev Mode показує купу моїх старань, зробити користування зручним!",
    5: "He тільки портали можуть міняти тобі гравітацію. Просто вір y ce6e i все вийде...  А нуй це лише для розробників, нечесно було б давати таку силу гравцю)",
    6: "Гравець не тільки плавний, ай виразний, достатньо сіганути в прірву, гарантую шок)",
    7: "Текстури, напевно мій найсильніший ворог. Якби тільки не слабкий пк, я б мабуть не знав про оптимуізацію...",
    8: "Партікли дуже мені складні для розуміння, це ж буквально купа частинок, як вони не з'їдають процесор...",
    9: "Першим вибухом у розробці гри був Vector2, зараз це моя улюблена частина коду, я навіть не знаю як би я робив гру без нього...",
    10: "Якщо ти не куриш як тим всім керувати, чи забув. затисни Ctrl і отримаєш список всіх клавіш та їх роботу.",
    11: '''ЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕ
           ЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕ
           ЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕеееееее
           ееееее  СІКС СЕВЕН '''
    }
advice_id = random.randint(1, len(ADVICE)) # 1
volume = 0.5
dragging_slider = False

class MenuState:
    MAIN = "main"
    SETTINGS = "settings"
current_state = MenuState.MAIN

class Button:
    def __init__(self, x, y, w, h, text, color):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hovered = False

    def draw(self):
        c = self.color
        if self.hovered:
            c = (
                min(c[0] + 30, 255),
                min(c[1] + 30, 255),
                min(c[2] + 30, 255),
            )

        shadow_rect = self.rect.move(-5, 7)
        pygame.draw.rect(screen, (0, 0, 0), shadow_rect, border_radius=12)
        pygame.draw.rect(screen, c, self.rect, border_radius=12)

        txt = big_font.render(self.text, True, WHITE)
        screen.blit(
            txt,
            (self.rect.centerx - txt.get_width() // 2,
             self.rect.centery - txt.get_height() // 2))

    def update(self, mouse):
        self.hovered = self.rect.collidepoint(mouse)

# ================== ГОЛОВНЕ МЕНЮ =======================
btn_play = Button( WIDTH // 2 - 180, 350, 400, 90, "ГРАТИ", BLUE)
btn_settings = Button(WIDTH // 2 - 180, 470, 400, 90, "НАЛАШТУВАННЯ", (50, 50, 80))

stars = []
for _ in range(120):
    stars.append((
        random.randint(0, WIDTH),
        random.randint(0, HEIGHT),
        random.randint(1, 3)
    ))

# ======================= ФОН ==========================
def draw_grid():
    screen.fill((10, 8, 25))

    # слабкий grid
    for x in range(0, WIDTH, 70):
        pygame.draw.line(screen, (20, 30, 60), (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, 70):
        pygame.draw.line(screen, (20, 30, 60), (0, y), (WIDTH, y), 1)

    # зірки
    for x, y, r in stars:
        pygame.draw.circle(screen, (220, 220, 255), (x, y), r)

    # Марс
    pygame.draw.circle(
        screen,
        (140, 60, 45),
        (1300, 180),
        120
    )

    # темні плями
    pygame.draw.circle(screen, (100, 40, 30), (1260, 150), 30)
    pygame.draw.circle(screen, (100, 40, 30), (1330, 220), 25)

    # орбіти
    pygame.draw.circle(screen, CYAN, (1300, 180), 160, 1)
    pygame.draw.circle(screen, CYAN, (1300, 180), 190, 1)

for r in range(100, 900, 80):
    pygame.draw.circle(screen, (20, 70, 120), (WIDTH//2, HEIGHT//2), r, 1)

pygame.draw.ellipse(
    screen,
    (90, 35, 25),
    (-100, 760, 700, 250))
pygame.draw.ellipse(
    screen,
    (110, 45, 35),
    (400, 780, 900, 220))

def draw_title():
    if current_state == MenuState.SETTINGS:
        font = title_font_small
        y, y1 = 40, 15
    else:
        font = title_font
        y, y1 = 110, 105
        

    shadow = font.render("GRAVITY SHIFT", True, (0, 0, 0))
    txt = font.render("GRAVITY SHIFT", True, CYAN)

    screen.blit(shadow, (WIDTH // 2 - shadow.get_width() // 2-7, y+10))
    screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, y))

    shadow1 = big_font.render("Випробування MAPC", True, (0, 0, 0))
    txt1 = big_font.render("Випробування MAPC", True, (180, 95, 65))

    screen.blit(shadow1, (WIDTH // 2 - shadow1.get_width() // 2-7, y1+115))
    screen.blit(txt1, (WIDTH // 2 - txt1.get_width() // 2-2, y1+110))

def neon_rect(rect):
    pygame.draw.rect(screen, DARK, rect, border_radius=12)
    pygame.draw.rect(screen, CYAN, rect, 3, border_radius=12)

# ================ НАЛАШТУВАННЯ UI ====================
def draw_control_panel():
    x = 220
    y = 240
    w = 250
    h = 250

    title = mid_font.render("КЕРУВАННЯ", True, CYAN)
    screen.blit(title, (x + 10, y - 40))
    rect = pygame.Rect(x, y, w, h)
    neon_rect(rect)
    mode = player.control_mode

    if mode == "both":
        txt = "Обидва"
    elif mode == "wasd_only":
        txt = "WASD"
    else:
        txt = "Стрілки"

    t = big_font.render(txt, True, WHITE)
    screen.blit(t,
        (rect.centerx - t.get_width() // 2,
         rect.centery - 20))

    hint = small_font.render("Перемикнути", True, GRAY)
    screen.blit(hint,
        (rect.centerx - hint.get_width() // 2,
         rect.bottom - 35))
    return rect

def draw_key_cross():
    cx = 310
    cy = 630
    size = 90
    mode = player.control_mode

    if mode == "both":
        labels = ["W / ↑", "A / ←", "S / ↓", "D / →"]
    elif mode == "wasd_only":
        labels = ["W", "A", "S", "D"]
    else:
        labels = ["↑", "←", "↓", "→"]

    positions = [
        (cx, cy - size),
        (cx - size, cy),
        (cx, cy),
        (cx + size, cy)
    ]

    for i, pos in enumerate(positions):
        r = pygame.Rect(pos[0], pos[1], 80, 80)
        pygame.draw.rect(screen, WHITE, r, 3)
        txt = mid_font.render(labels[i], True, WHITE)
        screen.blit(txt,
            (r.centerx - txt.get_width() // 2,
             r.centery - txt.get_height() // 2))

def draw_skin_panel():
    x = 660
    y = 240
    w = 250
    h = 250

    title = mid_font.render("СКІН ГРАВЦЯ", True, CYAN)
    screen.blit(title, (x + 10, y - 40))
    rect = pygame.Rect(x, y, w, h)
    neon_rect(rect)
    txt = big_font.render(player.current_preset, True, WHITE)
    screen.blit(txt,
        (rect.centerx - txt.get_width() // 2,
         rect.centery - 20))

    hint = small_font.render("Зміни пресет", True, GRAY)
    screen.blit(
        hint,
        (
            rect.centerx - hint.get_width() // 2,
            rect.bottom - 35
        ))

    return rect

def draw_skin_colors():
    colors = player.presets[player.current_preset]
    order = [
        ((0, 1), "Вниз"),
        ((0, -1), "Вверх"),
        ((-1, 0), "Вліво"),
        ((1, 0), "Вправо")
    ]
    x = 600
    y = 570

    for i, item in enumerate(order):
        vec, name = item
        c = colors[vec]
        r = pygame.Rect(x + i * 100, y, 80, 80)
        pygame.draw.rect(screen, c, r, border_radius=14)
        txt = mid_font.render(name, True, WHITE)
        screen.blit(txt,
            (r.centerx - txt.get_width() // 2,
             r.bottom + 15))

def draw_advice_panel():
    global advice_id
    x = 1060
    y = 240
    w = 380
    h = 300

    title = big_font.render("Порада дня", True, DARK)
    screen.blit(title, (x + 37, y - 40))
    title = big_font.render("Порада дня", True, CYAN)
    screen.blit(title, (x + 40, y - 43))
    rect = pygame.Rect(x, y, w, h)
    neon_rect(rect)

    hint1 = small_font.render("Наступна", True, GRAY)
    screen.blit(hint1,
        (rect.centerx - hint1.get_width() // 2,
         rect.bottom - 35))

    text = ADVICE[advice_id]
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = current + word + " "
        if mid_font.size(test)[0] < w - 40:
            current = test
        else:
            lines.append(current)
            current = word + " "

    lines.append(current)
    start_y = rect.y + 30

    for line in lines:
        txt = mid_font.render(line, True, WHITE)
        screen.blit(txt, (rect.x + 25, start_y))
        start_y += 35
    return rect

def draw_back():
    rect = pygame.Rect(40, 790, 220, 70)
    pygame.draw.rect(screen, RED, rect, border_radius=8)
    txt = big_font.render("НАЗАД", True, WHITE)
    screen.blit(txt,
        (rect.centerx - txt.get_width() // 2,
         rect.centery - txt.get_height() // 2))
    return rect

def draw_volume_slider():
    slider_x = 1080
    slider_y = 590
    slider_w = 320
    slider_h = 10

    # назва
    title = mid_font.render("Гучність", True, CYAN)
    screen.blit(title, (slider_x, slider_y - 35))

    # рамка
    outer = pygame.Rect(slider_x, slider_y, slider_w, slider_h)
    pygame.draw.rect(screen, WHITE, outer, border_radius=8)

    # внутрішній темний трек
    inner = pygame.Rect(slider_x + 2, slider_y + 2, slider_w - 4, slider_h - 4)

    pygame.draw.rect(screen, (60, 60, 60), inner, border_radius=8)
    # позиція повзунка
    knob_x = slider_x + int(volume * slider_w)
    pygame.draw.circle(screen, WHITE, (knob_x, slider_y + slider_h // 2), 12)
    return outer

running = True
while running:
    # ---------------- ЛОГІЧНИЙ МОНСТР ------------------
    mouse = pygame.mouse.get_pos()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if current_state == MenuState.MAIN:
                if btn_play.rect.collidepoint(mouse):
                    with open("notes.txt", "w", encoding="utf-8") as f:
                        f.write(player.current_preset + "\n")
                        f.write(player.control_mode + "\n")
                        f.write(str(volume))
                    subprocess.Popen([sys.executable, "main.py", player.current_preset, player.control_mode])
                    running = False
                elif btn_settings.rect.collidepoint(mouse):
                    current_state = MenuState.SETTINGS
                    advice_id = random.randint(1, len(ADVICE))
            elif current_state == MenuState.SETTINGS:
                if control_rect.collidepoint(mouse):
                    player.switch_control_mode()
                elif volume_rect.collidepoint(mouse):
                    dragging_slider = True
                elif skin_rect.collidepoint(mouse):
                    player.switch_skin()
                elif advice_rect.collidepoint(mouse):
                    advice_id += 1
                    if advice_id > len(ADVICE):
                        advice_id = 1
                elif back_rect.collidepoint(mouse):
                    current_state = MenuState.MAIN

    if event.type == pygame.MOUSEBUTTONUP:
       dragging_slider = False
    if dragging_slider:
        slider_x = 1080
        slider_w = 320
        rel = (mouse[0] - slider_x) / slider_w
        volume = max(0.0, min(1.0, rel))
        pygame.mixer.music.set_volume(volume)

    draw_grid()
    draw_title()

    if current_state == MenuState.MAIN:
        btn_play.update(mouse)
        btn_settings.update(mouse)
        btn_play.draw()
        btn_settings.draw()
    elif current_state == MenuState.SETTINGS:
        control_rect = draw_control_panel()
        draw_key_cross()
        skin_rect = draw_skin_panel()
        draw_skin_colors()
        advice_rect = draw_advice_panel()
        volume_rect = draw_volume_slider()
        back_rect = draw_back()

    pygame.display.flip()
    clock.tick(FPS)
pygame.quit()