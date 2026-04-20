from pygame import *
from classes import Player, Platform, TunnelPortal, JumpPad, Campfire
 
# --- ІНІЦІАЛІЗАЦІЯ ---
init()
window = display.set_mode((800, 600))
display.set_caption("Gravity Shift") # Назва, що звучить гордо
clk = time.Clock()

# Створюємо головного героя. Координати 400, 100 — це десь посередині зверху.
player = Player(400, 100)

# --- СВІТОБУДОВА ---
platforms = sprite.Group()
# Наша перша тестова платформа. Без неї гравець просто впаде в безодню.
test_rect = Platform(300, 400, 200, 50) 
platforms.add(test_rect)

portals = sprite.Group()

# Створюємо вертикальні портали. 
# Колір беремо з пресетів гравця, щоб візуально підказати: "Зайдеш сюди — станеш таким".
right_portal = TunnelPortal(200, 200, 30, 100, (1, 0), (100, 255, 100)) # Салатовий (Вправо)
portals.add(right_portal)
left_portal = TunnelPortal(600, 200, 30, 100, (-1, 0), (255, 200, 0))  # Золотий (Вліво)
portals.add(left_portal)

# Пади для стрибків (або зміни гравітації в польоті). Тонкі, щоб було важче влучити.
up_pad = JumpPad(20, 593, 70, 7, (0, -1), (255, 80, 80)) # Стеля стає підлогою
portals.add(up_pad)
down_pad = JumpPad(710, 0, 70, 7, (0, 1), (0, 255, 255)) # Повернення до нормальності
portals.add(down_pad)

# Точка збереження. side="left" означає, що гравець з'явиться зліва від багаття.
fire1 = Campfire(600, 570, side="left")
campfires = sprite.Group()
campfires.add(fire1)

# Перший запуск: ставимо точку респавну на багаття і відправляємо гравця туди.
player.respawn_pos = (fire1.spawn_x, fire1.spawn_y)
player.respawn()

run = True
while run:
    # --- ОБРОБКА ПОДІЙ ---
    for e in event.get():
        if e.type == QUIT: 
            run = False
        
            # Чит-коди для розробника: міняємо нравітацію натисканням цифр.
            if e.key == K_1: player.set_gravity(0, 1)   # Вниз
            if e.key == K_2: player.set_gravity(0, -1)  # Вгору
            if e.key == K_3: player.set_gravity(-1, 0)  # Вліво
            if e.key == K_4: player.set_gravity(1, 0)   # Вправо

            if e.type == KEYDOWN:
                if e.key == K_r:  # КНОПКА СМЕРТІ. Якщо застряг або просто набридло жити.
                    player.respawn()


            # Механіка Streetfly. Має ліміт — спалах є, інерція зникає.
            if e.key == K_LSHIFT or e.key == K_RSHIFT: 
                player.apply_streetfly()

            # Клавіша "M" для тих, кому не подобається стандартне керування.
            if e.key == K_m:
                player.switch_control_mode()

            # TAB — це стиль. Швидка зміна кольорової палітри (Classic <-> Cyber).
            if e.key == K_TAB:
                player.current_preset = "cyber" if player.current_preset == "classic" else "classic"
                player.update_color()

    # --- ЛОГІКА ВЗАЄМОДІЇ ---
    for fire in campfires:
        if fire.rect.colliderect(player.rect):
            # Кожного разу, коли проходимо крізь багаття, оновлюємо точку респавну.
            player.respawn_pos = (fire.spawn_x, fire.spawn_y)
    
    # ПЕРЕВІРКА НА ВИЛІТ ЗА МЕЖІ: 
    # Якщо ти випав за екран (смерть) — повертаємо до багаття.
    if player.rect.y > 600 or player.rect.y < -50 or player.rect.x > 800 or player.rect.x < -50:
        player.respawn()

    # Послідовність важлива: спочатку ввід, потім фізика, потім візуал.
    player.handle_input()
    player.apply_physics_wiht_window(platforms, portals)
    player.update_visuals()

    # --- МАЛЮВАННЯ ---
    window.fill((30, 30, 30)) # Темно-сірий фон, щоб очі не боліли
    
    # Малюємо об'єкти шарами: портали -> багаття -> платформи -> гравець.
    for p in portals:
        p.draw(window)
    for fire in campfires:
        fire.draw(window)
    
    platforms.draw(window) 
    player.draw(window)

    # Оновлення кадру
    display.update()
    clk.tick(60) # Тримаємо стабільні 60 FPS. Більше людське око (в цій грі) не побачить.

quit()