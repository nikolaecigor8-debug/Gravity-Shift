import pygame
import random

WIDTH = 800
HEIGHT = 600
FPS = 60

MARS_RED = (156, 46, 15)
DEEP_SPACE = (20, 10, 15)
MOUNTAIN_COLOR = (80, 30, 20)
PLATFORM_COLOR = (120, 40, 20)
DUST_COLOR = (200, 100, 50)
WHITE = (255, 255, 255)

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(PLATFORM_COLOR)
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 0)
        self.life = 255 # Прозорість (час життя)
        self.size = random.randint(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 5 # Частинка зникає

    def draw(self, surface, scroll):
        if self.life > 0:
            # Малюємо частинку з урахуванням прозорості
            p_surf = pygame.Surface((self.size, self.size))
            p_surf.set_alpha(self.life)
            p_surf.fill(DUST_COLOR)
            surface.blit(p_surf, (self.x - scroll, self.y))

class Player(pygame.sprite.Sprite):
    def __init__(self, platforms):
        super().__init__()
        self.colors = [
            (255, 255, 255), 
            (255, 255, 0),  
            (0, 0, 255),  
            (0, 255, 0), 
            (255, 165, 0)  
        ]
        self.current_color_index = 0
        self.animation_timer = 0
        
        self.image = pygame.Surface((40, 40))
        self.image.fill(self.colors[self.current_color_index])
        self.rect = self.image.get_rect()
        
        self.pos = pygame.math.Vector2(100, HEIGHT - 100)
        self.vel = pygame.math.Vector2(0, 0)
        self.acc = pygame.math.Vector2(0, 0)
        
        self.GRAVITY = 0.5
        self.FRICTION = -0.12
        self.ACCEL = 0.7
        self.JUMP_POWER = -14
        
        self.platforms = platforms
        self.particles = [] # Список частинок пилу

    def animate(self):
        # Змінюємо колір кожні 10 кадрів (приблизно 6 разів на секунду)
        self.animation_timer += 1
        if self.animation_timer >= 10:
            self.animation_timer = 0
            self.current_color_index = (self.current_color_index + 1) % len(self.colors)
            self.image.fill(self.colors[self.current_color_index])

    def jump(self):
        self.rect.y += 2
        hits = pygame.sprite.spritecollide(self, self.platforms, False)
        self.rect.y -= 2
        if hits or self.rect.bottom >= HEIGHT - 20:
            self.vel.y = self.JUMP_POWER
            # Додаємо звук стрибка 
            # jump_sound.play()

    def update(self):
        self.animate()
        self.acc = pygame.math.Vector2(0, self.GRAVITY)
        
        keys = pygame.key.get_pressed()
        moving = False
        if keys[pygame.K_LEFT]:
            self.acc.x = -self.ACCEL
            moving = True
        if keys[pygame.K_RIGHT]:
            self.acc.x = self.ACCEL
            moving = True

        self.acc.x += self.vel.x * self.FRICTION
        self.vel += self.acc
        self.pos += self.vel + 0.5 * self.acc

        # Створюємо пил при русі по землі
        if moving and abs(self.vel.y) < 1:
            for _ in range(2):
                self.particles.append(Particle(self.pos.x + 20, self.pos.y + 40))

        # Оновлення частинок
        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)

        # Стандартні колізії та обмеження
        if self.pos.x < 20: self.pos.x = 20
        self.rect.y = self.pos.y
        hits = pygame.sprite.spritecollide(self, self.platforms, False)
        if hits:
            if self.vel.y > 0:
                self.rect.bottom = hits[0].rect.top
                self.vel.y = 0
                self.pos.y = self.rect.y
            elif self.vel.y < 0:
                self.rect.top = hits[0].rect.bottom
                self.vel.y = 0
                self.pos.y = self.rect.y

        self.rect.x = self.pos.x
        hits = pygame.sprite.spritecollide(self, self.platforms, False)
        if hits:
            if self.vel.x > 0: self.rect.right = hits[0].rect.left
            elif self.vel.x < 0: self.rect.left = hits[0].rect.right
            self.pos.x = self.rect.x
            self.vel.x = 0

        if self.pos.y > HEIGHT - 20 - self.rect.height:
            self.pos.y = HEIGHT - 20 - self.rect.height
            self.vel.y = 0
        self.rect.topleft = self.pos

class Star:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(-HEIGHT, 0)
        self.speed = random.uniform(2, 5) 
        self.size = random.randint(1, 3)

    def update(self):
        self.y += self.speed
        # Якщо зірка вилетіла за межі екрана — повертаємо її нагору
        if self.y > HEIGHT:
            self.reset()

    def draw(self, surface):
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.size)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mars Mission")
clock = pygame.time.Clock()

# Завантаження музики
# pygame.mixer.music.load("mars_ambient.mp3")
# pygame.mixer.music.play(-1)

all_sprites = pygame.sprite.Group()
platforms = pygame.sprite.Group()

# Початкова платформа під ногами
start_p = Platform(0, HEIGHT - 60, 400, 40)
all_sprites.add(start_p)
platforms.add(start_p)
stars = [Star() for _ in range(50)]

scroll = 0
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_SPACE, pygame.K_UP, pygame.K_w]:
                player.jump()

    if 'player' not in locals():
        player = Player(platforms)
        all_sprites.add(player)
    
    all_sprites.update()

    if player.pos.x > WIDTH // 2:
        scroll = player.pos.x - WIDTH // 2
    else:
        scroll = 0

    # Генерація нових платформ 
    all_p = platforms.sprites()
    last_p = max(all_p, key=lambda p: p.rect.right)
    
    if last_p.rect.right < scroll + WIDTH + 200:
        new_w = random.randint(150, 300)
        new_x = last_p.rect.right + random.randint(80, 250) # Дальність стрибка
        new_y = random.randint(250, 500) # Висота платформ
        
        # Перевірка на занадто високий підйом (не більше 120px вгору)
        if abs(new_y - last_p.rect.y) > 120:
             new_y = last_p.rect.y + (120 if new_y > last_p.rect.y else -120)

        new_p = Platform(new_x, new_y, new_w, 30)
        all_sprites.add(new_p)
        platforms.add(new_p)

    screen.fill(DEEP_SPACE)

    for star in stars:
        star.update()
        star.draw(screen)

    # Нескінченний паралакс 
    bg_x = (-scroll * 0.2) % WIDTH
    for i in range(2):
        m_offset = bg_x + (i - 1) * WIDTH
        pygame.draw.polygon(screen, MOUNTAIN_COLOR, [(0+m_offset, 580), (200+m_offset, 300), (400+m_offset, 580)])
        pygame.draw.polygon(screen, MOUNTAIN_COLOR, [(400+m_offset, 580), (600+m_offset, 350), (800+m_offset, 580)])

    for p in player.particles:
        p.draw(screen, scroll)

    for sprite in all_sprites:
        screen.blit(sprite.image, (sprite.rect.x - scroll, sprite.rect.y))
    
    pygame.draw.rect(screen, MARS_RED, (0, HEIGHT - 20, WIDTH, 20))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()