from pygame import *
from classes import Player, Platform, TunnelPortal, JumpPad, Campfire, Finish, Camera, WorldLabel
import os
import json
# cd "Gravy Shift" (Якщо видає помилко по типу: "Я не бачу той json у твоїй тонній папці де лежить гра". Написати в консоль)

# --- ІНІЦІАЛІЗАЦІЯ ---
init()
window = display.set_mode((1400, 900), RESIZABLE)
display.set_caption("Gravity Shift")
clk = time.Clock()
ui_font = font.SysFont("Consolas", 18, bold=True)

x_window, y_window = 0, 0
width_window, height_window = 10000, 5000
# camera_target_# = c_t_#
c_t_x, c_t_y = 440, 4440

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "objects.json")

#----------------------DEF для роботи основи данних---------------------#

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
    finish = Finish(f_data["x"], f_data["y"], f_data.get("w", 90), f_data.get("h", 120)) if f_data else None

    labels = sprite.Group()
    for i, l in enumerate(data.get("labels", [])):
        labels.add(WorldLabel(l["text"], l["x"], l["y"], l.get("size", 20), tuple(l.get("color", (255, 255, 255))), l.get("bg_alpha", 0),obj_id=i))

    return platforms, portals, campfires, finish, labels

def auto_index_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Категорії, які мають поле "nomer"
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

auto_index_json('objects.json')
print("Усі ID (nomer) успішно синхронізовано!")

def sync_portals_color(portal_group, player_obj):
    """Оновлює всі портали та джамп-пади згідно з пресетом гравця"""
    for p in portal_group:
        if hasattr(p, 'update_color'):
            p.update_color(player_obj.presets, player_obj.current_preset)

def draw_ui_boxes(screen, player, dev_mode, camera_offset): # Додали camera_offset
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
        m_pos = mouse.get_pos()
        world_m_x = m_pos[0] - camera_offset[0]
        world_m_y = m_pos[1] - camera_offset[1]

        # Визначаємо текст фокусу камери (використовуємо твою назву c_t_x, c_t_y)
        if camera.focus_point:
            focus_status = f"({int(camera.focus_point[0])}, {int(camera.focus_point[1])})"
        else:
            focus_status = "Гравець"

        dev_lines = [
            "--- РЕЖИМ РОЗРОБНИКА ---",
            f"Гравець X:{int(player.rect.x)} Y:{int(player.rect.y)}",
            f"Миша   X:{int(world_m_x)} Y:{int(world_m_y)}",
            f"Фокус камери: {focus_status}",
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
            # Додаємо кольори: фокус камери зробимо, наприклад, золотистим
            if i == 0: t_color = (255, 255, 0)      # Заголовок
            elif i == 3: t_color = (255, 215, 0)    # Фокус камери (Gold)
            elif i == 2: t_color = (100, 200, 255)  # Миша
            elif i == 1: t_color = (150, 255, 150)  # Гравець
            else: t_color = (255, 255, 255)         # Все інше
            
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
        
        box3_w = int(250 * scale) 
        box3_h = padding * 1.6 + len(help_lines) * line_h
        x_pos_help = win_w - box3_w - margin
        
        bg3 = Surface((box3_w, box3_h), SRCALPHA)
        bg3.fill((0, 0, 50, 200))
        screen.blit(bg3, (x_pos_help, margin))
        
        for i, line in enumerate(help_lines):
            t_c = (100, 200, 255) if i < 2 else (255, 255, 255)
            txt = ui_font.render(line, True, t_c)
            screen.blit(txt, (x_pos_help + padding, margin + padding + i * line_h))

def draw_end_screen(screen, title, subtitle, color):
    win_w, win_h = screen.get_size()
    
    # 1. Напівпрозорий фон (Overlay)
    overlay = Surface((win_w, win_h), SRCALPHA)
    # color[0], color[1], color[2] — це RGB, 180 — це прозорість
    overlay.fill((color[0], color[1], color[2], 180)) 
    screen.blit(overlay, (0, 0))

    # 2. Тексти
    font_big = font.SysFont("Arial", 60, bold=True)
    font_small = font.SysFont("Arial", 25)

    title_surf = font_big.render(title, True, (255, 255, 255))
    sub_surf = font_small.render(subtitle, True, (250, 250, 250))

    # 3. Центрування
    screen.blit(title_surf, (win_w // 2 - title_surf.get_width() // 2, win_h // 2 - 50))
    screen.blit(sub_surf, (win_w // 2 - sub_surf.get_width() // 2, win_h // 2 + 30))

#-----------------------------------------------------------------------#

player = Player(0, 0)
camera = Camera(800, 600)

platforms, portals, campfires, finish_obj, labels = load_game_world(FILE_PATH)
all_debug_objects = list(platforms) + list(portals) + list(campfires) + list(labels)
sync_portals_color(portals, player)

if campfires:
    first_fire = list(campfires)[0]
    player.respawn_pos = (first_fire.spawn_x, first_fire.spawn_y)
    player.respawn()


dev_mode = False
game_won = False
game_over = False
draw_start_pos = None
is_drawing_rect = False
run = True
current_rect_data = {"x": 0, "y": 0, "w": 0, "h": 0}
click_circle_pos = None
click_circle_timer = 0
camera_target = False
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
                        player.gravity_vec = Vector2(0, -1)  # Вгору
                    elif e.key == K_3:
                        player.gravity_vec = Vector2(-1, 0)  # Вліво
                    elif e.key == K_4:
                        player.gravity_vec = Vector2(1, 0)   # Вправо

                    if e.key == K_p:
                        camera_target = not camera_target
                        if camera_target: 
                            camera.set_focus(c_t_x, c_t_y) 
                        else:
                            camera.clear_focus()
                    
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

        if dev_mode:
            if e.type == MOUSEBUTTONDOWN and e.button == 1:
                is_drawing_rect = True
                m_x, m_y = e.pos
                draw_start_pos = (m_x - camera_offset[0], m_y - camera_offset[1])
                print(f"Координати натиску миші: {draw_start_pos}")

            if e.type == MOUSEBUTTONUP and e.button == 1:
                is_drawing_rect = False
                print(f"Креслення: {current_rect_data}")

            if e.type == MOUSEBUTTONDOWN and e.button == 3:
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

                        import json
                        print(json.dumps(out_data, ensure_ascii=False) + ",")
                        
                        click_circle_pos = e.pos
                        click_circle_timer = 15
                        break

    if game_over:
        keys = key.get_pressed()
        if keys[K_r]:
            player.respawn()
            game_over = False

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
    if not game_won and not game_over:
        player.handle_input()
        player.apply_physics(platforms, portals, width_window, height_window)
        if player.is_dead:   ###-
            game_over = True ###-
        player.update_visuals()
        finish_obj.check_interaction(player.rect)
        camera.update(player)

        if camera.focus_point:
            camera.update(None)
        else:
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

    for lbl in labels:
        lbl.draw(window, camera_offset)

    finish_obj.draw(window, camera_offset)
    player.draw(window, camera_offset)

    if dev_mode:
        draw.rect(window, (255, 255, 255), camera.dead_zone, 1)
        for obj in all_debug_objects:
            obj.draw_debug(window, True, camera_offset)
    
    if dev_mode and is_drawing_rect and draw_start_pos:
        m_pos = mouse.get_pos()
        curr_world_x = m_pos[0] - camera_offset[0]
        curr_world_y = m_pos[1] - camera_offset[1]

        rect_x = min(draw_start_pos[0], curr_world_x)
        rect_y = min(draw_start_pos[1], curr_world_y)
        rect_w = abs(curr_world_x - draw_start_pos[0])
        rect_h = abs(curr_world_y - draw_start_pos[1])
        
        current_rect_data = {"x": int(rect_x), "y": int(rect_y), "w": int(rect_w), "h": int(rect_h)}

        # ПЕРЕТВОРЮЄМО У КООРДИНАТИ ЕКРАНА (щоб ми бачили це на моніторі)
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

    if click_circle_timer > 0 and click_circle_pos:
        draw.circle(window, (0, 150, 255), click_circle_pos, 20, 3)
        draw.circle(window, (0, 200, 255), click_circle_pos, 5)
        
        click_circle_timer -= 1 # Зменшуємо таймер кожен кадр

    if game_over:
        draw_end_screen(window, "ГРА ЗАКІНЧЕНА", "Тисни R, щоб спробувати ще раз", (100, 0, 0))
    elif game_won:
        draw_end_screen(window, "ПЕРЕМОГА!", "Ти справжній LOGIK!", (0, 100, 0))

    draw_ui_boxes(window, player, dev_mode, camera_offset)

    # БАГ ФКІКС: Стара логіка предбачала що при дії стрибка анульовувати величинни вправо вліво, що призводило наче до запинання гравця (-паркур)
    #print(f"{player.vel.x:.2f}")

    # Оновлення кадру
    display.update()
    clk.tick(60) # Тримаємо стабільні 60 FPS. Більше людське око (в цій грі) не побачить.

quit()