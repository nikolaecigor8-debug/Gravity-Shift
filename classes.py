import pygame
import random

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
        # --- ФІЗИЧНІ СТАТИ (Hitbox) ---
        self.size = 50
        self.rect = pygame.Rect(x, y, self.size, self.size) 
        
        # --- ХАРАКТЕРИСТИКИ ---
        self.speed = 6           # Швидкість бігу.        Не занадто повільно, щоб не нудити, не занадто швидко, щоб не "прошивати" стіни.
        self.jump_power = 16     # Потужність поштовху.   Дозволяє перелітати середні прірви.
        self.gravity_force = 0.6 # Константа прискорення. Чим більше — тим важчим здається кубик.
        
        # Напрям гравітації: (x,y). 
        # Це векторна магія: (0,1) тягне вниз, (0,-1) — до стелі. Вектор визначає, куди ми падаємо.
        self.gravity_vec = pygame.Vector2(0, 1) 
        
        # --- ФІЗИКА ---
        self.vel = pygame.Vector2(0, 0)
        self.on_ground = False # Прапорець-рятівник: без нього ми б могли стрибати прямо в повітрі (хоча це була б фіча як в Flappy Bird, а не баг).
        
        # --- ГРАФІКА (Fast Fall) ---
        self.is_fast_falling = False
        self.base_image = pygame.Surface((self.size, self.size))
        self.base_image.fill((0, 200, 255))
        self.image = self.base_image.copy()

        # --- СИСТЕМА КОЛЬОРІВ ---
        # Кожному напрямку — свій колір. Щоб гравець не забув, де в нього зараз підлога.
        self.presets = {
            "classic": {
                (0, 1): (0, 255, 255),  # Блакитний (класика)
                (0, -1): (255, 80, 80), # Корал (верх ногами)
                (-1, 0): (255, 200, 0), # Золотий (ліва стіна)
                (1, 0): (100, 255, 100) # Салатовий (права стіна)
            },
            "cyber": {
                (0, 1): (180, 0, 255),
                (0, -1): (255, 255, 0),
                (-1, 0): (0, 255, 255),
                (1, 0): (255, 150, 0) # Неоновий режим.
            },
            "random": {
                # Хаос-режим: кольори генеруються випадково. (ОДИН РАЗ НА ГРУ)
                (0, 1): (random.randint(1,225),random.randint(1,225),random.randint(1,225)),
                (0, -1): (random.randint(1,225),random.randint(1,225),random.randint(1,225)),
                (-1, 0): (random.randint(1,225),random.randint(1,225),random.randint(1,225)),
                (1, 0): (random.randint(1,225),random.randint(1,225),random.randint(1,225))
            }
        }
        self.current_preset = "classic"
        self.streetfly_flash = False # НЕ СКАЖУ!!!
        
        self.update_color()
        self.image = self.base_image.copy()

        # Режими керування: для тих, хто звик до стрілочок, і для WASD. (arrows_only, wasd_only, both)
        self.control_mode = "arrows_only" 

        self.respawn_pos = (x, y) # Координати останнього сейвпоінту (багаття)

    def handle_input(self):
            keys = pygame.key.get_pressed()
            
            # Гнучка система: вибираємо кнопки залежно від налаштувань режиму
            if self.control_mode == "both":
                move_left  = keys[pygame.K_LEFT]  or keys[pygame.K_a]
                move_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
                move_up    = keys[pygame.K_UP]    or keys[pygame.K_w]
                move_down  = keys[pygame.K_DOWN]  or keys[pygame.K_s]
            elif self.control_mode == "arrows_only":
                move_left, move_right = keys[pygame.K_LEFT], keys[pygame.K_RIGHT]
                move_up, move_down    = keys[pygame.K_UP],   keys[pygame.K_DOWN]
            else: # wasd_only
                move_left, move_right = keys[pygame.K_a], keys[pygame.K_d]
                move_up, move_down    = keys[pygame.K_w], keys[pygame.K_s]

            # 1. РУХ (перпендикулярно гравітації)
            # Якщо гравітація по Y (вгору/вниз), ми ходимо по X. Якщо по X — ходимо по Y. Логічно? Логічно.
            if self.gravity_vec.y != 0:
                self.vel.x = 0
                if move_left:  self.vel.x = -self.speed
                if move_right: self.vel.x = self.speed
            else:
                self.vel.y = 0
                if move_up:    self.vel.y = -self.speed
                if move_down:  self.vel.y = self.speed

            # 2. СТРИБОК ТА ПАДІННЯ
            # Тут ми визначаємо, яка кнопка зараз є "вгору" для стрибка, а яка "вниз" для прискорення.
            jump_press = False
            fall_press = False

            if self.gravity_vec   == (0, 1): jump_press, fall_press = move_up,    move_down
            elif self.gravity_vec == (0,-1): jump_press, fall_press = move_down,  move_up
            elif self.gravity_vec == (1, 0): jump_press, fall_press = move_left,  move_right
            elif self.gravity_vec == (-1,0): jump_press, fall_press = move_right, move_left

            # Стрибаємо тільки якщо під ногами відчуваємо тверду платформу (або край екрана)
            if jump_press and self.on_ground:
                self.vel = -self.gravity_vec * self.jump_power
                self.on_ground = False

            self.is_fast_falling = fall_press

    def switch_control_mode(self):
        """Циклічне перемикання між режимами керування. Для тих, хто не може визначитися."""
        modes = ["both", "arrows_only", "wasd_only"]
        current_idx = modes.index(self.control_mode)
        self.control_mode = modes[(current_idx + 1) % len(modes)]
        print(f"Поточний режим керування: {self.control_mode}")

    def set_gravity(self, x, y):
        """Зміна реальності: міняємо вектор тяжіння та перефарбовуємо гравця."""
        self.gravity_vec = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0) # Щоб не вилетіти в космос за інерцією при зміні фази
        self.update_color()

    def apply_physics_wiht_window(self, platforms, portals):
        """Ядро гри. Тут розраховуються всі зіткнення та сили."""
        self.on_ground = False # Спочатку вважаємо, що ми в польоті
        
        # 2. Гравітація та Fast Fall (швидке падіння)
        self.vel += self.gravity_vec * self.gravity_force
        if self.is_fast_falling:
            self.vel += self.gravity_vec * 2.0 # Додаткове прискорення "до підлоги"

        # --- ЕТАП Х (Горизонталь) ---
        self.rect.x += self.vel.x
        
        # Обмежувачі вікна (X): щоб гравець не став привидом і не пішов крізь монітор
        if self.rect.left < 0:
            self.rect.left = 0
            self.vel.x = 0
            if self.gravity_vec.x == -1: self.on_ground = True
        elif self.rect.right > 800:
            self.rect.right = 800
            self.vel.x = 0
            if self.gravity_vec.x == 1: self.on_ground = True

        # Колізії з платформами по X
        for wall in platforms:
            if self.rect.colliderect(wall.rect):
                if self.vel.x > 0: self.rect.right = wall.rect.left
                elif self.vel.x < 0: self.rect.left = wall.rect.right
                
                # Якщо гравітація горизонтальна і ми вперлися в стіну — це тепер наша підлога!
                if (self.vel.x * self.gravity_vec.x) > 0 or self.gravity_vec.x != 0:
                    self.on_ground = True
                self.vel.x = 0

        # --- ЕТАП Y (Вертикаль) ---
        self.rect.y += self.vel.y
        
        # Обмежувачі вікна (Y)
        if self.rect.top < 0:
            self.rect.top = 0
            self.vel.y = 0
            if self.gravity_vec.y == -1: self.on_ground = True
        elif self.rect.bottom > 600:
            self.rect.bottom = 600
            self.vel.y = 0
            if self.gravity_vec.y == 1: self.on_ground = True

        # Колізії з платформами по Y
        for wall in platforms:
            if self.rect.colliderect(wall.rect):
                # Визначаємо напрямок удару: головою чи ногами
                hit_dir = 1 if self.vel.y > 0 else -1
                
                if hit_dir == 1: self.rect.bottom = wall.rect.top
                else: self.rect.top = wall.rect.bottom

                # Важливий фікс: стаємо на землю ТІЛЬКИ якщо вектор падіння збігається з вектором гравітації.
                # Інакше можна було б "прилипати" до стелі, просто затиснувши стрибок.
                if hit_dir == self.gravity_vec.y:
                    self.on_ground = True
                
                self.vel.y = 0

        # ПЕРЕВІРКА ПОРТАЛІВ ТА ПАДІВ
        for portal in portals:
            portal.check_collision(self)

    def draw(self, screen):
        # Хитрість: малюємо картинку з центром у нашому логічному Rect.
        # Завдяки цьому ефекти розтягування (squash & stretch) виглядають природно.
        img_rect = self.image.get_rect(center=self.rect.center)
        screen.blit(self.image, img_rect)
    
    def update_color(self):
        """Беремо колір із вибраного пресета залежно від того, куди нас тягне гравітація."""
        color = self.presets[self.current_preset].get(tuple(self.gravity_vec), (255, 255, 255))
        self.base_image.fill(color)
        self.image = self.base_image.copy()

    def update_visuals(self):
            """Ефект 'резинки': візуальне задоволення від падіння."""
            if self.is_fast_falling and not self.on_ground:
                # Розтягуємо кубик по осі падіння і стискаємо по боках
                stretch, shrink = 1.4, 0.7
                if self.gravity_vec.y != 0:
                    new_w, new_h = int(self.size * shrink), int(self.size * stretch)
                else:
                    new_w, new_h = int(self.size * stretch), int(self.size * shrink)
                self.image = pygame.transform.scale(self.base_image, (new_w, new_h))
            else:
                # Повертаємо форму квадрата, коли ми спокійні або на землі
                self.image = self.base_image.copy()

            # ЕФЕКТ СТРІТФЛАЙ: короткий білий спалах, щоб гравець відчув "скидання" інерції.
            if self.streetfly_flash:
                self.image.fill((255, 255, 255)) 
                self.streetfly_flash = False

    def apply_streetfly(self):
        """Механіка Streetfly: рятувальний круг для обнулення швидкості в польоті."""
        self.vel = pygame.Vector2(0, 0)
        self.streetfly_flash = True 

    def respawn(self):
        """Повернення додому до багаття, коли рівень виявився сильнішим за тебе."""
        self.rect.topleft = self.respawn_pos
        self.vel = pygame.Vector2(0, 0)
        self.set_gravity(0, 1) # Скидаємо все на заводські налаштування (гравітація вниз)

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        # Платформа — це просто нерухомий сірий блок. Фундамент твого геймплею.
        self.image = pygame.Surface((w, h))
        self.image.fill((150, 150, 150)) 
        self.rect = self.image.get_rect(topleft=(x, y))

class TunnelPortal(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, target_gravity, color):
        super().__init__()
        # Портал — це тригер, який змінює фізику світу при проходженні крізь нього.
        self.rect = pygame.Rect(x, y, w, h)
        
        # Поділ на зону А і Б: щоб зрозуміти, що гравець дійсно ПЕРЕЙШОВ межу, а не просто торкнувся краю.
        self.rect_a = pygame.Rect(x, y, w // 2, h)
        self.rect_b = pygame.Rect(x + w // 2, y, w // 2, h)
        
        self.target_gravity = target_gravity
        self.color = color
        self.is_triggered = False

    def check_collision(self, player):
        # Якщо гравець накрив собою обидві "половинки" порталу — час міняти гравітацію.
        hit_a = self.rect_a.colliderect(player.rect)
        hit_b = self.rect_b.colliderect(player.rect)

        if hit_a and hit_b:
            if not self.is_triggered:
                player.set_gravity(*self.target_gravity)
                self.is_triggered = True
        elif not hit_a and not hit_b:
            # Скидаємо тригер, коли гравець повністю вийшов з порталу
            self.is_triggered = False

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

class JumpPad(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, target_gravity, color):
        super().__init__()
        # JumpPad — спрощена версія порталу. Достатньо просто доторкнутися.
        self.rect = pygame.Rect(x, y, w, h)
        self.target_gravity = target_gravity
        self.color = color
        self.is_triggered = False

    def check_collision(self, player):
        if self.rect.colliderect(player.rect):
            if not self.is_triggered:
                player.set_gravity(*self.target_gravity)
                self.is_triggered = True
        else:
            self.is_triggered = False

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

class Campfire(pygame.sprite.Sprite):
    def __init__(self, x, y, side="right"):
        super().__init__()
        # Багаття: затишок і безпека.
        self.rect = pygame.Rect(x, y, 50, 30)
        self.color = (255, 140, 0) # Помаранчевий вогник
        self.side = side
        
        # Смарт-спавн: вираховуємо, де поставити гравця після смерті, щоб він не застряг у вогні.
        offset = 20 
        player_w = 50 
        
        if self.side == "right":
            self.spawn_x = x + self.rect.width + offset
        else:
            self.spawn_x = x - player_w - offset
            
        self.spawn_y = y 

    def draw(self, screen):
        # Можна було б намалювати анімований вогонь, але поки що це стильний помаранчевий прямокутник.
        pygame.draw.rect(screen, self.color, self.rect)