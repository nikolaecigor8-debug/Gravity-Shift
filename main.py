from pygame import *
from classes import Player, Platform, TunnelPortal, JumpPad, Campfire, Finish, Camera
import os
import json
# cd "Gravy Shift" (Якщо видає помилко по типу: "Я не бачу той json у твоїх тонній папці де лежить гра". Написати в консоль)

# --- ІНІЦІАЛІЗАЦІЯ ---
init()
window = display.set_mode((800, 600), RESIZABLE)
display.set_caption("Gravity Shift")
clk = time.Clock()

x_window, y_window = 0, 0
width_window, height_window = 1500, 1000

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "objects.json")

def load_game_world(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    platforms = sprite.Group()
    portals = sprite.Group()
    campfires = sprite.Group()

    # Нумеруємо платформи. | Нотатка ідеї, norm умова платформи що на ню просто можна втаритися або спертися. 
    # Якщо змінити і уточнити це в json можна створити об'єкт вбивцю чи слизьку поверхню (friction збільшити)
    for i, p in enumerate(data.get("platforms", [])):
        p_type = p.get("type", "norm")
        platforms.add(Platform(p["x"], p["y"], p["w"], p["h"], p_type, obj_id=i))

    # Нумеруємо портали (продовжуємо або окрема нумерація)
    for i, p in enumerate(data.get("portals", [])):
        portals.add(TunnelPortal(p["x"], p["y"], p["target_gravity"], w=p.get("w"), h=p.get("h"), obj_id=i))

    # Нумеруємо пад-стрибуни
    for i, j in enumerate(data.get("jump_pads", [])):
        portals.add(JumpPad(j["x"], j["y"], j["target_gravity"], w=j.get("w"), h=j.get("h"), obj_id=i))

    # Нумеруємо багаття
    for i, c in enumerate(data.get("campfires", [])):
        campfires.add(Campfire(c["x"], c["y"], side=c.get("side", "center"), obj_id=i))

    # Фініш залишаємо без ID (як ти і хотів)
    f_data = data.get("finish")
    finish = Finish(f_data["x"], f_data["y"], f_data["w"], f_data["h"]) if f_data else None

    return platforms, portals, campfires, finish

def sync_portals_color(portal_group, player_obj):
    """Оновлює всі портали та джамп-пади згідно з пресетом гравця"""
    for p in portal_group:
        if hasattr(p, 'update_color'):
            p.update_color(player_obj.presets, player_obj.current_preset)

def draw_ui_boxes(screen, player, dev_mode):
    win_w, win_h = screen.get_size()
    
    # Масштабування: базовою висотою вважаємо 600px. 
    scale = win_h / 600.0 
    
    font_size = int(18 * scale)
    ui_font = font.SysFont("Consolas", font_size, bold=True)
    
    margin = int(15 * scale)     # Відступ від краю екрана
    padding = int(12 * scale)    # Внутрішній відступ у плашці
    line_h = int(22 * scale)     # Висота рядка тексту

    # --- 1. ПЛАШКА ГРАВЦЯ (ЗВЕРХУ ЛІВОРУЧ) ---
    gravity_name, p_color = player.get_gravity_info()
    p_lines = [
        f"Керування: {player.control_mode}",
        f"Скін: {player.current_preset}",
        f"Гравітація: " 
    ]
    
    box1_w = int(260 * scale)
    box1_h = padding * 1.6 + len(p_lines) * line_h
    
    bg1 = Surface((box1_w, box1_h), SRCALPHA)
    bg1.fill((0, 0, 0, 150)) # Напівпрозоре затінення
    screen.blit(bg1, (margin, margin))
    
    for i, line in enumerate(p_lines):
        txt = ui_font.render(line, True, (255, 255, 255))
        screen.blit(txt, (margin + padding, margin + padding + i * line_h))
    
    prefix_w = ui_font.size("Гравітація: ")[0]
    grav_txt = ui_font.render(gravity_name, True, p_color)
    screen.blit(grav_txt, (margin + padding + prefix_w, margin + padding + 2 * line_h))

    # --- 2. ПЛАШКА РОЗРОБНИКА (ЗНИЗУ ЛІВОРУЧ) ---
    if dev_mode:
        dev_lines = [
            "--- РЕЖИМ РОЗРОБНИКА ---",
            f"Гравець X:{int(player.rect.x)} Y:{int(player.rect.y)}",
            f"[1]-Down|[2]-Up|[3]-Left|[4]-Right",
            f"Spawn: {player.respawn_pos}"
        ]
        
        box2_w = int(365 * scale)
        box2_h = padding * 1.6 + len(dev_lines) * line_h
        y_pos = win_h - box2_h - margin
        
        bg2 = Surface((box2_w, box2_h), SRCALPHA)
        bg2.fill((0, 0, 0, 180))
        screen.blit(bg2, (margin, y_pos))
        
        for i, line in enumerate(dev_lines):
            # Головний заголовок жовтий, координати — салатові, кнопки — білі
            t_color = (255, 255, 0) if i == 0 else (150, 255, 150) if i == 1 else (255, 255, 255)
            txt = ui_font.render(line, True, t_color)
            screen.blit(txt, (margin + padding, y_pos + padding + i * line_h))

    # --- 3. ПЛАШКА ІНСТРУКЦІЇ (ЗВЕРХУ ПРАВОРУЧ) ---
    keys = key.get_pressed()
    if keys[K_LCTRL] or keys[K_RCTRL]:
        current_mode = player.control_mode.lower()
        
        if "wasd" in current_mode and "arrows" in current_mode:
            mode_display = "Обидва  "
        elif "wasd" in current_mode:
            mode_display = "WASD    "
        elif "arrows" in current_mode:
            mode_display = "Стрілки "
        else:
            mode_display = "Обидва  " # Резервний варіант
            
        help_lines = [
            "  КЕРУВАННЯ  ",
            "-------------",
            f"{mode_display} - Рух",
            "TAB      - Скін",
            "\F,L,\ M - Пресет",
            " \SHIFT\ - Зависання",
            #"G        - Діяти",
            "F11      - Весь екран",
            "ESCAPE   - Розробник",
            "CTRL     - Сховати"
        ]
        
        box3_w = int(240 * scale) 
        box3_h = padding * 1.6 + len(help_lines) * line_h
        x_pos_help = win_w - box3_w - margin
        
        bg3 = Surface((box3_w, box3_h), SRCALPHA)
        bg3.fill((0, 0, 50, 200))
        screen.blit(bg3, (x_pos_help, margin))
        
        for i, line in enumerate(help_lines):
            t_c = (100, 200, 255) if i < 2 else (255, 255, 255)
            txt = ui_font.render(line, True, t_c)
            screen.blit(txt, (x_pos_help + padding, margin + padding + i * line_h))

# Створюємо головного героя. Координати 400, 100 — це десь посередині зверху.
player = Player(400, 100)
camera = Camera(800, 600)

victory_font = font.SysFont("Verdana", 72, bold=True)
victory_text = victory_font.render("ПЕРЕМОГА!", True, (0, 255, 100))

platforms, portals, campfires, finish_obj = load_game_world(FILE_PATH)
sync_portals_color(portals, player)
# "c:\Users\nikol\OneDrive\Desktop\Моя LOGIKA\Gravy Shift\main.py"
# "objects.json"

if campfires:
    first_fire = list(campfires)[0]
    player.respawn_pos = (first_fire.spawn_x, first_fire.spawn_y)
    player.respawn()

all_debug_objects = list(platforms) + list(portals) + list(campfires)

dev_mode = False
game_won = False
run = True
while run:
    # --- ОБРОБКА ПОДІЙ ---
    for e in event.get():
        if e.type == QUIT: 
            run = False
        
        # Чит-коди для розробника: міняємо нравітацію натисканням цифр.
        if e.type == KEYDOWN:
            # Поки гравець не виграв він може рухатись (дуже дивно звучить правда?)
            if not game_won:

                if dev_mode:
                    if e.key == K_1:
                        player.gravity_vec = Vector2(0, 1)   # Вниз
                    elif e.key == K_2:
                        player.gravity_vec = Vector2(0,-1)  # Вгору
                    elif e.key == K_3:
                        player.gravity_vec = Vector2(-1,0)  # Вліво
                    elif e.key == K_4:
                        player.gravity_vec = Vector2(1, 0)   # Вправо
                    
                    player.update_color()
                    sync_portals_color(portals, player)

                if e.key == K_r:  # КНОПКА СМЕРТІ. Якщо застряг або просто набридло жити.
                    player.respawn()

                # Механіка Streetfly. Має ліміт — спалах є, інерція зникає.
                if e.key == K_LSHIFT or e.key == K_RSHIFT or e.key == K_f or e.key == K_l: 
                    player.apply_streetfly()

                # Клавіша "M" для тих, кому не подобається стандартне керування.
                if e.key == K_m:
                    player.switch_control_mode()

                # TAB — це скіни гравця. Швидка зміна кольорової палітри (Classic <-> Cyber).
                if e.key == K_TAB:
                    player.switch_skin()
                    sync_portals_color(portals, player)

            if e.key == K_g and not game_won:
                if finish_obj.check_interaction(player.rect):
                    game_won = True # ЧАС ЗУПИНЕНО

            if e.key == K_ESCAPE:
                dev_mode = not dev_mode
                print(f"Режим розробника: {dev_mode}")

            if e.key == K_F11:
                # Перемикання між віконним та повним екраном
                if window.get_flags() & FULLSCREEN:
                    window = display.set_mode((800, 600), RESIZABLE)
                else:
                    window = display.set_mode((0, 0), FULLSCREEN)

    # --- ЛОГІКА ВЗАЄМОДІЇ ---
    for fire in campfires:
        if fire.rect.colliderect(player.rect):
            # Кожного разу, коли проходимо крізь багаття, оновлюємо точку респавну.
            player.respawn_pos = (fire.spawn_x, fire.spawn_y)
    
    # --- КРИТИЧНИЙ БАГО-ФІКС (Друга межа респавну) ---
    # Якщо гравець подолав фізичну стіну (10000) і вилетів на +5 пікселів далі — респавн.
    if (player.rect.right > width_window + 5 or player.rect.left < -5 or 
        player.rect.bottom > height_window + 5 or player.rect.top < -5):
        player.respawn()


    # Послідовність важлива: спочатку ввід, потім фізика, потім візуал.
    if not game_won:
        player.handle_input()
        player.apply_physics(platforms, portals, width_window, height_window)
        player.update_visuals()
        finish_obj.check_interaction(player.rect)
        camera.update(player)


    # --- МАЛЮВАННЯ ---
    window.fill((30, 30, 30))
    camera_offset = camera.camera.topleft

    # Малюємо тонку білу лінію по периметру всього світу
    world_border = Rect(x_window, y_window, width_window, height_window).move(camera_offset)
    draw.rect(window, (255, 255, 255), world_border, 1)


    for obj in all_debug_objects:
        obj.is_hovered = obj.rect.inflate(4, 4).colliderect(player.rect)
        obj.draw(window, camera_offset, dev_mode=False)

    finish_obj.draw(window, camera_offset)
    player.draw(window, camera_offset)

    if dev_mode:
        for obj in all_debug_objects:
            obj.draw_debug(window, True, camera_offset)

    if game_won:
        screen_rect = window.get_rect()
        txt_rect = victory_text.get_rect(center=screen_rect.center)
        window.blit(victory_text, txt_rect)

    draw_ui_boxes(window, player, dev_mode)

    # Оновлення кадру
    display.update()
    clk.tick(60) # Тримаємо стабільні 60 FPS. Більше людське око (в цій грі) не побачить.

quit()