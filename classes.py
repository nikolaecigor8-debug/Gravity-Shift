import pygame
import random
import math

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
        # self.image = TextureFactory.get_texture(self.type, width, height)

        # --- ХАРАКТЕРИСТИКИ ---
        self.speed         = 7    # Швидкість бігу.
        self.jump_power    = 15   # Потужність поштовху.
        self.gravity_force = 0.7  # Константа прискорення.
        self.acceleration  = 1.0  # Як швидко ми розганяємося
        self.friction      = 0.4  # Як швидко ми зупиняємося (тертя)
        self.color = (0, 0, 0)
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
                (1, 0): (255, 150, 0)   # Неоновий режим.
            },
            "MKin": {
                (0, 1): (0, 0, 139),    # Темно синій
                (0, -1): (139, 0, 0),   # Темно червоний
                (-1, 0): (200,200,87),  # Темно жовтий  
                (1, 0):  (0, 100, 0)    # Темно зелений
            },
            "Sad =(": {
                (0, 1): (70, 70, 110),
                (0, -1): (110, 70, 70),
                (-1, 0): (220, 220, 170),
                (1, 0): (70, 100, 70)    # Вицвіло :(
            },
            "random": random_preset()
        }
        self.current_preset = "classic"
        self.streetfly_flash = False # НЕ СКАЖУ!!!

        self.update_color()

        # Режими керування: для тих, хто звик до стрілочок, і для WASD. (arrows_only, wasd_only, both)
        self.control_mode = "both"
        self.respawn_pos = (x, y) # Координати останнього сейвпоінту

    def set_skin(self, new_color):
        self.color = new_color
        self.image.fill(self.color)

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

    def draw_face(self, window, camera):
        """Універсальне малювання обличчя. 
            Логіка адаптується під будь-який вектор гравітації (gx, gy).
             + адаптивна пропорціонування (Fast Fall)."""
        gx, gy = int(self.gravity_vec.x), int(self.gravity_vec.y)
        t = pygame.time.get_ticks() / 1000
        
        curr_w, curr_h = self.image.get_size()
        sw, sh = curr_w / self.size, curr_h / self.size

        current_colors = self.presets.get(self.current_preset, self.presets["classic"])
        main_color = current_colors.get((gx, gy), (255, 255, 255))
        dark_color = [int(c * 0.3) for c in main_color]

        cx = self.rect.x + camera.camera.x + self.size // 2
        cy = self.rect.y + camera.camera.y + self.size // 2

        speed_factor = min(self.vel.length() / 20, 1.0)
        breath_e = math.sin(t * 3) * 1
        breath_m = math.sin((t - 0.07) * 3) * 1
        dynamic_stretch = min(self.vel.length() * 0.4, 10)

        # Пропорції обличчя (гримаса)
        eye_d_n     = 11     # Відстань між очима (вбік)
        eye_depth   = -13    # Зміщення очей (вгору/вперед відносно обличчя)
        mouth_depth = 6      # Зміщення рота (вниз/назад відносно обличчя)

        base_eye_s = (self.size // 5) + int(4 * speed_factor)
        base_m_len = 37
        base_m_thick = 6 + dynamic_stretch

        ew, eh = int(base_eye_s * sw), int(base_eye_s * sh)

        if gy != 0:  # ВЕРТИКАЛЬНА ГРАВІТАЦІЯ (Вгору / Вниз)
            mw_scr, mh_scr = int(base_m_len * sw), int(base_m_thick * sh)
            eye_dist = int(eye_d_n * sw)
            
            e_offset_fix = (base_eye_s - (self.size // 5)) * sh
            m_offset_fix = (dynamic_stretch / 2) * sh
            
            e_fwd = (eye_depth * sh + breath_e * sh - e_offset_fix)
            m_fwd = (mouth_depth * sh + breath_m * sh - m_offset_fix)

            e_y = cy + e_fwd * gy
            draw_e_y = e_y if gy == 1 else e_y - eh
            eyes_pos = [
                (cx - eye_dist - ew // 2, draw_e_y, ew, eh), # Ліве
                (cx + eye_dist - ew // 2, draw_e_y, ew, eh)  # Праве
            ]
            
            m_y = cy + m_fwd * gy
            draw_m_y = m_y if gy == 1 else m_y - mh_scr
            mouth_rect = (cx - mw_scr // 2, draw_m_y, mw_scr, mh_scr)

        else:  # ГОРИЗОНТАЛЬНА ГРАВІТАЦІЯ (Вліво / Вправо)
            mw_scr, mh_scr = int(base_m_thick * sw), int(base_m_len * sh)
            eye_dist = int(eye_d_n * sh)
            
            e_offset_fix = (base_eye_s - (self.size // 5)) * sw
            m_offset_fix = (dynamic_stretch / 2) * sw
            
            e_fwd = (eye_depth * sw + breath_e * sw - e_offset_fix)
            m_fwd = (mouth_depth * sw + breath_m * sw - m_offset_fix)

            e_x = cx + e_fwd * gx
            draw_e_x = e_x if gx == 1 else e_x - ew
            eyes_pos = [
                (draw_e_x, cy - eye_dist - eh // 2, ew, eh), # Верхнє
                (draw_e_x, cy + eye_dist - eh // 2, ew, eh)  # Нижнє
            ]
            
            m_x = cx + m_fwd * gx
            draw_m_x = m_x if gx == 1 else m_x - mw_scr
            mouth_rect = (draw_m_x, cy - mh_scr // 2, mw_scr, mh_scr)

        for eye in eyes_pos:
            pygame.draw.rect(window, dark_color, eye)
        pygame.draw.rect(window, dark_color, mouth_rect)


class Platform(DebugSprite):
    COLOR_MAP = {
        "norm": (120, 25, 15),   # Звичайна   - Марс поверхня
        "ore": (0, 0, 0),        # Звичайна   - Марс камінь/руда (йому байдуже на колір на заводі все є)
        "ice": (170, 210, 210),  # Крижана    - сіро-блакитна
        "death": (120, 0, 0)     # Смертельна - темно-червоний
    }

    def __init__(self, x, y, w, h, p_type="norm", obj_id=0):
        super().__init__(x, y, w, h, obj_id)
        # Раніше тут був IF ELSE для кожного скіна, 
        #   але це не оптимально тому його мінятиме словник COLOR_MAP.
        self.image = TextureFactory.get_texture(p_type, w, h)
        
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.p_type = p_type


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
        new_color = presets[current_preset].get(tuple(self.target_gravity), (255, 255, 255))
        
        if self.color != new_color:
            self.color = new_color
            tex_type = "portal" if isinstance(self, TunnelPortal) else "jump_pad"
            self.image = TextureFactory.get_texture(tex_type, self.rect.width, self.rect.height, self.color)

    def draw(self, screen, camera_offset, dev_mode=False):
        draw_rect = self.rect.move(camera_offset)
        # pygame.draw.rect(screen, self.color, draw_rect)
        screen.blit(self.image, self.rect.move(camera_offset))
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
        # self.rect = pygame.Rect(x, y, w, h)
        self.image = TextureFactory.get_texture("portal", w, h, color=self.color)

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
        # self.rect = pygame.Rect(x, y, w, h)
        self.image = TextureFactory.get_texture("jump_pad", self.rect.width, self.rect.height, color=self.color)

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

    @property
    def x(self): return self.camera.x
    
    @property
    def y(self): return self.camera.y


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


class Particle:
    def __init__(self):
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.vel = pygame.Vector2(0, 0)
        self.alpha = 0
        self.fade_speed = 0
        self.color = [0, 0, 0]
        self.active = False

    def spawn(self, x, y, size, vel, color, fade_speed):
        self.rect = pygame.Rect(x, y, size, size)
        self.vel = pygame.Vector2(vel)
        self.color = list(color)
        self.alpha = 255
        self.fade_speed = fade_speed
        self.active = True

    def update(self, screen_rect):
        if not self.active:
            return False

        self.rect.x += self.vel.x
        self.rect.y += self.vel.y
        self.alpha -= self.fade_speed

        if self.alpha <= 0 or not screen_rect.colliderect(self.rect):
            self.active = False
            return False
        return True

class ParticleSystem:
    def __init__(self, w, h, count=80):
        self.particles = []
        self.count = count
        self.directions = ["top","right", "bottom", "left"]
        self.current_direction = "right"
        # Недоробка, ідея в тому щоб помалювати перший цикл часток (вони вистрелювали разом пр першій появі)
        #   однак поки це не діє
        for p in range(self.count):
            p = Particle()
            p.rect.x = random.randint(0, w)
            p.rect.y = random.randint(0, h)
            p.life = random.randint(0, 0) 
            self.particles.append(p)

    def switch_direction(self):
        """Циклічно змінює напрям вітру"""
        current_index = self.directions.index(self.current_direction)
        next_index = (current_index + 1) % len(self.directions)
        self.current_direction = self.directions[next_index]
        print(f"Поточний напрям вітру: {self.current_direction}")

    def _adjust_pool(self, target_count):
        current_count = len(self.particles)
        if target_count > current_count:
            self.particles.extend([Particle() for _ in range(target_count - current_count)])
        elif target_count < current_count:
            inactive = [p for p in self.particles if not p.active]
            for i in range(min(len(inactive), current_count - target_count)):
                self.particles.remove(inactive[i])

    def run(self, surface, area_rect=None, side="top", color=(255, 255, 255),
            density=0.02, 
            speed_range=(2.0, 5.0), 
            size_range=(2, 5), 
            fade_range=(2, 5)):
        
        screen_rect = surface.get_rect()
        target_area = area_rect if area_rect else screen_rect
        
        # Розрахунок ліміту
        target_count = int(max(target_area.width, target_area.height) * density)
        self._adjust_pool(min(target_count, 1000))

        for p in self.particles:
            if not p.active:
                self.reset_particle(p, side, target_area, color, speed_range, size_range, fade_range)
            
            if p.update(screen_rect):
                p_surf = pygame.Surface((p.rect.width, p.rect.height))
                p_surf.set_alpha(p.alpha)
                p_surf.fill(p.color)
                surface.blit(p_surf, p.rect.topleft)

    def reset_particle(self, p, side, area, color, speed_r, size_r, fade_r):
        size = random.randint(*size_r)
        fade = random.uniform(*fade_r)
        speed = random.uniform(*speed_r)
        
        if side == "top":
            pos = (random.randint(area.left, area.right), area.top)
            vel = (random.uniform(-0.5, 0.5), speed)
        elif side == "bottom":
            pos = (random.randint(area.left, area.right), area.bottom)
            vel = (random.uniform(-0.5, 0.5), -speed)
        elif side == "left":
            pos = (area.left, random.randint(area.top, area.bottom))
            vel = (speed, random.uniform(-0.5, 0.5))
        else: # right
            pos = (area.right, random.randint(area.top, area.bottom))
            vel = (-speed, random.uniform(-0.5, 0.5))
        
        p.spawn(*pos, size, vel, color, fade)
 

class TextureFactory:
    _cache = {}  # Словник для збереження готових текстур
    @staticmethod
    def get_texture(name, w, h, color=(200, 200, 200), grain_size=4):
        """Головний метод: повертає готову або генерує нову текстуру."""
        key = (name, w, h, tuple(color))
        if key in TextureFactory._cache:
            return TextureFactory._cache[key]

        surf = pygame.Surface((w, h))
        
        # Вибір алгоритму малювання
        if name == "norm": 
            TextureFactory._draw_sedimentary(surf, w, h, grain_size)
        elif name == "ore":
            TextureFactory._draw_regolith(surf, w, h, grain_size)
        elif name == "portal":
            TextureFactory._draw_portal(surf, w, h, color, grain_size)
        elif name == "jump_pad":
            TextureFactory._draw_jump_pad(surf, w, h, color, grain_size)
        elif name == "ice": #lab
            TextureFactory._draw_lab(surf, w, h, grain_size)
        elif name == "death": #toxic
            TextureFactory._draw_toxic(surf, w, h, grain_size)
        elif name == "dither_bg":
            TextureFactory._draw_dither_bg(surf, w, h, grain_size)  
        elif name == "dynamic_bg":
            TextureFactory._draw_dynamic_bg(surf, w, h, grain_size)
        else:
            surf.fill((200, 200, 200)) # Default

        # ВАЖЛИВО: оптимізація для слабких пристроїв — конвертує поверхню для швидшого рендерингу.
        surf = surf.convert() 
        TextureFactory._cache[key] = surf
        return surf


    @staticmethod
    def _draw_sedimentary(surf, w, h, gs):
        """Осадова порода: горизонтальні шари з нерівними межами."""
        base_red = 160
        layer_h = h // random.randint(3, 5)
        for y in range(0, h, layer_h):
            color = (base_red + random.randint(-20, 20), 60, 30)
            pygame.draw.rect(surf, color, (0, y, w, layer_h))
            # Додаємо "зубці" на межі шарів для ефекту каменю
            for x in range(0, w, gs):
                if random.random() > 0.5:
                    pygame.draw.rect(surf, color, (x, y - gs, gs, gs))

    @staticmethod
    def _draw_regolith(surf, w, h, gs):
        """Пористий реголіт: база + випадкові плями-пори."""
        surf.fill((80, 30, 20)) # Темно-червоний
        for _ in range((w * h) // (gs * 100)):
            x, y = random.randint(0, w), random.randint(0, h)
            color = (50, 20, 10) # Колір пори
            pygame.draw.rect(surf, color, (x, y, gs, gs))

    @staticmethod
    def _draw_lab(surf, w, h, gs):
        """Лабораторія (Ice): великі квадрати 4-х кольорів."""
        colors = [(180, 220, 230), (140, 180, 200), (200, 240, 255), (100, 140, 160)]
        size = 32 # Розмір плитки
        for x in range(0, w, size):
            for y in range(0, h, size):
                color = random.choice(colors)
                pygame.draw.rect(surf, color, (x, y, size, size))
                pygame.draw.rect(surf, (255, 255, 255), (x, y, size, size), 1) # Обводка плитки

    @staticmethod
    def _draw_toxic(surf, w, h, gs):
        """Токсичний камінь: кислотні кольори та багато плям."""
        surf.fill((30, 60, 10)) # Брудно-зелений
        for _ in range((w * h) // (gs * 10)):
            x, y = random.randint(0, w), random.randint(0, h)
            color = random.choice([(50, 100, 20), (100, 200, 50), (20, 40, 5)])
            pygame.draw.rect(surf, color, (x, y, gs, gs))

    @staticmethod
    def _draw_dither_bg(surf, w, h, gs):
        """Фон: градієнт через дізерінг (шахова дошка)."""
        color_top = (50, 20, 20)
        color_bot = (20, 5, 5)
        surf.fill(color_bot)
        for y in range(0, h, gs):
            # Чим нижче, тим менше шансів намалювати верхній колір
            threshold = 1.0 - (y / h)
            for x in range(0, w, gs):
                if random.random() < threshold:
                    pygame.draw.rect(surf, color_top, (x, y, gs, gs))

    @staticmethod
    def _draw_portal(surf, w, h, color, gs):
        """Портали: смугаста енергія з дрібним шумом."""
        base_dark = [max(0, c - 100) for c in color]
        surf.fill(base_dark)

        # Малюємо смуги енергії
        for i in range(0, w + h, gs * 4):
            # Малюємо діагональні смуги для динаміки
            pygame.draw.line(surf, color, (0, i), (i, 0), gs)
        
        # Дрібний "електричний" шум
        sparkle = [min(255, c + 100) for c in color]
        for _ in range((w * h) // (gs * 30)):
            x, y = random.randint(0, w - 1), random.randint(0, h - 1)
            surf.set_at((x, y), sparkle)

    @staticmethod
    def _draw_jump_pad(surf, w, h, color, gs):
        # База — дуже темний варіант основного кольору (металева основа)
        base_dark = [max(10, c - 150) for c in color]
        surf.fill(base_dark)
        
        # Колір крапок — основний колір скіна (яскравий)
        for _ in range((w * h) // (gs * 20)): 
            x, y = random.randint(0, w - gs), random.randint(0, h - gs)
            dot_color = random.choice([color, [min(255, c + 60) for c in color]])
            pygame.draw.rect(surf, dot_color, (x, y, gs//2, gs//2))
            
        # Додатково можна додати тонку рамку кольору скіна, щоб об'єкт виділявся
        pygame.draw.rect(surf, color, (0, 0, w, h), 1)


    @staticmethod
    def _draw_dynamic_bg(surf, w, h, gs):
        color_top = (150, 60, 20)  # Рудий (Марс)
        color_underground = (40, 15, 10)   # Темна земля
        
        transition_y = int(h * 0.5) # 50% висоти — це початок підземелля
        transition_range = 300
        
        # Верх (небо/поверхня)
        pygame.draw.rect(surf, color_top, (0, 0, w, transition_y))
        # Низ (глибинне підземелля)
        pygame.draw.rect(surf, color_underground, (0, transition_y, w, h - transition_y))

        # "Піксельна каша" (Dithering) на межі
        for _ in range((w * transition_range) // (gs * 2)):
            rel_x = random.randint(0, w - gs)
            rel_y = random.randint(transition_y - transition_range // 2, transition_y + transition_range // 2)
            if rel_y < 0 or rel_y > h - gs: continue

            probability = (rel_y - (transition_y - transition_range // 2)) / transition_range
            
            if random.random() < probability:
                pygame.draw.rect(surf, color_underground, (rel_x, rel_y, gs, gs))
            else:
                pygame.draw.rect(surf, color_top, (rel_x, rel_y, gs, gs))

        for _ in range((w * (h - transition_y)) // (gs * 15)):
            x = random.randint(0, w - gs)
            y = random.randint(transition_y, h - gs)
            
            noise_type = random.random()
            if noise_type > 0.8: # Рідкісні світлі піщинки
                noise_color = (60, 25, 15)
                pygame.draw.rect(surf, noise_color, (x, y, gs // 2, gs // 2))
            elif noise_type < 0.2: # Темніші вкраплення
                noise_color = (25, 10, 5)
                pygame.draw.rect(surf, noise_color, (x, y, gs // 2, gs // 2))

