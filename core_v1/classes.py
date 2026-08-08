import pygame
import random
import math
import os
from colorama import Fore, Back, Style

# Шлях до папки ресурсів гри (відносно розташування core_v1)
_RESOURCE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "MARS_world", "Resources")

# Кольори UI
UI_BG_COLOR = (0, 0, 0, 150)
UI_DEV_BG_COLOR = (0, 0, 0, 180)
UI_HELP_BG_COLOR = (0, 0, 50, 200)
OVERLAY_GAME_OVER = (100, 0, 0, 180)
OVERLAY_WIN = (0, 100, 0, 180)

# Стилі повідомлень print 
INF = f"\033[48;2;0;0;80m{Fore.LIGHTCYAN_EX}[INFO]{Style.RESET_ALL}"
WRN = f"\033[48;2;100;100;0m{Fore.LIGHTYELLOW_EX}{Style.BRIGHT}[WARNING]{Style.RESET_ALL}"
ERR = f"{Back.RED}{Fore.WHITE}[ERROR]{Style.RESET_ALL}"
DEV = f"{Back.BLACK}{Fore.LIGHTBLACK_EX}[DEV_MODE]{Style.RESET_ALL}"
SUC = f"\033[48;2;0;80;0m{Fore.LIGHTGREEN_EX}[SUCCESS]{Style.RESET_ALL}"


# --=== Інфо-панелі в грі ===--
class PlayerInfoBox:
    def __init__(self, scale, font_name="Consolas"):
        self.scale = 0.0  # Початковий нуль, щоб перший кадр точно прорахував усе
        self.font_name = font_name
        self.font = None
        
        # Змінні для відстеження змін геймплею
        self.last_control = ""
        self.last_preset = ""
        self.last_style = ""
        self.last_gravity = None
        self.last_track = ""
        
        self.surface = None

    def update_and_draw(self, screen, player, current_track_name):
        win_w, win_h = screen.get_size()
        current_scale = win_h / 480.0
        
        # Готує дані для перевірки
        gravity_name, p_color = player.get_gravity_info()
        clean_music_name = current_track_name.rsplit('.', 1)[0]
        if len(clean_music_name) > 15:
            clean_music_name = clean_music_name[:12] + "..."
            
        # Перевіряє ресайз вікна АБО зміни у грі
        if (self.surface is None or self.scale != current_scale or
            self.last_control != player.control_mode or
            self.last_preset != player.current_preset or
            self.last_style != player.skin_styles.get(player.current_preset, 'ghost') or
            self.last_gravity != player.gravity_vec or
            self.last_track != clean_music_name):
            
            self.scale = current_scale
            self.last_control = player.control_mode
            self.last_preset = player.current_preset
            self.last_style = player.skin_styles.get(player.current_preset, 'ghost')
            self.last_gravity = player.gravity_vec.copy() if hasattr(player.gravity_vec, 'copy') else player.gravity_vec
            self.last_track = clean_music_name
            
            # --- ОНОВЛЮЄ РОЗМІР ШРИФТУ ТА ПЛАШКИ ---
            font_size = int(18 * self.scale)
            self.font = pygame.font.SysFont(self.font_name, font_size, bold=True)
            
            margin = int(15 * self.scale)
            padding = int(12 * self.scale)
            line_h = int(22 * self.scale)
            box_w = int(260 * self.scale)
            
            p_lines = [
                f"Керування: {self.last_control}",
                f"Скін:  {self.last_preset}",
                f"Стиль: {self.last_style}",
                f"Гравітація: ",
                f"Радіо: {self.last_track}"
            ]
            
            box_h = padding * 1.6 + len(p_lines) * line_h
            self.surface = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            self.surface.fill(UI_BG_COLOR)
            
            # Рендеринг тексту з новим розміром шрифту
            for i, line in enumerate(p_lines):
                txt = self.font.render(line, True, (255, 255, 255))
                self.surface.blit(txt, (padding, padding + i * line_h))
                
            prefix_w = self.font.size("Гравітація: ")[0]
            grav_txt = self.font.render(gravity_name, True, p_color)
            self.surface.blit(grav_txt, (padding + prefix_w, padding + 3 * line_h))
          
        # Вивід на екран  
        margin_draw = int(15 * current_scale)
        screen.blit(self.surface, (margin_draw, margin_draw))

class DevInfoBox:
    def __init__(self, scale, font_name="Consolas"):
        self.scale = 0.0
        self.font_name = font_name
        self.font = None
        self.surface = None
        self.last_state = None
        # Оновлення не кожен кадр а через проміжок
        self.frame_tick = 0
        self.update_interval = 6

    def update_and_draw(self, screen, player, camera, win_h):
        current_scale = win_h / 480.0

        # Рахує кадри
        self.frame_tick += 1

        m_pos = pygame.mouse.get_pos()
        world_m_x = m_pos[0] - camera.camera.x
        world_m_y = m_pos[1] - camera.camera.y
        focus_status = f"({int(camera.focus_point[0])}, {int(camera.focus_point[1])})" if camera.focus_point else "Гравець"
        
        current_state = (int(player.rect.x), int(player.rect.y), int(world_m_x), int(world_m_y), focus_status, player.respawn_pos, current_scale)

        # Текст оновиться тільки якщо поверхні ще немає АБО якщо підійшла черга по кадрах І стан дійсно інший
        if self.surface is None or (self.frame_tick % self.update_interval == 0 and self.last_state != current_state):
            self.last_state = current_state
            self.scale = current_scale
            
            font_size = int(18 * self.scale)
            self.font = pygame.font.SysFont(self.font_name, font_size, bold=True)
            
            padding = int(12 * self.scale)
            line_h = int(22 * self.scale)
            box_w = int(260 * self.scale)
            
            dev_lines = [
                "--- РЕЖИМ РОЗРОБНИКА ---",
                f"Гравець X:{current_state[0]} Y:{current_state[1]}",
                f" Миша   X:{current_state[2]} Y:{current_state[3]}",
                f"Фокус камери: {focus_status}",
                f" [1]-Down    [2]-Up   ",
                f" [3]-Left    [4]-Right",
                f"Spawn: {player.respawn_pos}"
            ]
            
            box_h = padding * 1.6 + len(dev_lines) * line_h
            self.surface = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            self.surface.fill(UI_DEV_BG_COLOR)
            
            for i, line in enumerate(dev_lines):
                if   i == 0: t_color = (255, 255, 0)
                elif i == 3: t_color = (255, 215, 0)
                elif i == 2: t_color = (100, 200, 255)
                elif i == 1: t_color = (150, 255, 150)
                else: t_color = (255, 255, 255)
                
                txt = self.font.render(line, True, t_color)
                self.surface.blit(txt, (padding, padding + i * line_h))
                
        margin_draw = int(15 * current_scale)
        y_pos = win_h - self.surface.get_height() - margin_draw
        screen.blit(self.surface, (margin_draw, y_pos))

class HelpInfoBox:
    def __init__(self, scale, font_name="Consolas"):
        self.scale = 0.0
        self.font_name = font_name
        self.font = None
        self.surface = None

    def draw(self, screen, win_w, player):
        win_h = screen.get_size()[1]
        current_scale = win_h / 550.0
        
        if self.surface is not None and self.scale != current_scale:
            self.surface = None

        if self.surface is None:
            self.scale = current_scale
            
            # --- ОНОВЛЮЄ РОЗМІР ШРИФТУ ТА ПЛАШКИ ---
            font_size = int(18 * self.scale)
            self.font = pygame.font.SysFont(self.font_name, font_size, bold=True)
            
            padding = int(12 * self.scale)
            line_h = int(22 * self.scale)
            box_w = int(250 * self.scale)

            current_mode = player.control_mode.lower()
            if "wasd" in current_mode and "arrows" in current_mode: mode_display = "Обидва  "
            elif "wasd" in current_mode: mode_display = "WASD    "
            elif "arrows" in current_mode: mode_display = "Стрілки "
            else: mode_display = "Обидва  "

            help_lines = [
                "  КЕРУВАННЯ  ",
                "-------------",
                "ESCAPE   - ПАУЗА",
                "(-) (+)  - Зміна музики ",
                f"{mode_display} - Рух",
                "SPACE    - Стрибок",
                "SHIFT    - Спринт",
                "F↑L↑|  R - Респавн",
                "M        - Керування",
                "TAB      - Скін",
                "F11      - Весь екран",
                "F9       - Сховати UI",
                "-----------------------",
                "ALT      - Розробник:",
                "LKM      - Креслення",
                "PKM      - Видобути",
                "P        - Режим камери",
                "V        - Напрям вітру",
                "O        - Сис.  світла",
                "C        - Колір    ^",
                '"["  "]" - Чіткість ^',
                "CTRL     - Підказки"
            ]

            box_h = padding * 1.6 + len(help_lines) * line_h
            self.surface = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            self.surface.fill(UI_HELP_BG_COLOR)

            for i, line in enumerate(help_lines):
                t_c = (100, 200, 255) if i < 2 else (255, 255, 255)
                txt = self.font.render(line, True, t_c)
                self.surface.blit(txt, (padding, padding + i * line_h))

        margin_draw = int(15 * current_scale)
        x_pos = win_w - self.surface.get_width() - margin_draw
        screen.blit(self.surface, (x_pos, margin_draw))


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
        (1, 0): "ВПРАВО"}
    CONTROL_MODES = ("both", 
                     "arrows_only", 
                     "wasd_only")
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
        self.speed         = 7    # Швидкість   (максимальна)
        self.jump_power    = 15   # Сила стрибка(повштовх)
        self.gravity_force = 0.7  # Гравітація  (тяжіння)
        self.acceleration  = 1.0  # Прискорення (розгін)
        self.friction      = 0.85  # Зупинка     (тертя)
        self.color = (0, 0, 0)    # Колір адаптивний тому тут по нулям.
        self.idle_timer = 0
        self.idle_threshold = random.randint(180, 300) # Час в кадрах до анімки
        self.eye_lift = 0.0
        self.jump_face_lift = 0
        self.brow_alpha = 0
        self.visual_tick = 0
        # Напрям гравітації: (x,y). 
        # Це векторна магія: (0,1) тягне вниз, (0,-1) — до стелі. Вектор визначає, куди ми падаємо.
        self.gravity_vec = pygame.Vector2(0, 1)
        
        # --- ФІЗИКА ---
        self.on_ground = False
        self.is_on_ice = False
        self.is_dead = False

        # --- ГРАФІКА (Fast Fall) ---
        self.is_fast_falling = False
        self.base_image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.image = self.base_image.copy()

        # --- СИСТЕМА ШЛЕЙФУ (ТІНІ) ---
        self.ghost_positions = []  # Список для зберігання копій гравця
        self.max_ghosts = 5        # Скільки "привидів" буде йти за гравцем

        # КЕШ ОБЛИЧЧЯ
        self._brow_cache = None
        self._brow_cache_key = None

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
            "random": random_preset()}
        
        self.skin_styles = {
            # "classic": "classic", Не треба бо це вже = за умовсчанням, 
                                  # воно існує через можливість кастомізації
            "cyber": "matrix_flow",
            "MKin": "noise_dust",
            "Sad =(": "liquid_lava",
            "random": "crystalline_shards"}
        
        self.current_preset = "classic"

        # --- STREETFLY ---
        self.streetfly_flash = False         # НЕ СКАЖУ!!!
        self.streetfly_cooldown = 300        # Кулдаун у мілісекундах (1 секунда)
        self.last_streetfly_time = -300      # Час останнього використання
        self.streetfly_ready_notified = True  # Прапорець, щоб кубик не блінкав сам по собі при старті гри


        self.is_rare_dust = False
        self.update_color()

        # Режими керування: для тих, хто звик до стрілочок, і для WASD. (arrows_only, wasd_only, both)
        self.control_mode = "both"
        self.respawn_pos = (x, y) # Координати останнього сейвпоінту
        self.last_campfire_id = 0
        self.vel = pygame.Vector2(0, 0)

  # --- конфігурації та геттері ---
    def set_skin(self, new_color):
        self.color = new_color
        self.image.fill(self.color)

    def switch_skin(self):
        """Динамічне перемикання скінів по колу через словник presets."""
        skin_names = list(self.presets.keys())
        self.current_preset = skin_names[(skin_names.index(self.current_preset) + 1) % len(skin_names)]
        self.is_rare_dust = (random.randint(1, 7) == 1)
        self.update_color()
        
        # Отримуємо колір для гравітації (0,1) та створюємо RGB фон
        current_colors = self.presets.get(self.current_preset, self.presets["classic"])
        bg_color = current_colors.get((0, 1), (0, 255, 255))
        r, g, b = bg_color
        
        # RGB фон та грубий шрифт через ANSI
        rgb_bg = f"\033[48;2;{r};{g};{b}m"
        bold = "\033[1m"
        
        print(f"{INF} Поточний скін: {rgb_bg}{Fore.WHITE}{bold} {self.current_preset} {Style.RESET_ALL}")

    def switch_control_mode(self):
        """Циклічне перемикання між режимами керування. Для тих, хто не може визначитися."""
        current_index = self.CONTROL_MODES.index(self.control_mode)
        self.control_mode = self.CONTROL_MODES[(current_index + 1) % len(self.CONTROL_MODES)]
        print(f"{INF} Поточний режим керування: {self.control_mode}")

    def set_gravity(self, x, y):
        """Міняємо вектор тяжіння та перефарбовуємо гравця."""
        self.gravity_vec.update(x, y)
        if self.vel.length() > 12:
            self.vel.scale_to_length(12)
        self.update_color()

    def get_gravity_info(self):
        """Повертає назву напрямку та поточний колір гравця для тексту."""
        gravity_key = (int(self.gravity_vec.x), int(self.gravity_vec.y))
        direction = self.GRAVITY_NAMES.get(gravity_key, "???:")
        color = self.presets[self.current_preset].get(gravity_key, (255, 255, 255))
        return direction, color

  # --- обробки вводу ---
    def read_input(self, keys):
        """Знає які клавіші - керування, залежно від вибраного режиму керування."""
        if self.control_mode == "arrows_only":
            return (keys[pygame.K_LEFT], 
                    keys[pygame.K_RIGHT], 
                    keys[pygame.K_UP], 
                    keys[pygame.K_DOWN])
        
        if self.control_mode == "wasd_only":
            return (keys[pygame.K_a], 
                    keys[pygame.K_d], 
                    keys[pygame.K_w], 
                    keys[pygame.K_s])
        
        return (keys[pygame.K_LEFT]  or keys[pygame.K_a],
                keys[pygame.K_RIGHT] or keys[pygame.K_d],
                keys[pygame.K_UP]    or keys[pygame.K_w],
                keys[pygame.K_DOWN]  or keys[pygame.K_s])

    def handle_input(self):
        move_left, move_right, move_up, move_down = self.read_input(pygame.key.get_pressed())
        # МІНІФІКС: Раніше гравець завжди зупинявся швидко. Тепер поверхня має більше варіантів
        # friction_value = 0.95 if self.is_on_ice else self.friction

        if not self.on_ground:
            # У повітрі — вільний політ
            friction_value = self.friction 

        elif self.is_on_ice:
            # На лабораторії — ковзання
            friction_value = 0.90

        else:
            # На звичайних блоках — гальмування
            friction_value = 0.6

        if self.gravity_vec.y != 0: # Рух по X (якщо гравітація вертикальна)
            self.apply_axis_motion("x", move_left, move_right, friction_value)
        else:                       # Рух по Y (якщо гравітація горизонтальна)
            self.apply_axis_motion("y", move_up, move_down, friction_value)

        self.apply_jump_and_fall(move_left, move_right, move_up, move_down)

  # --- фізика та рух ---
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

        # --- ЛОГІКА ОЧІКУВАННЯ ---  (для анімації обличчя)
        if self.vel.length() < 0.2:
            self.idle_timer += 1
        else:
            if self.idle_timer > 0:
                self.idle_threshold = random.randint(240, 390)
            self.idle_timer = 0
            self.eye_lift = max(0, self.eye_lift - 0.5)
            self.brow_alpha = max(0, self.brow_alpha - 15)

        if self.idle_timer > self.idle_threshold:
            if self.eye_lift < 2:
                self.eye_lift += 0.066
            self.brow_alpha = min(255, self.brow_alpha + 10)

        # Стиль гравця буде унікальним для classic
        if self.current_preset == "classic" and self.vel.length() > 0.5: 
            self.ghost_positions.append((self.rect.topleft, self.image))
            if len(self.ghost_positions) > self.max_ghosts:
                self.ghost_positions.pop(0)       
        else:
            if self.ghost_positions:
                self.ghost_positions.pop(0)

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
                if self.gravity_vec.x == -1: self.on_ground = True

            elif self.rect.right > limit:
                self.rect.right = limit
                self.vel.x = 0
                if self.gravity_vec.x == 1: self.on_ground = True
        else:
            # Жорстка підлога та стеля світу по Y
            self.rect.y += delta
            if self.rect.top < 0:
                self.rect.top = 0
                self.vel.y = 0
                if self.gravity_vec.y == -1: self.on_ground = True

            elif self.rect.bottom > limit:
                self.rect.bottom = limit
                self.vel.y = 0
                if self.gravity_vec.y == 1: self.on_ground = True

        # Колізії з платформами
        for wall in platforms:
            if not self.rect.colliderect(wall.rect):
                continue
            self.resolve_platform_collision(wall, axis, delta)

    def apply_axis_motion(self, axis, negative_pressed, positive_pressed, friction):
        """Прораховує рух по осі з урахуванням обмежень бігу та плавного згасання спринту."""
        velocity = getattr(self.vel, axis)
        max_speed = self.speed

        is_sprinting = abs(velocity) > max_speed

        if negative_pressed:
            if is_sprinting and velocity > 0:
                velocity -= self.acceleration
            elif velocity > -max_speed:
                velocity = max(-max_speed, velocity - self.acceleration)
        elif positive_pressed:
            if is_sprinting and velocity < 0:
                velocity += self.acceleration
            elif velocity < max_speed:
                velocity = min(max_speed, velocity + self.acceleration)
        else:
            if not is_sprinting:
                velocity *= friction

        if abs(velocity) > max_speed:
            sprint_decay = 0.92
            velocity *= sprint_decay

        if abs(velocity) < 0.05:
            velocity = 0.0

        setattr(self.vel, axis, velocity)
        # Поглянути яка швидкість зараз за x та y
        # print(self.vel)   

    def apply_jump_and_fall(self, move_left, move_right, move_up, move_down):
        gravity_tuple = (int(self.gravity_vec.x), int(self.gravity_vec.y))
        jump_key, fall_key = self.GRAVITY_ACTIONS.get(gravity_tuple, (None, None))
        key_map = {"left":  move_left, 
                   "right": move_right, 
                   "up":    move_up, 
                   "down":  move_down}

        keys = pygame.key.get_pressed()
        jump_press = key_map.get(jump_key, False) or keys[pygame.K_SPACE]
        fall_press = key_map.get(fall_key, False)

        if jump_press and self.on_ground:
            jump_velocity = -self.gravity_vec * self.jump_power
            if self.gravity_vec.y != 0:
                self.vel.y = jump_velocity.y
            else:
                self.vel.x = jump_velocity.x
            self.on_ground = False
            self.jump_face_lift = 6

        self.is_fast_falling = fall_press

    def apply_streetfly(self):
        """Механіка Streetfly: Анулює падіння + дає спринт, якщо гравець рухається."""
        # Перевірка на кулдаун
        current_time = pygame.time.get_ticks()
        if current_time - self.last_streetfly_time < self.streetfly_cooldown:
            return  # Здібність ще перезаряджається, ігнорує натискання

        move_left, move_right, move_up, move_down = self.read_input(pygame.key.get_pressed())
        sprint_power = 24 # Швидкість спринту
        activated = False 

        # --- АНУЛЮВАННЯ ПАДІННЯ ---
        if self.vel.dot(self.gravity_vec) > 0.1:
            self.vel -= self.vel.dot(self.gravity_vec) * self.gravity_vec
            self.streetfly_flash = True
            # activated = True

        # --- СПРИНТ ЗА НАМІРОМ ГРАВЦЯ --- (перевіряються натиснуті кнопки)
        if self.gravity_vec.y != 0: # ------- Вертикальна гравітація (Вниз/Вгору)
            if move_right and not move_left:
                self.vel.x = sprint_power
                activated = True
            elif move_left and not move_right:
                self.vel.x = -sprint_power
                activated = True

        else: # ---------------------------- Горизонтальна гравітація (Вліво/Вправо)
            if move_down and not move_up:
                self.vel.y = sprint_power
                activated = True
            elif move_up and not move_down:
                self.vel.y = -sprint_power
                activated = True

        # Спалах спрацює, якщо було анульовано падіння АБО активовано спринт
        # Якщо хоча б одна з умов спрацювала — запускає таймер кулдауну
        if activated:
            self.streetfly_flash = True
            self.last_streetfly_time = current_time
            self.streetfly_ready_notified = False

    def limit_speed(self, max_speed):
        if self.vel.length() > max_speed:
            self.vel.scale_to_length(max_speed)

    def resolve_platform_collision(self, wall, axis, delta):
        ''' Багато обраховуюча функція прорахунків заткнень з різними типами платформ. 
                Враховує напрямок удару та тип платформи для правильного реагування.'''
        hit_dir = 1 if delta > 0 else -1 if delta < 0 else 0
        # Визначаємо напрямок удару: 
        #       1 - рух у напрямку гравітації,
        #      -1 - проти гравітації.
        # Це допомагає зрозуміти, чи ми приземляємося на платформу або вдаряємося об неї знизу чи збоку.

        if axis == "x":
            if hit_dir > 0:   self.rect.right = wall.rect.left
            elif hit_dir < 0: self.rect.left = wall.rect.right
        else:
            if hit_dir > 0:   self.rect.bottom = wall.rect.top
            elif hit_dir < 0: self.rect.top = wall.rect.bottom

        # Реакції правда чи ні для різних типів платформ. 
        #   Звичайна платформа - просто зупинка
        #   Лід - ковзання, 
        #   смерть - смерть, 
        if wall.p_type == "lab":   self.is_on_ice = True
        if wall.p_type == "toxic": self.is_dead = True

        if axis == "x" and hit_dir == self.gravity_vec.x:
            self.on_ground = True
        if axis == "y" and hit_dir == self.gravity_vec.y:
            self.on_ground = True

        if axis == "x": self.vel.x = 0
        else: self.vel.y = 0

    def get_active_platforms(self, platforms):
        # Головна користа фішка гри. Не прораховувати колізії об'єктів які поза екраном
        # (Для гравця різниця не помітна а для пк шанс не закипіти від всіх об'єктів світу)
        visible_area = self.rect.inflate(9000, 600)
        return [p for p in platforms if p.rect.colliderect(visible_area)]

  # --- ігрові події ---
    def respawn(self):
        """Повернення додому до багаття, коли рівень виявився сильнішим за тебе..."""
        self.rect.topleft = self.respawn_pos
        self.vel = pygame.Vector2(0, 0)
        self.set_gravity(0, 1)
        self.is_dead = False

  # --- візуал ---
    def update_color(self):
        """Оновлює текстуру залежно від кольору + стилю."""
        gravity_key = (int(self.gravity_vec.x), int(self.gravity_vec.y))
        current_colors = self.presets.get(self.current_preset, self.presets["classic"])
        self.color = current_colors.get(gravity_key, (255, 255, 255))
        current_style = self.skin_styles.get(self.current_preset)

        self.base_image.fill((0, 0, 0, 0))

        # --- Малювання ---
        if current_style == "noise_dust":
            if self.is_rare_dust: TextureFactory.draw_noise_dust_none(self.base_image, self.color, gravity_key)
            else:                 TextureFactory.draw_noise_dust(self.base_image, self.color, gravity_key)
 
        elif current_style == "matrix_flow":
            TextureFactory.draw_matrix_flow(self.base_image, self.color, gravity_key, pygame.time.get_ticks())
     
        elif current_style == "crystalline_shards":
            TextureFactory.draw_crystalline_shards(self.base_image, self.color, gravity_key)
    
        elif current_style == "liquid_lava":
            TextureFactory.draw_liquid_lava(self.base_image, self.color, gravity_key, pygame.time.get_ticks())
        
        else:
            # Якщо стиль не заданий - звичайний квадрат з кольором. 
            # Це також запасний варіант, якщо щось піде не так з малюванням.
            self.base_image.fill(self.color)
            
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

        # --- АВТОМАТИЧНИЙ БЛІК ГОТОВНОСТІ ---
        current_time = pygame.time.get_ticks()
        if not self.streetfly_ready_notified:
            if current_time - self.last_streetfly_time >= self.streetfly_cooldown:
                self.streetfly_flash = True
                self.streetfly_ready_notified = True

        # ЕФЕКТ СТРІТФЛАЙ: короткий білий спалах.
        if self.streetfly_flash:
            self.image.fill((255, 255, 255))
            self.streetfly_flash = False
        self.jump_face_lift = max(0, self.jump_face_lift - 0.2)

        # Кадрування стиля гравця
        current_style = self.skin_styles.get(self.current_preset)
        # Залежно від скіна, різна частота
        # self.frame = 30 if current_style == "matrix_flow" else 10 if current_style == "liquid_lava" else 40
        if   current_style == "matrix_flow":
            self.frame = 30
        elif current_style == "liquid_lava":
            self.frame = 10
        elif current_style == "noise_dust":
            self.frame = 40
        # Саме оновлення
        if current_style in ("matrix_flow", "liquid_lava", "noise_dust"):
            self.visual_tick += 1
            # Оновлення кожні frame кадрів
            if self.visual_tick >= self.frame:
                self.visual_tick = 0
                self.update_color()

  # --- рендеринг ---
    def draw(self, screen, camera_offset):
        if self.current_preset == "classic":
            for i, (g_pos, g_img) in enumerate(self.ghost_positions):
                alpha = int((i + 1) * (180 / len(self.ghost_positions)))
                g_img.set_alpha(alpha)

                draw_x = g_pos[0] + camera_offset[0] + (self.rect.width - g_img.get_width())//2
                draw_y = g_pos[1] + camera_offset[1] + (self.rect.height - g_img.get_height())//2
               
                screen.blit(g_img, (draw_x, draw_y))
                g_img.set_alpha(255)

        img_rect = self.image.get_rect(center=self.rect.center)
        screen.blit(self.image, img_rect.move(camera_offset))

    def draw_face(self, window, camera):
        """Універсальне малювання обличчя. 
            Логіка адаптується під будь-який вектор гравітації (gx, gy).
             + адаптивна пропорціонування (Fast Fall), анімка очікування, руху"""
        gx, gy = int(self.gravity_vec.x), int(self.gravity_vec.y)
        t = pygame.time.get_ticks() / 1000.0
        
        curr_w, curr_h = self.image.get_size()
        sw, sh = curr_w / self.size, curr_h / self.size

        current_colors = self.presets.get(self.current_preset, self.presets["classic"])
        main_color = current_colors.get((gx, gy), (255, 255, 255))
        dark_color = (int(main_color[0] * 0.3), int(main_color[1] * 0.3), int(main_color[2] * 0.3))

        cx = self.rect.x + camera.camera.x + self.size // 2
        cy = self.rect.y + camera.camera.y + self.size // 2
        
        move_velocity = self.vel.x if gy != 0 else self.vel.y
        # НЕДОФІКС: Був момент коли при fast fall визначали одну сторону, 
        #          при розтягенні починалася не така математика і обличчя вилітало за гравця.
        # side_shift = max(-8, min(8, move_velocity * 1.1)) * sw
        shift_scale = sw if gy != 0 else sh
        side_shift = max(-8, min(8, move_velocity * 1.1)) * shift_scale

        vel_len = self.vel.length()
        speed_factor = min(vel_len * 0.05, 1.0)
        breath_e = math.sin(t * 3) 
        breath_m = math.sin((t - 0.07) * 3)
        dynamic_stretch = min(vel_len * 0.4, 10)

        eye_d_n     = 10.5   # Відстань між очима (вбік)
        eye_depth   = -13    # Зміщення очей (вгору/вперед відносно обличчя)
        mouth_depth = 6      # Зміщення рота (вниз/назад відносно обличчя)   

        base_eye_s = (self.size // 5) + int(4 * speed_factor)
        mouth_narrowness = max(0.4, 1.0 - (abs(move_velocity) * 0.04))
        base_m_len = 35 * mouth_narrowness 
        base_m_thick = 6 + dynamic_stretch

        ew, eh = int(base_eye_s * sw), int(base_eye_s * sh)

        # Математика вираховування координат 
        if gy != 0:  # ВЕРТИКАЛЬНА ГРАВІТАЦІЯ (Вгору / Вниз)
            mw_scr, mh_scr = int(base_m_len * sw), int(base_m_thick * sh)
            eye_dist = int(eye_d_n * sw)
            
            left_eye_dist = eye_dist * 0.6 if move_velocity > 1 else eye_dist
            right_eye_dist = eye_dist * 0.6 if move_velocity < -1 else eye_dist

            e_fwd = (eye_depth * sh + breath_e * sh - ((base_eye_s - 10) * sh))
            m_fwd = (mouth_depth * sh + breath_m * sh - (dynamic_stretch * 0.5 * sh))

            e_y = cy + e_fwd * gy - self.jump_face_lift * gy
            draw_e_y = e_y if gy == 1 else e_y - eh
            
            eyes_pos = [
                (cx - left_eye_dist - ew // 2 + side_shift, draw_e_y, ew, eh),   
                (cx + right_eye_dist - ew//2 + side_shift, draw_e_y - (self.eye_lift * gy), ew, eh) 
            ]
            
            m_y = cy + m_fwd * gy - self.jump_face_lift * gy
            draw_m_y = m_y if gy == 1 else m_y - mh_scr
            mouth_rect = (cx - mw_scr // 2 + side_shift, draw_m_y, mw_scr, mh_scr)

        else:      # ГОРИЗОНТАЛЬНА ГРАВІТАЦІЯ (Вліво / Вправо)
            mw_scr, mh_scr = int(base_m_thick * sw), int(base_m_len * sh)
            eye_dist = int(eye_d_n * sh)
            
            e_fwd = (eye_depth * sw + breath_e * sw - ((base_eye_s - 10) * sw))
            m_fwd = (mouth_depth * sw + breath_m * sw - (dynamic_stretch * 0.5 * sw))

            e_x = cx + e_fwd * gx - self.jump_face_lift * gx
            draw_e_x = e_x if gx == 1 else e_x - ew

            eyes_pos = [
                (draw_e_x, cy - eye_dist - eh // 2 + side_shift, ew, eh),   
                (draw_e_x - (self.eye_lift * gx), cy + eye_dist - eh//2 + side_shift, ew, eh) 
            ]
            
            m_x = cx + m_fwd * gx - self.jump_face_lift * gx
            draw_m_x = m_x if gx == 1 else m_x - mw_scr
            mouth_rect = (draw_m_x, cy - mh_scr // 2 + side_shift, mw_scr, mh_scr)

        # Малювання очей та рота
        for eye in eyes_pos:
            pygame.draw.rect(window, dark_color, eye)

        # Брови
        if self.brow_alpha > 0:
            b_width = (int(ew * 1.5) if gy != 0 else int(eh * 1.5)) + 1
            b_height = max(1, int(2 * (sh if gy != 0 else sw)))
            
            cache_key = (b_width, b_height, self.brow_alpha, dark_color[0])
            if self._brow_cache_key != cache_key:
                self._brow_cache = pygame.Surface((b_width, b_height) if gy != 0 else (b_height, b_width), pygame.SRCALPHA)
                self._brow_cache.fill((*dark_color, int(self.brow_alpha)))
                self._brow_cache_key = cache_key

            for i, (ex, ey, ew_cur, eh_cur) in enumerate(eyes_pos):
                if gy != 0:
                    bx = ex - (b_width - ew_cur) // 2
                    by = ey - b_height + 1 if gy > 0 else ey + eh_cur - 1
                    window.blit(self._brow_cache, (bx, by))
                else:
                    by = ey - (b_width - eh_cur) // 2
                    bx = ex - b_height + 1 if gx > 0 else ex + ew_cur - 1
                    window.blit(self._brow_cache, (bx, by))

        pygame.draw.rect(window, dark_color, mouth_rect)


class BackgroundObject(DebugSprite):
    """Фоновий об'єкт: без колізії, тільки візуал."""
    def __init__(self, x, y, w, h, bg_type="lab_bg", obj_id=0):
        super().__init__(x, y, w, h, obj_id)
        self.bg_type = bg_type
        self.image = TextureFactory.get_texture(bg_type, w, h)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        
        # для анімацій
        self.anim_timer = random.randint(0, 100)

    # def update(self):
    #     """Оновлення анімованих фонів."""
    #     self.anim_timer += 1

    #     if self.bg_type in ("toxic_bg"):
    #         if self.anim_timer % 30 == 0:
    #             pass

    def draw(self, screen, camera_offset, dev_mode=False):
        screen.blit(self.image, self.rect.move(camera_offset))
        self.draw_debug(screen, dev_mode, camera_offset)


class Platform(DebugSprite):
    COLOR_MAP = {
        "norm": (180, 85, 75),   # Звичайна   - Марсіанська поверхня
        "ore": (0, 0, 0),        # Звичайна   - Камінь/руда (йому байдуже на колір на фабриці все є)
        "crystal": (0, 0, 0),    # Звичайна   - Кристали    (теж ну треба, кольори саме на фабриці)
        "lab": (170, 210, 210),  # Крижана    - сіро-блакитна
        "toxic": (120, 0, 0)     # Смертельна - темно-червоний
    }

    def __init__(self, x, y, w, h, p_type="norm", obj_id=0):
        super().__init__(x, y, w, h, obj_id)
        # Раніше тут був IF ELSE для кожного скіна, 
        #   але це не оптимально тому його мінятиме словник COLOR_MAP.
        self.image = TextureFactory.get_texture(p_type, w, h)

        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.p_type = p_type

    # Розмір розширення підкладки (в пікселях з кожного боку)
    OUTLINE_INFLATE = 3

    def draw_outline(self, screen, camera_offset):
        """Перший прохід: малює розширений кольоровий силует (підкладку).
        
        Метод "Підкладки із затіненням" (Layered Buffer Outline):
        Малюємо inflate-прямокутник на 5px більший з усіх боків.
        Коли сусідні блоки стоять впритул, їхні підкладки зливаються
        в один суцільний силует — рамка з'являється лише на межі з повітрям.
        """
        outline_color = TextureFactory.get_outline_color(self.p_type)
        if outline_color is None:
            return 
        outline_rect = self.rect.inflate(
            self.OUTLINE_INFLATE * 2,
            self.OUTLINE_INFLATE * 2
        ).move(camera_offset)
        pygame.draw.rect(screen, outline_color, outline_rect)

    def draw(self, screen, camera_offset, dev_mode=False):
        """Другий прохід: малює справжню текстуру поверх підкладки."""
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
        screen.blit(self.image, self.rect.move(camera_offset))
        self.draw_debug(screen, dev_mode, camera_offset)
# \\\ логіка порталів ///

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

        # Поділ на зону А і Б: щоб зрозуміти, що гравець дійсно ПЕРЕЙШОВ межу, 
                                                  # а не просто торкнувся краю.
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
        # Розміри 60x80 - це базові, але я їх збільшую на 30% для кращої видимості та взаємодії.
        base_w, base_h = 60, 80
        w, h = int(base_w * 1.3), int(base_h * 1.3)
        super().__init__(x, y, w, h, obj_id)
        
        try:
            raw_image = pygame.image.load(os.path.join(_RESOURCE_DIR, "Picture", "Spawn_pic.png")).convert_alpha()
            self.image = pygame.transform.scale(raw_image, (w, h))
        except Exception:
            self.image = pygame.Surface((w, h))
            self.image.fill((0, 200, 255)) 

        self.rect = pygame.Rect(x, y, w, h)
        self.side = side

        offset = 20
        player_w = 50

        # ЛОГІКА РОЗУМНОГО СПАВНУ 
        if self.side == "right":
            self.spawn_x = x + w + offset
        elif self.side == "left":
            self.spawn_x = x - player_w - offset
        else:
            # Спавнить по центру, якщо щось невірно
            self.spawn_x = x + (w // 2) - (player_w // 2)

        # БАГ ФІКС: Підняття спавну на тррохи вище дасть не втопитися 
        #       в платформу що у наслідку кине тебе з неї 
        #           (Через нову фізику це буде помітно менше ніж раніше)
        self.spawn_y = y # - 20

    def draw(self, screen, camera_offset, dev_mode=False):
        draw_pos = self.rect.move(camera_offset)
        screen.blit(self.image, draw_pos)
        self.draw_debug(screen, dev_mode, camera_offset)


class Finish(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.fixed_width = 100
        self.fixed_height = 120

        try:
            raw_image = pygame.image.load(os.path.join(_RESOURCE_DIR, "Picture", "Finish_pic.png")).convert_alpha()
            self.image = pygame.transform.scale(raw_image, (self.fixed_width, self.fixed_height))
        except Exception as e:
            print(f"{ERR} Помилка завантаження Finish_pic.png: {e}")
            self.image = pygame.Surface((self.fixed_width, self.fixed_height))
            self.image.fill((255, 0, 0)) 

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
            prompt_y = draw_rect.top - 35 
            
            bg_rect = pygame.Rect(prompt_x - 5, prompt_y - 2, self.prompt_text.get_width() + 10, self.prompt_text.get_height() + 4)
            pygame.draw.rect(screen, (0, 0, 0, 150), bg_rect)
            
            screen.blit(self.prompt_text, (prompt_x, prompt_y))


class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.screen_size = (width, height)
        self.dead_zone = pygame.Rect(200, 150, 400, 300)
        self.lerp_speed = 0.05
        # Точка фіксації для презентацій (якщо None — камера стежить за гравцем)
        self.focus_point = None
 
    def resize(self, width, height):
        self.camera.size = (width, height)
        self.screen_size = (width, height)
        self.dead_zone.width = int(width * 0.4)
        self.dead_zone.height = int(height * 0.4)
        self.dead_zone.center = (width // 2, height // 2)

    def recenter(self, target):
        if self.focus_point:
            tx, ty = self.focus_point
        else:
            tx, ty = target.rect.centerx, target.rect.centery

        self.camera.x = -tx + (self.screen_size[0] // 2)
        self.camera.y = -ty + (self.screen_size[1] // 2)

    @property
    def x(self): return self.camera.x
    
    @property
    def y(self): return self.camera.y

    def update(self, target):
        screen_w, screen_h = self.screen_size

        if self.focus_point:
            # Режим презентації: ціль — координати
            target_center_x, target_center_y = self.focus_point
        else:
            # Звичайний режим:   ціль — гравець
            target_center_x, target_center_y = target.rect.centerx, target.rect.centery
            player_on_screen_x = target.rect.centerx + self.camera.x
            player_on_screen_y = target.rect.centery + self.camera.y
           
            self.dead_zone.width = int(screen_w * 0.4)
            self.dead_zone.height = int(screen_h * 0.4)
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

        self.camera.x = int(self.camera.x)
        self.camera.y = int(self.camera.y)

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)


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


class TextPanel(DebugSprite):
    """Об'єкт-тригер у світі. При E — відкриває текстову панель."""
    # Ширина зони взаємодії: трохи ширша за сам об'єкт
    INTERACT_MARGIN = 40

    def __init__(self, x, y, w, h, panel_type="sign", title="", text="", obj_id=0):
        super().__init__(x, y, w, h, obj_id)

        self.panel_type = panel_type   # "sign" | "monologue"
        self.title      = title
        self.text       = text

        # Зона взаємодії (ширша за хітбокс)
        self.interact_rect = pygame.Rect(
            x - self.INTERACT_MARGIN,
            y - self.INTERACT_MARGIN,
            w + self.INTERACT_MARGIN * 2,
            h + self.INTERACT_MARGIN * 2
        )

        self.player_nearby = False   # True коли гравець у зоні
        self.can_interact  = False   # True тільки коли стан змінився (для підказки)

        # Маленький шрифт підказки [E]
        self._hint_font = pygame.font.SysFont("Consolas", 16, bold=True)
        self._hint_surf = None  # кешується

        # Математична текстура об'єкта у світі
        self.image = TextPanel._make_sign_texture(w, h)
        self.rect  = pygame.Rect(x, y, w, h)

    # Текстура об'єкта (математична, як у TextureFactory)
    @staticmethod
    def _make_sign_texture(w, h):
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        # Фон: темно-синя лабораторна плитка
        base = (30, 45, 65)
        surf.fill(base)

        # Математичний шум: дрібні пікселі різної яскравості
        for _ in range((w * h) // 12):
            px = random.randint(0, w - 1)
            py = random.randint(0, h - 1)
            br = random.randint(-15, 25)
            c  = (
                max(0, min(255, base[0] + br)),
                max(0, min(255, base[1] + br)),
                max(0, min(255, base[2] + br)),
            )
            surf.set_at((px, py), c)

        # Рамка: тонка блакитна лінія
        BORDER = (0, 180, 220)
        pygame.draw.rect(surf, BORDER, (0, 0, w, h), 2)

        # Горизонтальна смуга зверху (як табличка)
        pygame.draw.rect(surf, (0, 160, 200), (0, 0, w, 6))

        # Мінімалістичний символ [?] або [!] по центру
        font = pygame.font.SysFont("Consolas", max(14, h // 3), bold=True)
        sym  = font.render("!", True, (0, 220, 255))
        surf.blit(sym, (w // 2 - sym.get_width() // 2,
                        h // 2 - sym.get_height() // 2 + 4))

        return surf

    # Оновлення (викликати у render_game або update_game_logic)
    def update(self, player_rect):
        """Перевіряє чи гравець поруч. Повертає True при першому вході."""
        was_nearby = self.player_nearby
        self.player_nearby = self.interact_rect.colliderect(player_rect)
        return self.player_nearby and not was_nearby  # True = гравець тільки-но увійшов

    # Малювання у світі
    def draw(self, screen, camera_offset, dev_mode=False):
        draw_rect = self.rect.move(camera_offset)
        screen.blit(self.image, draw_rect)
        self.draw_debug(screen, dev_mode, camera_offset)

        if self.player_nearby:
            self._draw_hint(screen, draw_rect)

    def _draw_hint(self, screen, draw_rect):
        """Маленька підказка [E] над об'єктом, пульсує."""
        if self._hint_surf is None:
            hint = self._hint_font.render("[E]", True, (0, 220, 255))
            # Фон-пілюля
            pw = hint.get_width() + 12
            ph = hint.get_height() + 6
            surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
            pygame.draw.rect(surf, (0, 20, 40, 200), (0, 0, pw, ph), border_radius=5)
            pygame.draw.rect(surf, (0, 180, 220, 200), (0, 0, pw, ph), 1, border_radius=5)
            surf.blit(hint, (6, 3))
            self._hint_surf = surf

        t   = pygame.time.get_ticks() / 1000.0
        bob = int(math.sin(t * 4.0) * 3)  # невелике підстрибування

        x = draw_rect.centerx - self._hint_surf.get_width() // 2
        y = draw_rect.top - self._hint_surf.get_height() - 8 + bob
        screen.blit(self._hint_surf, (x, y))

class PanelRenderer:
    """Анімована панель тексту. Малюється на ui_buffer."""

    # Обмеження розміру плашки
    MAX_W = 860
    MIN_W = 360
    MAX_H = 420
    PADDING = 28
    LINE_SPACING = 26
    FONT_TITLE_SIZE = 22
    FONT_BODY_SIZE  = 17

    # Швидкість анімації відкриття
    ANIM_SPEED = 0.14

    def __init__(self):
        self.active = False
        self.panel = None   # посилання на TextPanel
        self._anim = 0.0   # 0.0 → 1.0

        # Кеші
        self._surface = None
        self._last_win = (0, 0)
        self._last_panel = None

        # Шрифти
        self._font_title = pygame.font.SysFont("Consolas", self.FONT_TITLE_SIZE, bold=True)
        self._font_body = pygame.font.SysFont("Consolas", self.FONT_BODY_SIZE,  bold=False)
        self._font_close = pygame.font.SysFont("Consolas", 14, bold=True)

    # ------------------------------------------------------------------
    def open(self, panel):
        """Відкриває панель (викликати у handle_keydown_events)."""
        self.panel = panel
        self.active = True
        self._anim = 0.0
        self._surface = None  # скидає кеш, бо контент нові

    def close(self):
        self.active = False
        self.panel = None
        self._anim = 0.0

    def is_open(self):
        return self.active

    # ------------------------------------------------------------------
    def draw(self, ui_buffer):
        """Головний метод. Викликати у draw_ui_boxes або перед lighting.render.
            ui_buffer — pygame.Surface з SRCALPHA."""
        if not self.active or self.panel is None:
            return

        win_w, win_h = ui_buffer.get_size()

        # Плавна анімація відкриття
        if self._anim < 1.0:
            self._anim = min(1.0, self._anim + self.ANIM_SPEED)
        ease = self._ease_out(self._anim)

        # Перебудувати поверхню якщо потрібно
        if (self._surface is None
                or self._last_win != (win_w, win_h)
                or self._last_panel is not self.panel):
            self._build_surface(win_w, win_h)

        if self._surface is None:
            return

        full_w, full_h = self._surface.get_size()

        # Позиція: центровано по X, трохи нижче верху (для "sign" / "monologue")
        target_x = win_w  // 2 - full_w // 2
        target_y = 40

        # Анімація: з'являється зверху
        anim_y = target_y - int((1.0 - ease) * (full_h + target_y + 10))
        alpha  = int(ease * 255)

        self._surface.set_alpha(alpha)
        ui_buffer.blit(self._surface, (target_x, anim_y))

    # ------------------------------------------------------------------
    def _build_surface(self, win_w, win_h):
        """Будує кешовану поверхню для поточного panel."""
        self._last_win = (win_w, win_h)
        self._last_panel = self.panel

        p = self.panel
        PAD = self.PADDING

        # --- Розрахунок ширини ---
        avail_w = min(self.MAX_W, int(win_w * 0.72))
        avail_w = max(avail_w, self.MIN_W)
        text_area_w = avail_w - PAD * 2

        # --- Обгортка тексту ---
        title_lines = self._wrap(p.title, self._font_title, text_area_w) if p.title else []
        body_lines = self._wrap(p.text,  self._font_body,  text_area_w)

        # --- Розрахунок висоти ---
        title_h = len(title_lines) * (self.FONT_TITLE_SIZE + 4)
        sep_h = 12 if title_lines else 0     # відступ між заголовком і тілом
        body_h = len(body_lines)  * self.LINE_SPACING
        close_h = 20                           # рядок "[E] — закрити"

        total_h = PAD + title_h + sep_h + body_h + PAD // 2 + close_h + PAD
        total_h = min(total_h, self.MAX_H)
        total_h = max(total_h, 80)

        # --- Поверхня ---
        surf = pygame.Surface((avail_w, total_h), pygame.SRCALPHA)

        # Математичний фон: шарувата текстура
        self._draw_bg(surf, avail_w, total_h, p)

        # --- Заголовок ---
        cy = PAD
        for line in title_lines:
            t = self._font_title.render(line, True, (0, 220, 255))
            surf.blit(t, (PAD, cy))
            cy += self.FONT_TITLE_SIZE + 4

        if title_lines:
            # Лінія-роздільник
            pygame.draw.line(surf, (0, 180, 220, 160),
                             (PAD, cy + 4), (avail_w - PAD, cy + 4), 1)
            cy += sep_h

        # --- Тіло тексту ---
        clip_bottom = total_h - PAD // 2 - close_h - 2
        for line in body_lines:
            if cy + self.LINE_SPACING > clip_bottom:
                # Обрізаємо — при необхідності можна пізніше додати скрол
                trunc = self._font_body.render("...", True, (150, 180, 200))
                surf.blit(trunc, (PAD, cy))
                break
            t = self._font_body.render(line, True, (210, 230, 245))
            surf.blit(t, (PAD, cy))
            cy += self.LINE_SPACING

        # --- Підказка "закрити" ---
        close_txt = self._font_close.render("[E]  або  [Esc]  — закрити", True, (80, 130, 160))
        surf.blit(close_txt, (PAD, total_h - PAD // 2 - close_h + 2))

        self._surface = surf

    # ------------------------------------------------------------------
    def _draw_bg(self, surf, w, h, panel):
        """Математичний фон панелі — схожий до lab-текстури, але темніший."""

        # 1. Базова заливка
        base = (8, 18, 32)
        surf.fill((*base, 230))

        # 2. Математичний шум — тонкі пікселі
        for _ in range((w * h) // 60):
            px = random.randint(0, w - 1)
            py = random.randint(0, h - 1)
            br = random.randint(-8, 18)
            c  = (
                max(0, min(255, base[0] + br)),
                max(0, min(255, base[1] + br * 2)),
                max(0, min(255, base[2] + br * 3)),
                210
            )
            surf.set_at((px, py), c)

        # 3. Горизонтальні мікро-смуги (технічний стиль)
        for y in range(0, h, 8):
            alpha = random.randint(3, 12)
            line_surf = pygame.Surface((w, 1), pygame.SRCALPHA)
            line_surf.fill((100, 180, 255, alpha))
            surf.blit(line_surf, (0, y))

        # 4. Зовнішня рамка: ціан
        pygame.draw.rect(surf, (0, 200, 240, 255), (0, 0, w, h), 2, border_radius=8)

        # 5. Внутрішня рамка: тонша, темніша
        pygame.draw.rect(surf, (0, 100, 140, 120), (3, 3, w - 6, h - 6), 1, border_radius=6)

        # 6. Маленькі кути-акценти (технічний вигляд)
        corner_len = 14
        accent = (0, 220, 255, 200)
        for cx, cy, dx, dy in [
            (0, 0, 1, 1), (w, 0, -1, 1), (0, h, 1, -1), (w, h, -1, -1)
        ]:
            pygame.draw.line(surf, accent, (cx, cy), (cx + dx * corner_len, cy), 2)
            pygame.draw.line(surf, accent, (cx, cy), (cx, cy + dy * corner_len), 2)

        # 7. Верхня кольорова смуга (колір залежить від типу)
        stripe_color = (0, 200, 240, 180) if panel.panel_type == "sign" else (180, 100, 255, 180)
        stripe_surf  = pygame.Surface((w - 4, 4), pygame.SRCALPHA)
        stripe_surf.fill(stripe_color)
        surf.blit(stripe_surf, (2, 2))

    # ------------------------------------------------------------------
    @staticmethod
    def _wrap(text, font, max_w):
        """Ділить текст на рядки за шириною."""
        if not text:
            return []
        words = text.split(" ")
        lines = []
        current = ""
        for word in words:
            test = (current + " " + word).strip()
            if font.size(test)[0] <= max_w:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    @staticmethod
    def _ease_out(t):
        """Плавна анімація: exp ease-out."""
        return 1.0 - (1.0 - t) ** 3


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
        if not self.active: return False
        self.rect.x += self.vel.x
        self.rect.y += self.vel.y
        self.alpha -= self.fade_speed

        if self.alpha <= 0 or not screen_rect.colliderect(self.rect):
            self.active = False
            return False
        return True

class ParticleSystem:
    _surface_cache = {}

    def __init__(self, w, h, count=80):
        self.particles = []
        self.count = count
        self.directions = ["top","right", "bottom", "left"]
        self.current_direction = "right"
        # Недоробка, ідея в тому щоб помалювати перший цикл часток 
        # (вони вистрелювали разом при першій появі) однак поки це не діє
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
        print(f"{DEV} Поточний напрям вітру: {self.current_direction}")

    def run(self, surface, area_rect=None, side="top", color=(255, 255, 255),
            density=0.02, speed_range=(2.0, 5.0), size_range=(2, 5), fade_range=(2, 5)):
        
        screen_rect = surface.get_rect()
        target_area = area_rect if area_rect else screen_rect
        
        # Розрахунок ліміту
        target_count = int(max(target_area.width, target_area.height) * density)
        self._adjust_pool(min(target_count, 1000))

        for p in self.particles:
            if not p.active:
                self.reset_particle(p, side, target_area, color, speed_range, size_range, fade_range)
            
            if p.update(screen_rect):
                alpha_step = max(0, min(255, (int(p.alpha) // 15) * 15))
                cache_key = (p.rect.width, p.rect.height, p.color[0], p.color[1], p.color[2], alpha_step)
                
                if cache_key not in self._surface_cache:
                    s = pygame.Surface((p.rect.width, p.rect.height), pygame.SRCALPHA)
                    s.fill((*p.color, alpha_step))
                    self._surface_cache[cache_key] = s.convert_alpha()
                    
                surface.blit(self._surface_cache[cache_key], p.rect.topleft)

    def reset_particle(self, p, side, area, color, speed_r, size_r, fade_r):
        size = random.randint(*size_r)
        fade = random.uniform(*fade_r)
        speed = random.uniform(*speed_r)
        
        if   side == "top":
            pos = (random.randint(area.left, area.right), area.top)
            vel = (random.uniform(-0.5, 0.5), speed)
        elif side == "bottom":
            pos = (random.randint(area.left, area.right), area.bottom)
            vel = (random.uniform(-0.5, 0.5), -speed)
        elif side == "left":
            pos = (area.left, random.randint(area.top, area.bottom))
            vel = (speed, random.uniform(-0.5, 0.5))
        else:       # right
            pos = (area.right, random.randint(area.top, area.bottom))
            vel = (-speed, random.uniform(-0.5, 0.5))
        
        p.spawn(*pos, size, vel, color, fade)
 
    def _adjust_pool(self, target_count):
        current_count = len(self.particles)
        if target_count > current_count:
            self.particles.extend([Particle() for _ in range(target_count - current_count)])
        elif target_count < current_count:
            inactive = [p for p in self.particles if not p.active]
            for i in range(min(len(inactive), current_count - target_count)):
                self.particles.remove(inactive[i])


class TextureFactory:
    _cache = {}  # Словник для збереження готових текстур

    # Кольори обведення для кожного типу платформи (Layered Buffer Outline)
    OUTLINE_COLORS = {
        "norm":  (130, 60, 45),    # Тепло-оранжевий силует   було (220, 110, 90)
        "ore":   (30, 5, 5),     # Темно-вугільний          було (90, 50, 40)    
        "lab":   (110, 140, 150),  # Крижаний блиск           було (200, 230, 240)
        "toxic": (15, 40, 5),     # Токсичний зелений        було (50, 160, 30)
    }

    @staticmethod
    def get_outline_color(p_type):
        """Повертає колір силуету-підкладки для вказаного типу платформи."""
        return TextureFactory.OUTLINE_COLORS.get(p_type, None)

    @staticmethod
    def get_texture(name, w, h, color=(200, 200, 200), grain_size=4):
        key = (name, w, h, tuple(color))
        if key in TextureFactory._cache:
            return TextureFactory._cache[key]

        surf = pygame.Surface((w, h))
        
        # Вибір алгоритму малювання
        if   name == "norm":       # Платформа поверхні
            TextureFactory._draw_sedimentary(surf, w, h, grain_size)
        elif name == "ore":        # Платформа підземна
            TextureFactory._draw_regolith(surf, w, h, grain_size)
        elif name == "crystal":    # Платформа кристал
            TextureFactory._draw_crystal(surf, w, h, grain_size)
        elif name == "lab":        # Платформа лаболаторії (слизька)
            TextureFactory._draw_lab(surf, w, h)
        elif name == "toxic":      # Платформа мінералів   (смерть)
            TextureFactory._draw_toxic(surf, w, h, grain_size) 

        elif name == "portal":     # Портал тунельний
            TextureFactory._draw_portal(surf, w, h, color, grain_size)
        elif name == "jump_pad":   # Портал пад
            TextureFactory._draw_jump_pad(surf, w, h, color, grain_size)

        elif name == "dynamic_bg": # Рухливий дво поверховий фон
            TextureFactory._draw_dynamic_bg(surf, w, h, grain_size)

        elif name == "lab_bg":     # Фон типу лабораторії
            TextureFactory._draw_lab_bg(surf, w, h)
        elif name == "cave_bg":    # Фон типу звичних     печер
            TextureFactory._draw_cave_bg(surf, w, h, grain_size)
        elif name == "crystal_bg": # Фон типу кристальних печер
            TextureFactory._draw_crystal_bg(surf, w, h, grain_size)
        elif name == "toxic_bg":   # Фон типу отруйних    печер
            TextureFactory._draw_toxic_bg(surf, w, h, grain_size)

        else:                      # Нічого з цього не підійшло
            surf.fill((200, 200, 200)) # Звичайно (помилка)

        # ВАЖЛИВО: оптимізація для слабких пристроїв — конвертує поверхню для швидшого рендерингу.
        surf = surf.convert() 
        TextureFactory._cache[key] = surf
        return surf

    # ------- Конвеєри стилів ------- 
# (кожен def відповідальний за розмальовку свого стиля для об'єктів)

  # Платформи всіх призначень ---------------------
    @staticmethod
    def _draw_sedimentary(surf, w, h, gs):
        """Осадова порода: горизонтальні шари"""
        base_red = 160
        layer_h = h // random.randint(3, 5)
        for y in range(0, h, layer_h):
            color = (base_red + random.randint(-20, 20), 60, 30)
            pygame.draw.rect(surf, color, (0, y, w, layer_h))
            for x in range(0, w, gs):
                if random.random() > 0.5:
                    pygame.draw.rect(surf, color, (x, y - gs, gs, gs))

    @staticmethod
    def _draw_regolith(surf, w, h, gs):
        """Пористий реголіт: база + випадкові плями-пори."""
        surf.fill((80, 30, 20))
        for _ in range((w * h) // (gs * 70)):
            x, y = random.randint(0, w), random.randint(0, h)
            pygame.draw.rect(surf, (50, 20, 10), (x, y, gs, gs))

    @staticmethod
    def _draw_crystal(surf, w, h, gs):
        """Кристалічна порода: насичені кольори, світла рамка та вкраплення."""
        # Пресети дрогоціностей
        crystal_presets = [
            (0, 160, 190),   # Глибокий ціан
            (140, 40, 180),  # Аметистовий
            (40, 160, 40),   # Смарагдовий
            (210, 140, 0)    # Янтарний
        ]
        base_color = random.choice(crystal_presets)
        bright_color = tuple(min(255, c + 75) for c in base_color)
        surf.fill(base_color)
        pygame.draw.rect(surf, bright_color, (0, 0, w, h), 2)
        
        # Вкраплення всередині
        num_sparkles = (w * h) // (gs * 60)
        for _ in range(num_sparkles):
            x = random.randint(3, w - 4)
            y = random.randint(3, h - 4)
            pygame.draw.rect(surf, bright_color, (x, y, gs // 1, gs // 1))

    @staticmethod
    def _draw_lab(surf, w, h):
        """Лабораторія: великі квадрати 4-х кольорів."""
        colors = [(180, 220, 230), (140, 180, 200), (200, 240, 255), (100, 140, 160)]
        size = 32 # Розмір плитки
        for x in range(0, w, size):
            for y in range(0, h, size):
                color = random.choice(colors)
                pygame.draw.rect(surf, color, (x, y, size, size))
                pygame.draw.rect(surf, (255, 255, 255), (x, y, size, size), 1) # Обведення плитки

    @staticmethod
    def _draw_toxic(surf, w, h, gs):
        """Токсичний камінь: кислотні кольори та багато плям
        Ядерна руда марсу використовується як паливо в лаболаторіях"""
        surf.fill((20, 60, 10)) # Брудно-зелений
        for _ in range((w * h) // (gs * 5)):
            x, y = random.randint(0, w), random.randint(0, h)
            color = random.choice([(50, 100, 20), (100, 200, 50), (20, 40, 5)])
            pygame.draw.rect(surf, color, (x, y, gs, gs))


  # Портали -----------------------------------------
    @staticmethod
    def _draw_portal(surf, w, h, color, gs):
        """Портали: смугасті енергетичні аномалії з дрібним шумом.\
            Подібні до...     ...ГрАвЦя?!?"""
        base_dark = [max(0, c - 100) for c in color]
        surf.fill(base_dark)
        for i in range(0, w + h, gs * 4):
            pygame.draw.line(surf, color, (0, i), (i, 0), gs)
        sparkle = [min(255, c + 100) for c in color]
        for _ in range((w * h) // (gs * 30)):
            x, y = random.randint(0, w - 1), random.randint(0, h - 1)
            surf.set_at((x, y), sparkle)

    @staticmethod
    def _draw_jump_pad(surf, w, h, color, gs):
        '''Аномальна лідина, розтікається навіть на стелі.
        Пориста з опроміненням, що схоже...     ...на гравця?!?'''
        base_dark = [max(10, c - 150) for c in color]
        surf.fill(base_dark)

        for _ in range((w * h) // (gs * 20)): 
            x, y = random.randint(0, w - gs), random.randint(0, h - gs)
            dot_color = random.choice([color, [min(255, c + 60) for c in color]])
            pygame.draw.rect(surf, dot_color, (x, y, gs//2, gs//2))
        pygame.draw.rect(surf, color, (0, 0, w, h), 1)


  # Фон головний ------------------------------------
    @staticmethod
    def _draw_dynamic_bg(surf, w, h, gs):
        color_top         = (200, 110, 70) # Рудий (Марс)
        color_underground = (40, 15, 10)   # Темна земля
        
        transition_y = int(h * 0.5) # 50% висоти — це початок підземелля
        transition_range = 300
        
        # Верх (небо/поверхня)
        pygame.draw.rect(surf, color_top, (0, 0, w, transition_y))
        # Низ (глибинне підземелля)
        pygame.draw.rect(surf, color_underground, (0, transition_y, w, h - transition_y))

        # "Піксельна каша" на межі між
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
            if   noise_type > 0.8: # Рідкісні світлі піщинки
                pygame.draw.rect(surf, (60, 25, 15), (x, y, gs // 2, gs // 2))
            elif noise_type < 0.2: # Темніші вкраплення
                pygame.draw.rect(surf, (25, 10, 5), (x, y, gs // 2, gs // 2))


  # Фоно об'єкти ------------------------------------
    @staticmethod
    def _draw_lab_bg(surf, w, h):
        surf.fill((35, 45, 55))
        tile = 32
        
        # Сітка (плитка)
        for x in range(0, w, tile):
            for y in range(0, h, tile):
                pygame.draw.rect(surf, (45, 55, 65), (x, y, tile, tile), 1)

        # -СИСТЕМНІ КАБЕЛІ-
        cable_colors = [(0, 90, 128), (128, 60, 0), (40, 128, 50)]
        # Кількість довгих ліній залежить від розміру об'єкта
        num_chains = (w * h) // 15000 + 2 

        for _ in range(num_chains):
            color = random.choice(cable_colors)
            curr_x = random.randrange(0, w, tile) + tile // 2
            curr_y = random.randrange(0, h, tile) + tile // 2
            
            # Кабель з 3-5 сегментів
            num_segments = random.randint(3, 6)
            for _ in range(num_segments):
                # Напрямок (вгору, вниз, вліво, вправо)
                dx, dy = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
                # Довжина сегмента кратна плитці
                length = random.randint(2, 5) * tile

                next_x = curr_x + dx * length
                next_y = curr_y + dy * length
                pygame.draw.line(surf, color, (curr_x, curr_y), (next_x, next_y), 3)
                pygame.draw.rect(surf, (80, 80, 90), (curr_x - 3, curr_y - 3, 6, 6))
                curr_x, curr_y = next_x, next_y

        # -ТЕХНОЛОГІЧНІ ЩИТКИ-
        for _ in range((w * h) // 35000 + 1):
            px = random.randrange(0, w, tile) + 4
            py = random.randrange(0, h, tile) + 4
            # Корпус щитка
            pygame.draw.rect(surf, (70, 80, 90), (px, py, 24, 24))
            pygame.draw.rect(surf, (140, 140, 150), (px, py, 24, 24), 1)
            # Сигнальний вогник
            pygame.draw.rect(surf, (0, 255, 100), (px + 16, py + 4, 4, 4))

    @staticmethod
    def _draw_cave_bg(surf, w, h, gs):
        """Суцільний фон печери: логіка глибокого підземелля без поверхні."""
        base_color = (40, 15, 10)
        surf.fill(base_color)
        num_particles = (w * h) // (gs * 15)

        for _ in range(num_particles):
            rx, ry = random.randint(0, w - gs), random.randint(0, h - gs)

            rand_val = random.random()
            if rand_val < 0.2:
                p_color = (60, 25, 15)  # Світліші піщинки
            elif rand_val < 0.4:
                p_color = (25, 10, 5)   # Глибокі тіні
            else:
                continue

            pygame.draw.rect(surf, p_color, (rx, ry, gs // 2, gs // 2))

    @staticmethod
    def _draw_crystal_bg(surf, w, h, gs):
        """Фон кристалічної печери.
             Порода + темніший шар
             Примусовою дистанція між."""
        TextureFactory._draw_cave_bg(surf, w, h, gs)

        # Пресети дрогоціностей
        crystal_presets = [
            (0, 160, 190),   # Глибокий ціан
            (140, 40, 180),  # Аметистовий
            (40, 160, 40),   # Смарагдовий
            (210, 140, 0)    # Янтарний
        ]
        
        dark_offset = 120 # темніший колір зі списку 0-255/колір-чорний
        light_cr_color = 70 # Світлість кольору рамки і вкрапок
        bg_presets = [
            tuple(max(10, c - dark_offset) for c in color) 
            for color in crystal_presets]
        
        # Чек ліст вже ісеуючих координат для дистанції каменів
        placed_crystals = []
        min_distance = 60  # Мінімальна дистанція між центрами 
        
        # Кількість спроб генерації (проти вічного циклу)
        num_crystals = (w * h) // 20000 + 1 
        max_attempts = 50 

        for _ in range(num_crystals):
            base_color = random.choice(bg_presets)
            bright_color = tuple(min(255, c + light_cr_color) for c in base_color)
            # Розмір кристалів
            cw, ch = random.randint(15, 35), random.randint(15, 35)

            # Спроби знайти підходяще місце
            for _ in range(max_attempts):
                # Місце кристалів
                cx = random.randint(5, w - cw - 5)
                cy = random.randint(5, h - ch - 5)
                new_center = pygame.Vector2(cx + cw // 2, cy + ch // 2)

                # Перевірка відстані
                too_close = any(new_center.distance_to(old_center) < min_distance for old_center in placed_crystals)
                
                if not too_close:
                    pygame.draw.rect(surf, base_color, (cx, cy, cw, ch))
                    pygame.draw.rect(surf, bright_color, (cx, cy, cw, ch), 1)
                    
                    for _ in range(random.randint(2, 5)):
                        sx = random.randint(cx + 2, cx + cw - 4)
                        sy = random.randint(cy + 2, cy + ch - 4)
                        pygame.draw.rect(surf, bright_color, (sx, sy, gs // 1, gs // 1))
                    
                    placed_crystals.append(new_center)
                    break

    @staticmethod
    def _draw_toxic_bg(surf, w, h, gs):
        """Фон токсичної печери
             радіоактивна руда + печери
        Структуровані поклади руди, що випирають з фону піксельними зернами."""
        base_underground = (40, 15, 10)
        surf.fill(base_underground)

        for _ in range((w * h) // (gs * 20)):
            rx, ry = random.randint(0, w - gs), random.randint(0, h - gs)
            if random.random() < 0.2:
                pygame.draw.rect(surf, (25, 10, 5), (rx, ry, gs // 2, gs // 2))

        # Менша яскравість оригінальних кольорів
        toxic_colors = [(20, 40, 8), 
                        (40, 80, 20), 
                        (10, 15, 5)]

        placed_clusters = []
        min_distance = 110 # Дистанція між покладами
        
        num_clusters = (w * h) // 30000 + 1 
        max_attempts = 50 

        for _ in range(num_clusters):
            # Випадковий розмір
            cw, ch = random.randint(20, 100), random.randint(20, 100)
            for _ in range(max_attempts):
                cx = random.randint(10, w - cw - 10)
                cy = random.randint(10, h - ch - 10)
                new_center = pygame.Vector2(cx + cw // 2, cy + ch // 2)

                too_close = any(new_center.distance_to(old_center) < min_distance for old_center in placed_clusters)
                
                if not too_close:
                    grains_count = (cw * ch) // (gs * 2) 
                    for _ in range(grains_count):
                        gx = cx + random.randint(0, cw - gs)
                        gy = cy + random.randint(0, ch - gs)
                        grain_color = random.choice(toxic_colors)
                        pygame.draw.rect(surf, grain_color, (gx, gy, gs, gs))
                        if random.random() > 0.8:
                            pygame.draw.rect(surf, grain_color, (gx, gy, gs * 2, gs))
                    placed_clusters.append(new_center)
                    break


  # Текстура гравця ---------------------------------
    @staticmethod
    def draw_energy_core(surf, base_color, gravity):
        """
        Малює динамічне енергетичне ядро.
        surf: поверхня спрайту (зазвичай квадратна)
        base_color: основний адаптивний колір гравця
        gravity: кортеж гравітації, наприклад (0, 1) або (-1, 0)
        """
        w, h = surf.get_size()
        center_x, center_y = w // 2, h // 2
        
        # Визначає зсув ядра (протилежно вектору гравітації)
        # Якщо гравітація (0, 1), то зміщуємо на offset_dist пікселів по Y
        offset_dist = 6
        offset_x = -gravity[0] * offset_dist
        offset_y = -gravity[1] * offset_dist
        core_center = (center_x + offset_x, center_y + offset_y)

        # Створює "світлий" колір для центру
        # Функція min(c + 100, 255) гарантує, що ми не вийдемо за межі RGB
        bright_color = tuple(min(c + 100, 255) for c in base_color)
        mid_color = tuple(min(c + 50, 255) for c in base_color)

        # Малює шари (від країв до центру)
        # Фон (найтемніший)
        surf.fill(base_color)

        # Середнє коло
        pygame.draw.circle(surf, mid_color, core_center, w // 2.5)
        
        # Ядро (найсвітліше)
        pygame.draw.circle(surf, bright_color, core_center, w // 5)

        # Додає легкий "відблиск" (опціонально)
        glow_pos = (core_center[0] - 2, core_center[1] - 2)
        pygame.draw.circle(surf, (255, 255, 255), glow_pos, 2)

    @staticmethod
    def draw_matrix_flow(surf, base_color, gravity, time_tick):
        """Малює ефект цифрового потоку.
        time_tick: лічильник кадрів"""
        w, h = surf.get_size()
        # Фон темний відтінок основного кольору
        bg_dark = tuple(max(c - 100, 10) for c in base_color)
        surf.fill(bg_dark)

        num_strips = 8 # Кількість смужок
        speed = 0.2    # Швидкість потоку 

        for i in range(num_strips):
            # Дощ але стабільних смужок
            offset = (i * (w // num_strips)) + 3
            flow_pos = (time_tick * speed + i * 15) % (h if gravity[1] != 0 else w)
            
            # Колір смужки (оригінал)
            strip_color = tuple(min(c + 50, 255) for c in base_color)
    
            # Координати залежно від гравітації
            if   gravity == (0, 1): # Вниз
                pygame.draw.rect(surf, strip_color, (offset, flow_pos, 2, 10))
            elif gravity == (0,-1): # Вгору
                pygame.draw.rect(surf, strip_color, (offset, h - flow_pos, 2, 10))
            elif gravity == (-1,0): # Вліво
                pygame.draw.rect(surf, strip_color, (w - flow_pos, offset, 10, 2))
            elif gravity == (1, 0): # Вправо
                pygame.draw.rect(surf, strip_color, (flow_pos, offset, 10, 2))
            else: # Стандартний вигляд якщо гравітація 0
                 pygame.draw.rect(surf, strip_color, (offset, flow_pos, 2, 8))

    @staticmethod
    def draw_crystalline_shards(surf, base_color, gravity):
        """Малює ефект ограненого каменю."""
        w, h = surf.get_size()
        center = (w // 2, h // 2)

        top_left,    top_right    = (0, 0), (w, 0)
        bottom_left, bottom_right = (0, h), (w, h)
        # Світло світить ПРОТИ гравітації. 
        # Якщо гравітація вниз (0, 1), світло зверху (0, -1)
        light_dir = (-gravity[0], -gravity[1])

        # Описуємо 4 грані (трикутники) та їх "нормалі" (куди вони дивляться)
        # Нормаль потрібна для розрахунку освітлення
        shards = [
            {"points": [center, top_left, top_right],    "normal": (0, -1)},   # Верхня
            {"points": [center, bottom_left, bottom_right], "normal": (0, 1)}, # Нижня
            {"points": [center, top_left, bottom_left],  "normal": (-1, 0)},   # Ліва
            {"points": [center, top_right, bottom_right], "normal": (1, 0)}    # Права
        ]

        for shard in shards:
            # Від -1 (тінь) до 1 (відблиск)
            dot = shard["normal"][0] * light_dir[0] + shard["normal"][1] * light_dir[1]
            
            # Якщо dot > 0 -> світліше, якщо dot < 0 -> темніше
            shift = int(dot * 40) 
            shard_color = tuple(max(0, min(255, c + shift)) for c in base_color)
            pygame.draw.polygon(surf, shard_color, shard["points"])

        # Тонкі лінії граней, бо можу
        line_color = tuple(max(0, min(255, c + 60)) for c in base_color)
        pygame.draw.line(surf, line_color, center, top_left, 1)
        pygame.draw.line(surf, line_color, center, top_right, 1)
        pygame.draw.line(surf, line_color, center, bottom_left, 1)
        pygame.draw.line(surf, line_color, center, bottom_right, 1)
        pygame.draw.rect(surf, line_color, (0, 0, w, h), 1)

    @staticmethod
    def draw_liquid_lava(surf, base_color, gravity, time_tick):
        """Малює ефект "Рідкого наповнювача" з анімованою хвилею.
            Казав що гравець з речовини, ось гіперполізація"""
        w, h = surf.get_size()
        # Світлий колір для "порожньої" частини (верх)
        top_color = tuple(min(c + 80, 255) for c in base_color)
        surf.fill(top_color)

        # Параметри хвилі
        wave_height = 5  # Амплітуда
        frequency = 0.1  # Частота хвиль
        speed = 0.005    # Швидкість руху  
        
        points = []
        if gravity[1] != 0:
            is_down = gravity[1] > 0
            for x in range(w + 1):
                wave_y = math.sin(x * frequency + time_tick * speed) * wave_height
                y_pos = (h * 0.4) + wave_y if is_down else (h * 0.6) + wave_y
                points.append((x, y_pos))
            
            if is_down: points.extend([(w, h), (0, h)])
            else: points.extend([(w, 0), (0, 0)])  
        else:
            is_right = gravity[0] > 0
            for y in range(h + 1):
                wave_x = math.sin(y * frequency + time_tick * speed) * wave_height
                x_pos = (w * 0.4) + wave_x if is_right else (w * 0.6) + wave_x
                points.append((x_pos, y))
            
            if is_right: points.extend([(w, h), (w, 0)])
            else: points.extend([(0, h), (0, 0)])
            
        if len(points) > 2:
            pygame.draw.polygon(surf, base_color, points)
            
        # Рамочка щоб це була ємність
        pygame.draw.rect(surf, (180, 180, 180), (0, 0, w, h), 2 )

    @staticmethod
    def draw_noise_dust_none(surf, base_color, gravity):
        """Малює ефект піщаних частинок.
        Частинки групуються біля краю, куди тягне гравітація."""
        w, h = surf.get_size()
        frame_color = tuple(min(c + 40, 255) for c in base_color)
        num_particles = 150 # Кількість частинок-пікселів
        for _ in range(num_particles):
            # Розрахунок координат по X
            if gravity[0] > 0:   # Гравітація вправо
                rx = random.random() ** 0.5
            elif gravity[0] < 0: # Гравітація вліво
                rx = random.random() ** 2.0
            else:                # Рівномірно
                rx = random.random()
                
            # Розрахунок координат по Y
            if gravity[1] > 0:   # Гравітація вниз
                ry = random.random() ** 0.5
            elif gravity[1] < 0: # Гравітація вгору
                ry = random.random() ** 2.0
            else:                # Рівномірно
                ry = random.random()

            x = int(rx * (w - 2))
            y = int(ry * (h - 2))
            # Частинки світліші за фон
            var = random.randint(40, 120) 
            p_color = tuple(min(255, c + var) for c in base_color)
            if random.random() > 0.9: # 10% частинок будуть супер-яскравими
                p_color = (255, 255, 255)

            # Частинка
            pygame.draw.rect(surf, p_color, (x, y, 2, 2))
        # Тонка рамка
        pygame.draw.rect(surf, frame_color, (0, 0, w, h), 2)
    # |||||||||||||||||||РАЗОМ||||||||||||||||||||
    @staticmethod
    def draw_noise_dust(surf, base_color, gravity):
        surf.fill(base_color)
        TextureFactory.draw_noise_dust_none(surf, base_color, gravity)




# - test -
class TextureFactory_gemini:
    _cache = {}  # Словник для збереження готових текстур

    # Кольори обведення для кожного типу платформи (Layered Buffer Outline)
    OUTLINE_COLORS = {
        "norm":  (130, 60, 45),    # Тепло-оранжевий силует
        "ore":   (30, 5, 5),       # Темно-вугільний          
        "lab":   (110, 140, 150),  # Крижаний блиск           
        "toxic": (15, 40, 5),      # Токсичний зелений        
    }

    @staticmethod
    def get_outline_color(p_type):
        """Повертає колір силуету-підкладки для вказаного типу платформи."""
        return TextureFactory.OUTLINE_COLORS.get(p_type, None)

    @staticmethod
    def get_texture(name, w, h, color=(200, 200, 200), grain_size=4):
        key = (name, w, h, tuple(color))
        if key in TextureFactory._cache:
            return TextureFactory._cache[key]

        surf = pygame.Surface((w, h))
        
        # Вибір алгоритму малювання
        if   name == "norm":       # Платформа поверхні
            TextureFactory._draw_sedimentary(surf, w, h, grain_size)
        elif name == "ore":        # Платформа підземна
            TextureFactory._draw_regolith(surf, w, h, grain_size)
        elif name == "crystal":    # Платформа кристал
            TextureFactory._draw_crystal(surf, w, h, grain_size)
        elif name == "lab":        # Платформа лабораторії (слизька)
            TextureFactory._draw_lab(surf, w, h)
        elif name == "toxic":      # Платформа мінералів   (небезпека)
            TextureFactory._draw_toxic(surf, w, h, grain_size) 

        elif name == "portal":     # Портал тунельний
            TextureFactory._draw_portal(surf, w, h, color, grain_size)
        elif name == "jump_pad":   # Джамп пад
            TextureFactory._draw_jump_pad(surf, w, h, color, grain_size)

        elif name == "dynamic_bg": # Рухливий двоповерховий фон
            TextureFactory._draw_dynamic_bg(surf, w, h, grain_size)

        elif name == "lab_bg":     # Фон типу лабораторії
            TextureFactory._draw_lab_bg(surf, w, h)
        elif name == "cave_bg":    # Фон типу звичних печер
            TextureFactory._draw_cave_bg(surf, w, h, grain_size)
        elif name == "crystal_bg": # Фон типу кристальних печер
            TextureFactory._draw_crystal_bg(surf, w, h, grain_size)
        elif name == "toxic_bg":   # Фон типу отруйних печер
            TextureFactory._draw_toxic_bg(surf, w, h, grain_size)

        else:                      # Резервний колір на випадок помилки
            surf.fill((200, 200, 200))

        # Оптимізація для швидшого рендерингу
        surf = surf.convert() 
        TextureFactory._cache[key] = surf
        return surf

    # ------- Конвеєри стилів ------- 

    # Платформи всіх призначень ---------------------
    @staticmethod
    def _draw_sedimentary(surf, w, h, gs):
        """Осадова порода: горизонтальні марсіанські шари з мікротріщинами."""
        base_red = 160
        layer_h = max(4, h // random.randint(3, 5))
        for y in range(0, h, layer_h):
            color = (base_red + random.randint(-20, 20), 60, 30)
            pygame.draw.rect(surf, color, (0, y, w, layer_h))
            
            # Ерозія та накладання піксельних зсувів на межах шарів
            for x in range(0, w, gs):
                if random.random() > 0.4:
                    pygame.draw.rect(surf, color, (x, y - gs, gs, gs))
                # Рідкісні темні вкраплення древньої породи
                if random.random() > 0.96:
                    pygame.draw.rect(surf, (90, 30, 15), (x, y + random.randint(0, layer_h-gs), gs * 2, gs))

    @staticmethod
    def _draw_regolith(surf, w, h, gs):
        """Пористий реголіт: база + пори з ілюзією глибини (світлотінь)."""
        surf.fill((80, 30, 20))
        # Малюємо пори
        for _ in range((w * h) // (gs * 65)):
            x = random.randrange(0, w, gs)
            y = random.randrange(0, h, gs)
            # Глибока тінь пори
            pygame.draw.rect(surf, (40, 15, 10), (x, y, gs, gs))
            # Освітлений нижній край пори для 16-бітного об'єму
            if y + gs < h:
                pygame.draw.rect(surf, (110, 45, 30), (x, y + gs, gs, max(1, gs // 2)))

    @staticmethod
    def _draw_crystal(surf, w, h, gs):
        """Кристалічна порода: насичені грані, чітка внутрішня геометрія."""
        crystal_presets = [
            (0, 160, 190),   # Глибокий ціан
            (140, 40, 180),  # Аметистовий
            (40, 160, 40),   # Смарагдовий
            (210, 140, 0)    # Янтарний
        ]
        base_color = random.choice(crystal_presets)
        bright_color = tuple(min(255, c + 75) for c in base_color)
        dark_color = tuple(max(0, c - 50) for c in base_color)
        
        surf.fill(base_color)
        
        # Двоколірна рамка для ефекту огранювання
        pygame.draw.rect(surf, bright_color, (0, 0, w, h), max(1, gs // 2))
        pygame.draw.rect(surf, dark_color, (max(1, gs // 2), max(1, gs // 2), w - gs, h - gs), 1)
        
        # Кристалічні вкраплення-іскри
        num_sparkles = (w * h) // (gs * 50)
        for _ in range(num_sparkles):
            x = random.randint(gs, w - gs * 2)
            y = random.randint(gs, h - gs * 2)
            # Малюємо маленькі "ромбики" з двох пікселів
            pygame.draw.rect(surf, bright_color, (x, y, gs, gs))
            if x + gs < w:
                surf.set_at((x + gs, y), bright_color)

    @staticmethod
    def _draw_lab(surf, w, h):
        """Лабораторія: металеві плити з заклепками та фаскою."""
        colors = [(180, 220, 230), (140, 180, 200), (200, 240, 255), (100, 140, 160)]
        size = 32 # Фіксована плитка під сітку
        for x in range(0, w, size):
            for y in range(0, h, size):
                color = random.choice(colors)
                pygame.draw.rect(surf, color, (x, y, size, size))
                
                # Світла внутрішня лінія (блиск зверху-зліва)
                pygame.draw.line(surf, (255, 255, 255), (x, y), (x + size, y), 1)
                pygame.draw.line(surf, (255, 255, 255), (x, y), (x, y + size), 1)
                
                # Темна зовнішня лінія (тінь знизу-справа)
                pygame.draw.line(surf, (50, 70, 80), (x + size - 1, y), (x + size - 1, y + size), 1)
                pygame.draw.line(surf, (50, 70, 80), (x, y + size - 1), (x + size, y + size - 1), 1)
                
                # Технологічні гвинти по кутах кожної плити
                screw_color = (40, 50, 60)
                for sx, sy in [(x + 3, y + 3), (x + size - 5, y + 3), (x + 3, y + size - 5), (x + size - 5, y + size - 5)]:
                    pygame.draw.rect(surf, screw_color, (sx, sy, 2, 2))

    @staticmethod
    def _draw_toxic(surf, w, h, gs):
        """Токсичний камінь: кислотні прожилки, що роз'їдають марсіанську руду."""
        surf.fill((20, 55, 12)) 
        # Малюємо кластери отруйних виділень
        for _ in range((w * h) // (gs * 6)):
            x = random.randrange(0, w, gs)
            y = random.randrange(0, h, gs)
            color = random.choice([(45, 95, 18), (110, 215, 45), (15, 35, 5)])
            pygame.draw.rect(surf, color, (x, y, gs, gs))
            # Додатковий піксель вбік для створення ефекту органічних покладів
            if random.random() > 0.6:
                pygame.draw.rect(surf, color, (x + (gs if random.random() > 0.5 else -gs), y, gs, gs))

    # Портали -----------------------------------------
    @staticmethod
    def _draw_portal(surf, w, h, color, gs):
        """Портали: смугасті енергетичні аномалії з подвійним заломленням ліній."""
        base_dark = [max(0, c - 110) for c in color]
        surf.fill(base_dark)
        
        # Малюємо основні енергетичні лінії
        for i in range(-w, w + h, gs * 4):
            pygame.draw.line(surf, color, (i, 0), (i + h, h), gs)
            # Додаткова суб-лінія для змішування спектра
            sub_color = tuple(min(255, c + 40) for c in color)
            pygame.draw.line(surf, sub_color, (i + gs * 2, 0), (i + h + gs * 2, h), max(1, gs // 2))

        # Яскраві квантові спалахи
        sparkle = [min(255, c + 120) for c in color]
        for _ in range((w * h) // (gs * 25)):
            x, y = random.randint(0, w - 1), random.randint(0, h - 1)
            surf.set_at((x, y), sparkle)

    @staticmethod
    def _draw_jump_pad(surf, w, h, color, gs):
        """Аномальна рідина: закіпаюча желеподібна субстанція з рамкою."""
        base_dark = [max(10, c - 140) for c in color]
        surf.fill(base_dark)

        # Бульбашки всередині рідини pad-а
        for _ in range((w * h) // (gs * 15)): 
            x = random.randint(1, w - gs - 1)
            y = random.randint(1, h - gs - 1)
            dot_color = random.choice([color, [min(255, c + 70) for c in color]])
            # Малюємо зернисті блоки
            pygame.draw.rect(surf, dot_color, (x, y, gs, max(1, gs // 2)))
            
        # Силова стрибкова рамка
        pygame.draw.rect(surf, color, (0, 0, w, h), 1)
        bright_border = tuple(min(255, c + 90) for c in color)
        # Бліки на кутах рамки
        surf.set_at((0, 0), bright_border)
        surf.set_at((w - 1, 0), bright_border)
        surf.set_at((0, h - 1), bright_border)
        surf.set_at((w - 1, h - 1), bright_border)

    # Фон головний ------------------------------------
    @staticmethod
    def _draw_dynamic_bg(surf, w, h, gs):
        color_top         = (200, 110, 70) # Рудий марсіанський пісок
        color_underground = (40, 15, 10)   # Темна глибинна порода
        
        transition_y = int(h * 0.5) 
        transition_range = 240 # Компактніша зона для виразного піксель-арту
        
        pygame.draw.rect(surf, color_top, (0, 0, w, transition_y))
        pygame.draw.rect(surf, color_underground, (0, transition_y, w, h - transition_y))

        # Стилізований під 16-bit дизеринг (хрестоподібне змішування на межі)
        for y in range(transition_y - transition_range // 2, transition_y + transition_range // 2, gs):
            if y < 0 or y > h - gs: continue
            # Ймовірність появи нижнього кольору зростає з глибиною
            ratio = (y - (transition_y - transition_range // 2)) / transition_range
            
            for x in range(0, w, gs):
                # Шаховий або випадковий дизеринг в залежності від глибини
                if random.random() < ratio:
                    if (x // gs + y // gs) % 2 == 0 or random.random() > 0.3:
                        pygame.draw.rect(surf, color_underground, (x, y, gs, gs))
                else:
                    if (x // gs + y // gs) % 2 != 0 and random.random() > 0.7:
                        pygame.draw.rect(surf, color_top, (x, y, gs, gs))

        # Загальний шум у товщі землі
        for _ in range((w * (h - transition_y)) // (gs * 20)):
            x = random.randint(0, w - gs)
            y = random.randint(transition_y, h - gs)
            if random.random() > 0.7:
                pygame.draw.rect(surf, (55, 20, 12), (x, y, gs, gs // 2 if gs > 1 else 1))
            else:
                pygame.draw.rect(surf, (25, 8, 4), (x, y, gs, gs // 2 if gs > 1 else 1))

    # Фоно об'єкти ------------------------------------
    @staticmethod
    def _draw_lab_bg(surf, w, h):
        surf.fill((35, 45, 55))
        tile = 32
        
        # Задній каркас стіни (плити)
        for x in range(0, w, tile):
            for y in range(0, h, tile):
                pygame.draw.rect(surf, (43, 53, 63), (x, y, tile, tile), 1)

        # Смугасті високовольтні кабелі
        cable_colors = [(0, 90, 128), (128, 60, 0), (40, 128, 50)]
        num_chains = (w * h) // 14000 + 2 

        for _ in range(num_chains):
            color = random.choice(cable_colors)
            stripe_color = tuple(min(255, c + 40) for c in color)
            
            curr_x = random.randrange(0, w, tile) + tile // 2
            curr_y = random.randrange(0, h, tile) + tile // 2
            
            num_segments = random.randint(3, 6)
            for _ in range(num_segments):
                dx, dy = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
                length = random.randint(2, 4) * tile

                next_x = curr_x + dx * length
                next_y = curr_y + dy * length
                
                # Малюємо кабель
                pygame.draw.line(surf, color, (curr_x, curr_y), (next_x, next_y), 3)
                
                # Наносимо ізоляційні смужки на кабель (пунктирний ефект)
                if dx != 0:
                    for sx in range(min(curr_x, next_x), max(curr_x, next_x), 6):
                        pygame.draw.line(surf, stripe_color, (sx, curr_y - 1), (sx, curr_y + 1), 1)
                else:
                    for sy in range(min(curr_y, next_y), max(curr_y, next_y), 6):
                        pygame.draw.line(surf, stripe_color, (curr_x - 1, sy), (curr_x + 1, sy), 1)

                # Розподільчі коробки в місцях згину
                pygame.draw.rect(surf, (75, 80, 85), (curr_x - 3, curr_y - 3, 6, 6))
                curr_x, curr_y = next_x, next_y

        # Технологічні інтерфейси / Щитки керування
        for _ in range((w * h) // 32000 + 1):
            px = random.randrange(0, w - 24, tile) + 4
            py = random.randrange(0, h - 24, tile) + 4
            pygame.draw.rect(surf, (65, 75, 85), (px, py, 24, 24))
            pygame.draw.rect(surf, (120, 130, 140), (px, py, 24, 24), 1)
            
            # Миготливі індикатори датчиків
            pygame.draw.rect(surf, random.choice([(0, 255, 100), (255, 50, 50)]), (px + 16, py + 4, 4, 4))
            pygame.draw.rect(surf, (200, 200, 50), (px + 4, py + 14, 6, 3))

    @staticmethod
    def _draw_cave_bg(surf, w, h, gs):
        """Суцільний фон печери з виразними тіньовими заглибленнями."""
        base_color = (40, 15, 10)
        surf.fill(base_color)
        num_particles = (w * h) // (gs * 12)

        for _ in range(num_particles):
            rx = random.randint(0, w - gs)
            ry = random.randint(0, h - gs)

            rand_val = random.random()
            if rand_val < 0.18:
                p_color = (55, 22, 14)   # Вивітрені породи
            elif rand_val < 0.42:
                p_color = (22, 8, 4)     # Глибокі ніші-тіні
            else:
                continue

            pygame.draw.rect(surf, p_color, (rx, ry, gs, gs // 2 if gs > 1 else 1))

    @staticmethod
    def _draw_crystal_bg(surf, w, h, gs):
        """Фон кристалічної печери з витриманою дистанцією між друзами."""
        TextureFactory._draw_cave_bg(surf, w, h, gs)

        crystal_presets = [(0, 160, 190), (140, 40, 180), (40, 160, 40), (210, 140, 0)]
        dark_offset = 130 
        light_cr_color = 65 
        
        bg_presets = [tuple(max(8, c - dark_offset) for c in color) for color in crystal_presets]
        
        placed_crystals = []
        min_distance = 64  
        
        num_crystals = (w * h) // 18000 + 1 
        max_attempts = 40 

        for _ in range(num_crystals):
            base_color = random.choice(bg_presets)
            bright_color = tuple(min(255, c + light_cr_color) for c in base_color)
            cw, ch = random.randint(16, 32), random.randint(16, 32)

            for _ in range(max_attempts):
                cx = random.randint(4, w - cw - 4)
                cy = random.randint(4, h - ch - 4)
                new_center = pygame.Vector2(cx + cw // 2, cy + ch // 2)

                too_close = any(new_center.distance_to(old_center) < min_distance for old_center in placed_crystals)
                
                if not too_close:
                    # Градуйована заливка фонового кристалу (напівромб)
                    pygame.draw.rect(surf, base_color, (cx, cy, cw, ch))
                    pygame.draw.rect(surf, bright_color, (cx, cy, cw, ch), 1)
                    
                    # Маленькі внутрішні кристалічні відблиски
                    for _ in range(random.randint(2, 4)):
                        sx = random.randint(cx + 2, cx + cw - 3)
                        sy = random.randint(cy + 2, cy + ch - 3)
                        pygame.draw.rect(surf, bright_color, (sx, sy, max(1, gs // 2), max(1, gs // 2)))
                    
                    placed_crystals.append(new_center)
                    break

    @staticmethod
    def _draw_toxic_bg(surf, w, h, gs):
        """Фон токсичної печери: структуровані радіоактивні плавуни породи."""
        base_underground = (35, 12, 8)
        surf.fill(base_underground)

        for _ in range((w * h) // (gs * 20)):
            rx, ry = random.randint(0, w - gs), random.randint(0, h - gs)
            if random.random() < 0.25:
                pygame.draw.rect(surf, (20, 6, 3), (rx, ry, gs, gs))

        toxic_colors = [(18, 38, 6), (35, 70, 18), (10, 15, 4)]
        placed_clusters = []
        min_distance = 100 
        
        num_clusters = (w * h) // 28000 + 1 
        max_attempts = 45 

        for _ in range(num_clusters):
            cw, ch = random.randint(24, 80), random.randint(24, 80)
            for _ in range(max_attempts):
                cx = random.randint(8, w - cw - 8)
                cy = random.randint(8, h - ch - 8)
                new_center = pygame.Vector2(cx + cw // 2, cy + ch // 2)

                too_close = any(new_center.distance_to(old_center) < min_distance for old_center in placed_clusters)
                
                if not too_close:
                    grains_count = (cw * ch) // (gs * 2) 
                    for _ in range(grains_count):
                        gx = cx + random.randint(0, cw - gs)
                        gy = cy + random.randint(0, ch - gs)
                        grain_color = random.choice(toxic_colors)
                        
                        pygame.draw.rect(surf, grain_color, (gx, gy, gs, gs))
                        # Формуємо горизонтальні пласти радіоактивного сланцю
                        if random.random() > 0.75:
                            pygame.draw.rect(surf, grain_color, (gx, gy, gs * 2, gs))
                            
                    placed_clusters.append(new_center)
                    break


    # Текстура гравця ---------------------------------
    @staticmethod
    def draw_energy_core(surf, base_color, gravity):
        """Енергетичне ядро: технологічний стабілізатор зміщення."""
        w, h = surf.get_size()
        center_x, center_y = w // 2, h // 2
        
        offset_dist = 6
        offset_x = -gravity[0] * offset_dist
        offset_y = -gravity[1] * offset_dist
        core_center = (center_x + offset_x, center_y + offset_y)

        bright_color = tuple(min(c + 100, 255) for c in base_color)
        mid_color = tuple(min(c + 50, 255) for c in base_color)

        surf.fill(base_color)

        # Огранювання енергетичної сфери
        pygame.draw.circle(surf, mid_color, core_center, w // 2.5)
        pygame.draw.circle(surf, bright_color, core_center, w // 5)

        # Перехрестя стабілізації гравітаційного вектора (піксельні піни)
        cross_color = tuple(max(0, c - 40) for c in base_color)
        pygame.draw.line(surf, cross_color, (center_x, 2), (center_x, h - 3), 1)
        pygame.draw.line(surf, cross_color, (2, center_y), (w - 3, center_y), 1)

        # Кутовий відблиск ядра
        glow_pos = (core_center[0] - 2, core_center[1] - 2)
        pygame.draw.circle(surf, (255, 255, 255), glow_pos, 1)

    @staticmethod
    def draw_matrix_flow(surf, base_color, gravity, time_tick):
        """Ефект цифрового потоку: коди з ефектом затухання хвоста."""
        w, h = surf.get_size()
        bg_dark = tuple(max(c - 110, 8) for c in base_color)
        surf.fill(bg_dark)

        num_strips = 8 
        speed = 0.25    

        for i in range(num_strips):
            offset = (i * (w // num_strips)) + 2
            # Визначаємо циклічну позицію голови потоку
            flow_pos = (time_tick * speed + i * 12) % (h if gravity[1] != 0 else w)
            
            # Кольори для створення ефекту згасання (Голова -> Хвіст)
            head_color = (255, 255, 255)
            body_color = tuple(min(255, c + 60) for c in base_color)
            tail_color = base_color
    
            # Напрямок рендерингу цифрового дощу
            if gravity == (0, 1):    # Гравітація вниз
                pygame.draw.rect(surf, tail_color, (offset, flow_pos - 6, 2, 6))
                pygame.draw.rect(surf, body_color, (offset, flow_pos - 2, 2, 3))
                pygame.draw.rect(surf, head_color, (offset, flow_pos, 2, 2))
            elif gravity == (0, -1): # Гравітація вгору
                pygame.draw.rect(surf, tail_color, (offset, h - flow_pos + 2, 2, 6))
                pygame.draw.rect(surf, body_color, (offset, h - flow_pos - 1, 2, 3))
                pygame.draw.rect(surf, head_color, (offset, h - flow_pos - 3, 2, 2))
            elif gravity == (-1, 0): # Гравітація вліво
                pygame.draw.rect(surf, tail_color, (w - flow_pos + 2, offset, 6, 2))
                pygame.draw.rect(surf, body_color, (w - flow_pos - 1, offset, 3, 2))
                pygame.draw.rect(surf, head_color, (w - flow_pos - 3, offset, 2, 2))
            elif gravity == (1, 0):  # Гравітація вправо
                pygame.draw.rect(surf, tail_color, (flow_pos - 6, offset, 6, 2))
                pygame.draw.rect(surf, body_color, (flow_pos - 2, offset, 3, 2))
                pygame.draw.rect(surf, head_color, (flow_pos, offset, 2, 2))
            else:                    # Стан спокою (дефолтний хаотичний потік)
                pygame.draw.rect(surf, body_color, (offset, flow_pos, 2, 6))

    @staticmethod
    def draw_crystalline_shards(surf, base_color, gravity):
        """Ефект ограненого об'ємного каменю з контрастними ребрами."""
        w, h = surf.get_size()
        center = (w // 2, h // 2)

        top_left,    top_right    = (0, 0), (w, 0)
        bottom_left, bottom_right = (0, h), (w, h)
        
        # Напрямок падаючого світла протилежний вектору сили тяжіння
        light_dir = (-gravity[0], -gravity[1])

        shards = [
            {"points": [center, top_left, top_right],    "normal": (0, -1)},   # Верх
            {"points": [center, bottom_left, bottom_right], "normal": (0, 1)}, # Низ
            {"points": [center, top_left, bottom_left],  "normal": (-1, 0)},   # Ліво
            {"points": [center, top_right, bottom_right], "normal": (1, 0)}    # Право
        ]

        for shard in shards:
            dot = shard["normal"][0] * light_dir[0] + shard["normal"][1] * light_dir[1]
            shift = int(dot * 45) 
            shard_color = tuple(max(0, min(255, c + shift)) for c in base_color)
            pygame.draw.polygon(surf, shard_color, shard["points"])

        # Виразні неонові межі граней кристала
        line_color = tuple(max(0, min(255, c + 70)) for c in base_color)
        pygame.draw.line(surf, line_color, center, top_left, 1)
        pygame.draw.line(surf, line_color, center, top_right, 1)
        pygame.draw.line(surf, line_color, center, bottom_left, 1)
        pygame.draw.line(surf, line_color, center, bottom_right, 1)
        pygame.draw.rect(surf, line_color, (0, 0, w, h), 1)

    @staticmethod
    def draw_liquid_lava(surf, base_color, gravity, time_tick):
        """Ефект рідкої плазми: коливання хвилі + бульбашки газу."""
        w, h = surf.get_size()
        top_color = tuple(min(c + 70, 255) for c in base_color)
        surf.fill(top_color)

        wave_height = 4  
        frequency = 0.15 
        speed = 0.006    
        
        points = []
        if gravity[1] != 0:
            is_down = gravity[1] > 0
            for x in range(w + 1):
                wave_y = math.sin(x * frequency + time_tick * speed) * wave_height
                y_pos = (h * 0.45) + wave_y if is_down else (h * 0.55) + wave_y
                points.append((x, y_pos))
            
            if is_down: points.extend([(w, h), (0, h)])
            else: points.extend([(w, 0), (0, 0)])  
        else:
            is_right = gravity[0] > 0
            for y in range(h + 1):
                wave_x = math.sin(y * frequency + time_tick * speed) * wave_height
                x_pos = (w * 0.45) + wave_x if is_right else (w * 0.55) + wave_x
                points.append((x_pos, y))
            
            if is_right: points.extend([(w, h), (w, 0)])
            else: points.extend([(0, h), (0, 0)])
            
        if len(points) > 2:
            pygame.draw.polygon(surf, base_color, points)
            
        # Генерація поодиноких внутрішніх бульбашок у товщі рідини
        bubble_color = tuple(min(c + 110, 255) for c in base_color)
        random.seed(time_tick // 12) # Уповільнюємо хаос зміни позицій бульбашок
        for _ in range(3):
            bx = random.randint(4, w - 5)
            by = random.randint(int(h * 0.6), h - 5)
            surf.set_at((bx, by), bubble_color)
            
        # Герметична рамка контейнера речовини
        pygame.draw.rect(surf, (140, 140, 140), (0, 0, w, h), 2)

    @staticmethod
    def draw_noise_dust_none(surf, base_color, gravity):
        """Пилові частки: кінетична акумуляція маси біля площини опори."""
        w, h = surf.get_size()
        frame_color = tuple(min(c + 45, 255) for c in base_color)
        num_particles = 140 
        
        for _ in range(num_particles):
            # Математичне зміщення щільності до країв під дією гравітації
            if gravity[0] > 0:   
                rx = random.random() ** 0.4
            elif gravity[0] < 0: 
                rx = random.random() ** 2.2
            else:                
                rx = random.random()
                
            if gravity[1] > 0:   
                ry = random.random() ** 0.4
            elif gravity[1] < 0: 
                ry = random.random() ** 2.2
            else:                
                ry = random.random()

            x = int(rx * (w - 2))
            y = int(ry * (h - 2))
            
            var = random.randint(35, 100) 
            p_color = tuple(min(255, c + var) for c in base_color)
            
            # Супер-яскраві енергетичні фотони (10%)
            if random.random() > 0.90: 
                p_color = (255, 255, 255)

            # Малюємо блоки пилу розміром 1х1 або 2x1 для різноманітності текстури
            surf.set_at((x, y), p_color)
            if random.random() > 0.85 and x + 1 < w:
                surf.set_at((x + 1, y), p_color)

        pygame.draw.rect(surf, frame_color, (0, 0, w, h), 2)

    @staticmethod
    def draw_noise_dust(surf, base_color, gravity):
        """Повна перемальовка контейнера пилу."""
        surf.fill(base_color)
        TextureFactory.draw_noise_dust_none(surf, base_color, gravity)

class TextureFactory_claude:
    """Фабрика текстур із кешуванням.

    Усі поверхні генеруються один раз і зберігаються у _cache.
    Ключ кешу: (name, w, h, color) — тому один і той же тип з різними
    розмірами або кольорами зберігається окремо.
    """

    _cache: dict = {}

    # Кольори обведення для кожного типу платформи (Layered Buffer Outline).
    # Значення навмисно темніші за реальний колір: їх накладають «під» плитку
    # як силует-тінь, тому пересвічення виглядало б неправдиво.
    OUTLINE_COLORS = {
        "norm":  (130,  60,  45),   # Тепло-оранжевий силует   (було 220, 110, 90)
        "ore":   ( 30,   5,   5),   # Темно-вугільний           (було  90,  50, 40)
        "lab":   (110, 140, 150),   # Крижаний блиск            (було 200, 230, 240)
        "toxic": ( 15,  40,   5),   # Токсичний зелений         (було  50, 160, 30)
    }

    @staticmethod
    def get_outline_color(p_type: str) -> tuple | None:
        """Повертає колір силуету-підкладки для вказаного типу платформи.

        Повертає None, якщо тип невідомий — це сигнал для рендерера
        не малювати обведення взагалі.
        """
        return TextureFactory.OUTLINE_COLORS.get(p_type)

    @staticmethod
    def get_texture(name: str, w: int, h: int,
                    color: tuple = (200, 200, 200), grain_size: int = 4):
        """Повертає (або генерує) готову поверхню для вказаного імені текстури.

        Перший запит — малюємо, конвертуємо і кешуємо.
        Усі наступні запити з тими самими параметрами — повертаємо із кешу.

        Args:
            name:       Ідентифікатор текстури (напр. "norm", "lab", "portal").
            w, h:       Ширина й висота поверхні в пікселях.
            color:      Основний колір — використовується для порталів і jump pad.
            grain_size: Розмір «зерна» для шумових алгоритмів.
        """
        key = (name, w, h, tuple(color))
        if key in TextureFactory._cache:
            return TextureFactory._cache[key]

        surf = pygame.Surface((w, h))

        # --- Платформи ---
        if   name == "norm":
            TextureFactory._draw_sedimentary(surf, w, h, grain_size)
        elif name == "ore":
            TextureFactory._draw_regolith(surf, w, h, grain_size)
        elif name == "crystal":
            TextureFactory._draw_crystal(surf, w, h, grain_size)
        elif name == "lab":
            TextureFactory._draw_lab(surf, w, h)
        elif name == "toxic":
            TextureFactory._draw_toxic(surf, w, h, grain_size)

        # --- Інтерактивні об'єкти ---
        elif name == "portal":
            TextureFactory._draw_portal(surf, w, h, color, grain_size)
        elif name == "jump_pad":
            TextureFactory._draw_jump_pad(surf, w, h, color, grain_size)

        # --- Фон ---
        elif name == "dynamic_bg":
            TextureFactory._draw_dynamic_bg(surf, w, h, grain_size)
        elif name == "lab_bg":
            TextureFactory._draw_lab_bg(surf, w, h)
        elif name == "cave_bg":
            TextureFactory._draw_cave_bg(surf, w, h, grain_size)
        elif name == "crystal_bg":
            TextureFactory._draw_crystal_bg(surf, w, h, grain_size)
        elif name == "toxic_bg":
            TextureFactory._draw_toxic_bg(surf, w, h, grain_size)

        else:
            # Сіра заглушка — сигнал, що ідентифікатор невідомий.
            surf.fill((200, 200, 200))

        # ВАЖЛИВО: convert() перекладає поверхню у формат дисплея —
        # рендеринг стає значно швидшим, особливо на слабких пристроях.
        surf = surf.convert()
        TextureFactory._cache[key] = surf
        return surf

    # =========================================================================
    # Конвеєри стилів
    # Кожен метод відповідальний за візуальне наповнення свого типу об'єкта.
    # =========================================================================

    # --- Платформи -----------------------------------------------------------

    @staticmethod
    def _draw_sedimentary(surf, w, h, gs):
        """Осадова порода: горизонтальні кольорові шари із зернистим краєм.

        Кількість шарів випадкова (3–5), щоб жодні дві платформи не виглядали
        однаково. Зернистий «перехід» між шарами додає відчуття нашарування.
        """
        base_red = 160
        num_layers = random.randint(3, 5)
        layer_h = max(1, h // num_layers)

        for layer_i, y in enumerate(range(0, h, layer_h)):
            # Кожен шар трохи відрізняється за яскравістю червоного
            r = base_red + random.randint(-20, 20)
            layer_color = (r, 60, 30)
            pygame.draw.rect(surf, layer_color, (0, y, w, layer_h))

            # Зернистий край між шарами — не малюємо для першого рядка,
            # щоб не виходити за межі поверхні вгору.
            if layer_i > 0:
                for x in range(0, w, gs):
                    if random.random() > 0.5:
                        pygame.draw.rect(surf, layer_color, (x, y - gs, gs, gs))

    @staticmethod
    def _draw_regolith(surf, w, h, gs):
        """Пористий реголіт: темна база зі випадковими порами-плямами.

        Імітує вигляд глибинної підземної породи — щільно спресованої
        і майже позбавленої кольору.
        """
        BASE  = (80, 30, 20)
        PORE  = (50, 20, 10)
        surf.fill(BASE)

        num_pores = (w * h) // (gs * 70)
        for _ in range(num_pores):
            x = random.randint(0, w - gs)
            y = random.randint(0, h - gs)
            pygame.draw.rect(surf, PORE, (x, y, gs, gs))

    @staticmethod
    def _draw_crystal(surf, w, h, gs):
        """Кристалічна порода: насичений колір, рамка та вкраплення-іскри.

        Пресети: ціан, аметист, смарагд, бурштин — щоб кожен кристал
        мав власну «дорогоцінну» особистість.
        """
        PRESETS = [
            (  0, 160, 190),   # Глибокий ціан
            (140,  40, 180),   # Аметистовий
            ( 40, 160,  40),   # Смарагдовий
            (210, 140,   0),   # Янтарний
        ]
        base_color   = random.choice(PRESETS)
        bright_color = tuple(min(255, c + 75) for c in base_color)

        surf.fill(base_color)
        # Тонка яскрава рамка підкреслює огранку
        pygame.draw.rect(surf, bright_color, (0, 0, w, h), 2)

        # Іскри всередині — «вкраплення» дрібних граней
        num_sparkles = (w * h) // (gs * 60)
        for _ in range(num_sparkles):
            x = random.randint(3, w - 4)
            y = random.randint(3, h - 4)
            pygame.draw.rect(surf, bright_color, (x, y, gs, gs))

    @staticmethod
    def _draw_lab(surf, w, h):
        """Лабораторна плитка: великі квадрати з відтінками холодного сірого.

        Плитки варіюються за яскравістю — між чотирма пресетами — і розділені
        тонкою білою сіткою, що нагадує стерильний кахель.
        """
        TILE_COLORS = [
            (180, 220, 230),   # Холодний світло-блакитний
            (140, 180, 200),   # Матовий блакитно-сірий
            (200, 240, 255),   # Майже білий льодяний
            (100, 140, 160),   # Темний сланцевий
        ]
        TILE_SIZE = 32

        for x in range(0, w, TILE_SIZE):
            for y in range(0, h, TILE_SIZE):
                color = random.choice(TILE_COLORS)
                pygame.draw.rect(surf, color, (x, y, TILE_SIZE, TILE_SIZE))
                # Тонка біла сітка між плитками
                pygame.draw.rect(surf, (255, 255, 255), (x, y, TILE_SIZE, TILE_SIZE), 1)

    @staticmethod
    def _draw_toxic(surf, w, h, gs):
        """Токсична руда: кислотні відтінки зеленого з густим плямистим шумом.

        Ядерна руда марсу — паливо лабораторій. Рясно «кровоточить» зеленню:
        чим більше плям, тим вища концентрація отрути. Смертельна на дотик.
        """
        BASE = (20, 60, 10)   # Брудно-болотний
        SPOT_COLORS = [
            ( 50, 100, 20),   # Темний кислотний
            (100, 200, 50),   # Яскравий отруйний
            ( 20,  40,  5),   # Майже чорно-зелений
        ]
        surf.fill(BASE)

        num_spots = (w * h) // (gs * 5)
        for _ in range(num_spots):
            x = random.randint(0, w - gs)
            y = random.randint(0, h - gs)
            pygame.draw.rect(surf, random.choice(SPOT_COLORS), (x, y, gs, gs))

    # --- Портали та інтерактивні об'єкти -------------------------------------

    @staticmethod
    def _draw_portal(surf, w, h, color, gs):
        """Тунельний портал: смугастий енергетичний вихор із зерном-шумом.

        Діагональні смуги передають «потік» енергії крізь аномалію.
        Яскраві точки-іскри — залишки матерії, що пройшла крізь нього.
        (Підозріло схоже на щось знайоме... на гравця?!)
        """
        base_dark = tuple(max(0, c - 100) for c in color)
        sparkle   = tuple(min(255, c + 100) for c in color)

        surf.fill(base_dark)

        # Діагональні енергетичні смуги
        for i in range(0, w + h, gs * 4):
            pygame.draw.line(surf, color, (0, i), (i, 0), gs)

        # Випадкові іскри поверх смуг
        num_sparkles = (w * h) // (gs * 30)
        for _ in range(num_sparkles):
            x = random.randint(0, w - 1)
            y = random.randint(0, h - 1)
            surf.set_at((x, y), sparkle)

    @staticmethod
    def _draw_jump_pad(surf, w, h, color, gs):
        """Аномальна рідина-прискорювач: пориста з м'яким опроміненням.

        Розтікається навіть по стелі — тому дрібні краплі розсіяні
        рівномірно по всій поверхні, без тяжіння до низу.
        (Теж підозріло схоже на гравця — але це вже теорія.)
        """
        base_dark   = tuple(max(10, c - 150) for c in color)
        bright_color = tuple(min(255, c + 60) for c in color)

        surf.fill(base_dark)

        # Крапки двох відтінків: нормальний і підсвічений
        num_dots = (w * h) // (gs * 20)
        for _ in range(num_dots):
            x = random.randint(0, w - gs)
            y = random.randint(0, h - gs)
            dot_color = random.choice([color, bright_color])
            pygame.draw.rect(surf, dot_color, (x, y, gs // 2, gs // 2))

        # Тонка рамка — межа рідини
        pygame.draw.rect(surf, color, (0, 0, w, h), 1)

    # --- Фон головний --------------------------------------------------------

    @staticmethod
    def _draw_dynamic_bg(surf, w, h, gs):
        """Двошаровий рухливий фон: марсіанська поверхня + глибоке підземелля.

        Перехід між шарами — широка «піксельна каша», що імітує
        природне розмиття між ґрунтом і скелею. Нижній пласт
        засіяний дрібними вкрапленнями для відчуття глибини.
        """
        COLOR_SURFACE      = (200, 110,  70)   # Рудо-оранжевий Марс
        COLOR_UNDERGROUND  = ( 40,  15,  10)   # Темна стиснута порода

        # 50% висоти — початок підземелля
        transition_y     = int(h * 0.5)
        transition_range = 300

        # Два чіткі прямокутники — база фону
        pygame.draw.rect(surf, COLOR_SURFACE,     (0, 0,            w, transition_y))
        pygame.draw.rect(surf, COLOR_UNDERGROUND, (0, transition_y, w, h - transition_y))

        # «Піксельна каша» на межі — вірогідність появи підземного кольору
        # зростає лінійно від верхньої межі переходу до нижньої.
        half_range = transition_range // 2
        num_border_pixels = (w * transition_range) // (gs * 2)
        for _ in range(num_border_pixels):
            rx = random.randint(0, w - gs)
            ry = random.randint(transition_y - half_range, transition_y + half_range)
            if ry < 0 or ry > h - gs:
                continue
            probability = (ry - (transition_y - half_range)) / transition_range
            c = COLOR_UNDERGROUND if random.random() < probability else COLOR_SURFACE
            pygame.draw.rect(surf, c, (rx, ry, gs, gs))

        # Додаткові вкраплення у підземній частині — тональне збагачення
        num_underground_particles = (w * (h - transition_y)) // (gs * 15)
        for _ in range(num_underground_particles):
            x = random.randint(0, w - gs)
            y = random.randint(transition_y, h - gs)
            r = random.random()
            if   r > 0.8:   # Рідкісні світліші піщинки
                pygame.draw.rect(surf, (60, 25, 15), (x, y, gs // 2, gs // 2))
            elif r < 0.2:   # Темніші глибинні тіні
                pygame.draw.rect(surf, (25, 10,  5), (x, y, gs // 2, gs // 2))

    # --- Фон об'єктів --------------------------------------------------------

    @staticmethod
    def _draw_lab_bg(surf, w, h):
        """Фон лабораторії: темна плиткова сітка з кабелями і щитками.

        Кабелі прокладені ламаними лініями зі з'єднувальними вузлами —
        як справжня промислова проводка. Щитки мають сигнальний вогник,
        що означає: система активна.
        """
        TILE  = 32
        CABLE_COLORS = [
            (  0,  90, 128),   # Синій (дані)
            (128,  60,   0),   # Помаранчевий (живлення)
            ( 40, 128,  50),   # Зелений (заземлення)
        ]

        surf.fill((35, 45, 55))

        # Тонка плиткова сітка — структурна основа лабораторії
        for x in range(0, w, TILE):
            for y in range(0, h, TILE):
                pygame.draw.rect(surf, (45, 55, 65), (x, y, TILE, TILE), 1)

        # --- Системні кабелі ---
        # Кількість ліній залежить від площі поверхні
        num_cables = (w * h) // 15000 + 2
        for _ in range(num_cables):
            color  = random.choice(CABLE_COLORS)
            curr_x = random.randrange(0, w, TILE) + TILE // 2
            curr_y = random.randrange(0, h, TILE) + TILE // 2

            # Кожен кабель — 3–6 сегментів, що ідуть по сітці
            for _ in range(random.randint(3, 6)):
                dx, dy = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
                length = random.randint(2, 5) * TILE

                next_x = curr_x + dx * length
                next_y = curr_y + dy * length
                pygame.draw.line(surf, color, (curr_x, curr_y), (next_x, next_y), 3)
                # З'єднувальний вузол у точці перегину
                pygame.draw.rect(surf, (80, 80, 90), (curr_x - 3, curr_y - 3, 6, 6))
                curr_x, curr_y = next_x, next_y

        # --- Технологічні щитки ---
        num_panels = (w * h) // 35000 + 1
        for _ in range(num_panels):
            px = random.randrange(0, w, TILE) + 4
            py = random.randrange(0, h, TILE) + 4
            # Корпус щитка
            pygame.draw.rect(surf, ( 70,  80,  90), (px, py, 24, 24))
            pygame.draw.rect(surf, (140, 140, 150), (px, py, 24, 24), 1)
            # Зелений сигнальний вогник — система в нормі
            pygame.draw.rect(surf, (0, 255, 100), (px + 16, py + 4, 4, 4))

    @staticmethod
    def _draw_cave_bg(surf, w, h, gs):
        """Фон глибокої печери: суцільна темна порода з тональним шумом.

        Два відтінки вкраплень — світліші піщинки й глибокі тіні —
        надають поверхні «живої» нерівномірності, що відрізняє натуральну
        печеру від просто чорного прямокутника.
        """
        BASE         = (40, 15, 10)
        LIGHT_GRAIN  = (60, 25, 15)   # Освітлені піщинки
        DARK_GRAIN   = (25, 10,  5)   # Глибокі тіні

        surf.fill(BASE)

        num_particles = (w * h) // (gs * 15)
        for _ in range(num_particles):
            rx = random.randint(0, w - gs)
            ry = random.randint(0, h - gs)
            r  = random.random()
            if   r < 0.2:
                color = LIGHT_GRAIN
            elif r < 0.4:
                color = DARK_GRAIN
            else:
                continue
            pygame.draw.rect(surf, color, (rx, ry, gs // 2, gs // 2))

    @staticmethod
    def _draw_crystal_bg(surf, w, h, gs):
        """Фон кристалічної печери: темна порода з вкрапленнями кристалів.

        Кристали розміщуються з мінімальною відстанню між собою —
        щоб уникнути «каші» і натомість створити відчуття рідкісних
        дорогоцінних жил, вкраплених у скелю.
        """
        PRESETS = [
            (  0, 160, 190),   # Глибокий ціан
            (140,  40, 180),   # Аметистовий
            ( 40, 160,  40),   # Смарагдовий
            (210, 140,   0),   # Янтарний
        ]
        DARK_OFFSET  = 120   # Наскільки темнішими є фонові кристали
        BRIGHT_SHIFT =  70   # Яскравість рамки та вкрапок

        bg_presets = [tuple(max(10, c - DARK_OFFSET) for c in p) for p in PRESETS]

        # База — звичайна печера
        TextureFactory._draw_cave_bg(surf, w, h, gs)

        min_distance = 60    # Мінімальна відстань між центрами кристалів
        max_attempts = 50    # Обмеження спроб — захист від нескінченного циклу
        num_crystals = (w * h) // 20000 + 1
        placed: list[pygame.Vector2] = []

        for _ in range(num_crystals):
            base_color   = random.choice(bg_presets)
            bright_color = tuple(min(255, c + BRIGHT_SHIFT) for c in base_color)
            cw = random.randint(15, 35)
            ch = random.randint(15, 35)

            for _ in range(max_attempts):
                cx = random.randint(5, w - cw - 5)
                cy = random.randint(5, h - ch - 5)
                new_center = pygame.Vector2(cx + cw // 2, cy + ch // 2)

                if any(new_center.distance_to(p) < min_distance for p in placed):
                    continue   # Занадто близько — спробуємо ще раз

                # Кристал знайшов місце — малюємо
                pygame.draw.rect(surf, base_color,   (cx, cy, cw, ch))
                pygame.draw.rect(surf, bright_color, (cx, cy, cw, ch), 1)

                # Вкраплення-іскри всередині кристала
                for _ in range(random.randint(2, 5)):
                    sx = random.randint(cx + 2, cx + cw - 4)
                    sy = random.randint(cy + 2, cy + ch - 4)
                    pygame.draw.rect(surf, bright_color, (sx, sy, gs, gs))

                placed.append(new_center)
                break

    @staticmethod
    def _draw_toxic_bg(surf, w, h, gs):
        """Фон токсичної печери: радіоактивна руда у темній породі.

        Структуровані поклади виглядають як жили — скупчення зерен,
        що «просочуються» крізь тріщини в скелі. Дистанція між покладами
        гарантує читабельність без злиття в суцільну масу.
        """
        BASE_UNDERGROUND = (40, 15, 10)
        DARK_GRAIN       = (25, 10,  5)
        TOXIC_GRAIN_COLORS = [
            (20,  40,  8),   # Темний мох
            (40,  80, 20),   # Кислотний середній
            (10,  15,  5),   # Майже чорно-зелений
        ]

        surf.fill(BASE_UNDERGROUND)

        # Фоновий шум — та ж текстура печери, але тонша
        num_base_particles = (w * h) // (gs * 20)
        for _ in range(num_base_particles):
            rx = random.randint(0, w - gs)
            ry = random.randint(0, h - gs)
            if random.random() < 0.2:
                pygame.draw.rect(surf, DARK_GRAIN, (rx, ry, gs // 2, gs // 2))

        # Структуровані поклади токсичної руди
        min_distance = 110   # Відстань між центрами покладів
        max_attempts = 50
        num_clusters = (w * h) // 30000 + 1
        placed: list[pygame.Vector2] = []

        for _ in range(num_clusters):
            cw = random.randint(20, 100)
            ch = random.randint(20, 100)

            for _ in range(max_attempts):
                cx = random.randint(10, w - cw - 10)
                cy = random.randint(10, h - ch - 10)
                new_center = pygame.Vector2(cx + cw // 2, cy + ch // 2)

                if any(new_center.distance_to(p) < min_distance for p in placed):
                    continue

                # Малюємо покрад зернами різного розміру
                num_grains = (cw * ch) // (gs * 2)
                for _ in range(num_grains):
                    gx    = cx + random.randint(0, cw - gs)
                    gy    = cy + random.randint(0, ch - gs)
                    gcolor = random.choice(TOXIC_GRAIN_COLORS)
                    pygame.draw.rect(surf, gcolor, (gx, gy, gs, gs))
                    # 20% зерен — подвійний розмір для «жирніших» вкраплень
                    if random.random() > 0.8:
                        pygame.draw.rect(surf, gcolor, (gx, gy, gs * 2, gs))

                placed.append(new_center)
                break

    # --- Текстури гравця -----------------------------------------------------

    @staticmethod
    def draw_energy_core(surf, base_color: tuple, gravity: tuple):
        """Малює динамічне енергетичне ядро гравця.

        Ядро завжди «спливає» проти вектора гравітації — воно ніби
        намагається вирватись у протилежний бік. Три шари (фон, середина,
        центр) + відблиск дають відчуття глибини і власного світіння.

        Args:
            surf:       Поверхня спрайту (зазвичай квадратна).
            base_color: Основний адаптивний колір гравця.
            gravity:    Кортеж напрямку гравітації, напр. (0, 1) або (-1, 0).
        """
        w, h = surf.get_size()
        center_x, center_y = w // 2, h // 2

        # Ядро зміщується ПРОТИ гравітації — відчуття «підйомної сили»
        offset_dist = 6
        core_center = (
            center_x - gravity[0] * offset_dist,
            center_y - gravity[1] * offset_dist,
        )

        # Три рівні яскравості: база → середній → яскравий центр
        mid_color    = tuple(min(c + 50,  255) for c in base_color)
        bright_color = tuple(min(c + 100, 255) for c in base_color)

        # Фон (найтемніший шар — «оболонка»)
        surf.fill(base_color)
        # Середній ореол
        pygame.draw.circle(surf, mid_color,    core_center, w // 2)
        # Яскраве внутрішнє ядро
        pygame.draw.circle(surf, bright_color, core_center, w // 5)
        # Мікро-відблиск — «зірочка» зі зміщенням 2 пікселі
        glow_pos = (core_center[0] - 2, core_center[1] - 2)
        pygame.draw.circle(surf, (255, 255, 255), glow_pos, 2)

    @staticmethod
    def draw_matrix_flow(surf, base_color: tuple, gravity: tuple, time_tick: int):
        """Ефект цифрового потоку: смужки «дощу» у напрямку гравітації.

        Смужки рухаються синхронно з `time_tick`, кожна зі своїм зсувом —
        тому рух здається паралельним, але не механічним.

        Args:
            time_tick: Лічильник кадрів від зовнішнього циклу.
        """
        w, h = surf.get_size()
        bg_dark     = tuple(max(c - 100, 10)  for c in base_color)
        strip_color = tuple(min(c +  50, 255) for c in base_color)

        surf.fill(bg_dark)

        NUM_STRIPS = 8
        SPEED      = 0.2   # Пікселів за тік

        for i in range(NUM_STRIPS):
            offset   = (i * (w // NUM_STRIPS)) + 3
            flow_pos = int(time_tick * SPEED + i * 15)

            if   gravity == ( 0,  1):   # Вниз
                y = flow_pos % h
                pygame.draw.rect(surf, strip_color, (offset, y,        2, 10))
            elif gravity == ( 0, -1):   # Вгору
                y = h - flow_pos % h
                pygame.draw.rect(surf, strip_color, (offset, y,        2, 10))
            elif gravity == (-1,  0):   # Вліво
                x = w - flow_pos % w
                pygame.draw.rect(surf, strip_color, (x,      offset,  10,  2))
            elif gravity == ( 1,  0):   # Вправо
                x = flow_pos % w
                pygame.draw.rect(surf, strip_color, (x,      offset,  10,  2))
            else:                       # Нульова гравітація — статичний дощ
                y = flow_pos % h
                pygame.draw.rect(surf, strip_color, (offset, y,        2,  8))

    @staticmethod
    def draw_crystalline_shards(surf, base_color: tuple, gravity: tuple):
        """Ефект ограненого каменю: чотири грані з динамічним освітленням.

        Світло завжди б'є ПРОТИ гравітації, тому верхня грань (відносно
        напрямку падіння) завжди світліша — як на справжньому кристалі.
        Скалярний добуток (dot product) нормалі й вектора світла визначає
        яскравість кожної грані: від -1 (глибока тінь) до +1 (відблиск).
        """
        w, h = surf.get_size()
        center = (w // 2, h // 2)

        # Кути прямокутного спрайту
        TL, TR = (0, 0),  (w, 0)
        BL, BR = (0, h),  (w, h)

        # Вектор світла — протилежний гравітації
        light = (-gravity[0], -gravity[1])

        shards = [
            {"points": [center, TL, TR], "normal": ( 0, -1)},   # Верхня грань
            {"points": [center, BL, BR], "normal": ( 0,  1)},   # Нижня грань
            {"points": [center, TL, BL], "normal": (-1,  0)},   # Ліва грань
            {"points": [center, TR, BR], "normal": ( 1,  0)},   # Права грань
        ]

        for shard in shards:
            nx, ny = shard["normal"]
            # dot > 0 → назустріч світлу → світліше; dot < 0 → в тіні → темніше
            dot   = nx * light[0] + ny * light[1]
            shift = int(dot * 40)
            color = tuple(max(0, min(255, c + shift)) for c in base_color)
            pygame.draw.polygon(surf, color, shard["points"])

        # Тонкі ребра граней — підкреслюють геометрію огранки
        edge_color = tuple(max(0, min(255, c + 60)) for c in base_color)
        pygame.draw.line(surf, edge_color, center, TL, 1)
        pygame.draw.line(surf, edge_color, center, TR, 1)
        pygame.draw.line(surf, edge_color, center, BL, 1)
        pygame.draw.line(surf, edge_color, center, BR, 1)
        pygame.draw.rect(surf, edge_color, (0, 0, w, h), 1)

    @staticmethod
    def draw_liquid_lava(surf, base_color: tuple, gravity: tuple, time_tick: int):
        """Ефект рідкого наповнювача: анімована хвиля «рівня рідини».

        Верхня (порожня) частина — яскравіша; нижня (заповнена рідиною) —
        основний колір. Хвиля синусоїдальна й повільно рухається з часом.
        Рамка позначає межі ємності.

        (Той самий матеріал, з якого зроблений гравець? Лише гіпотеза.)
        """
        w, h = surf.get_size()
        top_color = tuple(min(c + 80, 255) for c in base_color)
        surf.fill(top_color)

        WAVE_AMP  = 5      # Амплітуда хвилі в пікселях
        FREQUENCY = 0.1    # Просторова частота
        SPEED     = 0.005  # Швидкість руху фази

        points = []

        if gravity[1] != 0:
            # Вертикальна гравітація — хвиля горизонтальна
            is_down = gravity[1] > 0
            base_y  = h * 0.4 if is_down else h * 0.6
            for x in range(w + 1):
                wave_y = math.sin(x * FREQUENCY + time_tick * SPEED) * WAVE_AMP
                points.append((x, base_y + wave_y))
            if is_down:
                points.extend([(w, h), (0, h)])
            else:
                points.extend([(w, 0), (0, 0)])
        else:
            # Горизонтальна гравітація — хвиля вертикальна
            is_right = gravity[0] > 0
            base_x   = w * 0.4 if is_right else w * 0.6
            for y in range(h + 1):
                wave_x = math.sin(y * FREQUENCY + time_tick * SPEED) * WAVE_AMP
                points.append((base_x + wave_x, y))
            if is_right:
                points.extend([(w, h), (w, 0)])
            else:
                points.extend([(0, h), (0, 0)])

        if len(points) > 2:
            pygame.draw.polygon(surf, base_color, points)

        # Рамка ємності — нейтральний сірий, щоб не конкурувати з кольором рідини
        pygame.draw.rect(surf, (180, 180, 180), (0, 0, w, h), 2)

    @staticmethod
    def draw_noise_dust_none(surf, base_color: tuple, gravity: tuple):
        """Малює шар піщаних частинок поверх існуючого вмісту поверхні.

        Частинки групуються біля краю, куди тягне гравітація: степеневий
        розподіл (r ** 0.5 або r ** 2.0) змушує більшість точок «осідати»
        ближче до відповідного боку. 10% частинок — білі «зірочки».

        Цей метод НЕ заливає фон — лише додає частинки поверх того,
        що вже є. Для повної текстури використовуй draw_noise_dust.
        """
        w, h = surf.get_size()
        frame_color   = tuple(min(c + 40, 255) for c in base_color)
        NUM_PARTICLES = max(50, (w * h) // 80)   # Масштабується з розміром

        for _ in range(NUM_PARTICLES):
            # Розподіл по X залежить від горизонтальної гравітації
            if   gravity[0] > 0:
                rx = random.random() ** 0.5   # Більше частинок праворуч
            elif gravity[0] < 0:
                rx = random.random() ** 2.0   # Більше частинок ліворуч
            else:
                rx = random.random()          # Рівномірно

            # Розподіл по Y залежить від вертикальної гравітації
            if   gravity[1] > 0:
                ry = random.random() ** 0.5   # Більше частинок знизу
            elif gravity[1] < 0:
                ry = random.random() ** 2.0   # Більше частинок зверху
            else:
                ry = random.random()          # Рівномірно

            x = int(rx * (w - 2))
            y = int(ry * (h - 2))

            if random.random() > 0.9:
                p_color = (255, 255, 255)   # Яскрава «зірочка»
            else:
                var     = random.randint(40, 120)
                p_color = tuple(min(255, c + var) for c in base_color)

            pygame.draw.rect(surf, p_color, (x, y, 2, 2))

        # Тонка рамка — підкреслює межі об'єкта
        pygame.draw.rect(surf, frame_color, (0, 0, w, h), 2)

    @staticmethod
    def draw_noise_dust(surf, base_color: tuple, gravity: tuple):
        """Повна текстура пилу: суцільна заливка + шар частинок.

        Спочатку заливає поверхню основним кольором, потім накладає
        draw_noise_dust_none зі своїм степеневим розподілом частинок.
        """
        surf.fill(base_color)
        TextureFactory.draw_noise_dust_none(surf, base_color, gravity)



# M.
