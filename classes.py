import pygame
import random

def random_color():
    # Випадковий колір для хаосу-пресета гравця.
    return (random.randint(1, 225), random.randint(1, 225), random.randint(1, 225))

def random_preset():
    return {
        (0, 1): random_color(),
        (0, -1): random_color(),
        (-1, 0): random_color(),
        (1, 0): random_color()
    }

class DebugSprite(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, obj_id=0):
        super().__init__()
        self.rect = pygame.Rect(x, y, w, h)
        self.obj_id = obj_id
        self.is_hovered = False
        self.font = pygame.font.SysFont("Consolas", 16, bold=True)

    def draw_debug(self, screen, dev_mode, camera_offset):
        if not dev_mode:
            return

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
    GRAVITY_NAMES = {
        (0, 1): "ВНИЗ",
        (0, -1): "ВГОРУ",
        (-1, 0): "ВЛІВО",
        (1, 0): "ВПРАВО"
    }

    CONTROL_MODES = ("both", "arrows_only", "wasd_only")
    GRAVITY_ACTIONS = {
        (0, 1): ("up", "down"),
        (0, -1): ("down", "up"),
        (1, 0): ("left", "right"),
        (-1, 0): ("right", "left")
    }

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
        # Кожному напрямку — свій колір. Це допомагає орієнтуватися, куди зараз тягне.
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
            "random": random_preset()
        }
        self.current_preset = "classic"
        self.streetfly_flash = False # НЕ СКАЖУ!!!

        self.update_color()

        # Режими керування: для тих, хто звик до стрілочок, і для WASD. (arrows_only, wasd_only, both)
        self.control_mode = "both"
        self.respawn_pos = (x, y) # Координати останнього сейвпоінту

    def switch_skin(self):
        """Динамічне перемикання скінів по колу через словник presets."""
        skin_names = list(self.presets.keys())
        self.current_preset = skin_names[(skin_names.index(self.current_preset) + 1) % len(skin_names)]
        self.update_color()
        print(f"Поточний скін: {self.current_preset}")

    def read_input(self, keys):
        """Знає які клавіші - керування, залежно від вибраного режиму керування."""
        if self.control_mode == "arrows_only":
            return (
                keys[pygame.K_LEFT],
                keys[pygame.K_RIGHT],
                keys[pygame.K_UP],
                keys[pygame.K_DOWN]
            )
        if self.control_mode == "wasd_only":
            return (
                keys[pygame.K_a],
                keys[pygame.K_d],
                keys[pygame.K_w],
                keys[pygame.K_s]
            )
        return (
            keys[pygame.K_LEFT] or keys[pygame.K_a],
            keys[pygame.K_RIGHT] or keys[pygame.K_d],
            keys[pygame.K_UP] or keys[pygame.K_w],
            keys[pygame.K_DOWN] or keys[pygame.K_s]
        )

    def handle_input(self):
        move_left, move_right, move_up, move_down = self.read_input(pygame.key.get_pressed())
        friction_value = 0.95 if self.is_on_ice else self.friction

        if self.gravity_vec.y != 0: # Рух по X (якщо гравітація вертикальна)
            self.apply_axis_motion("x", move_left, move_right, friction_value)
        else:                       # Рух по Y (якщо гравітація горизонтальна)
            self.apply_axis_motion("y", move_up, move_down, self.friction)

        self.apply_jump_and_fall(move_left, move_right, move_up, move_down)

    def apply_axis_motion(self, axis, negative_pressed, positive_pressed, friction):
        """Прораховує вже передбачені вісі для рівного та фіксованого pyxy."""
        velocity = getattr(self.vel, axis)
        if negative_pressed:
            velocity -= self.acceleration
        elif positive_pressed:
            velocity += self.acceleration
        else:
            velocity *= friction

        max_speed = self.speed
        setattr(self.vel, axis, max(-max_speed, min(max_speed, velocity)))

    def apply_jump_and_fall(self, move_left, move_right, move_up, move_down):
        gravity_tuple = (int(self.gravity_vec.x), int(self.gravity_vec.y))
        jump_key, fall_key = self.GRAVITY_ACTIONS.get(gravity_tuple, (None, None))
        key_map = {
            "left": move_left,
            "right": move_right,
            "up": move_up,
            "down": move_down
        }

        jump_press = key_map.get(jump_key, False)
        fall_press = key_map.get(fall_key, False)

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
        current_index = self.CONTROL_MODES.index(self.control_mode)
        self.control_mode = self.CONTROL_MODES[(current_index + 1) % len(self.CONTROL_MODES)]
        print(f"Поточний режим керування: {self.control_mode}")

    def set_gravity(self, x, y):
        """Міняємо вектор тяжіння та перефарбовуємо гравця."""
        self.gravity_vec.update(x, y)
        if self.vel.length() > 12:
            self.vel.scale_to_length(12)
        self.update_color()

    def get_active_platforms(self, platforms):
        # Головна користа фішка гри. Не прораховувати колізії об'єктів які поза екраном
        # (Для гравця різниця не помітна а для пк шанс не закипіти від всіх об'єктів світу)
        visible_area = self.rect.inflate(9000, 600)
        return [p for p in platforms if p.rect.colliderect(visible_area)]

    def limit_speed(self, max_speed):
        if self.vel.length() > max_speed:
            self.vel.scale_to_length(max_speed)

    def apply_physics(self, platforms, portals, world_w, world_h):
        """Ядро гри. Розрахунок фізики та колізій у великому світі."""
        self.on_ground = False
        self.is_on_ice = False

        gravity_step = self.gravity_vec * self.gravity_force
        self.vel += gravity_step

        max_speed = 100 if self.is_fast_falling else 50
        if self.is_fast_falling:
            self.vel += gravity_step * 2.0
        self.limit_speed(max_speed)

        # Враховуємо лише платформи, які знаходяться поруч, для оптимізації.
        active_platforms = self.get_active_platforms(platforms)
        self.move_axis("x", active_platforms, world_w)
        self.move_axis("y", active_platforms, world_h)

        self.pos = pygame.Vector2(self.rect.topleft)
        for portal in portals:
            portal.check_collision(self)

    def move_axis(self, axis, platforms, limit):
        # Раніше це було прямов в apply_physics, але виніс в окрему функцію, 
        #       щоб розмежувати логіку. (Передбачаю при великому коді буде помилок)
        delta = getattr(self.vel, axis)
        # getattr - це як магія, яка дозволяє звертатися до vel.x або vel.y через змінну axis.
        #       З'єднує значення в дужках міняючи , на . (self.vel.axis)

        # Жорсткі стіни світу по X
        if axis == "x":
            self.rect.x += delta
            if self.rect.left < 0:
                self.rect.left = 0
                self.vel.x = 0
                if self.gravity_vec.x == -1:
                    self.on_ground = True
            elif self.rect.right > limit:
                self.rect.right = limit
                self.vel.x = 0
                if self.gravity_vec.x == 1:
                    self.on_ground = True
        else:
            # Жорстка підлога та стеля світу по Y
            self.rect.y += delta
            if self.rect.top < 0:
                self.rect.top = 0
                self.vel.y = 0
                if self.gravity_vec.y == -1:
                    self.on_ground = True
            elif self.rect.bottom > limit:
                self.rect.bottom = limit
                self.vel.y = 0
                if self.gravity_vec.y == 1:
                    self.on_ground = True

        # Колізії з платформами
        for wall in platforms:
            if not self.rect.colliderect(wall.rect):
                continue
            self.resolve_platform_collision(wall, axis, delta)

    def resolve_platform_collision(self, wall, axis, delta):
        ''' Багато обраховуюча функція прорахунків заткнень з різними типами платформ. 
                Враховує напрямок удару та тип платформи для правильного реагування.'''
        hit_dir = 0
        # Визначаємо напрямок удару: 
        #       1 - рух у напрямку гравітації,
        #      -1 - проти гравітації.
        # Це допомагає зрозуміти, чи ми приземляємося на платформу або вдаряємося об неї знизу чи збоку.
        if delta > 0:
            hit_dir = 1
        elif delta < 0:
            hit_dir = -1

        if axis == "x":
            if hit_dir > 0:
                self.rect.right = wall.rect.left
            elif hit_dir < 0:
                self.rect.left = wall.rect.right
        else:
            if hit_dir > 0:
                self.rect.bottom = wall.rect.top
            elif hit_dir < 0:
                self.rect.top = wall.rect.bottom

        # Раекції правда чи ні для різних типів платформ. 
        #   Звичайна платформа - просто зупинка
        #   Лід - ковзання, 
        #   смерть - смерть, 
        if wall.p_type == "ice":
            self.is_on_ice = True
        if wall.p_type == "death":
            self.is_dead = True

        if axis == "x" and hit_dir == self.gravity_vec.x:
            self.on_ground = True
        if axis == "y" and hit_dir == self.gravity_vec.y:
            self.on_ground = True

        if axis == "x":
            self.vel.x = 0
        else:
            self.vel.y = 0

    def draw(self, screen, camera_offset):
        img_rect = self.image.get_rect(center=self.rect.center)
        screen.blit(self.image, img_rect.move(camera_offset))

    def update_color(self):
        """Береться колір із вибраного пресета залежно від того, куди є гравітація."""
        gravity_key = (int(self.gravity_vec.x), int(self.gravity_vec.y))
        color = self.presets[self.current_preset].get(gravity_key, (255, 255, 255))
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
        """Повернення додому до багаття, коли рівень виявився сильнішим за тебе..."""
        self.rect.topleft = self.respawn_pos
        self.vel = pygame.Vector2(0, 0)
        self.set_gravity(0, 1)
        self.is_dead = False

    def get_gravity_info(self):
        """Повертає назву напрямку та поточний колір гравця для тексту."""
        gravity_key = (int(self.gravity_vec.x), int(self.gravity_vec.y))
        direction = self.GRAVITY_NAMES.get(gravity_key, "???:")
        color = self.presets[self.current_preset].get(gravity_key, (255, 255, 255))
        return direction, color


class Platform(DebugSprite):
    COLOR_MAP = {
        "norm": (100, 100, 100), # Звичайна   - сіра
        "ice": (170, 210, 210),  # Крижана    - сіро-блакитна
        "death": (120, 0, 0)     # Смертельна - темно-червоний
    }

    def __init__(self, x, y, w, h, p_type="norm", obj_id=0):
        super().__init__(x, y, w, h, obj_id)
        self.p_type = p_type
        self.image = pygame.Surface((w, h))
        # Раніше тут був IF ELSE для кожного скіна, 
        #   але це не оптимально тому його мінятиме словник COLOR_MAP.
        self.image.fill(self.COLOR_MAP.get(p_type, (0, 0, 0)))  # (0, 0, 0) - тут як сейв що каже про "не знайшов"

    def draw(self, screen, camera_offset, dev_mode=False):
        screen.blit(self.image, self.rect.move(camera_offset))
        self.draw_debug(screen, dev_mode, camera_offset)


class GravityTrigger(DebugSprite):
    ''''Базовий клас для o6'єктів, які змінюють гравітацію.
           Син DebugSprite i Батько всім портальним штукам.'''
    def __init__(self, x, y, w, h, target_gravity, color, obj_id=0):
        super().__init__(x, y, w, h, obj_id)
        self.target_gravity = target_gravity
        self.color = color
        self.is_triggered = False

    def update_color(self, presets, current_preset):
        self.color = presets[current_preset].get(tuple(self.target_gravity), self.color)

    def draw(self, screen, camera_offset, dev_mode=False):
        draw_rect = self.rect.move(camera_offset)
        pygame.draw.rect(screen, self.color, draw_rect)
        self.draw_debug(screen, dev_mode, camera_offset)


class TunnelPortal(GravityTrigger):
    def __init__(self, x, y, target_gravity, w=None, h=None, color=(0, 0, 0), obj_id=0):
        if w is None or h is None:
            if target_gravity[0] != 0: # Ліво [-1, 0] або Вправо [1, 0]
                w, h = 40, 120         #    |Вертикальний   портал|
            else:                      # Вгору [0, -1] або Вниз [0, 1]
                w, h = 120, 40         #    |Горизонтальний портал|

        super().__init__(x, y, w, h, target_gravity, color, obj_id)
        # Портал — це тригер, який змінює фізику світу при проходженні крізь нього.
        self.rect = pygame.Rect(x, y, w, h)

        # Поділ на зону А і Б: щоб зрозуміти, що гравець дійсно ПЕРЕЙШОВ межу, а не просто торкнувся краю.
        if w > h: 
            self.rect_a = pygame.Rect(x, y, w, h // 2)
            self.rect_b = pygame.Rect(x, y + h // 2, w, h // 2)
        else:
            self.rect_a = pygame.Rect(x, y, w // 2, h)
            self.rect_b = pygame.Rect(x + w // 2, y, w // 2, h)

    def check_collision(self, player):
        # Механіка спрацювання: гравець має торкнутися обох зон одночасно
        hit_a = self.rect_a.colliderect(player.rect)
        hit_b = self.rect_b.colliderect(player.rect)

        if hit_a and hit_b and not self.is_triggered:
            player.set_gravity(*self.target_gravity)
            self.is_triggered = True
        elif not hit_a and not hit_b:
            self.is_triggered = False


class JumpPad(GravityTrigger):
    def __init__(self, x, y, target_gravity, w=None, h=None, color=(0, 0, 0), obj_id=0):
        if w is None or h is None:
            if target_gravity[1] != 0: 
                w, h = 70, 7      # Гравітація  вгору/вниз  -> пад горизонтальний
            else:                      
                w, h = 7, 70      # Гравітація вліво/вправо -> пад вертикальний

        super().__init__(x, y, w, h, target_gravity, color, obj_id)
        self.rect = pygame.Rect(x, y, w, h)

    def check_collision(self, player):
        if self.rect.colliderect(player.rect):
            if not self.is_triggered:
                player.set_gravity(*self.target_gravity)
                self.is_triggered = True
        else:
            self.is_triggered = False


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
            
        # БАГ ФІКС: Підняття спавну на тррохи вище дасть не втопитися 
        #       в платформу що у наслідку кине тебе з неї 
        #           (Через нову фізику це буде помітно менше ніж раніше)
        self.spawn_y = y - 20

    def draw(self, screen, camera_offset, dev_mode=False):
        # Можна було б намалювати анімований вогонь, 
        #   але поки що це стильний помаранчевий прямокутник.
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
        # Точка фіксації для презентацій (якщо None — камера стежить за гравцем)
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

