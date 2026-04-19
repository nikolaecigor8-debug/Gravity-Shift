import pygame

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
        # --- ФІЗИЧНІ СТАТИ (Hitbox) ---
        self.size = 50
        self.rect = pygame.Rect(x, y, self.size, self.size) # Логічний квадрат
        
        # --- ХАРАКТЕРИСТИКИ ---
        self.speed = 6           # Швидкість руху (перпендикулярно гравітації)
        self.jump_power = 16     # Сила стрибка
        self.gravity_force = 0.6 # Потужність тяжіння
        
        # Напрям гравітації: (x,y). 
        # (0,1) - вниз, (0,-1) - вгору, (1,0) - вправо, (-1,0) - вліво
        self.gravity_vec = pygame.Vector2(0, 1) 
        
        # --- ФІЗИКА ---
        self.vel = pygame.Vector2(0, 0)
        self.on_ground = False #для повноцінної роботи
        
        # --- ГРАФІКА (Fast Fall) ---
        self.is_fast_falling = False
        self.base_image = pygame.Surface((self.size, self.size))
        self.base_image.fill((0, 200, 255))
        self.image = self.base_image.copy()

        # --- СИСТЕМА КОЛЬОРІВ ---
        self.presets = {
            "classic": {
                (0, 1): (0, 255, 255),  # Блакитний
                (0, -1): (255, 80, 80), # Червной/Корал
                (-1, 0): (255, 200, 0), # Золотий
                (1, 0): (100, 255, 100) # Салатовий
            },
            "cyber": {
                (0, 1): (180, 0, 255),  # Фіолетовий
                (0, -1): (255, 255, 0), # Жовтий
                (-1, 0): (0, 255, 255), # Бірюзовий
                (1, 0): (255, 150, 0)   # Помаранчевий
            }
        }
        self.current_preset = "classic"
        self.streetfly_flash = False
        
        self.base_image = pygame.Surface((self.size, self.size))
        self.update_color() # Метод, який ми створимо нижче
        self.image = self.base_image.copy()

    def handle_input(self):
            keys = pygame.key.get_pressed()
            
            # 1. ОБНУЛЕННЯ ШВИДКОСТІ (перпендикулярно гравітації)
            # Якщо падаємо по Y, обнуляємо X. Якщо по X — обнуляємо Y.
            if self.gravity_vec.y != 0:
                self.vel.x = 0
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:  self.vel.x = -self.speed
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.vel.x = self.speed
            else:
                self.vel.y = 0
                if keys[pygame.K_UP] or keys[pygame.K_w]:    self.vel.y = -self.speed
                if keys[pygame.K_DOWN] or keys[pygame.K_s]:  self.vel.y = self.speed
            #PS: wasd буде пресетом в налаштуваннях, одночасної дії неповинно бути.

            # 2. СТРИБОК (завжди ВГОРУ, якщо гравітація ВНИЗ)
            # Визначаємо "клавішу стрибка" як ту, що протилежна вектору гравітації
            jump_key = None
            fall_key = None

            if self.gravity_vec == (0, 1):   # Гравітація вниз
                jump_key, fall_key = pygame.K_UP, pygame.K_DOWN
            elif self.gravity_vec == (0, -1): # Гравітація вгору
                jump_key, fall_key = pygame.K_DOWN, pygame.K_UP
            elif self.gravity_vec == (1, 0):  # Гравітація вправо
                jump_key, fall_key = pygame.K_LEFT, pygame.K_RIGHT
            elif self.gravity_vec == (-1, 0): # Гравітація вліво
                jump_key, fall_key = pygame.K_RIGHT, pygame.K_LEFT

            # Виконання стрибка
            if jump_key and keys[jump_key] and self.on_ground:
                self.vel = -self.gravity_vec * self.jump_power
                self.on_ground = False

            # Агресивне падіння
            self.is_fast_falling = keys[fall_key] if fall_key else False

    def set_gravity(self, x, y):
        """Зміна напрямку гравітації та оновлення кольору згідно з пресетом"""
        self.gravity_vec = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0) # Скидаємо інерцію

        # Використовуємо метод оновлення кольору, який працює з пресетами
        self.update_color()

    def apply_physics(self, platforms):
        # 1. Перед початком перевірок скидаємо стан "на землі"
        self.on_ground = False

        # 2. Додаємо силу тяжіння до швидкості
        # Додати ліміт щоб швидкість не сягнула шв світла
        self.vel += self.gravity_vec * self.gravity_force

        # 3. Додатковий імпульс для швидкого падіння (якщо натиснуто S/Shift)
        if self.is_fast_falling:
            self.vel += self.gravity_vec * 2.0

        # --- ЕТАП Х (Горизонтальний рух) ---
        self.rect.x += self.vel.x
        for wall in platforms:
            if self.rect.colliderect(wall.rect):
                if self.vel.x > 0: # Врізалися правою стороною
                    self.rect.right = wall.rect.left
                elif self.vel.x < 0: # Врізалися лівою стороною
                    self.rect.left = wall.rect.right
                
                # Перевірка на "землю" (якщо гравітація горизонтальна)
                if (self.vel.x * self.gravity_vec.x) > 0:
                    self.on_ground = True
                
                self.vel.x = 0 # Зупиняємо рух по X

        # Перевірка платформ (Y)
        for wall in platforms:
            if self.rect.colliderect(wall.rect):
                # Якщо падаємо (vel.y > 0) — врізалися низом. Якщо летимо (vel.y < 0) — верхом.
                hit_dir = 1 if self.vel.y > 0 else -1
                
                if hit_dir == 1: self.rect.bottom = wall.rect.top
                else: self.rect.top = wall.rect.bottom

                # ГОЛОВНИЙ ФІКС: Стаємо на землю, тільки якщо напрямок удару збігається з напрямком гравітації
                # PS: Був прикол з прилипанням до стелі затиснутим стрибком
                if hit_dir == self.gravity_vec.y:
                    self.on_ground = True
                
                self.vel.y = 0
    
    def apply_physics_wiht_window(self, platforms):
        # 1. Скидаємо стан перед прорахунком
        self.on_ground = False
        
        # 2. Гравітація та швидке падіння
        self.vel += self.gravity_vec * self.gravity_force
        if self.is_fast_falling:
            self.vel += self.gravity_vec * 2.0

        # --- ЕТАП Х (Горизонталь) ---
        self.rect.x += self.vel.x
        
        # Перевірка меж вікна (X)
        if self.rect.left < 0:
            self.rect.left = 0
            self.vel.x = 0
            if self.gravity_vec.x == -1: self.on_ground = True
        elif self.rect.right > 800:
            self.rect.right = 800
            self.vel.x = 0
            if self.gravity_vec.x == 1: self.on_ground = True

        # Перевірка платформ (X)
        for wall in platforms:
            if self.rect.colliderect(wall.rect):
                if self.vel.x > 0: self.rect.right = wall.rect.left
                elif self.vel.x < 0: self.rect.left = wall.rect.right
                
                if (self.vel.x * self.gravity_vec.x) > 0 or self.gravity_vec.x != 0:
                    self.on_ground = True
                self.vel.x = 0

        # --- ЕТАП Y (Вертикаль) ---
        self.rect.y += self.vel.y
        
        # Перевірка меж вікна (Y)
        if self.rect.top < 0:
            self.rect.top = 0
            self.vel.y = 0
            if self.gravity_vec.y == -1: self.on_ground = True
        elif self.rect.bottom > 600:
            self.rect.bottom = 600
            self.vel.y = 0
            if self.gravity_vec.y == 1: self.on_ground = True

        # Перевірка платформ (Y)
        for wall in platforms:
            if self.rect.colliderect(wall.rect):
                # Якщо падаємо (vel.y > 0) — врізалися низом. Якщо летимо (vel.y < 0) — верхом.
                hit_dir = 1 if self.vel.y > 0 else -1
                
                if hit_dir == 1: self.rect.bottom = wall.rect.top
                else: self.rect.top = wall.rect.bottom

                # ГОЛОВНИЙ ФІКС: Стаємо на землю, тільки якщо напрямок удару збігається з напрямком гравітації
                # PS: Був прикол з прилипанням до стелі затиснутим стрибком
                if hit_dir == self.gravity_vec.y:
                    self.on_ground = True
                
                self.vel.y = 0

        
            ''' Якщо раптом ти це знайшов, це фан штучка щоб грат від перемінни гравітації.
                Вона вставляється замість "#" (28 стр.), і може випликати помилки чи конфліктну реакцію при змінні керування! '''
            # if e.key == K_s: player.set_gravity(0, 1)   # S - вниз
            # if e.key == K_w: player.set_gravity(0, -1)  # W - вгору
            # if e.key == K_a: player.set_gravity(-1, 0)  # A - вліво
            # if e.key == K_d: player.set_gravity(1, 0)   # D - вправо

    def draw(self, screen):
        # ВАЖЛИВО: Центруємо розтягнуте зображення по центру квадратного хітбокса
        # Це дозволяє гравцю візуально розтягуватися в обидві сторони одночасно,
        # не змінюючи точку зіткнення.
        img_rect = self.image.get_rect(center=self.rect.center)
        screen.blit(self.image, img_rect)
    
    def update_color(self):
        """Оновлює базовий колір згідно з поточним пресетом та гравітацією"""
        color = self.presets[self.current_preset].get(tuple(self.gravity_vec), (255, 255, 255))
        self.base_image.fill(color)
        self.image = self.base_image.copy()

    def update_visuals(self):
            """Ефект 'резинки' + Стрітфлай спалах"""
            if self.is_fast_falling:
                stretch, shrink = 1.4, 0.7
                if self.gravity_vec.y != 0:
                    new_w, new_h = int(self.size * shrink), int(self.size * stretch)
                else:
                    new_w, new_h = int(self.size * stretch), int(self.size * shrink)
                self.image = pygame.transform.scale(self.base_image, (new_w, new_h))
            else:
                self.image = self.base_image.copy()

            # ЕФЕКТ СТРІТФЛАЙ (Білий спалах)
            if self.streetfly_flash:
                self.image.fill((255, 255, 255)) 
                self.streetfly_flash = False

    def apply_streetfly(self):
        """Механіка Стрітфлай: обнуляємо швидкість, щоб скинути накопичене прискорення падіння."""
        self.vel = pygame.Vector2(0, 0)
        self.streetfly_flash = True  # Активуємо спалах


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill((150, 150, 150)) # Сірий колір
        self.rect = self.image.get_rect(topleft=(x, y))

 