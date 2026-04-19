from pygame import *
from classes import Player, Platform

init()
window = display.set_mode((800, 600))
display.set_caption("Gravity Shift")
clk = time.Clock()

player = Player(400, 100)

platforms = sprite.Group()
test_rect = Platform(300, 400, 200, 50) 
platforms.add(test_rect)

run = True
while run:
    for e in event.get():
        if e.type == QUIT: 
            run = False

        # Коди зміни гравітації
        if e.type == KEYDOWN:
            if e.key == K_1: player.set_gravity(0, 1)   # Вниз
            if e.key == K_2: player.set_gravity(0, -1)  # Вгору
            if e.key == K_3: player.set_gravity(-1, 0)  # Вліво
            if e.key == K_4: player.set_gravity(1, 0)   # Вправо
            #

            if e.key == K_f or e.key == K_RSHIFT: player.apply_streetfly()   # БАГ КНОПКА НЕ ЮЗАТИ ПРИ ПАДІННІ :3

            if e.key == K_TAB:
                player.current_preset = "cyber" if player.current_preset == "classic" else "classic"
                player.update_color()

    # Логіка
    player.handle_input()
    player.apply_physics_wiht_window(platforms)
    player.update_visuals()

    # Малювання
    window.fill((30, 30, 30))
    
    # Малюємо всі платформи з групи
    platforms.draw(window) 
    player.draw(window)

    display.update()
    clk.tick(60)

quit()