from pygame import *
from pygame.locals import *
from classes import Player, Platform, BackgroundObject,  \
    TunnelPortal, JumpPad, Campfire, Finish, WorldLabel,  \
    Camera, TextureFactory, ParticleSystem, random_color,  \
    PlayerInfoBox, DevInfoBox, HelpInfoBox, OVERLAY_GAME_OVER,  OVERLAY_WIN
import os
import json
import subprocess
import sys

# ============================ КОНСТАНТИ ГРИ ==================================

WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 900
WORLD_WIDTH = 10000
WORLD_HEIGHT = 5000
FPS = 60

# Камера
CAMERA_TARGET_X = 450
CAMERA_TARGET_Y = 3650

# BG
BG_WIDTH = WINDOW_WIDTH + 400

init()
mixer.init()

#|-------------- ФІЛЬТР ЕКРАНУ ------------------|
# Пікселізація
death_pixel_scale = 1.0  # Початковий стан (Чим більша цифра, тим сильніша дія фільтру)
MAX_PIXEL_MUSH = 30.0    # Максимальна сила руйнування кадру
WIN_PIXEL_SPEED = 0.3    # Швидкість перетворення в кашу
game_buffer = Surface((WINDOW_WIDTH, WINDOW_HEIGHT))

# Розмиття
win_blur_scale = 1.0      # Початковий стан розмиття
MAX_WIN_BLUR = 12.0       # Максимальне замилювання (значення 10-15 цілком достатньо, щоб не боліли очі)
WIN_BLUR_SPEED = 0.15     # Швидкість плавної появи ефекту

# Трясіння
periodic_shake_enabled = True  # Чи ввімкнено ритмічне трясіння
shake_period = 3               # Через кожен кадр робити поштовх
shake_intensity = 5            # Сила поштовху
shake_tick = 0                 # Внутрішній таймер
post_surf = Surface((WINDOW_WIDTH, WINDOW_HEIGHT))

#|-----------------------------------------------|

window = display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), RESIZABLE)
display.set_caption("Gravity Shift - МАРС")
clock = time.Clock()
ui_font = font.SysFont("Consolas", 18, bold=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OBJECTS_FILE = os.path.join(BASE_DIR, "objects.json")

music_dir = os.path.join(BASE_DIR, "Music")
playlist = []
game_volume = 0.1


# ====================== СИСТЕМА ЗБЕРЕЖЕННЯ ==========================
save_file = "save.json"

default_save = {
    "world_id": "objects.json",
    "player": {"x": None, "y": None, "campfires": 0, "gravity": [0, 1]},
    "settings": {"preset": "classic", "control_mode": "both", "window_size": [WINDOW_WIDTH, WINDOW_HEIGHT], "is_fullscreen": False},
    "audio": {"volume": 0.1, "track_name": None, "track_pos": 0},
    "dev": {"dev_mode": False}}

try:
    if os.path.exists(save_file):
        with open(save_file, "r", encoding="utf-8") as f:
            save_data = json.load(f)
    else:
        save_data = default_save.copy()
except Exception as e:
    print(f"Помилка читання save.json: {e}")
    save_data = default_save.copy()

game_volume      = save_data.get("audio",    {}).get("volume", 0.1)
saved_window     = save_data.get("settings", {}).get("window_size", [WINDOW_WIDTH, WINDOW_HEIGHT])
saved_fullscreen = save_data.get("settings", {}).get("is_fullscreen", False)

# ====================== ЗАПУСК ГРИ | ЕКРАН ОЧІКУВАННЯ ========================

if saved_fullscreen:
    window = display.set_mode((0, 0), FULLSCREEN)
else:
    window = display.set_mode(tuple(saved_window), RESIZABLE)


loading_font = font.SysFont("Consolas", 80, bold=True)
sub_font     = font.SysFont("Arial Black", 18, bold=False)

loading_text = loading_font.render("Gravity Shift", True, (0, 220, 255))
sub_text     = sub_font.render("ПРОВАНТАЖЕННЯ МАРСІАНСЬКОГО ПРОСТОРУ", True, (180, 95, 65))

window.fill((0, 0, 10))

text_rect = loading_text.get_rect(center=(WINDOW_WIDTH // 2, (WINDOW_HEIGHT // 2) - 10))
sub_rect  = sub_text.get_rect(center=(WINDOW_WIDTH // 2, text_rect.bottom + 10))

window.blit(loading_text, text_rect)
window.blit(sub_text, sub_rect)

display.flip()

# =========================== ДОПОМІЖНІ ФУНКЦІЇ ===============================

def is_on_screen(rect, camera_x, camera_y, display_w, display_h):
    """Перевіряє чи знаходиться прямокутник на екрані"""
    return (rect.x + camera_x + rect.width > 0 and
            rect.x + camera_x < display_w and
            rect.y + camera_y + rect.height > 0 and
            rect.y + camera_y < display_h)

def load_game_world(filename, player_obj):
    """Завантажує об'єкти гри з JSON файлу"""
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    platforms = sprite.Group()
    portals = sprite.Group()
    campfires = sprite.Group()
    backgrounds = sprite.Group()

    for i, p in enumerate(data.get("platforms", [])):
        p_type = p.get("type", "norm")
        platforms.add(Platform(p["x"], p["y"], p["w"], p["h"], p_type, obj_id=i))

    for i, b in enumerate(data.get("backgrounds", [])):
        b_type = b.get("type", "cave_bg")
        backgrounds.add(BackgroundObject(b["x"], b["y"], b["w"], b["h"], b_type, obj_id=i))    

    for i, p in enumerate(data.get("portals", [])):
        target_g = tuple(p["target_gravity"])
        # Отримуємо початковий колір під поточний скін гравця
        start_color = player_obj.presets[player_obj.current_preset].get(target_g, (255, 255, 255))
        portals.add(TunnelPortal(p["x"], p["y"], p["target_gravity"],
                                w=p.get("w"), h=p.get("h"), color=start_color, obj_id=i))

    for i, j in enumerate(data.get("jump_pads", [])):
        target_g = tuple(j["target_gravity"])
        start_color = player_obj.presets[player_obj.current_preset].get(target_g, (255, 255, 255))
        portals.add(JumpPad(j["x"], j["y"], j["target_gravity"],
                           w=j.get("w"), h=j.get("h"), color=start_color, obj_id=i))

    for i, c in enumerate(data.get("campfires", [])):
        campfires.add(Campfire(c["x"], c["y"], side=c.get("side", "center"), obj_id=i))

    f_data = data.get("finish")
    finish = Finish(f_data["x"], f_data["y"], f_data.get("w", 90), f_data.get("h", 120)) if f_data else None

    labels = sprite.Group()
    for i, l in enumerate(data.get("labels", [])):
        labels.add(WorldLabel(l["text"], l["x"], l["y"], l.get("size", 20),
                             tuple(l.get("color", (255, 255, 255))),
                             l.get("bg_alpha", 0), obj_id=i))

    return platforms, backgrounds, portals, campfires, finish, labels

def auto_index_json(file_path):
    """Автоматично індексує об'єкти в JSON файлі"""
    # Для мапмейкера: автоматично додає індекс об'єкта для орієнтації в об'єктах.

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    categories = ['platforms', 'portals', 'jump_pads', 'campfires', 'labels']

    for category in categories:
        if category in data:
            for index, obj in enumerate(data[category]):
                obj['nomer'] = str(index)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("{\n")

        for key, value in data.items():
            f.write(f'  "{key}": ')
            if isinstance(value, list):
                f.write("[\n")
                for i, item in enumerate(value):
                    line = json.dumps(item, ensure_ascii=False)
                    comma = "," if i < len(value) - 1 else ""
                    f.write(f'    {line}{comma}\n')
                f.write("  ]")
            else:
                f.write(json.dumps(value, ensure_ascii=False))

            if key != list(data.keys())[-1]:
                f.write(",\n")
            else:
                f.write("\n")

        f.write("}")

def sync_portals_color(portal_group, player_obj):
    for portal in portal_group:
        if hasattr(portal, 'update_color'):
            portal.update_color(player_obj.presets, player_obj.current_preset)

# ============================== UI ФУНКЦІЇ ===================================

def draw_ui_boxes(screen, player, dev_mode):
    """Малює всі UI елементи на екрані з оптимізованим кешуванням"""
    win_w, win_h = screen.get_size()

    # Плашка гравця (тепер вона супер-оптимальна)
    player_ui_box.update_and_draw(screen, player, current_track_name)

    # Плашка розробника 
    if dev_mode:
        dev_ui_box.update_and_draw(screen, player, camera, win_h)

    # Плашка інструкцій (для неї теж можна зробити клас, але оскільки вона викликається рідко через Ctrl, можна лишити стару)
    keys = key.get_pressed()
    if keys[K_LCTRL] or keys[K_RCTRL]:
        help_ui_box.draw(screen, win_w, player)

def draw_end_screen(screen, title, subtitle, color):
    """Малює екран завершення гри (Поразка або Перемога)"""
    win_w, win_h = screen.get_size()

    overlay = Surface((win_w, win_h), SRCALPHA)
    overlay.fill(color)
    screen.blit(overlay, (0, 0))

    font_big = font.SysFont("Arial", 60, bold=True)
    font_small = font.SysFont("Arial", 25)

    title_surf = font_big.render(title, True, (255, 255, 255))
    sub_surf = font_small.render(subtitle, True, (250, 250, 250))

    screen.blit(title_surf, (win_w // 2 - title_surf.get_width() // 2, win_h // 2 - 50))
    screen.blit(sub_surf, (win_w // 2 - sub_surf.get_width() // 2, win_h // 2 + 30))

# ========================== ФУНКЦІЇ ПАМЯТІ ===================================

def play_track(idx, start_time_ms=0):
    global current_track_idx, current_track_name
    if not playlist: return
    
    current_track_idx = idx % len(playlist)
    current_track_name = playlist[current_track_idx]
    
    mixer.music.load(os.path.join(music_dir, current_track_name))
    
    # Конвертуємо мілісекунди в секунди для запуску треку з потрібної позиції
    start_sec = start_time_ms / 1000.0
    mixer.music.play(-1, start=start_sec)

def save_full_progress():
    """Зберігає ПОВНИЙ стан гри (для кнопки 'В меню')."""
    win_w, win_h = window.get_size()
    music_pos = max(0, mixer.music.get_pos()) 

    out_data = {
        "world_id": os.path.basename(OBJECTS_FILE),
        "player": {
            "x": player.rect.x,
            "y": player.rect.y,
            "campfires": player.last_campfire_id,
            "gravity": [int(player.gravity_vec.x), int(player.gravity_vec.y)]
        },
        "settings": {
            "preset": player.current_preset,
            "control_mode": player.control_mode,
            "window_size": [win_w, win_h],
            "is_fullscreen": bool(window.get_flags() & FULLSCREEN)
        },
        "audio": {
            "volume": game_volume,
            "track_name": current_track_name,
            "track_pos": music_pos
        }
    }
    with open(save_file, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=4)

def standart_progress():
    """Скидає абсолютно все до заводських налаштувань (викликається при закритті на хрестик)."""
    try:
        with open(save_file, "w", encoding="utf-8") as f:
            json.dump(default_save, f, ensure_ascii=False, indent=4)
        print("Прогрес та налаштування повністю скинуто до заводських.")
    except Exception as e:
        print(f"Помилка при скиданні налаштувань: {e}")

# =========================== ІНІЦІАЛІЗАЦІЯ ГРИ ===============================
# Об'єкти UI
win_w, win_h = window.get_size()
scale = win_h / 600.0

# Розумні плашки
player_ui_box = PlayerInfoBox(scale, font_name="Consolas")
dev_ui_box = DevInfoBox(scale, font_name="Consolas")
help_ui_box = HelpInfoBox(scale, font_name="Consolas")

# Синхронізація ID в JSON
auto_index_json(OBJECTS_FILE)
print("Усі ID (nomer) успішно синхронізовано!")

# База гри
player = Player(0, 0)
player.current_preset = save_data.get("settings", {}).get("preset", "classic")
player.control_mode   = save_data.get("settings", {}).get("control_mode", "both")
player.update_color()

camera = Camera(WINDOW_WIDTH, WINDOW_HEIGHT)

# Провантаження світу
saved_world = save_data.get("world_id", os.path.basename(OBJECTS_FILE))
world_path = os.path.join(BASE_DIR, saved_world)

platforms, backgrounds, portals, campfires, finish_obj, labels = load_game_world(OBJECTS_FILE, player)
all_debug_objects = list(platforms) + list(portals) + list(campfires) + list(labels)
sync_portals_color(portals, player)

# Встановлення першої точки спавну
if campfires:
    first_fire = list(campfires)[0]
    player.respawn_pos = (first_fire.spawn_x, first_fire.spawn_y)

# Партікли
wind_system = ParticleSystem(WINDOW_WIDTH, 2500, count=100)
# platform_dust = ParticleSystem()

# Перезапис координат із збереження
p_data = save_data.get("player", {})
if p_data.get("x") is not None and p_data.get("y") is not None:
    player.rect.x = p_data["x"]
    player.rect.y = p_data["y"]

# Логіка завантаження багаття
if p_data.get("campfires") is not None:
    player.last_campfire_id = p_data["campfires"]
    for fire in campfires:
        if fire.obj_id == player.last_campfire_id:
            player.respawn_pos = (fire.spawn_x, fire.spawn_y)
            break
player.respawn()

if p_data.get("x") is not None and p_data.get("y") is not None:
    player.rect.x = p_data["x"]
    player.rect.y = p_data["y"]
if p_data.get("gravity"):
    player.set_gravity(p_data["gravity"][0], p_data["gravity"][1])

# Логіка завантаження музики
if os.path.exists(music_dir):
    playlist = [f for f in os.listdir(music_dir) if f.endswith(('.mp3', '.ogg', '.wav')) and "Main_menu" not in f]
    playlist.sort()
current_track_idx = 0
current_track_name = "No Music"

# ПАУЗА
game_paused = False
pause_blur_scale = 1.0
MAX_PAUSE_BLUR = 10.0
PAUSE_BLUR_SPEED = 0.35

# Логіка стартового запуску
saved_track = save_data.get("audio", {}).get("track_name")
saved_pos = save_data.get("audio", {}).get("track_pos", 0)

if playlist:
    if saved_track in playlist:
        current_track_idx = playlist.index(saved_track)
    else:
        current_track_idx = playlist.index("noncopyright.mp3") if "noncopyright.mp3" in playlist else 0
        saved_pos = 0 # Якщо трек не знайдено, починаємо з нуля
        
    play_track(current_track_idx, start_time_ms=saved_pos)
    mixer.music.set_volume(game_volume)

# ========================= ОБРОБКА ПОДІЙ =====================================

def handle_keydown_events(e, player, camera, portals, finish_obj):
    """Обробляє натискання клавіш"""
    global game_won, dev_mode, current_track_idx, draw_ui, game_paused

    if not game_won:
        if dev_mode:
            handle_dev_key_events(e, player, camera, portals)

        # Респавн
        if e.key == K_r:  
            player.respawn()

        # Механіка Streetfly
        if e.key in (K_LSHIFT, K_RSHIFT, K_f, K_l):
            player.apply_streetfly()

        # Зміна режиму керування
        if e.key == K_m:
            player.switch_control_mode()

        # Зміна скінів (Якщо бажаєте додати більше пресетів, просто розширте список у класі Player > presets (±67стр))
        if e.key == K_TAB:
            new_color = random_color()
            player.color = new_color
            player.image.fill(new_color)
            player.switch_skin()
            sync_portals_color(portals, player)

        if e.key == K_ESCAPE:
            game_paused = not game_paused
        
    if e.key == K_EQUALS:
        play_track(current_track_idx + 1)
    elif e.key == K_MINUS:
        play_track(current_track_idx - 1)

    # Перевірка перемоги
    if e.key == K_g and not game_won:
        if finish_obj.check_interaction(player.rect):
            game_won = True

    # Режим розробника
    if e.key == K_LALT or e.key ==  K_RALT:
        dev_mode = not dev_mode
        print(f"Режим розробника: {dev_mode}")

    # Повноекранний режим (Або просто перетягуйте межі екрану, якщо хочете власно налаштувати розмір)
    if e.key == K_F11:
        global window
        if window.get_flags() & FULLSCREEN:
            window = display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), RESIZABLE)
        else:
            window = display.set_mode((0, 0), FULLSCREEN)

    if e.key == K_F9:
        draw_ui = not draw_ui

def handle_dev_key_events(e, player, camera, portals):
    """Обробляє події клавіш для режимі розробника"""
    if e.key == K_1:
        player.gravity_vec = Vector2(0, 1)   # Вниз
    elif e.key == K_2:
        player.gravity_vec = Vector2(0, -1)  # Вгору
    elif e.key == K_3:
        player.gravity_vec = Vector2(-1, 0)  # Вліво
    elif e.key == K_4:
        player.gravity_vec = Vector2(1, 0)   # Вправо

    # Режим камери (Фіксація за гравцем або координатами)
    if e.key == K_p:
        global camera_target
        camera_target = not camera_target
        if camera_target:
            camera.focus_point = (CAMERA_TARGET_X, CAMERA_TARGET_Y)
        else:
            camera.focus_point = None
    
    if e.key == K_v: # Зміна напрямку вітру
        wind_system.switch_direction()


    player.update_color()
    sync_portals_color(portals, player)

def handle_dev_mouse_events(e, camera, all_debug_objects):
    """Обробляє події миші для режима розробника"""
    global draw_start_pos, is_drawing_rect, current_rect_data, click_circle_pos, click_circle_timer

    if e.type == MOUSEBUTTONDOWN and e.button == 1:  # ЛКМ - початок креслення
        camera_offset = camera.camera.topleft
        m_x, m_y = e.pos
        draw_start_pos = (m_x - camera_offset[0], m_y - camera_offset[1])
        is_drawing_rect = True
        print(f"Координати натиску миші: {json.dumps(current_rect_data) + ","}")

    elif e.type == MOUSEBUTTONUP and e.button == 1:  # ЛКМ - кінець креслення
        is_drawing_rect = False
        print(f"Креслення: {json.dumps(current_rect_data) + ","}")

    elif e.type == MOUSEBUTTONDOWN and e.button == 3:  # ПКМ - видобування даних
        camera_offset = camera.camera.topleft
        world_x = e.pos[0] - camera_offset[0]
        world_y = e.pos[1] - camera_offset[1]

        for obj in all_debug_objects:
            if obj.rect.collidepoint(world_x, world_y):
                out_data = {
                    "x": int(obj.rect.x),
                    "y": int(obj.rect.y),
                    "w": int(obj.rect.width),
                    "h": int(obj.rect.height)
                }

                for attr_name, value in vars(obj).items():
                    if attr_name in ["rect", "image", "width", "height"]:
                        continue

                    if type(value).__module__.startswith('pygame'):
                        if isinstance(value, Vector2):
                            out_data[attr_name] = [int(value.x), int(value.y)]
                        continue

                    if isinstance(value, (str, int, float, list, bool, dict)):
                        out_data[attr_name] = value

                print(json.dumps(out_data, ensure_ascii=False) + ",")

                click_circle_pos = e.pos
                click_circle_timer = 15
                break

def handle_pause_click(mouse_pos):
    global game_paused, running, return_to_menu

    if pause_buttons[0].collidepoint(mouse_pos):
        # ДОГРАТИ
        game_paused = False

    elif pause_buttons[1].collidepoint(mouse_pos):
        # НАЛАШТУНКИ (поки пусто)
        pass

    elif pause_buttons[2].collidepoint(mouse_pos):
        # Я ЩЕ ПОВЕРНУСЯ (вихід до головного меню)
        save_full_progress()
        return_to_menu = True
        running = False

# ========================= ІГРОВА ЛОГІКА =====================================

def update_game_logic(player, campfires, platforms, portals, camera, finish_obj):
    """Оновлює логіку гри"""
    global game_won, game_over

    # Взаємодія з багаттям
    for fire in campfires:
        if fire.rect.colliderect(player.rect):
            player.respawn_pos = (fire.spawn_x, fire.spawn_y)
            player.last_campfire_id = fire.obj_id

    # Перевірка меж світу (+ запобіжник вильоту за межі)
    if (player.rect.right > WORLD_WIDTH + 5 or player.rect.left < -5 or
        player.rect.bottom > WORLD_HEIGHT + 5 or player.rect.top < -5):
        player.respawn()

    # Оновлення гри, якщо не виграно і не програно
    if not game_won and not game_over:
        player.handle_input()
        player.apply_physics(platforms, portals, WORLD_WIDTH, WORLD_HEIGHT)
        if player.is_dead: game_over = True
        player.update_visuals()
        finish_obj.check_interaction(player.rect)

        if player.rect.y < 1000:
            if player.gravity_vec != (0, 1):
                player.set_gravity(0, 1)
                player.streetfly_flash = True
                print("Система безпеки марсіанського простору: Всі об'єкти спостереження залишаються на орбіті!")

        # Оновлення камери
        win_w, win_h = window.get_size()
        view_rect = Rect(-camera.camera.x, -camera.camera.y, win_w, win_h)

        if camera.focus_point:
            camera.update(None)
        else:
            camera.update(player)

# ============================ МАЛЮВАННЯ ======================================

def render_game(window, player, labels, finish_obj, camera, 
                dev_mode, all_debug_objects, backgrounds, draw_ui):
    """Малює всі елементи гри"""
    global click_circle_timer, click_circle_pos, is_drawing_rect, draw_start_pos

    # Раніше фон був монотонним. Добре що це було змінено)
    # window.fill((150, 90, 5))
    # window.blit(background_surface, (0, 0))
    scroll_range_world = WORLD_HEIGHT - WINDOW_HEIGHT
    scroll_range_bg = bg_surface.get_height() - WINDOW_HEIGHT

    if scroll_range_world != 0:
        rel_y = camera.camera.y / scroll_range_world
        parallax_y = rel_y * scroll_range_bg
    else:
        parallax_y = 0

    bg_w = bg_surface.get_width()
    parallax_x = (camera.camera.x * 0.1) % bg_w

    window.blit(bg_surface, (parallax_x - bg_w, parallax_y))
    window.blit(bg_surface, (parallax_x, parallax_y))

    camera_offset = camera.camera.topleft

    #------------------------------------------------------------------------------ Так тут
    #------------------------------------------------------------------------------

    # Межі світу
    world_border = Rect(0, 0, WORLD_WIDTH, WORLD_HEIGHT).move(camera_offset)
    draw.rect(window, (255, 255, 255), world_border, 1)

    # Область видимості для оптимізації
    win_w, win_h = window.get_size()
    view_rect = Rect(-camera.camera.x, -camera.camera.y, win_w, win_h)

    # Об'єкт фону для виключень. Для мість де звичний не підійде
    for bg in backgrounds:
        if bg.rect.colliderect(view_rect):
            bg.update()
            bg.draw(window, camera_offset)
            
    # Ігрові об'єкти
    for obj in all_debug_objects:
        if obj.rect.colliderect(view_rect):
            obj.is_hovered = obj.rect.inflate(4, 4).colliderect(player.rect)
            obj.draw(window, camera_offset, dev_mode=False)

    # Мітки
    for lbl in labels:
        lbl.draw(window, camera_offset)

    # Фініш
    finish_obj.draw(window, camera_offset)

    # Гравець
    player.draw(window, camera_offset)

    # ------------------------------------------------------------------------------ Тут на свій розсуд: вималовувати поверх всього світу
    # Партікли вітру (зліва направо)
    if player.rect.y <= 2500:
        wind_system.run(
            window,
            density=0.9,                 # Щільність часток
        side=wind_system.current_direction, # Сторона появи (top, bottom, left, right)
            color=(200, 160, 130),        # Колір часток
            speed_range=(13.0, 23.0),    # Швидкість руху
            size_range=(4, 6),           # Розмір
            fade_range=(1, 3)            # Згасання (З часом вони пропадають)
        )

    # Недоробка треба інша логіка промальовки частинок через фіксованість до вікна. + Частинки падають іншого краю обєкта в та через обєкт
    # all_platforms = platforms.sprites() 

    # if all_platforms:
    #     p0 = all_platforms[0]
    #     p0_visual_rect = camera.apply(p0)

    #     screen_rect = window.get_rect()
    #     visible_area = p0_visual_rect.clip(screen_rect)

    #     if visible_area.width > 0 and visible_area.height > 0:
    #         platform_dust.run(
    #             window, 
    #             area_rect=visible_area, 
    #             side="top",
    #             color=(255,255,255),
    #             density=0.08,
    #             speed_range=(1.0, 4.0),
    #             size_range=(2, 4),
    #             fade_range=(2, 6)
    #         )

    #------------------------------------------------------------------------------  або знайти такіж риски вище і малювати трохи вище фону

    # Дебаг елементи
    if dev_mode:
        draw.rect(window, (255, 255, 255), camera.dead_zone, 1)
        for obj in all_debug_objects:
            obj.draw_debug(window, True, camera_offset)

    # Креслення прямокутника в dev режимі
    if dev_mode and is_drawing_rect and draw_start_pos:
        draw_dev_rectangle(window, camera_offset)

    # Клік-вибірка об'єкта в dev режимі
    if click_circle_timer > 0 and click_circle_pos:
        draw.circle(window, (0, 150, 255), click_circle_pos, 20, 3)
        draw.circle(window, (0, 200, 255), click_circle_pos, 5)
        click_circle_timer -= 1

    if draw_ui:
            # UI елементи
            draw_ui_boxes(window, player, dev_mode)
            
    #         # Екрани завершення
    #         if game_over:
    #             draw_end_screen(window, "ТЕБЕ ОПРОМІНЕНО", "щоб відновити себе тисни R", OVERLAY_GAME_OVER)
    #         elif game_won:
    #             draw_end_screen(window, "ПЕРЕМОГА!", "Дубрався до свого друга!", OVERLAY_WIN)

def draw_dev_rectangle(window, camera_offset):
    """Код для креслення в dev режимі"""
    global current_rect_data

    m_pos = mouse.get_pos()
    curr_world_x = m_pos[0] - camera_offset[0]
    curr_world_y = m_pos[1] - camera_offset[1]

    rect_x = min(draw_start_pos[0], curr_world_x)
    rect_y = min(draw_start_pos[1], curr_world_y)
    rect_w = abs(curr_world_x - draw_start_pos[0])
    rect_h = abs(curr_world_y - draw_start_pos[1])

    current_rect_data = {"x": int(rect_x), "y": int(rect_y), "w": int(rect_w), "h": int(rect_h)}

    screen_x = rect_x + camera_offset[0]
    screen_y = rect_y + camera_offset[1]

    if rect_w > 0 and rect_h > 0:
        s = Surface((rect_w, rect_h), SRCALPHA)
        s.fill((0, 100, 255, 80))
        window.blit(s, (screen_x, screen_y))

        draw.rect(window, (0, 200, 255), (screen_x, screen_y, rect_w, rect_h), 2)

        debug_info = f"x:{int(rect_x)} y:{int(rect_y)} w:{int(rect_w)} h:{int(rect_h)}"

        info_surf = ui_font.render(debug_info, True, (255, 255, 255))

        bg_rect = info_surf.get_rect(topleft=(screen_x, screen_y - 25))
        draw.rect(window, (0, 0, 0), bg_rect.inflate(4, 2))

        window.blit(info_surf, (screen_x, screen_y - 25))

def apply_pixelate_blur(src_surface, dest_surface, current_scale):
    """Приймає вихідний буфер (src_surface), стискає його в 'кашу'
        і розтягує на весь розмір головного вікна (dest_surface)."""
    actual_w, actual_h = dest_surface.get_size()
    
    if current_scale <= 1.0:
        # Якщо ефект вимкнено або повернуто до норми — просто копіюємо 1:1
        transform.scale(src_surface, (actual_w, actual_h), dest_surface)
        return

    # Обчислюємо знижену роздільну здатність для ефекту
    low_res_w = max(1, int(src_surface.get_width() // current_scale))
    low_res_h = max(1, int(src_surface.get_height() // current_scale))
    
    # Стискаємо зображення (створюється ефект втрати пікселів)
    small_surf = transform.scale(src_surface, (low_res_w, low_res_h))
    
    # Розтягуємо назад на повний екран головного вікна
    transform.scale(small_surf, (actual_w, actual_h), dest_surface)

def apply_smooth_blur(src_surface, dest_surface, current_scale):
    """Приймає вихідний буфер (src_surface), плавно замилює його через smoothscale
        і розтягує на весь розмір головного вікна (dest_surface)."""
    actual_w, actual_h = dest_surface.get_size()
    
    if current_scale <= 1.0:
        # Якщо ефект не активний — просто копіюємо картинку без змін
        transform.scale(src_surface, (actual_w, actual_h), dest_surface)
        return

    # Обчислюємо тимчасову низьку роздільну здатність для розмиття
    low_res_w = max(1, int(src_surface.get_width() // current_scale))
    low_res_h = max(1, int(src_surface.get_height() // current_scale))
    
    # Стискаємо картинку з м'яким згладжуванням сусідніх пікселів
    small_surf = transform.smoothscale(src_surface, (low_res_w, low_res_h))
    
    # Розтягуємо назад на повний екран головного вікна
    transform.smoothscale(small_surf, (actual_w, actual_h), dest_surface)

def draw_screen():
    """Менеджер конвеєру рендерингу (Поразка, Перемога, Гра)"""
    global death_pixel_scale, win_blur_scale

    if game_over:
        if death_pixel_scale < MAX_PIXEL_MUSH:
            death_pixel_scale += WIN_PIXEL_SPEED

        # Малює світ у буфер
        render_game(game_buffer, player, labels, finish_obj, camera, 
                    dev_mode, all_debug_objects, backgrounds, draw_ui=False)
        player.draw_face(game_buffer, camera)

        # Фільтр поразки
        apply_pixelate_blur(game_buffer, window, death_pixel_scale)

        # Чіткий UI поверх
        draw_ui_boxes(window, player, dev_mode)
        draw_end_screen(window, "ТЕБЕ ОПРОМІНЕНО", "Щоб відновити себе тисни R", OVERLAY_GAME_OVER)

    elif game_won:
        if win_blur_scale < MAX_WIN_BLUR:
            win_blur_scale += WIN_BLUR_SPEED

        # Малює світ у буфер
        render_game(game_buffer, player, labels, finish_obj, camera, 
                    dev_mode, all_debug_objects, backgrounds, draw_ui=False)
        player.draw_face(game_buffer, camera)

        # Фільтр перемоги
        apply_smooth_blur(game_buffer, window, win_blur_scale)

        # Чіткий UI поверх
        draw_ui_boxes(window, player, dev_mode)
        draw_end_screen(window, "ПЕРЕМОГА!", "Дібрався до свого друга!", OVERLAY_WIN)

    else:
        # Звичайний ігровий процес
        death_pixel_scale = 1.0
        win_blur_scale = 1.0
        render_game(window, player, labels, finish_obj, camera, 
                    dev_mode, all_debug_objects, backgrounds, draw_ui=draw_ui)
        player.draw_face(window, camera)

def draw_pause_menu(screen):
    """Меню паузи"""
    global pause_buttons
    win_w, win_h = screen.get_size()

    # Затемнення
    overlay = Surface((win_w, win_h), SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    screen.blit(overlay, (0, 0))

    title_font = font.SysFont("Consolas", 56, bold=True)
    button_font = font.SysFont("Consolas", 28, bold=True)

    title = title_font.render("ЗУПИНКА ЧАСУ", True, (255, 255, 255))
    screen.blit(title, (win_w // 2 - title.get_width() // 2, win_h // 2 - 180))

    buttons = [
        "ДОГРАТИ",
        "НАЛАШТУНКИ (СКОРО)",
        "Я ЩЕ ПОВЕРНУСЯ"]

    pause_buttons = []
    mouse_pos  = mouse.get_pos()

    for i, text in enumerate(buttons):
        rect = Rect(win_w // 2 - 180, win_h // 2 - 60 + i * 90, 360, 60)
        hover = rect.collidepoint(mouse_pos )
        bg = (80, 30, 20) if hover else (40, 10, 10)
        draw.rect(screen, bg, rect, border_radius=10)
        draw.rect(screen, (180, 85, 75), rect, 2, border_radius=10)

        txt = button_font.render(text, True, (255,255,255))
        screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))
        pause_buttons.append(rect)

# ============================= СТАН ГРИ ======================================
dev_mode  = False
draw_ui   = True
game_won  = False
game_over = False
game_paused = False
return_to_menu = False

# Змінні для креслення в dev режимі
draw_start_pos     = None
is_drawing_rect    = False
current_rect_data  = {"x": 0, "y": 0, "w": 0, "h": 0}
click_circle_pos   = None
click_circle_timer = 0
camera_target      = False



# ======================= ОСНОВНИЙ ІГРОВИЙ ЦИКЛ ===============================
bg_surface = TextureFactory.get_texture("dynamic_bg", BG_WIDTH, WORLD_HEIGHT)

running = True
while running:
    for e in event.get():
        if e.type == QUIT:
            standart_progress()
            running = False
        
        elif e.type == MOUSEBUTTONDOWN and game_paused:
            if e.button == 1:
                handle_pause_click(e.pos)

        elif e.type == KEYDOWN:
            handle_keydown_events(e, player, camera, portals, finish_obj)

        elif dev_mode:
            handle_dev_mouse_events(e, camera, all_debug_objects)

    if game_over:
        keys = key.get_pressed()
        if keys[K_r]:
            player.respawn()
            game_over = False

    if not game_paused:
        update_game_logic(player, campfires, platforms, portals, camera, finish_obj)
    
    draw_screen()

    if game_paused:
        pause_blur_scale = min(MAX_PAUSE_BLUR, pause_blur_scale + PAUSE_BLUR_SPEED)
        w, h = window.get_size()
        small = transform.smoothscale(window, (max(1, int(w / pause_blur_scale)), max(1, int(h / pause_blur_scale))))
        blurred = transform.smoothscale(small, (w, h))

        window.blit(blurred, (0, 0))
        draw_pause_menu(window)
    else:
        pause_blur_scale = 1.0



    # ------------------------ Трясіння ----------------------------
    # shake_x = 0
    # shake_y = 0

    # if periodic_shake_enabled:
    #     shake_tick += 1
    #     if shake_tick % shake_period == 0:
    #         shake_x = random.randint(-shake_intensity, shake_intensity)
    #         shake_y = random.randint(-shake_intensity, shake_intensity)

    # actual_win_w, actual_win_h = window.get_size()
    # if post_surf.get_size() != (actual_win_w, actual_win_h):
    #     post_surf = Surface((actual_win_w, actual_win_h))

    # if filter_enabled and pixel_scale > 1.0:
    #     low_res_w = max(1, int(WINDOW_WIDTH / pixel_scale))
    #     low_res_h = max(1, int(WINDOW_HEIGHT / pixel_scale))
        
    #     small_surf = transform.smoothscale(game_buffer, (low_res_w, low_res_h))
    #     transform.smoothscale(small_surf, (actual_win_w, actual_win_h), post_surf)
    # else:
    #     transform.scale(game_buffer, (actual_win_w, actual_win_h), post_surf)

    # window.fill((0, 0, 0))
    # window.blit(post_surf, (shake_x, shake_y))


    display.update()
    clock.tick(FPS)
if return_to_menu:
    subprocess.Popen([sys.executable, "START_HERE.py"])
quit()



