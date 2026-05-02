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
        self.speed         = 7    # Швидкість бігу.
        self.jump_power    = 15   # Потужність поштовху.
        self.gravity_force = 0.7  # Константа прискорення.
        self.acceleration  = 1.0  # Як швидко ми розганяємося
        self.friction      = 0.4  # Як швидко ми зупиняємося (тертя)
        
        # Напрям гравітації: (x,y). 
        # Це векторна магія: (0,1) тягне вниз, (0,-1) — до стелі. Вектор визначає, куди ми падаємо.
        self.gravity_vec = pygame.Vector2(0, 1) 
        
        # --- ФІЗИКА ---
        self.vel = pygame.Vector2(0, 0)
        self.on_ground = False
        self.is_on_ice = False
        self.is_dead = False

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
        self.control_mode = "both" 

        self.respawn_pos = (x, y) # Координати останнього сейвпоінту


    def switch_skin(self):
        """Динамічне перемикання скінів по колу через словник presets"""
        skin_names = list(self.presets.keys())
        current_idx = skin_names.index(self.current_preset)
        next_idx = (current_idx + 1) % len(skin_names)
        
        self.current_preset = skin_names[next_idx]
        self.update_color()
        print(f"Поточний скін: {self.current_preset}")


    def handle_input(self):
        keys = pygame.key.get_pressed()

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

        current_friction = 0.95 if self.is_on_ice else self.friction

        # 1. РУХ (перпендикулярно гравітації) з інерцією
        if self.gravity_vec.y != 0:
            # Рух по X (якщо гравітація вертикальна)
            if move_left:
                self.vel.x -= self.acceleration
            elif move_right:
                self.vel.x += self.acceleration
            else:
                self.vel.x *= current_friction
            
            if abs(self.vel.x) > self.speed:
                self.vel.x = self.speed if self.vel.x > 0 else -self.speed
        else:
            # Рух по Y (якщо гравітація горизонтальна)
            if move_up:
                self.vel.y -= self.acceleration
            elif move_down:
                self.vel.y += self.acceleration
            else:
                self.vel.y *= self.friction
            
            if abs(self.vel.y) > self.speed:
                self.vel.y = self.speed if self.vel.y > 0 else -self.speed

        # 2. СТРИБОК ТА ПАДІННЯ
        jump_press = False
        fall_press = False

        if self.gravity_vec   == (0, 1): jump_press, fall_press = move_up,    move_down
        elif self.gravity_vec == (0,-1): jump_press, fall_press = move_down,  move_up
        elif self.gravity_vec == (1, 0): jump_press, fall_press = move_left,  move_right
        elif self.gravity_vec == (-1,0): jump_press, fall_press = move_right, move_left

        if jump_press and self.on_ground:
            jump_velocity = -self.gravity_vec * self.jump_power
            
            if self.gravity_vec.y != 0:
                self.vel.y = jump_velocity.y
            else:
                self.vel.x = jump_velocity.x
                
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
        limit = 12
        # Бувай пластикова фізика яка відчувалася як удар об стінку!
        # self.vel = pygame.Vector2(0, 0)
        if self.vel.length() > limit:
            self.vel.scale_to_length(limit)
        self.update_color()

# apply_physics_with_window - більше не буде, прощавайте старі межі!
    def apply_physics(self, platforms, portals, world_w, world_h):
            """Ядро гри. Розрахунок фізики та колізій у великому світі 10000x10000."""
            self.on_ground = False 
            self.is_on_ice = False
            
            gravity_step = self.gravity_vec * self.gravity_force
            self.vel += gravity_step

            current_max_speed = 50
            nearby_rect = self.rect.inflate(9000, 600)
            active_platforms = [p for p in platforms if p.rect.colliderect(nearby_rect)]

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

            # Колізії з платформами по X
            for wall in active_platforms:
                if self.rect.colliderect(wall.rect):
                    if self.vel.x > 0: self.rect.right = wall.rect.left
                    elif self.vel.x < 0: self.rect.left = wall.rect.right
                    if wall.p_type == "ice":
                        self.is_on_ice = True
                    if wall.p_type == "death":
                        self.is_dead = True
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

            # Колізії з платформами по Y
            for wall in active_platforms:
                if self.rect.colliderect(wall.rect):
                    hit_dir = 1 if self.vel.y > 0 else -1
                    if hit_dir == 1: self.rect.bottom = wall.rect.top
                    else: self.rect.top = wall.rect.bottom
                    if wall.p_type == "ice":
                        self.is_on_ice = True
                    if wall.p_type == "death":
                        self.is_dead = True
                    if hit_dir == self.gravity_vec.y:
                        self.on_ground = True
                    self.vel.y = 0

            self.pos = pygame.Vector2(self.rect.topleft)

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
                # Розтягування кубика по осі падіння
                stretch, shrink = 1.4, 0.7
                if self.gravity_vec.y != 0:
                    new_w, new_h = int(self.size * shrink), int(self.size * stretch)
                else:
                    new_w, new_h = int(self.size * stretch), int(self.size * shrink)
                self.image = pygame.transform.scale(self.base_image, (new_w, new_h))
            else:
                self.image = self.base_image.copy()

            # ЕФЕКТ СТРІТФЛАЙ: короткий білий спалах.
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
        self.set_gravity(0, 1)
        self.is_dead = False


    def get_gravity_info(self):
        """Повертає назву напрямку та поточний колір гравця для тексту."""
        names = {
            (0, 1): "ВНИЗ",
            (0,-1): "ВГОРУ",
            (-1,0): "ВЛІВО",
            (1, 0): "ВПРАВО"
        }
        direction = names.get(tuple(self.gravity_vec), "???")
        color = self.presets[self.current_preset].get(tuple(self.gravity_vec), (255, 255, 255))
        return direction, color


class Platform(DebugSprite):
    def __init__(self, x, y, w, h, p_type="norm", obj_id=0):
        super().__init__(x, y, w, h, obj_id)
        self.p_type = p_type
        self.image = pygame.Surface((w, h))
        self.image.fill((80, 80, 80))
        # Прикол тест нової необов'язкової опції в словнику якщо це за умовчанням тоді чорний :3
        if self.p_type == "norm":
            self.image.fill((100, 100, 100)) # Звичайна - сіра
        elif self.p_type == "ice":
            self.image.fill((170, 210, 210)) # Крижана - сіро-блакитна
        elif self.p_type == "death":
            self.image.fill((120, 0, 0))     # Темно-червоний
        else:
            self.image.fill((0, 0, 0))       # Білий


    def draw(self, screen, camera_offset, dev_mode=False):
        screen.blit(self.image, self.rect.move(camera_offset))
        self.draw_debug(screen, dev_mode, camera_offset)


class TunnelPortal(DebugSprite):
    def __init__(self, x, y, target_gravity, w=None, h=None, color=(0, 0, 0), obj_id=0):
        if w is None or h is None:
            if target_gravity[0] != 0: # Ліво [-1, 0] або Вправо [1, 0]
                w, h = 40, 120         #    |Вертикальний   портал|
            else:                      # Вгору [0, -1] або Вниз [0, 1]
                w, h = 120, 40         #    |Горизонтальний портал|

        super().__init__(x, y, w, h, obj_id)
        # Портал — це тригер, який змінює фізику світу при проходженні крізь нього.
        self.rect = pygame.Rect(x, y, w, h)
        
        # Поділ на зону А і Б: щоб зрозуміти, що гравець дійсно ПЕРЕЙШОВ межу, а не просто торкнувся краю.
        if w > h: 
            self.rect_a = pygame.Rect(x, y, w, h // 2)
            self.rect_b = pygame.Rect(x, y + h // 2, w, h // 2)
        else:
            self.rect_a = pygame.Rect(x, y, w // 2, h)
            self.rect_b = pygame.Rect(x + w // 2, y, w // 2, h)
        
        self.target_gravity = target_gravity
        self.color = color
        self.is_triggered = False


    def update_color(self, presets, current_preset):
        """Оновлюється колір порталу відповідно до пресета гравця"""
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
            self.is_triggered = False


    def draw(self, screen, camera_offset, dev_mode=False):
        draw_rect = self.rect.move(camera_offset)
        pygame.draw.rect(screen, self.color, draw_rect)
        self.draw_debug(screen, dev_mode, camera_offset)


class JumpPad(DebugSprite):
    def __init__(self, x, y, target_gravity, w=None, h=None, color=(0, 0, 0), obj_id=0):
        if w is None or h is None:
            if target_gravity[1] != 0: 
                w, h = 70, 7      # Гравітація  вгору/вниз  -> пад горизонтальний
            else:                      
                w, h = 7, 70      # Гравітація вліво/вправо -> пад вертикальний

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
        
        offset = 20 
        player_w = 50 
        
        # ЛОГІКА РОЗУМНОГО СПАВНУ
        if self.side == "right":
            self.spawn_x = x + w + offset
        elif self.side == "left":
            self.spawn_x = x - player_w - offset
        else:
            # Спавнить по центру, якщо вказано невірно
            self.spawn_x = x + (w // 2) - (player_w // 2)
        
        # БАГ ФІКС: Підняття спавну на тррохи вище дасть не втопитися в платформу що в наслідку кине тебе з неї (зправа або зліва, через роботу фізики)
        self.spawn_y = y - 20


    def draw(self, screen, camera_offset, dev_mode=False):
        # Можна було б намалювати анімований вогонь, але поки що це стильний помаранчевий прямокутник.
        draw_rect = self.rect.move(camera_offset)
        pygame.draw.rect(screen, self.color, draw_rect)  
        self.draw_debug(screen, dev_mode, camera_offset)


class Finish(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill((255, 0, 0))  # Ядерно-червоний
        self.rect = self.image.get_rect(topleft=(x, y))
        
        self.is_active = False
        self.font = pygame.font.SysFont("Arial", 20, bold=True)
        self.prompt_text = self.font.render("Press G", True, (255, 255, 255))


    def check_interaction(self, player_rect):
        self.is_active = self.rect.colliderect(player_rect)
        return self.is_active


    def draw(self, screen, camera_offset):
        screen.blit(self.image, self.rect.move(camera_offset))
        if self.is_active:
            draw_rect = self.rect.move(camera_offset)
            prompt_x = draw_rect.centerx - self.prompt_text.get_width() // 2
            prompt_y = draw_rect.centery - 35
            screen.blit(self.prompt_text, (prompt_x, prompt_y))


class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.dead_zone = pygame.Rect(200, 150, 400, 300)
        self.lerp_speed = 0.05 
        # НОВЕ: Точка фіксації для презентацій (якщо None — камера стежить за гравцем)
        self.focus_point = None 


    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)


    def update(self, target):
        screen = pygame.display.get_surface()
        screen_w, screen_h = screen.get_size()

        if self.focus_point:
            # Режим презентації: ціль — координати
            target_center_x, target_center_y = self.focus_point
        else:
            # Звичайний режим:   ціль — гравець
            target_center_x, target_center_y = target.rect.centerx, target.rect.centery

            player_on_screen_x = target.rect.centerx + self.camera.x
            player_on_screen_y = target.rect.centery + self.camera.y

            self.dead_zone.width = screen_w * 0.4
            self.dead_zone.height = screen_h * 0.4
            self.dead_zone.center = (screen_w // 2, screen_h // 2)

            if player_on_screen_x < self.dead_zone.left:
                self.camera.x += self.dead_zone.left - player_on_screen_x
            elif player_on_screen_x > self.dead_zone.right:
                self.camera.x -= player_on_screen_x - self.dead_zone.right

            if player_on_screen_y < self.dead_zone.top:
                self.camera.y += self.dead_zone.top - player_on_screen_y
            elif player_on_screen_y > self.dead_zone.bottom:
                self.camera.y -= player_on_screen_y - self.dead_zone.bottom

        ideal_x = -target_center_x + (screen_w // 2)
        ideal_y = -target_center_y + (screen_h // 2)
        
        self.camera.x += (ideal_x - self.camera.x) * self.lerp_speed
        self.camera.y += (ideal_y - self.camera.y) * self.lerp_speed

class WorldLabel(DebugSprite):
    def __init__(self, text, x, y, size=20, color=(255, 255, 255), bg_alpha=0, obj_id=0):
        self.font_label = pygame.font.SysFont("Consolas", size, bold=True)
        self.text_surf = self.font_label.render(text, True, color)
        
        w, h = self.text_surf.get_size()
        
        super().__init__(x, y, w, h, obj_id)
        
        self.bg_alpha = bg_alpha
        if self.bg_alpha > 0:
            self.bg_surf = pygame.Surface((w + 10, h + 6), pygame.SRCALPHA)
            self.bg_surf.fill((0, 0, 0, self.bg_alpha))
        else:
            self.bg_surf = None

    def draw(self, screen, camera_offset, dev_mode=False):
        draw_pos = self.rect.move(camera_offset)
        if self.bg_surf:
            screen.blit(self.bg_surf, (draw_pos.x - 5, draw_pos.y - 3))
        screen.blit(self.text_surf, draw_pos)
        self.draw_debug(screen, dev_mode, camera_offset)

