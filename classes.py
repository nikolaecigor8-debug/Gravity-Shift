# Привіт це мій гайд-записник який має намір допомогти розумітися і моїй ідеї цієї гри <3
# Основні параметри світу:
#   Розмір вікна: 800x600 пікселів.
#   Розмір гравця: 50x50 пікселів.
#   Координати: (0, 0) — лівий верхній кут. X зростає вправо, Y — вниз.
#
# Ігрові поняття:
#   Vector2 — Найголовніша фішка гри, вона має лише (0, 0)/(x, y) але це допомагає пк легко розуміти як прораховувати всі рухи по координатам.
#       Це дає грі міняти розуміння прощин для гравця, буквально перевертати гравітацію.    (   [0, 1]-Вниз,  [0, -1]-Вгору, [-1, 0]-Вліво, [1, 0]-Вправо   )
#       На цьому і побудована сама гра, міняти гравітацію щоб долати паркур і дійти до мети ВЕЛИКИХ червоних дверей. (поки це лише прямокутник але буде абстрактними)
#   Словник json — там ти знайдеш всі об'єкти моли дуже зручно там зберігаються і легко редагуються і всіх сенсах. Для цього я навіть додав dev_mode який вмикаєтсья на K_ESCAPE.
#       Цей мод відображає активність обєктів рамкою і також показує номер у словнику де він зберігається (зверни увагу що номер починається з 0-го і починається після назви об'єкта, цей номер і є всі характеристики)
#   Streetfly — Напевняк ви помітили в класі гравця Def apply_streetfly: Це прямо і буквально повторення гравітації Vector2 для того щоб анулити прискорення падіння. Це і дає тобі пролеціти довше.
# 
#  Об'єкти:
#   Player       - це гравець, зазвичай куб але він теж здатний редагуватися.
#   Platforms    - це чотирикутники які дають змогу гравцю стояти стрибати та впиратися на щось окрам вікна.
#   TunnelPortal - це двочастинові фігури (у грі це не помітно), розділені на дві тонші частини щоб при дотику на дві змінити гравітацію гравеві.
#   JumpPad      - також портал але діють негайно і задумані для лежання на площинах.
#   Campfires    - це багаття працює як точка збереження, спавнить поруч зправа або зліва залежно від налаштування. Має фіксовані розміри і безобмежену кількість копій. (тоді спавнити тебе буде останні дотичний до тебе) 
#   finish       - це фінал, великі червонеі двері що просять G для активації, закінчуючи гру і виводячи... Щоб там не було, але виводить..

# https://github.com/nikolaecigor8-debug/Gravity-Shift.git

import pygame
import random

class DebugSprite(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, obj_id=0):
        super().__init__()
        self.rect = pygame.Rect(x, y, w, h)
        self.obj_id = obj_id
        self.is_hovered = False
        self.font = pygame.font.SysFont("Consolas", 16, bold=True)

    def draw_debug(self, screen, dev_mode, camera_offset):
        if dev_mode:
            draw_rect = self.rect.move(camera_offset)

            color = (255, 255, 0) if self.is_hovered else (0, 150, 255)
            pygame.draw.rect(screen, color, draw_rect, 2)
            
            id_text = self.font.render(f"#{self.obj_id}", True, (255, 255, 255))
            
            bg_w = id_text.get_width() + 6
            bg_h = id_text.get_height() + 2
            bg_surface = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
            # Колір: (0,0,0) - чорний, 140 - рівень прозорості (півтінь)
            bg_surface.fill((0, 0, 0, 140)) 
            
            bg_surface.blit(id_text, (3, 1))
            
            bg_rect = bg_surface.get_rect(center=draw_rect.center) 
            screen.blit(bg_surface, bg_rect)

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
        # --- ФІЗИЧНІ СТАТИ (Hitbox) ---
        self.size = 50
        self.rect = pygame.Rect(x, y, self.size, self.size) 
        
        # --- ХАРАКТЕРИСТИКИ ---
        self.speed         = 7    # Швидкість бігу.        Не занадто повільно, щоб не нудити, не занадто швидко, щоб не "прошивати" стіни.
        self.jump_power    = 15   # Потужність поштовху.   Дозволяє перелітати середні прірви.
        self.gravity_force = 0.7  # Константа прискорення. Чим більше — тим важчим здається кубик.
        self.acceleration  = 1.0  # Як швидко ми розганяємося
        self.friction      = 0.4  # Як швидко ми зупиняємося (тертя)
        
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

        # 1. РУХ (перпендикулярно гравітації) з інерцією
        if self.gravity_vec.y != 0:
            # Рух по X (якщо гравітація вертикальна)
            if move_left:
                self.vel.x -= self.acceleration
            elif move_right:
                self.vel.x += self.acceleration
            else:
                self.vel.x *= self.friction # Плавна зупинка
            
            # Обмежуємо максимальну швидкість ходьби
            if abs(self.vel.x) > self.speed:
                self.vel.x = self.speed if self.vel.x > 0 else -self.speed
        else:
            # Рух по Y (якщо гравітація горизонтальна)
            if move_up:
                self.vel.y -= self.acceleration
            elif move_down:
                self.vel.y += self.acceleration
            else:
                self.vel.y *= self.friction # Плавна зупинка
            
            # Обмежуємо максимальну швидкість ходьби
            if abs(self.vel.y) > self.speed:
                self.vel.y = self.speed if self.vel.y > 0 else -self.speed

        # 2. СТРИБОК ТА ПАДІННЯ
        jump_press = False
        fall_press = False

        if self.gravity_vec   == (0, 1): jump_press, fall_press = move_up,    move_down
        elif self.gravity_vec == (0,-1): jump_press, fall_press = move_down,  move_up
        elif self.gravity_vec == (1, 0): jump_press, fall_press = move_left,  move_right
        elif self.gravity_vec == (-1,0): jump_press, fall_press = move_right, move_left

        # Стрибаємо тільки якщо під ногами відчуваємо тверду платформу
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
        """Міняємо вектор тяжіння та перефарбовуємо гравця."""
        self.gravity_vec = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.update_color()
# apply_physics_with_window - більше не буде, прощавайте старі межі!
    def apply_physics(self, platforms, portals, world_w, world_h):
            """Ядро гри. Розрахунок фізики та колізій у великому світі 10000x10000."""
            self.on_ground = False 
            
            gravity_step = self.gravity_vec * self.gravity_force
            self.vel += gravity_step

            current_max_speed = 50

            # Гравітація та Fast Fall
            if self.is_fast_falling:
                self.vel += gravity_step * 2.0
                current_max_speed = 100
            
            if self.vel.length() > current_max_speed:
                self.vel.scale_to_length(current_max_speed)

            # --- ЕТАП Х (Горизонталь) ---
            self.rect.x += self.vel.x
            
            # Жорсткі стіни світу по X
            if self.rect.left < 0:
                self.rect.left = 0
                self.vel.x = 0
                if self.gravity_vec.x == -1: self.on_ground = True
            elif self.rect.right > world_w:
                self.rect.right = world_w
                self.vel.x = 0
                if self.gravity_vec.x == 1: self.on_ground = True

            # Колізії з платформами по X (залишаємо без змін)
            for wall in platforms:
                if self.rect.colliderect(wall.rect):
                    if self.vel.x > 0: self.rect.right = wall.rect.left
                    elif self.vel.x < 0: self.rect.left = wall.rect.right
                    if (self.vel.x * self.gravity_vec.x) > 0 or self.gravity_vec.x != 0:
                        self.on_ground = True
                    self.vel.x = 0

            # --- ЕТАП Y (Вертикаль) ---
            self.rect.y += self.vel.y
            
            # Жорстка підлога та стеля світу по Y
            if self.rect.top < 0:
                self.rect.top = 0
                self.vel.y = 0
                if self.gravity_vec.y == -1: self.on_ground = True
            elif self.rect.bottom > world_h:
                self.rect.bottom = world_h
                self.vel.y = 0
                if self.gravity_vec.y == 1: self.on_ground = True

            # Колізії з платформами по Y (залишаємо без змін)
            for wall in platforms:
                if self.rect.colliderect(wall.rect):
                    hit_dir = 1 if self.vel.y > 0 else -1
                    if hit_dir == 1: self.rect.bottom = wall.rect.top
                    else: self.rect.top = wall.rect.bottom
                    if hit_dir == self.gravity_vec.y:
                        self.on_ground = True
                    self.vel.y = 0

            # Синхронізація позиції
            self.pos = pygame.Vector2(self.rect.topleft)

            # Перевірка порталів
            for portal in portals:
                portal.check_collision(self)

    def draw(self, screen, camera_offset):
        img_rect = self.image.get_rect(center=self.rect.center)
        screen.blit(self.image, img_rect.move(camera_offset))
    
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

class Platform(DebugSprite):
    def __init__(self, x, y, w, h, p_type="norm", obj_id=0):
        super().__init__(x, y, w, h, obj_id) # Викликаємо конструктор бази
        self.p_type = p_type
        self.image = pygame.Surface((w, h))
        self.image.fill((100, 100, 100))
        # Прикол тест нової необов'язкової опції в словнику якщо це за умовчанням тоді чорний :3
        if self.p_type == "norm":
            self.image.fill((100, 100, 100))
        else:
            self.image.fill((0, 0, 0))
            
    def draw(self, screen, camera_offset, dev_mode=False):
        screen.blit(self.image, self.rect.move(camera_offset))
        self.draw_debug(screen, dev_mode, camera_offset)

class TunnelPortal(DebugSprite):
    def __init__(self, x, y, target_gravity, w=None, h=None, color=(0, 0, 0), obj_id=0):
        # 1. АВТОМАТИЧНЕ ВИЗНАЧЕННЯ РОЗМІРІВ
        if w is None or h is None:
            if target_gravity[0] != 0: # Ліво [-1, 0] або Вправо [1, 0]
                w, h = 30, 100         #    |Вертикальний   портал|
            else:                      # Вгору [0, -1] або Вниз [0, 1]
                w, h = 100, 30         #    |Горизонтальний портал|

        super().__init__(x, y, w, h, obj_id)
        # Портал — це тригер, який змінює фізику світу при проходженні крізь нього.
        self.rect = pygame.Rect(x, y, w, h)
        
        # Поділ на зону А і Б: щоб зрозуміти, що гравець дійсно ПЕРЕЙШОВ межу, а не просто торкнувся краю.
        if w > h: 
            # Горизонтальний портал: ділимо по висоті (верхня і задня половини)
            self.rect_a = pygame.Rect(x, y, w, h // 2)
            self.rect_b = pygame.Rect(x, y + h // 2, w, h // 2)
        else:
            # Вертикальний портал: ділимо по ширині (ліва і права половини)
            self.rect_a = pygame.Rect(x, y, w // 2, h)
            self.rect_b = pygame.Rect(x + w // 2, y, w // 2, h)
        
        self.target_gravity = target_gravity
        self.color = color
        self.is_triggered = False

    def update_color(self, presets, current_preset):
        """Оновлюємо колір порталу відповідно до пресета гравця"""
        gravity_tuple = tuple(self.target_gravity)
        self.color = presets[current_preset].get(gravity_tuple, self.color) #

    def check_collision(self, player):
        # Механіка спрацювання: гравець має торкнутися обох зон одночасно
        hit_a = self.rect_a.colliderect(player.rect) 
        hit_b = self.rect_b.colliderect(player.rect)

        if hit_a and hit_b:
            if not self.is_triggered:
                player.set_gravity(*self.target_gravity)
                self.is_triggered = True
        elif not hit_a and not hit_b:
            # Скидаємо тригер лише коли гравець повністю вийшов з об'єкта
            self.is_triggered = False

    def draw(self, screen, camera_offset, dev_mode=False):
        draw_rect = self.rect.move(camera_offset)
        pygame.draw.rect(screen, self.color, draw_rect)
        self.draw_debug(screen, dev_mode, camera_offset)

class JumpPad(DebugSprite):
    def __init__(self, x, y, target_gravity, w=None, h=None, color=(0, 0, 0), obj_id=0):
        # JumpPad — спрощена версія порталу. Достатньо просто доторкнутися.
        if w is None or h is None:
            if target_gravity[1] != 0: # Гравітація вгору/вниз -> пад лежить горизонтально
                w, h = 70, 7
            else:                      # Гравітація вліво/вправо -> пад стоїть вертикально
                w, h = 7, 70

        super().__init__(x, y, w, h, obj_id)
        self.rect = pygame.Rect(x, y, w, h)
        self.target_gravity = target_gravity
        self.color = color
        self.is_triggered = False

    def update_color(self, presets, current_preset):
        gravity_tuple = tuple(self.target_gravity)
        self.color = presets[current_preset].get(gravity_tuple, self.color)

    def check_collision(self, player):
        if self.rect.colliderect(player.rect):
            if not self.is_triggered:
                player.set_gravity(*self.target_gravity)
                self.is_triggered = True
        else:
            self.is_triggered = False

    def draw(self, screen, camera_offset, dev_mode=False):
        draw_rect = self.rect.move(camera_offset)
        pygame.draw.rect(screen, self.color, draw_rect)
        self.draw_debug(screen, dev_mode, camera_offset)

class Campfire(DebugSprite):
    def __init__(self, x, y, side="center", obj_id=0):
        # Стандартний розмір багаття 50x30
        w, h = 50, 30
        super().__init__(x, y, w, h, obj_id)
        # Багаття: затишок і безпека.
        self.rect = pygame.Rect(x, y, w, h)
        self.color = (255, 140, 0) # Помаранчевий вогник
        self.side = side
        
        # Смарт-спавн: вираховуємо, де поставити гравця після смерті.
        offset = 20 
        player_w = 50 
        
        # ЛОГІКА РОЗУМНОГО СПАВНУ
        if self.side == "right":
            # Справа від багаття
            self.spawn_x = x + w + offset
        elif self.side == "left":
            # Зліва від багаття
            self.spawn_x = x - player_w - offset
        else:
            # По центру (center) або якщо вказано невірно
            self.spawn_x = x + (w // 2) - (player_w // 2)
        
        # БАГ ФІКС: Підняття спавну на тррохи вище дасть не втопитися в платформу що в наслідку кине тебе з неї (зправа або зліва, через роботу фізики)
        self.spawn_y = y - 20

    def draw(self, screen, camera_offset, dev_mode=False):
        # Можна було б намалювати анімований вогонь, але поки що це стильний помаранчевий прямокутник.
        draw_rect = self.rect.move(camera_offset)
        pygame.draw.rect(screen, self.color, draw_rect)
        
        # Якщо увімкнено dev_mode, можна малювати крапку, де саме з'явиться гравець
        if dev_mode:
            spawn_point = (self.spawn_x + camera_offset[0] + 25, self.spawn_y + camera_offset[1] + 25)
            pygame.draw.circle(screen, (0, 255, 0), spawn_point, 5)
            
        self.draw_debug(screen, dev_mode, camera_offset)

class Finish(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill((255, 0, 0))  # Ядерно-червоний
        self.rect = self.image.get_rect(topleft=(x, y))
        
        self.is_active = False # Чи стоїть гравець у дверях
        self.font = pygame.font.SysFont("Arial", 20, bold=True)
        self.prompt_text = self.font.render("Press G", True, (255, 255, 255))

    def check_interaction(self, player_rect):
        # Перевіряємо, чи гравець у зоні дверей
        self.is_active = self.rect.colliderect(player_rect)
        return self.is_active

    def draw(self, screen, camera_offset):
        screen.blit(self.image, self.rect.move(camera_offset))
        if self.is_active:
            # Малюємо "G" трохи вище середини
            draw_rect = self.rect.move(camera_offset)
            prompt_x = draw_rect.centerx - self.prompt_text.get_width() // 2
            prompt_y = draw_rect.centery - 35
            screen.blit(self.prompt_text, (prompt_x, prompt_y))

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        # Повертаємо новий прямокутник, зсунутий на координати камери
        return entity.rect.move(self.camera.topleft)

    def update(self, target):
        screen = pygame.display.get_surface()
        screen_w, screen_h = screen.get_size()

        x = -target.rect.centerx + (screen_w // 2)
        y = -target.rect.centery + (screen_h // 2)
        
        self.camera = pygame.Rect(x, y, screen_w, screen_h)
