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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "objects.json")

def load_game_world(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    platforms = sprite.Group()
    portals = sprite.Group()
    campfires = sprite.Group()

    # Нумеруємо платформи
    for i, p in enumerate(data.get("platforms", [])):
        platforms.add(Platform(p["x"], p["y"], p["w"], p["h"], obj_id=i))

    # Нумеруємо портали (продовжуємо або окрема нумерація)
    for i, p in enumerate(data.get("portals", [])):
        portals.add(TunnelPortal(p["x"], p["y"], p["w"], p["h"], p["target_gravity"], p["color"], obj_id=i))

    # Нумеруємо пад-стрибуни
    for i, j in enumerate(data.get("jump_pads", [])):
        portals.add(JumpPad(j["x"], j["y"], j["w"], j["h"], j["target_gravity"], j["color"], obj_id=i))

    # Нумеруємо багаття
    for i, c in enumerate(data.get("campfires", [])):
        campfires.add(Campfire(c["x"], c["y"], side=c["side"], obj_id=i))

    # Фініш залишаємо без ID (як ти і хотів)
    f_data = data.get("finish")
    finish = Finish(f_data["x"], f_data["y"], f_data["w"], f_data["h"]) if f_data else None

    return platforms, portals, campfires, finish

def sync_portals_color(portal_group, player_obj):
    """Оновлює всі портали та джамп-пади згідно з пресетом гравця"""
    for p in portal_group:
        if hasattr(p, 'update_color'):
            p.update_color(player_obj.presets, player_obj.current_preset)

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

                if e.key == K_1: player.set_gravity(0, 1)   # Вниз
                if e.key == K_2: player.set_gravity(0, -1)  # Вгору
                if e.key == K_3: player.set_gravity(-1, 0)  # Вліво
                if e.key == K_4: player.set_gravity(1, 0)   # Вправо
                if e.key == K_r:  # КНОПКА СМЕРТІ. Якщо застряг або просто набридло жити.
                    player.respawn()

                # Механіка Streetfly. Має ліміт — спалах є, інерція зникає.
                if e.key == K_LSHIFT or e.key == K_RSHIFT: 
                    player.apply_streetfly()

                # Клавіша "M" для тих, кому не подобається стандартне керування.
                if e.key == K_m:
                    player.switch_control_mode()

                # TAB — це скіни гравця. Швидка зміна кольорової палітри (Classic <-> Cyber).
                if e.key == K_TAB:
                    player.current_preset = "random" if player.current_preset == "classic" else "classic"
                    player.update_color()
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
    if (player.rect.right > 10005 or player.rect.left < -5 or 
        player.rect.bottom > 10005 or player.rect.top < -5):
        player.respawn()


    # Послідовність важлива: спочатку ввід, потім фізика, потім візуал.
    if not game_won:
        player.handle_input()
        player.apply_physics(platforms, portals)
        player.update_visuals()
        finish_obj.check_interaction(player.rect)
        camera.update(player)


    # --- МАЛЮВАННЯ ---
    window.fill((30, 30, 30))
    camera_offset = camera.camera.topleft

    # Малюємо тонку білу лінію по периметру всього світу
    world_border = Rect(0, 0, 10000, 10000).move(camera_offset)
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

    # Оновлення кадру
    display.update()
    clk.tick(60) # Тримаємо стабільні 60 FPS. Більше людське око (в цій грі) не побачить.

quit()