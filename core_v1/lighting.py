import pygame
import moderngl
import numpy as np
from colorama import Back, init
init(autoreset=True)

class LightingEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.max_blocks = 64 # Кількість допустимих до рендеру тіней блоківю.    Менше - можуть бути світлі блоки  |  Більше - пк закипить
        self.downscale = 4  # Масштаб зменшення.  Екранї/Пропорцію = масштабно менше пікселів!!!

        self.ctx = moderngl.create_context()

        # ================== ВЕРШИННИЙ ШЕЙДЕР ==================
        self.vertex_shader = """
        #version 330 core
        in vec2 in_vert;
        out vec2 v_uv;
        void main() {
            gl_Position = vec4(in_vert, 0.0, 1.0);
            v_uv = (in_vert + vec2(1.0)) * 0.5;
        }
        """

        # ================== ШЕЙДЕР 1: КАРТА СВІТЛА (Низька роздільна здатність) ==================
        self.light_fragment = """
        #version 330 core
        in vec2 v_uv;
        out vec4 fragColor;

        uniform vec2 u_screen_res;
        uniform vec2 u_light;           // Позиція гравця (локальне світло)
        uniform vec3 u_light_color;     // Колір локального світла (гравець)
        uniform int u_num_blocks;
        uniform float u_blocks[320];    // 64 блоки * 5 параметрів (x, y, hw, hh, indoor)
        uniform float u_surface_limit;  // Межа поверхня/підземелля у координатах шейдера

        // --- Параметри глобального сонця Марсу ---
        // Напрямок «назустріч сонцю» (нормалізований у main)
        // vec2(-0.5, 1.0) → світло зверху-зліва (типове для 2D платформера)
        const vec2 SUN_DIR_RAW   = vec2(-0.5, 1.0);
        const vec3 SUN_COLOR     = vec3(1.0, 0.72, 0.42); // Тепло-помаранчеве марсіанське сонце
        const float SUN_INTENSITY = 0.78;                 // Загальна яскравість сонця
        const float SUN_MAX_DIST  = 3000.0;               // Промінь не зупиняється на межах екрана
        const float SHADOW_SOFTNESS = 14.0;               // М'якість пенумбри паралельних тіней
        const float GRADIENT_REACH  = 50.0;               // Глибина проникнення світла в тверде тіло
        // Фоновий марсіанський «пил» — ніколи не буває абсолютної темряви
        const vec3 AMBIENT = vec3(0.02, 0.01, 0.00);

        float sdBox(vec2 p, vec2 b) {
            vec2 d = abs(p) - b;
            return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0);
        }

        float map(vec2 p) {
            float minDist = 999999.0;
            for (int i = 0; i < u_num_blocks; i++) {
                int idx = i * 5;
                vec2 center   = vec2(u_blocks[idx],     u_blocks[idx + 1]);
                vec2 halfSize = vec2(u_blocks[idx + 2], u_blocks[idx + 3]);
                minDist = min(minDist, sdBox(p - center, halfSize));
            }
            return minDist;
        }

        // --- Паралельні тіні від глобального сонця ---
        // rd — постійний вектор сонця, без загасання з відстанню
        float calcSunShadow(vec2 ro, vec2 rd) {
            float res = 1.0;
            float t   = 2.0; // Невеликий зсув, щоб не зіткнутися з поверхнею старту
            for (int i = 0; i < 48; i++) {
                float h = map(ro + rd * t);
                if (h < 0.5) return 0.0; // Абсолютна тінь (геометрія перекрила промінь)
                res = min(res, SHADOW_SOFTNESS * h / t);
                t  += clamp(h, 1.5, 40.0); // Адаптивний крок (sphere tracing)
                if (t >= SUN_MAX_DIST) break;
            }
            return clamp(res, 0.0, 1.0);
        }

        // --- Локальне світло гравця (точкове, з загасанням і м'якими тінями) ---
        float calcPlayerShadow(vec2 ro, vec2 rd, float maxDist) {
            float res = 1.0;
            float t   = 1.0;
            for (int i = 0; i < 40; i++) {
                float h = map(ro + rd * t);
                if (h < 0.01) return 0.1;
                res = min(res, 20.0 * h / t);
                t  += h;
                if (t >= maxDist) break;
            }
            return clamp(res, 0.0, 1.0);
        }

        void main() {
            vec2 st = v_uv * u_screen_res;

            // Нормалізований вектор сонця — однаковий для кожного пікселя (паралельне світло)
            vec2 sunDir = normalize(SUN_DIR_RAW);

            vec3 light_acc = AMBIENT;
            float sceneDist = map(st);

            // ================================================================
            // ГІЛКА A: Відкрите повітря
            // ================================================================
            if (sceneDist > 0.0) {
                // --- Глобальне сонячне освітлення (паралельний промінь) ---
                // Тільки вище межі підземелля — об'єкти за екраном не дають хибних просвітів
                if (st.y > u_surface_limit) {
                    float sunShadow = calcSunShadow(st, sunDir);
                    light_acc += SUN_COLOR * SUN_INTENSITY * sunShadow;
                }

                // --- Локальне світло гравця (точкове) ---
                vec2  playerRay  = u_light - st;
                float playerDist = length(playerRay);
                float radius     = 700.0;
                float atten      = pow(clamp(1.0 - playerDist / radius, 0.0, 1.0), 1.8);
                float playerShad = calcPlayerShadow(st, normalize(playerRay), playerDist);
                light_acc += u_light_color * atten * playerShad;

            // ================================================================
            // ГІЛКА B: Тверде тіло (земля, платформи)
            // ================================================================
            } else {
                // Зміщуємо точку в напрямку сонця на GRADIENT_REACH пікселів.
                // Якщо зміщена точка вийшла у відкритий простір (SDF > 0) —
                // піксель знаходиться поблизу освітленого краю.
                vec2  probePos  = st + sunDir * GRADIENT_REACH;
                float probeDist = map(probePos);

                // Знаходимо який саме блок містить поточний піксель і читаємо його indoor_flag
                float indoor_flag = 0.0;
                float closestDist = 999999.0;
                for (int i = 0; i < u_num_blocks; i++) {
                    int idx = i * 5;
                    vec2 center   = vec2(u_blocks[idx],     u_blocks[idx + 1]);
                    vec2 halfSize = vec2(u_blocks[idx + 2], u_blocks[idx + 3]);
                    float d = sdBox(st - center, halfSize);
                    if (d < closestDist) {
                        closestDist  = d;
                        indoor_flag  = u_blocks[idx + 4];
                    }
                }

                if (probeDist > 0.0 && st.y > u_surface_limit && indoor_flag < 0.5) {
                    // Нормалізуємо: скільки «виступає» назовні відносно GRADIENT_REACH
                    float raw = clamp(probeDist / GRADIENT_REACH, 0.0, 1.0);
                    // Нелінійна крива: край яскравіший, вглиб — швидше темнішає
                    float edgeGlow = pow(raw, 1.5);
                    light_acc += SUN_COLOR * SUN_INTENSITY * edgeGlow;
                }
                // Пікселі глибоко всередині отримують лише AMBIENT (вже в light_acc)

                // Локальне світло гравця працює і всередині блоків
                // (щоб гравець підсвічував вхід у тунель зсередини)
                vec2  playerRay  = u_light - st;
                float playerDist = length(playerRay);
                float radius     = 500.0;
                float atten      = pow(clamp(1.0 - playerDist / radius, 0.0, 1.0), 2.2);
                light_acc += u_light_color * atten * 1.0;
            }

            fragColor = vec4(light_acc, 0.6);
        }
        """

        # ================== ШЕЙДЕР 2: КОМПОЗИТНИЙ (Повна роздільна здатність) ==================
        # ОПТИМІЗОВАНИЙ КОМПОЗИТНИЙ ШЕЙДЕР
        self.composite_fragment = """
        #version 330 core
        in vec2 v_uv;
        out vec4 fragColor;

        uniform sampler2D u_game_tex;  // Відрендерена гра
        uniform sampler2D u_ui_tex;    // Чіткий інтерфейс
        uniform sampler2D u_light_tex; // Розмита карта світла

        uniform vec2 u_resolution;
        uniform int u_effect_type;
        uniform float u_effect_scale;
        uniform bool u_enable_lighting; // Новий прапорець

        vec4 getBlurredGameTex(vec2 uv, float radius) {
            vec4 color = vec4(0.0);
            float total = 0.0;
            vec2 texOffset = 1.0 / u_resolution;
            
            // ОПТИМІЗАЦІЯ: Матриця 3x3 замість 5x5 (9 вибірок замість 25) з ширшим кроком
            for(float x = -1.0; x <= 1.0; x++) {
                for(float y = -1.0; y <= 1.0; y++) {
                    vec2 sampleUV = uv + vec2(x, y) * texOffset * radius * 1.5;
                    sampleUV = clamp(sampleUV, 0.0, 1.0);
                    float weight = exp(-(x*x + y*y) / 4.0);
                    color += texture(u_game_tex, sampleUV) * weight;
                    total += weight;
                }
            }
            return color / total;
        }

        void main() {
            vec2 base_uv = vec2(v_uv.x, 1.0 - v_uv.y); // Переворот Pygame текстур
            vec4 game_pixel;

            // Застосування ефектів до гри
            if (u_effect_type == 1 && u_effect_scale > 1.0) {
                vec2 pixels = u_resolution / u_effect_scale;
                vec2 pixelated_uv = floor(base_uv * pixels) / pixels;
                game_pixel = texture(u_game_tex, pixelated_uv);
            } else if (u_effect_type == 2 && u_effect_scale > 1.0) {
                game_pixel = getBlurredGameTex(base_uv, u_effect_scale);
            } else {
                game_pixel = texture(u_game_tex, base_uv);
            }

            vec4 ui_pixel = texture(u_ui_tex, base_uv);
            vec3 final_game_color = game_pixel.rgb;
            
            // Якщо освітлення увімкнене, накладаємо його
            // Беремо м'яке світло (координати v_uv тут прямі, бо це текстура з OpenGL)
            if (u_enable_lighting) {
                vec4 light_pixel = texture(u_light_tex, v_uv);
                final_game_color *= light_pixel.rgb;
            }

            // Змішування: Гра * Світло + Інтерфейс
            vec3 final_mix = mix(final_game_color, ui_pixel.rgb, ui_pixel.a);
            fragColor = vec4(final_mix, 1.0);
        }
        """

        # Компілюємо програми
        self.light_prog = self.ctx.program(vertex_shader=self.vertex_shader, fragment_shader=self.light_fragment)
        self.comp_prog = self.ctx.program(vertex_shader=self.vertex_shader, fragment_shader=self.composite_fragment)

        # Геометрія (повноекранний квадрат)
        vertices = np.array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1], dtype='f4')
        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.vao_light = self.ctx.simple_vertex_array(self.light_prog, self.vbo, "in_vert")
        self.vao_comp = self.ctx.simple_vertex_array(self.comp_prog, self.vbo, "in_vert")
        
        self.block_buffer = np.zeros(self.max_blocks * 5, dtype='f4')

        # Об'єкти пам'яті
        self.tex_game = None
        self.tex_ui = None
        self.tex_light = None
        self.fbo_light = None
        self._allocate_textures(self.width, self.height)

    def _allocate_textures(self, w, h):
        """Перестворює буфери під час зміни розміру вікна."""
        if self.fbo_light: self.fbo_light.release()
        if self.tex_light: self.tex_light.release()
        if self.tex_game: self.tex_game.release()
        if self.tex_ui: self.tex_ui.release()

        # Повнорозмірні текстури Pygame
        self.tex_game = self.ctx.texture((w, h), 4)
        self.tex_ui = self.ctx.texture((w, h), 4)
        self.tex_game.swizzle = 'BGRA'
        self.tex_ui.swizzle = 'BGRA'

        # ЗМЕНШЕНА текстура світла
        scale = max(1, int(self.downscale))
        light_w, light_h = max(1, w // scale), max(1, h // scale)
        self.tex_light = self.ctx.texture((light_w, light_h), 3) 
        
        # ОСЬ ТУТ МАГІЯ: Вказуємо лінійну фільтрацію для м'якого апскейлу!
        self.tex_light.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.fbo_light = self.ctx.framebuffer(color_attachments=[self.tex_light])

    def set_downscale(self, value):
        value = max(1, int(value))
        if value != self.downscale:
            self.downscale = value
            self._allocate_textures(self.width, self.height)

    def render(self, game_surf, ui_surf, player_rect, platforms, camera, light_color, effect_type=0, effect_scale=1.0, lighting_enabled=True):
        win_w, win_h = game_surf.get_size()
        
        if win_w != self.width or win_h != self.height:
            self.width, self.height = win_w, win_h
            self._allocate_textures(win_w, win_h)

        # 1. ЗАВАНТАЖУЄМО ДАНІ
        self.tex_game.write(game_surf.get_view('1'))
        self.tex_ui.write(ui_surf.get_view('1'))

        # Вмикаємо/вимикаємо освітлення на рівні GPU
        self.comp_prog["u_enable_lighting"].value = lighting_enabled

        if lighting_enabled:
            # Підготовка блоків
            count = 0
            self.block_buffer[:] = 0.0
            view_rect = pygame.Rect(-camera.x, -camera.y, win_w, win_h)

            for p in platforms:
                if count >= self.max_blocks: break
                if not view_rect.colliderect(p.rect): continue
                
                # Координати залишаємо у ВЕЛИКОМУ масштабі, шейдер сам розбереться
                self.block_buffer[count*5]     = p.rect.centerx + camera.x
                self.block_buffer[count*5 + 1] = self.height - (p.rect.centery + camera.y)
                self.block_buffer[count*5 + 2] = p.rect.width / 2.0
                self.block_buffer[count*5 + 3] = p.rect.height / 2.0
                self.block_buffer[count*5 + 4] = 1.0 if getattr(p, 'indoor', False) else 0.0
                count += 1

            screen_px = float(player_rect.centerx + camera.x)
            screen_py = float(self.height - (player_rect.centery + camera.y))
            norm_color = (light_color[0]/255.0, light_color[1]/255.0, light_color[2]/255.0)

            # 2. ПРОХІД СВІТЛА (Рендер на малий FBO)
            self.fbo_light.use()
            self.ctx.viewport = (0, 0, self.tex_light.width, self.tex_light.height)
            self.ctx.clear(0.0, 0.0, 0.0)

            self.light_prog["u_screen_res"].value = (self.width, self.height)
            self.light_prog["u_light"].value = (screen_px, screen_py)
            self.light_prog["u_light_color"].value = norm_color
            self.light_prog["u_num_blocks"].value = count
            self.light_prog["u_blocks"].write(self.block_buffer.tobytes())

            # Межа підземелля у світових координатах → координати шейдера (OpenGL Y знизу вгору)
            surface_limit_world = 2600
            surface_limit_shader = self.height - (surface_limit_world + camera.y)
            self.light_prog["u_surface_limit"].value = float(surface_limit_shader)
            
            self.vao_light.render(moderngl.TRIANGLES)

        # 3. ПРОХІД КОМПОЗИЦІЇ (Рендер на головний екран)
        self.ctx.screen.use()
        self.ctx.viewport = (0, 0, win_w, win_h)
        self.ctx.clear(0.0, 0.0, 0.0)

        # Прив'язуємо текстури до слотів пам'яті GPU
        self.tex_game.use(0)
        self.comp_prog["u_game_tex"].value = 0
        
        self.tex_ui.use(1)
        self.comp_prog["u_ui_tex"].value = 1
        
        if lighting_enabled:
            self.tex_light.use(2)
            self.comp_prog["u_light_tex"].value = 2

        self.comp_prog["u_resolution"].value = (self.width, self.height)
        self.comp_prog["u_effect_type"].value = effect_type
        self.comp_prog["u_effect_scale"].value = float(effect_scale)

        self.vao_comp.render(moderngl.TRIANGLES)

print(f"{Back.CYAN}!---Модуль освітлення застосовано---!")

# M.
