from pygame import *
from pygame.locals import *
from classes import Player, Platform, TunnelPortal, JumpPad, Campfire, Finish, Camera, WorldLabel
import os
import json
 
# ============================ КОНСТАНТИ ГРИ ==================================

WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 900
WORLD_WIDTH = 10000
WORLD_HEIGHT = 5000
FPS = 60

# Кольори UI
UI_BG_COLOR = (0, 0, 0, 150)
UI_DEV_BG_COLOR = (0, 0, 0, 180)
UI_HELP_BG_COLOR = (0, 0, 50, 200)
OVERLAY_GAME_OVER = (100, 0, 0, 180)
OVERLAY_WIN = (0, 100, 0, 180)

# Камера
CAMERA_TARGET_X = 440
CAMERA_TARGET_Y = 4440

init()
window = display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), RESIZABLE)
display.set_caption("Gravity Shift")
clock = time.Clock()
ui_font = font.SysFont("Consolas", 18, bold=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OBJECTS_FILE = os.path.join(BASE_DIR, "objects.json")

# =========================== ДОПОМІЖНІ ФУНКЦІЇ ===============================

def is_on_screen(rect, camera_x, camera_y, display_w, display_h):
    """Перевіряє чи знаходиться прямокутник на екрані"""
    return (rect.x + camera_x + rect.width > 0 and
            rect.x + camera_x < display_w and
            rect.y + camera_y + rect.height > 0 and
            rect.y + camera_y < display_h)

def load_game_world(filename):
    """Завантажує об'єкти гри з JSON файлу"""
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    platforms = sprite.Group()
    portals = sprite.Group()
    campfires = sprite.Group()

    for i, p in enumerate(data.get("platforms", [])):
        p_type = p.get("type", "norm")
        platforms.add(Platform(p["x"], p["y"], p["w"], p["h"], p_type, obj_id=i))

    for i, p in enumerate(data.get("portals", [])):
        portals.add(TunnelPortal(p["x"], p["y"], p["target_gravity"],
                                w=p.get("w"), h=p.get("h"), obj_id=i))

    for i, j in enumerate(data.get("jump_pads", [])):
        portals.add(JumpPad(j["x"], j["y"], j["target_gravity"],
                           w=j.get("w"), h=j.get("h"), obj_id=i))

    for i, c in enumerate(data.get("campfires", [])):
        campfires.add(Campfire(c["x"], c["y"], side=c.get("side", "center"), obj_id=i))

    f_data = data.get("finish")
    finish = Finish(f_data["x"], f_data["y"], f_data.get("w", 90), f_data.get("h", 120)) if f_data else None

    labels = sprite.Group()
    for i, l in enumerate(data.get("labels", [])):
        labels.add(WorldLabel(l["text"], l["x"], l["y"], l.get("size", 20),
                             tuple(l.get("color", (255, 255, 255))),
                             l.get("bg_alpha", 0), obj_id=i))

    return platforms, portals, campfires, finish, labels

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
    """Малює всі UI елементи на екрані"""
    win_w, win_h = screen.get_size()
    scale = win_h / 600.0

    font_size = int(18 * scale)
    ui_font_scaled = font.SysFont("Consolas", font_size, bold=True)

    margin = int(15 * scale)
    padding = int(12 * scale)
    line_h = int(22 * scale)

    # Плашка гравця (зверху ліворуч)
    draw_player_info_box(screen, player, margin, padding, line_h, scale, ui_font_scaled)

    # Плашка розробника (знизу ліворуч)
    if dev_mode:
        draw_dev_info_box(screen, player, camera, margin, padding, line_h, scale, ui_font_scaled, win_h)

    # Плашка інструкцій (зверху праворуч)
    keys = key.get_pressed()
    if keys[K_LCTRL] or keys[K_RCTRL]:
        draw_help_box(screen, player, margin, padding, line_h, scale, ui_font_scaled, win_w)

def draw_player_info_box(screen, player, margin, padding, line_h, scale, font):
    """Малює інформацію про гравця"""
    gravity_name, p_color = player.get_gravity_info()
    p_lines = [
        f"Керування: {player.control_mode}",
        f"Скін: {player.current_preset}",
        f"Гравітація: "
    ]

    box_w = int(260 * scale)
    box_h = padding * 1.6 + len(p_lines) * line_h

    bg = Surface((box_w, box_h), SRCALPHA)
    bg.fill(UI_BG_COLOR)
    screen.blit(bg, (margin, margin))

    for i, line in enumerate(p_lines):
        txt = font.render(line, True, (255, 255, 255))
        screen.blit(txt, (margin + padding, margin + padding + i * line_h))

    prefix_w = font.size("Гравітація: ")[0]
    grav_txt = font.render(gravity_name, True, p_color)
    screen.blit(grav_txt, (margin + padding + prefix_w, margin + padding + 2 * line_h))

def draw_dev_info_box(screen, player, camera, margin, padding, line_h, scale, font, win_h):
    """Малює інформацію для розробника"""
    m_pos = mouse.get_pos()
    world_m_x = m_pos[0] - camera.camera.x
    world_m_y = m_pos[1] - camera.camera.y

    focus_status = f"({int(camera.focus_point[0])}, {int(camera.focus_point[1])})" if camera.focus_point else "Гравець"

    dev_lines = [
        "--- РЕЖИМ РОЗРОБНИКА ---",
        f"Гравець X:{int(player.rect.x)} Y:{int(player.rect.y)}",
        f"Миша   X:{int(world_m_x)} Y:{int(world_m_y)}",
        f"Фокус камери: {focus_status}",
        f"[1]-Down|[2]-Up|[3]-Left|[4]-Right",
        f"Spawn: {player.respawn_pos}"
    ]

    box_w = int(365 * scale)
    box_h = padding * 1.6 + len(dev_lines) * line_h
    y_pos = win_h - box_h - margin

    bg = Surface((box_w, box_h), SRCALPHA)
    bg.fill(UI_DEV_BG_COLOR)
    screen.blit(bg, (margin, y_pos))

    for i, line in enumerate(dev_lines):
        if i == 0: t_color = (255, 255, 0)      # Заголовок
        elif i == 3: t_color = (255, 215, 0)    # Фокус камери
        elif i == 2: t_color = (100, 200, 255)  # Миша
        elif i == 1: t_color = (150, 255, 150)  # Гравець
        else: t_color = (255, 255, 255)         # Все інше

        txt = font.render(line, True, t_color)
        screen.blit(txt, (margin + padding, y_pos + padding + i * line_h))

def draw_help_box(screen, player, margin, padding, line_h, scale, font, win_w):
    """Малює плашку інструкції керування"""
    current_mode = player.control_mode.lower()

    if "wasd" in current_mode and "arrows" in current_mode:
        mode_display = "Обидва  "
    elif "wasd" in current_mode:
        mode_display = "WASD    "
    elif "arrows" in current_mode:
        mode_display = "Стрілки "
    else:
        mode_display = "Обидва  "

    help_lines = [
        "  КЕРУВАННЯ  ",
        "-------------",
        f"{mode_display} - Рух",
        "TAB      - Скін",
        "F↓L↓| M  - Пресет",
        "SHIFT    - Зависання",
        "R        - Респавн",
        "F11      - Весь екран",
        "ESCAPE   - Розробник:",
        "LKM      - Креслення",
        "PKM      - Видобути",
        "P        - Режим камери",
        "CTRL     - Сховати"
    ]

    box_w = int(250 * scale)
    box_h = padding * 1.6 + len(help_lines) * line_h
    x_pos = win_w - box_w - margin

    bg = Surface((box_w, box_h), SRCALPHA)
    bg.fill(UI_HELP_BG_COLOR)
    screen.blit(bg, (x_pos, margin))

    for i, line in enumerate(help_lines):
        t_c = (100, 200, 255) if i < 2 else (255, 255, 255)
        txt = font.render(line, True, t_c)
        screen.blit(txt, (x_pos + padding, margin + padding + i * line_h))

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

# ========================= ІНІЦІАЛІЗАЦІЯ ГРИ =================================

# Синхронізація ID в JSON
auto_index_json(OBJECTS_FILE)
print("Усі ID (nomer) успішно синхронізовано!")

# База гри
player = Player(0, 0)
camera = Camera(WINDOW_WIDTH, WINDOW_HEIGHT)

# Провантаження світу
platforms, portals, campfires, finish_obj, labels = load_game_world(OBJECTS_FILE)
all_debug_objects = list(platforms) + list(portals) + list(campfires) + list(labels)
sync_portals_color(portals, player)

# Встановлення першої точки спавну
if campfires:
    first_fire = list(campfires)[0]
    player.respawn_pos = (first_fire.spawn_x, first_fire.spawn_y)
    player.respawn()

# ========================= ОБРОБКА ПОДІЙ =====================================

def handle_keydown_events(e, player, camera, portals, finish_obj):
    """Обробляє натискання клавіш"""
    global game_won, dev_mode

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
            player.switch_skin()
            sync_portals_color(portals, player)

    # Перевірка перемоги
    if e.key == K_g and not game_won:
        if finish_obj.check_interaction(player.rect):
            game_won = True

    # Режим розробника
    if e.key == K_ESCAPE:
        dev_mode = not dev_mode
        print(f"Режим розробника: {dev_mode}")

    # Повноекранний режим (Або просто перетягуйте межі екрану, якщо хочете власно налаштувати розмір)
    if e.key == K_F11:
        global window
        if window.get_flags() & FULLSCREEN:
            window = display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), RESIZABLE)
        else:
            window = display.set_mode((0, 0), FULLSCREEN)

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
        print(f"Координати натиску миші: {draw_start_pos}")

    elif e.type == MOUSEBUTTONUP and e.button == 1:  # ЛКМ - кінець креслення
        is_drawing_rect = False
        print(f"Креслення: {current_rect_data}")

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

# ========================= ІГРОВА ЛОГІКА =====================================

def update_game_logic(player, campfires, platforms, portals, camera, finish_obj):
    """Оновлює логіку гри"""
    global game_won, game_over

    # Взаємодія з багаттям
    for fire in campfires:
        if fire.rect.colliderect(player.rect):
            player.respawn_pos = (fire.spawn_x, fire.spawn_y)

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

        # Оновлення камери
        win_w, win_h = window.get_size()
        view_rect = Rect(-camera.camera.x, -camera.camera.y, win_w, win_h)

        if camera.focus_point:
            camera.update(None)
        else:
            camera.update(player)

# ============================ МАЛЮВАННЯ ======================================

def render_game(window, player, labels, finish_obj, camera, 
                dev_mode, all_debug_objects, game_over, game_won):
    """Малює всі елементи гри"""
    global click_circle_timer, click_circle_pos, is_drawing_rect, draw_start_pos

    window.fill((30, 30, 30))
    camera_offset = camera.camera.topleft

    # Межі світу
    world_border = Rect(0, 0, WORLD_WIDTH, WORLD_HEIGHT).move(camera_offset)
    draw.rect(window, (255, 255, 255), world_border, 1)

    # Область видимості для оптимізації
    win_w, win_h = window.get_size()
    view_rect = Rect(-camera.camera.x, -camera.camera.y, win_w, win_h)

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

    # Екрани завершення
    if game_over:
        draw_end_screen(window, "ГРА ЗАКІНЧЕНА", "Тисни R, щоб спробувати ще раз", OVERLAY_GAME_OVER)
    elif game_won:
        draw_end_screen(window, "ПЕРЕМОГА!", "Ти справжній LOGIK!", OVERLAY_WIN)

    # UI елементи
    draw_ui_boxes(window, player, dev_mode)

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

# ============================= СТАН ГРИ ======================================

dev_mode = False
game_won = False
game_over = False

# Змінні для креслення в dev режимі
draw_start_pos = None
is_drawing_rect = False
current_rect_data = {"x": 0, "y": 0, "w": 0, "h": 0}
click_circle_pos = None
click_circle_timer = 0
camera_target = False

# ======================= ОСНОВНИЙ ІГРОВИЙ ЦИКЛ ===============================
# Щоб оптимізувати гру для слабих всі дії було виведено з циклу, зібрано все по темам і розділено на функції.
running = True
while running:
    for e in event.get():
        if e.type == QUIT:
            running = False

        elif e.type == KEYDOWN:
            handle_keydown_events(e, player, camera, portals, finish_obj)

        elif dev_mode:
            handle_dev_mouse_events(e, camera, all_debug_objects)

    if game_over:
        keys = key.get_pressed()
        if keys[K_r]:
            player.respawn()
            game_over = False

    update_game_logic(player, campfires, platforms, portals, camera, finish_obj)

    render_game(window, player, labels, finish_obj, camera, 
                dev_mode, all_debug_objects, game_over, game_won)

    display.update()
    clock.tick(FPS)

quit()