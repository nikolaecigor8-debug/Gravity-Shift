import pygame
import os
import sys
import json
import subprocess
import time

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# _CORE_DIR = os.path.join(_ROOT_DIR, "core_v1")
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

# Імпорти з core_v#. Оновлювати назву з назвою оновленого ядра правил.
from core_v1.classes import                  \
    Player, Platform, BackgroundObject,      \
    TunnelPortal, JumpPad, Campfire, Finish, \
    WorldLabel, TextPanel, PanelRenderer,    \
    Camera, TextureFactory, ParticleSystem,  \
    PlayerInfoBox, DevInfoBox, HelpInfoBox,  \
    random_color,                            \
    OVERLAY_GAME_OVER,  OVERLAY_WIN,         \
    INF, WRN, ERR, DEV, SUC
   
from core_v1.lighting import LightingEngine
from colorama import Back, init

# Перевірка коли гра всеж почнеться
start_time = time.perf_counter()

pygame.init()
pygame.mixer.init()
init(autoreset=True)

# ============================ КОНСТАНТИ ГРИ ==================================

info = pygame.display.Info()
safe_w = int(info.current_w * 0.9)
safe_h = int(info.current_h * 0.9)

WINDOW_WIDTH = min(1600, safe_w)
WINDOW_HEIGHT = min(900, safe_h)

# WINDOW_WIDTH = 1600 # Розмір для 1080 екранів 1400, 750
# WINDOW_HEIGHT = 900 # Оригінальний 1600, 900

WORLD_WIDTH = 10000
WORLD_HEIGHT = 5000
FPS = 60

# Камера
CAMERA_TARGET_X = 450
CAMERA_TARGET_Y = 365

# BG
BG_WIDTH = WINDOW_WIDTH + 400

pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)

#|-------------- ФІЛЬТР ЕКРАНУ ------------------|
# Всі важкі розрахунки пост-процесингу тепер на GPU (lighting.py)
death_pixel_scale = 1.0  
MAX_PIXEL_MUSH = 30.0    
WIN_PIXEL_SPEED = 0.3    

win_blur_scale = 1.0      
MAX_WIN_BLUR = 12.0       
WIN_BLUR_SPEED = 0.15     
#|-----------------------------------------------|

window = pygame.display.set_mode(
             (WINDOW_WIDTH, WINDOW_HEIGHT),
    pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
pygame.time.wait(100)

game_buffer = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
ui_buffer = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
lighting = LightingEngine(WINDOW_WIDTH, WINDOW_HEIGHT)


pygame.display.set_caption("Gravity Shift - МАРС")
clock = pygame.time.Clock()
ui_font = pygame.font.SysFont("Consolas", 18, bold=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OBJECTS_FILE = os.path.join(BASE_DIR, "objects.json")

music_dir = os.path.join(BASE_DIR, "Resources", "Music")
playlist = []
game_volume = 0.1


# Шрифти
title_font = pygame.font.SysFont("Consolas", 56, bold=True)
button_font = pygame.font.SysFont("Consolas", 28, bold=True)

# ====================== СИСТЕМА ЗБЕРЕЖЕННЯ ==========================
save_file = os.path.join(_ROOT_DIR, "core_v1", "save.json")

default_save = {
    "world_id": "objects.json",
    "player": {"x": None, "y": None, "campfires": 0, "gravity": [0, 1]},
    "settings": {"preset": "classic", "control_mode": "both", "is_fullscreen": False, "lighting_enabled": True, "white_light_active": True},
    "audio": {"volume": 0.1, "track_name": None, "track_pos": 0}}

try:
    if os.path.exists(save_file):
        with open(save_file, "r", encoding="utf-8") as f:
            save_data = json.load(f)
    else:
        save_data = default_save.copy()
except Exception as e:
    print(f"{ERR} Помилка читання save.json: {e}")
    save_data = default_save.copy()

game_volume = save_data.get("audio", {}).get("volume", 0.1)
saved_fullscreen = save_data.get("settings", {}).get("is_fullscreen", False)

# ====================== ЗАПУСК ГРИ | ЕКРАН ОЧІКУВАННЯ ========================

if saved_fullscreen:
    window = pygame.display.set_mode((0, 0), 
        pygame.FULLSCREEN | pygame.OPENGL | pygame.DOUBLEBUF)
else:
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), 
        pygame.RESIZABLE  | pygame.OPENGL | pygame.DOUBLEBUF)

loading_font = pygame.font.SysFont("Consolas", 80, bold=True)
sub_font     = pygame.font.SysFont("Arial Black", 18, bold=False)

loading_text = loading_font.render("Gravity Shift", True, (0, 220, 255))
sub_text     = sub_font.render("ПРОВАНТАЖЕННЯ МАРСІАНСЬКОГО ПРОСТОРУ", True, (180, 95, 65))

game_buffer.fill((0, 0, 10))
ui_buffer.fill((0, 0, 0, 0))

text_rect = loading_text.get_rect(center=(WINDOW_WIDTH // 2, (WINDOW_HEIGHT // 2) - 10))
sub_rect  = sub_text.get_rect(center=(WINDOW_WIDTH // 2, text_rect.bottom + 10))

ui_buffer.blit(loading_text, text_rect)
ui_buffer.blit(sub_text, sub_rect)

dummy_rect = pygame.Rect(WINDOW_WIDTH//2, WINDOW_HEIGHT//2, 10, 10)
class DummyCam: x, y = 0, 0
lighting.render(game_buffer, ui_buffer, dummy_rect, [], DummyCam(), (255, 255, 255))
pygame.display.flip()

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

    platforms = pygame.sprite.Group()
    portals = pygame.sprite.Group()
    campfires = pygame.sprite.Group()
    backgrounds = pygame.sprite.Group()

    for i, p in enumerate(data.get("platforms", [])):
        p_type = p.get("type", "norm")
        plat = Platform(p["x"], p["y"], p["w"], p["h"], p_type, obj_id=i)
        plat.indoor = p.get("indoor", False)
        platforms.add(plat)

    for i, b in enumerate(data.get("backgrounds", [])):
        b_type = b.get("type", "cave_bg")
        backgrounds.add(BackgroundObject(b["x"], b["y"], b["w"], b["h"], b_type, obj_id=i))    

    for i, p in enumerate(data.get("portals", [])):
        target_g = tuple(p["target_gravity"])
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

    labels = pygame.sprite.Group()
    for i, l in enumerate(data.get("labels", [])):
        labels.add(WorldLabel(l["text"], l["x"], l["y"], l.get("size", 20),
                             tuple(l.get("color", (255, 255, 255))),
                             l.get("bg_alpha", 0), obj_id=i))

    # --- TextPanel (таблички, монологи) ---
    panels = pygame.sprite.Group()
    for i, pn in enumerate(data.get("panels", [])):
        panels.add(TextPanel(
            pn["x"], pn["y"],
            pn.get("w", 60), pn.get("h", 80),
            panel_type = pn.get("type", "sign"),
            title      = pn.get("title", ""),
            text       = pn.get("text", ""),
            obj_id     = i
        ))

    return platforms, backgrounds, portals, campfires, finish, labels, panels

def auto_index_json(file_path):
    """Автоматично індексує об'єкти в JSON файлі"""
    # Для мапмейкера: автоматично додає індекс об'єкта для орієнтації розробника.
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
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
        help_ui_box.draw(screen, win_w, player)

    # Малюємо відкриту панель зверху всього
    try:
        panel_renderer.draw(screen)
    except NameError:
        pass

def draw_end_screen(screen, title, subtitle, color):
    """Малює екран завершення гри (Поразка або Перемога)"""
    win_w, win_h = screen.get_size()
    overlay = pygame.Surface((win_w, win_h), pygame.SRCALPHA)
    overlay.fill(color)
    screen.blit(overlay, (0, 0))

    font_big = pygame.font.SysFont("Arial", 60, bold=True)
    font_small = pygame.font.SysFont("Arial", 25)

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
    pygame.mixer.music.load(os.path.join(music_dir, current_track_name))
    
    # Конвертує мілісекунди в секунди для запуску треку з потрібної позиції
    start_sec = start_time_ms / 1000.0
    pygame.mixer.music.play(-1, start=start_sec)

def save_full_progress():
    """Зберігає ПОВНИЙ стан гри (для кнопки 'В меню')."""
    win_w, win_h = window.get_size()
    music_pos = max(0, pygame.mixer.music.get_pos()) 

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
            "is_fullscreen": bool(window.get_flags() & pygame.FULLSCREEN),
            "lighting_enabled": lighting_enabled,
            "white_light_active": white_light_active
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
        print(f"{WRN} Прогрес та налаштування повністю скинуто до звичайних.")
    except Exception as e:
        print(f"{ERR} Помилка при скиданні налаштувань: {e}")

# =========================== ІНІЦІАЛІЗАЦІЯ ГРИ ===============================
# Об'єкти UI
win_w, win_h = window.get_size()
scale = win_h / 600.0

# Розумні плашки
player_ui_box = PlayerInfoBox(scale, font_name="Consolas")
dev_ui_box = DevInfoBox(scale, font_name="Consolas")
help_ui_box = HelpInfoBox(scale, font_name="Consolas")

# Рендерер панелей (відповідає за відкриття/закриття UI панелей)
panel_renderer = PanelRenderer()

# Синхронізація ID в JSON
auto_index_json(OBJECTS_FILE)
print(f"{SUC} Усі ID (nomer) успішно синхронізовано!")

# База гри
player = Player(0, 0)
player.current_preset = save_data.get("settings", {}).get("preset", "classic")
player.control_mode   = save_data.get("settings", {}).get("control_mode", "both")
player.update_color()

camera = Camera(WINDOW_WIDTH, WINDOW_HEIGHT)

# Провантаження світу
saved_world = save_data.get("world_id", os.path.basename(OBJECTS_FILE))
world_path = os.path.join(BASE_DIR, saved_world)

platforms, backgrounds, portals, campfires, finish_obj, labels, panels = load_game_world(OBJECTS_FILE, player)
all_debug_objects = list(platforms) + list(portals) + list(campfires) + list(panels) # + list(labels)
sync_portals_color(portals, player)

# Встановлення першої точки спавну
if campfires:
    first_fire = list(campfires)[0]
    player.respawn_pos = (first_fire.spawn_x, first_fire.spawn_y)

# Партікли
wind_system = ParticleSystem(WINDOW_WIDTH, 2500, count=100)
# platform_dust = ParticleSystem()

# Перезапис координат із збереження, якщо вони є
p_data = save_data.get("player", {})
has_saved_pos = False
if p_data.get("x") is not None and p_data.get("y") is not None:
    player.rect.x = p_data["x"]
    player.rect.y = p_data["y"]
    has_saved_pos = True

# Логіка завантаження багаття
if p_data.get("campfires") is not None:
    player.last_campfire_id = p_data["campfires"]
    for fire in campfires:
        if fire.obj_id == player.last_campfire_id:
            player.respawn_pos = (fire.spawn_x, fire.spawn_y)
            break
if not has_saved_pos:
    player.respawn()

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
    pygame.mixer.music.set_volume(game_volume)

# ========================= ОБРОБКА ПОДІЙ =====================================

def handle_keydown_events(e, player, camera, portals, finish_obj):
    """Обробляє натискання клавіш"""
    global game_won, dev_mode, current_track_idx, draw_ui, game_paused, lighting_enabled, window, game_buffer, ui_buffer, lighting, panel_renderer, panels

    if not game_won:
        if dev_mode:
            handle_dev_key_events(e, player, camera, portals, lighting)

        # Респавн
        if e.key == pygame.K_r:
            player.respawn()

        # Механіка Streetfly
        if e.key in (pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_f, pygame.K_l):
            player.apply_streetfly()

        # Зміна режиму керування
        if e.key == pygame.K_m:
            player.switch_control_mode()

        # Зміна скінів
        if e.key == pygame.K_TAB:
            new_color = random_color()
            player.color = new_color
            player.image.fill(new_color)
            player.switch_skin()
            sync_portals_color(portals, player)

        # Взаємодія з панелями
        if e.key == pygame.K_e:
            if panel_renderer.is_open():
                panel_renderer.close()
            else:
                for pn in panels:
                    if getattr(pn, 'player_nearby', False):
                        panel_renderer.open(pn)
                        break

        if e.key == pygame.K_ESCAPE:
            if panel_renderer.is_open():
                panel_renderer.close()
            else:
                game_paused = not game_paused

    if e.key == pygame.K_EQUALS:
        play_track(current_track_idx + 1)
    elif e.key == pygame.K_MINUS:
        play_track(current_track_idx - 1)

    # Перевірка перемоги
    if e.key == pygame.K_g and not game_won:
        if finish_obj.check_interaction(player.rect):
            game_won = True

    # Режим розробника
    if e.key == pygame.K_LALT or e.key ==  pygame.K_RALT:
        dev_mode = not dev_mode
        dev_mode_ON_OFF = Back.GREEN + "Увімнуто" if dev_mode else Back.RED + "Вимкнено"
        print(f"{DEV} Режим розробника: {dev_mode_ON_OFF}")

    # Повноекранний режим
    if e.key == pygame.K_F11:
        if window.get_flags() & pygame.FULLSCREEN:
            window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE | pygame.OPENGL | pygame.DOUBLEBUF)
            new_w, new_h = WINDOW_WIDTH, WINDOW_HEIGHT
        else:
            window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.OPENGL | pygame.DOUBLEBUF)
            new_w, new_h = window.get_size()

        game_buffer = pygame.Surface((new_w, new_h))
        ui_buffer = pygame.Surface((new_w, new_h), pygame.SRCALPHA)
        lighting = LightingEngine(new_w, new_h)

        camera.resize(new_w, new_h)
        camera.recenter(player)

    if e.key == pygame.K_F9:
        draw_ui = not draw_ui

def handle_dev_key_events(e, player, camera, portals, lighting): # lighting
    """Обробляє події клавіш для режимі розробника"""
    if   e.key == pygame.K_1: player.gravity_vec = pygame.Vector2(0, 1)   # Вниз
    elif e.key == pygame.K_2: player.gravity_vec = pygame.Vector2(0, -1)  # Вгору
    elif e.key == pygame.K_3: player.gravity_vec = pygame.Vector2(-1, 0)  # Вліво
    elif e.key == pygame.K_4: player.gravity_vec = pygame.Vector2(1, 0)   # Вправо

    # Режим камери (Фіксація за гравцем або координатами)
    if e.key == pygame.K_p:
        global camera_target
        camera_target = not camera_target
        if camera_target: camera.focus_point = (CAMERA_TARGET_X, CAMERA_TARGET_Y)
        else: camera.focus_point = None
        print(f"{DEV} Фокус камери: {Back.WHITE + 'Координати' if camera_target else Back.BLUE + 'Гравець'}")

    
    # Зміна напрямку вітру
    if e.key == pygame.K_v: 
        wind_system.switch_direction()

    # Перемикач світла
    if e.key == pygame.K_o:
        global lighting_enabled
        lighting_enabled = not lighting_enabled
        light_ON_OFF = Back.GREEN + "Увімнуто" if lighting_enabled else Back.RED + "Вимкнено"
        print(f"{DEV} Система освітлення: {light_ON_OFF}")

    # Колір світла на білий або гравця
    if e.key == pygame.K_c: 
        global white_light_active
        white_light_active = not white_light_active
        print(f"{DEV} Тип освітлення: {Back.WHITE + 'Чисте' if white_light_active else Back.BLUE + 'Гравець'}")

    if e.key == pygame.K_LEFTBRACKET:
        new_scale = max(1, lighting.downscale - 1)
        lighting.set_downscale(new_scale)
        print(f"{DEV} lighting.downscale -> {lighting.downscale}")
    elif e.key == pygame.K_RIGHTBRACKET:
        lighting.set_downscale(lighting.downscale + 1)
        print(f"{DEV} lighting.downscale -> {lighting.downscale}")

    player.update_color()
    sync_portals_color(portals, player)

def handle_dev_mouse_events(e, camera, all_debug_objects):
    """Обробляє події миші для режима розробника"""
    global draw_start_pos, is_drawing_rect, current_rect_data, click_circle_pos, click_circle_timer

    if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:    # ЛКМ - початок креслення
        camera_offset = camera.camera.topleft
        m_x, m_y = e.pos
        draw_start_pos = (m_x - camera_offset[0], m_y - camera_offset[1])
        is_drawing_rect = True
        current_rect_data = {"x": int(draw_start_pos[0]), "y": int(draw_start_pos[1]), "w": 0, "h": 0}

    elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:    # ЛКМ - кінець креслення
        camera_offset = camera.camera.topleft
        end_x = e.pos[0] - camera_offset[0]
        end_y = e.pos[1] - camera_offset[1]
        rect_x = min(draw_start_pos[0], end_x)
        rect_y = min(draw_start_pos[1], end_y)
        rect_w = abs(end_x - draw_start_pos[0])
        rect_h = abs(end_y - draw_start_pos[1])
        current_rect_data = {"x": int(rect_x), "y": int(rect_y), "w": int(rect_w), "h": int(rect_h)}
        is_drawing_rect = False

        if rect_w > 0 or rect_h > 0:
            print(f"{DEV} {Back.CYAN} Креслення: {json.dumps(current_rect_data, ensure_ascii=False) + ','}")
            # print("\n")
        else:
            print(f"{DEV} {Back.GREEN} Координати натискання: {json.dumps({'x': current_rect_data['x'], 'y': current_rect_data['y']}, ensure_ascii=False) + ','}")
            # print("\n")
            current_rect_data = {"x": 0, "y": 0, "w": 0, "h": 0}

    elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:  # ПКМ - видобування даних
        camera_offset = camera.camera.topleft
        world_x = e.pos[0] - camera_offset[0]
        world_y = e.pos[1] - camera_offset[1]

        for obj in all_debug_objects:
            if obj.rect.collidepoint(world_x, world_y):
                out_data = {"x": int(obj.rect.x), 
                            "y": int(obj.rect.y), 
                            "w": int(obj.rect.width), 
                            "h": int(obj.rect.height)}
                for attr_name, value in vars(obj).items():
                    if attr_name in ["rect", "image", "width", "height"]: continue

                    if type(value).__module__.startswith('pygame'):
                        if isinstance(value, pygame.Vector2): out_data[attr_name] = [int(value.x), int(value.y)]
                        continue

                    if isinstance(value, (str, int, float, list, bool, dict)):
                        out_data[attr_name] = value

                print(f"{DEV} {Back.YELLOW} {json.dumps(out_data, ensure_ascii=False) + ','}")
                # print("\n")
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

        # Оновлення панелей (перевірка наближення гравця)
        for pn in panels:
            pn.update(player.rect)

        # Автоматичне закриття відкритої панелі при виході з зони
        if panel_renderer.is_open() and panel_renderer.panel is not None:
            if not panel_renderer.panel.player_nearby:
                panel_renderer.close()

        if player.rect.y < 1000:
            if player.gravity_vec != (0, 1):
                player.set_gravity(0, 1)
                player.streetfly_flash = True
                print(f"{INF} Система безпеки марсіанського простору: Всі об'єкти спостереження залишаються на орбіті! \n")

        # Оновлення камери
        if camera.focus_point:
            camera.update(None)
        else:
            camera.update(player)

# ============================ МАЛЮВАННЯ ======================================

def render_game(target_surface, player, labels, panels, finish_obj, camera, 
                dev_mode, all_debug_objects, backgrounds, draw_ui):
    """Малює всі елементи гри"""
    global click_circle_timer, click_circle_pos, is_drawing_rect, draw_start_pos

    # Раніше фон був монотонним. Добре що це було змінено)
    # window.fill((150, 90, 5))
    # window.blit(background_surface, (0, 0))

    current_win_w, current_win_h = target_surface.get_size()
    
    scroll_range_world = WORLD_HEIGHT - current_win_h
    scroll_range_bg = bg_surface.get_height() - current_win_h

    if scroll_range_world != 0:
        rel_y = camera.camera.y / scroll_range_world
        parallax_y = rel_y * scroll_range_bg
    else:
        parallax_y = 0

    bg_w = bg_surface.get_width()
    parallax_x = (camera.camera.x * 0.1) % bg_w

    target_surface.blit(bg_surface, (parallax_x - bg_w, parallax_y))
    target_surface.blit(bg_surface, (parallax_x, parallax_y))

    camera_offset = camera.camera.topleft

    #------------------------------------------------------------------------------ Так тут
    #------------------------------------------------------------------------------

    # Межі світу
    world_border = pygame.Rect(0, 0, WORLD_WIDTH, WORLD_HEIGHT).move(camera_offset)
    pygame.draw.rect(target_surface, (255, 255, 255), world_border, 1)

    # Область видимості для оптимізації
    win_w, win_h = target_surface.get_size()
    view_rect = pygame.Rect(-camera.camera.x, -camera.camera.y, win_w, win_h)

    # Об'єкт фону для виключень. Для мість де звичний не підійде
    for bg in backgrounds:
        if bg.rect.colliderect(view_rect):
            bg.update()
            bg.draw(target_surface, camera_offset)
            
    # Фініш
    finish_obj.draw(target_surface, camera_offset)

    # Ігрові об'єкти: Метод "Підкладки із затіненням" (Layered Buffer Outline)
    #
    # Прохід 1 — ШАР КОНТУРІВ:
    #   Малюємо inflate-підкладки (+5px з кожного боку) для всіх платформ.
    #   Сусідні блоки зливаються в єдиний силует; рамка видна лише на межі з повітрям.
    for obj in all_debug_objects:
        if obj.rect.colliderect(view_rect):
            if isinstance(obj, Platform):
                obj.draw_outline(target_surface, camera_offset)

    # Прохід 2 — ШАР ТЕКСТУР + інші об'єкти:
    #   Текстури перекривають внутрішню частину силуету — видним залишається
    #   лише зовнішній край підкладки. Гравець малюється пізніше і перекриває все.
    for obj in all_debug_objects:
        if obj.rect.colliderect(view_rect):
            obj.is_hovered = obj.rect.inflate(4, 4).colliderect(player.rect)
            obj.draw(target_surface, camera_offset, dev_mode=False)

    # Текст
    for lbl in labels:
        lbl.draw(target_surface, camera_offset)

    # Панелі (таблички, монологи)
    for pn in panels:
        if pn.rect.colliderect(view_rect):
            pn.draw(target_surface, camera_offset, dev_mode=dev_mode)

    # Гравець
    player.draw(target_surface, camera_offset)
    
    # ------------------------------------------------------------------------------ Тут на свій розсуд: вималовувати поверх всього світу
    # Партікли вітру (зліва направо)
    if player.rect.y <= 2500:
        wind_system.run(
            target_surface,
            density=0.5,                 # Щільність часток
            side=wind_system.current_direction, # Сторона появи (top, bottom, left, right)
            color=(200, 160, 130),        # Колір часток
            speed_range=(13.0, 23.0),    # Швидкість руху
            size_range=(4, 6),           # Розмір
            fade_range=(1, 3)            # Згасання (З часом вони пропадають)
        )

    #------------------------------------------------------------------------------  або знайти такіж риски вище і малювати трохи вище фону

    # Дебаг елементи
    if dev_mode:
        pygame.draw.rect(target_surface, (255, 255, 255), camera.dead_zone, 1)
        for obj in all_debug_objects:
            obj.draw_debug(target_surface, True, camera_offset)

    # Креслення прямокутника в dev режимі
    if dev_mode and is_drawing_rect and draw_start_pos:
        draw_dev_rectangle(target_surface, camera_offset)

    # Клік-вибірка об'єкта в dev режимі
    if click_circle_timer > 0 and click_circle_pos:
        pygame.draw.circle(target_surface, (255, 200, 20), click_circle_pos, 20, 3)
        pygame.draw.circle(target_surface, (255, 240, 120), click_circle_pos, 5)
        click_circle_timer -= 1

def draw_dev_rectangle(target_surface, camera_offset):
    """Код для креслення в dev режимі"""
    global current_rect_data

    m_pos = pygame.mouse.get_pos()
    curr_world_x = m_pos[0] - camera_offset[0]
    curr_world_y = m_pos[1] - camera_offset[1]

    rect_x = min(draw_start_pos[0], curr_world_x)
    rect_y = min(draw_start_pos[1], curr_world_y)
    rect_w = abs(curr_world_x - draw_start_pos[0])
    rect_h = abs(curr_world_y - draw_start_pos[1])

    current_rect_data = {"x": int(rect_x), "y": int(rect_y), "w": int(rect_w), "h": int(rect_h)}

    start_screen_x = draw_start_pos[0] + camera_offset[0]
    start_screen_y = draw_start_pos[1] + camera_offset[1]
    screen_x = rect_x + camera_offset[0]
    screen_y = rect_y + camera_offset[1]

    if rect_w == 0 and rect_h == 0:
        # Зелений індикатор точки натискання тільки до початку реального креслення
        pygame.draw.circle(target_surface, (0, 255, 100), (start_screen_x, start_screen_y), 6)
        pygame.draw.circle(target_surface, (0, 180, 80), (start_screen_x, start_screen_y), 10, 2)

    if rect_w > 0 and rect_h > 0:
        s = pygame.Surface((rect_w, rect_h), pygame.SRCALPHA)
        s.fill((0, 120, 255, 80))
        target_surface.blit(s, (screen_x, screen_y))

        pygame.draw.rect(target_surface, (0, 180, 255), (screen_x, screen_y, rect_w, rect_h), 2)

        debug_info = f"x:{int(rect_x)} y:{int(rect_y)} w:{int(rect_w)} h:{int(rect_h)}"
        info_surf = ui_font.render(debug_info, True, (255, 255, 255))
        bg_rect = info_surf.get_rect(topleft=(screen_x, screen_y - 25))
        pygame.draw.rect(target_surface, (0, 0, 0), bg_rect.inflate(4, 2))
        target_surface.blit(info_surf, (screen_x, screen_y - 25))

# ============================ МЕНЕДЖЕР РЕНДЕРУ (GPU) =========================

def draw_screen():
    """Менеджер конвеєру рендерингу. Всі ефекти тепер працюють через GPU (lighting.py)"""
    global death_pixel_scale, win_blur_scale

    game_buffer.fill((0, 0, 0))
    ui_buffer.fill((0, 0, 0, 0))

    if game_over:
        if death_pixel_scale < MAX_PIXEL_MUSH:
            death_pixel_scale = min(MAX_PIXEL_MUSH, death_pixel_scale + WIN_PIXEL_SPEED)

        # Малює світ у буфер
        render_game(game_buffer, player, labels, panels, finish_obj, camera, 
                dev_mode, all_debug_objects, backgrounds, draw_ui=False)
        player.draw_face(game_buffer, camera)

        # Чіткий UI поверх
        draw_ui_boxes(ui_buffer, player, dev_mode)
        draw_end_screen(ui_buffer, "ТЕБЕ ОПРОМІНЕНО", "Щоб відновити себе тисни R", OVERLAY_GAME_OVER)

        lighting.render(game_buffer, ui_buffer, player.rect, platforms, camera, (255, 0, 0), effect_type=1, effect_scale=death_pixel_scale, lighting_enabled=lighting_enabled)

    elif game_won:
        if win_blur_scale < MAX_WIN_BLUR:
            win_blur_scale = min(MAX_WIN_BLUR, win_blur_scale + WIN_BLUR_SPEED)

        # Малює світ у буфер
        render_game(game_buffer, player, labels, panels, finish_obj, camera, 
                dev_mode, all_debug_objects, backgrounds, draw_ui=False)
        player.draw_face(game_buffer, camera)

        # Чіткий UI поверх
        draw_ui_boxes(ui_buffer, player, dev_mode)
        draw_end_screen(ui_buffer, "ПЕРЕМОГА!", "Дібрався до свого друга!", OVERLAY_WIN)

        # Віддаємо на відеокарту з ефектом розмиття (2)
        lighting.render(game_buffer, ui_buffer, player.rect, platforms, camera, (0, 255, 100), effect_type=2, effect_scale=win_blur_scale, lighting_enabled=lighting_enabled)

    else:
        # Звичайний ігровий процес
        death_pixel_scale = 1.0
        win_blur_scale = 1.0
        
        render_game(game_buffer, player, labels, panels, finish_obj, camera, 
                dev_mode, all_debug_objects, backgrounds, draw_ui=draw_ui)
        player.draw_face(game_buffer, camera)
        
        if draw_ui:
            draw_ui_boxes(ui_buffer, player, dev_mode)
            
        current_light = (255, 255, 255) if white_light_active else player.color
        lighting.render(game_buffer, ui_buffer, player.rect, platforms, camera, current_light, effect_type=0, effect_scale=1.0, lighting_enabled=lighting_enabled)

def draw_pause_menu(ui_buffer):
    """Меню паузи (Оптимізоване)"""
    global pause_buttons, pause_overlay_cache
    win_w, win_h = ui_buffer.get_size()

    if pause_overlay_cache is None or pause_overlay_cache.get_size() != (win_w, win_h):
        pause_overlay_cache = pygame.Surface((win_w, win_h), pygame.SRCALPHA)
        pause_overlay_cache.fill((0, 0, 0, 170))
    ui_buffer.blit(pause_overlay_cache, (0, 0))

    title = title_font.render("ЗУПИНКА ЧАСУ", True, (255, 255, 255))
    ui_buffer.blit(title, (win_w // 2 - title.get_width() // 2, win_h // 2 - 180))

    buttons = ["ДОГРАТИ", 
               "НАЛАШТУНКИ (СКОРО)", 
               "Я ЩЕ ПОВЕРНУСЯ"]
    pause_buttons = []
    mouse_pos = pygame.mouse.get_pos()

    for i, text in enumerate(buttons):
        rect = pygame.Rect(win_w // 2 - 180, win_h // 2 - 60 + i * 90, 360, 60)
        hover = rect.collidepoint(mouse_pos)
        bg = (80, 30, 20) if hover else (40, 10, 10)
        
        pygame.draw.rect(ui_buffer, bg, rect, border_radius=10)
        pygame.draw.rect(ui_buffer, (180, 85, 75), rect, 2, border_radius=10)

        txt = button_font.render(text, True, (255,255,255))
        ui_buffer.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))
        pause_buttons.append(rect)

# ============================= СТАН ГРИ ======================================
dev_mode = False
draw_ui = True
game_won = False
game_over = False
game_paused = False
return_to_menu = False
lighting_enabled = True

cached_pause_bg = None
pause_overlay_cache = None
pause_buttons = []

# Змінні для креслення в dev режимі
draw_start_pos = None
is_drawing_rect = False
current_rect_data = {"x": 0, "y": 0, "w": 0, "h": 0}
click_circle_pos = None
click_circle_timer = 0
camera_target = False
white_light_active = False


lighting_enabled = save_data.get("settings", {}).get("lighting_enabled", True)
white_light_active = save_data.get("settings", {}).get("white_light_active", False)
is_fullscreen = save_data.get("settings", {}).get("is_fullscreen", False)
# ======================= ОСНОВНИЙ ІГРОВИЙ ЦИКЛ ===============================
bg_surface = TextureFactory.get_texture("dynamic_bg", BG_WIDTH, WORLD_HEIGHT).convert()

end_time = time.perf_counter()
load_time = (end_time - start_time) * 1000
print(f"{INF} Простір завантажено за: {load_time:.2f} мілісекунд \n")

running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            standart_progress()
            running = False

        elif e.type == pygame.VIDEORESIZE:
            new_w, new_h = e.w, e.h

            window = pygame.display.set_mode((new_w, new_h), pygame.RESIZABLE | pygame.OPENGL | pygame.DOUBLEBUF)

            game_buffer = pygame.Surface((new_w, new_h))
            ui_buffer = pygame.Surface((new_w, new_h), pygame.SRCALPHA)
            lighting = LightingEngine(new_w, new_h)

            camera.resize(new_w, new_h)
            camera.recenter(player)
        
        elif e.type == pygame.MOUSEBUTTONDOWN and game_paused:
            if e.button == 1:
                handle_pause_click(e.pos)

        elif e.type == pygame.KEYDOWN:
            handle_keydown_events(e, player, camera, portals, finish_obj)

        elif dev_mode:
            handle_dev_mouse_events(e, camera, all_debug_objects)

    if game_over:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_r]:
            player.respawn()
            game_over = False

    if not game_paused:
        update_game_logic(player, campfires, platforms, portals, camera, finish_obj)
        draw_screen()
        pause_blur_scale = 1.0

    else:
        # ПАУЗА: Рендеримо світ у буфер і віддаємо шейдеру команду "Розмити (2)"
        if pause_blur_scale < MAX_PAUSE_BLUR:
            game_buffer.fill((0, 0, 0))
            render_game(game_buffer, player, labels, panels, finish_obj, camera, 
                        dev_mode, all_debug_objects, backgrounds, draw_ui=False)
            pause_blur_scale = min(MAX_PAUSE_BLUR, pause_blur_scale + PAUSE_BLUR_SPEED)
            
        ui_buffer.fill((0,0,0,0))
        draw_pause_menu(ui_buffer) 
        
        lighting.render(game_buffer, ui_buffer, player.rect, platforms, camera, player.color, effect_type=2, effect_scale=pause_blur_scale, lighting_enabled=lighting_enabled)

    pygame.display.set_caption(f"Gravity Shift - МАРС     (FPS: {int(clock.get_fps())})")
    pygame.display.flip()
    clock.tick(FPS)
if return_to_menu:
    subprocess.Popen([sys.executable, os.path.join(_ROOT_DIR, "START_HERE.py")], cwd=_ROOT_DIR)
pygame.quit()

# M.
