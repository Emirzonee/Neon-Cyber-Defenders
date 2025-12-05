import pygame
import random
import sys
import math

# --- AYARLAR ---
SCREEN_WIDTH = 1000 
SCREEN_HEIGHT = 750
FPS = 60

# --- RENKLER ---
BG_COLOR = (5, 5, 12)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
CYAN = (0, 255, 255)       # P1 Rengi (Eksik olan buydu)
NEON_PINK = (255, 20, 147) # P2 Rengi
NEON_RED = (255, 50, 50)   # Virus
YELLOW = (255, 255, 100)
BAR_BG = (50, 50, 50)      
BAR_FILL = (0, 200, 255)   

# Power-up Renkleri
PWR_RAPID = (255, 100, 100)
PWR_GIANT = (200, 100, 255)
PWR_SHIELD = (100, 200, 255)
PWR_REVIVE = (255, 255, 255)

# --- OYUN DURUMLARI ---
STATE_MENU = 0
STATE_HOWTO = 1
STATE_PLAYING = 2
STATE_GAMEOVER = 3
STATE_LEVEL_UP = 4 
STATE_WIN = 5 # EKSİK OLAN BUYDU, EKLENDİ!

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("NEON CYBER DEFENDERS: FINAL")
clock = pygame.time.Clock()

# --- FONT TANIMLARI ---
font_small = pygame.font.Font(None, 24)
font_medium = pygame.font.Font(None, 36)
font_big = pygame.font.Font(None, 70)
font_pixel = pygame.font.Font(None, 50)
font_bold = pygame.font.Font(None, 60) 

# --- YARDIMCI FONKSİYONLAR ---
def draw_heart(surface, x, y, color):
    pygame.draw.circle(surface, color, (x - 6, y - 6), 6)
    pygame.draw.circle(surface, color, (x + 6, y - 6), 6)
    points = [(x - 12, y - 2), (x + 12, y - 2), (x, y + 12)]
    pygame.draw.polygon(surface, color, points)

# --- SINIFLAR ---

class FloatingText(pygame.sprite.Sprite):
    def __init__(self, text, x, y, color, size=30):
        super().__init__()
        font = pygame.font.Font(None, size)
        self.image = font.render(text, True, color)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed_y = -1.5
        self.life = 50

    def update(self):
        self.rect.y += self.speed_y
        self.life -= 1
        if self.life <= 0: self.kill()
        if self.life < 15: self.image.set_alpha(self.life * 15)

class Star:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.speed = random.randint(1, 4)
        self.size = random.randint(1, 3)
        self.brightness = random.randint(50, 200)

    def update(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT:
            self.y = 0
            self.x = random.randint(0, SCREEN_WIDTH)

    def draw(self, surface):
        c = (self.brightness, self.brightness, self.brightness)
        pygame.draw.circle(surface, c, (self.x, self.y), self.size)

class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        super().__init__()
        self.image = pygame.Surface((5, 5))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 6)
        self.vel_x = math.cos(angle) * speed
        self.vel_y = math.sin(angle) * speed
        self.life = 30

    def update(self):
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        self.life -= 1
        if self.life <= 0: self.kill()

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, force_type=None):
        super().__init__()
        if force_type: self.type = force_type
        else: self.type = random.choice(['R', 'G', 'S'])
        
        if self.type == 'R': self.color = PWR_RAPID
        elif self.type == 'G': self.color = PWR_GIANT
        elif self.type == 'S': self.color = PWR_SHIELD
        elif self.type == 'L': self.color = PWR_REVIVE
            
        self.image = pygame.Surface((34, 34))
        self.image.fill(self.color)
        
        symbol = "+" if self.type == 'L' else self.type
        txt = font_medium.render(symbol, True, BLACK)
        self.image.blit(txt, (8, 4))
        
        self.rect = self.image.get_rect()
        self.rect.x = random.randrange(20, SCREEN_WIDTH - 50)
        self.rect.y = -50
        self.speed_y = 9 

    def update(self):
        self.rect.y += self.speed_y
        if self.rect.top > SCREEN_HEIGHT: self.kill()

# --- OYUNCU ---
class Player(pygame.sprite.Sprite):
    def __init__(self, controls, color, start_x):
        super().__init__()
        self.controls = controls
        self.color = color
        self.base_size = 40
        self.size = self.base_size
        
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(start_x, SCREEN_HEIGHT - 80))
        
        self.speed = 7
        self.score = 0
        self.lives = 5 
        self.is_dead = False
        
        self.invincible_timer = 0
        self.rapid_fire_timer = 0
        self.giant_timer = 0
        self.shoot_delay = 0
        
        self.draw_ship()

    def draw_ship(self):
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        if self.is_dead: return

        points = [(self.size//2, 0), (self.size, self.size), (self.size//2, self.size-10), (0, self.size)]
        pygame.draw.polygon(self.image, self.color, points)
        if self.invincible_timer > 0:
            pygame.draw.circle(self.image, WHITE, (self.size//2, self.size//2), self.size//2 + 5, 2)

    def revive(self):
        self.is_dead = False
        self.lives = 3 
        self.invincible_timer = 180
        self.draw_ship()

    def activate_powerup(self, p_type, teammate=None):
        msg = ""
        if p_type == 'R': 
            self.rapid_fire_timer = 300; msg = "RAPID FIRE!"
        elif p_type == 'G': 
            self.giant_timer = 300
            self.size = self.base_size * 2
            self.rect = self.rect.inflate(self.size/2, self.size/2)
            self.draw_ship()
            msg = "GIANT MODE!"
        elif p_type == 'S': 
            self.invincible_timer = 300; msg = "SHIELD UP!"
        elif p_type == 'L': 
            if teammate and teammate.is_dead:
                teammate.revive()
                msg = "ALLY REVIVED!"
            else:
                if self.lives < 5: 
                    self.lives += 1; msg = "+1 HEALTH"
                else: 
                    self.score += 500; msg = "MAX HP BONUS"
        return msg

    def take_damage(self):
        if self.invincible_timer == 0 and not self.is_dead:
            self.lives -= 1
            self.invincible_timer = 60 
            if self.lives <= 0:
                self.is_dead = True
                self.image.fill((0,0,0,0))
            return True
        return False

    def update(self):
        if self.is_dead: return

        if self.shoot_delay > 0: self.shoot_delay -= 1
        if self.rapid_fire_timer > 0: self.rapid_fire_timer -= 1
        
        if self.invincible_timer > 0: 
            self.invincible_timer -= 1
            alpha = 100 if (self.invincible_timer // 5) % 2 == 0 else 255
            self.image.set_alpha(alpha)
        else:
            self.image.set_alpha(255)

        if self.giant_timer > 0:
            self.giant_timer -= 1
            if self.giant_timer == 0:
                self.size = self.base_size
                self.draw_ship()

        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        
        if self.controls == 'WASD':
            if keys[pygame.K_a]: dx = -1
            if keys[pygame.K_d]: dx = 1
            if keys[pygame.K_w]: dy = -1
            if keys[pygame.K_s]: dy = 1
            if keys[pygame.K_SPACE] or self.rapid_fire_timer > 0:
                if keys[pygame.K_SPACE] or keys[pygame.K_f]: self.try_shoot()

        elif self.controls == 'ARROWS':
            if keys[pygame.K_LEFT]: dx = -1
            if keys[pygame.K_RIGHT]: dx = 1
            if keys[pygame.K_UP]: dy = -1
            if keys[pygame.K_DOWN]: dy = 1
            if (keys[pygame.K_RCTRL] or keys[pygame.K_KP_ENTER] or keys[pygame.K_RETURN]):
                self.try_shoot()

        if dx != 0 or dy != 0:
            length = math.sqrt(dx**2 + dy**2)
            dx, dy = dx / length, dy / length
            self.rect.x += dx * self.speed
            self.rect.y += dy * self.speed

        self.rect.clamp_ip(screen.get_rect())

    def try_shoot(self):
        limit = 6 if self.rapid_fire_timer > 0 else 18
        if self.shoot_delay == 0:
            self.shoot_delay = limit
            size = 4 if self.giant_timer == 0 else 10
            b = Bullet(self.rect.centerx, self.rect.top, size, self)
            all_sprites.add(b)
            bullets.add(b)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, size, owner):
        super().__init__()
        self.owner = owner
        self.image = pygame.Surface((size, size * 3))
        self.image.fill(owner.color)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed_y = -15

    def update(self):
        self.rect.y += self.speed_y
        if self.rect.bottom < 0: self.kill()

# --- DÜŞMAN (VİRÜS) ---
class Virus(pygame.sprite.Sprite):
    def __init__(self, level):
        super().__init__()
        self.level = level
        self.size = 40
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.color = NEON_RED
        self.rect = self.image.get_rect()
        
        self.start_x = random.randrange(20, SCREEN_WIDTH - 60)
        self.rect.x = self.start_x
        self.rect.y = -50
        
        base_speed = random.uniform(2, 4)
        self.speed_y = base_speed + (level * 0.8) 
        
        self.oscillation_speed = 0
        self.oscillation_amp = 0
        if level >= 3:
            self.oscillation_speed = 0.05 + (level * 0.01)
            self.oscillation_amp = 40 + (level * 5)

        self.draw_virus()

    def draw_virus(self):
        center = (self.size//2, self.size//2)
        pygame.draw.circle(self.image, self.color, center, 10)
        for i in range(0, 360, 45):
            rad = math.radians(i)
            end_x = center[0] + math.cos(rad) * 16
            end_y = center[1] + math.sin(rad) * 16
            pygame.draw.line(self.image, self.color, center, (end_x, end_y), 2)

    def update(self):
        self.rect.y += self.speed_y
        
        if self.level >= 3:
            self.rect.x = self.start_x + math.sin(self.rect.y * self.oscillation_speed) * self.oscillation_amp
            
            if self.rect.right > SCREEN_WIDTH: self.rect.right = SCREEN_WIDTH
            if self.rect.left < 0: self.rect.left = 0

        if self.rect.top > SCREEN_HEIGHT:
            self.kill()
            return "MISSED"

# --- GLOBAL DEĞİŞKENLER ---
game_state = STATE_MENU
level = 1
progress = 0
max_progress = 100 
spawn_timer = 0
powerup_timer = 0
game_over_text = ""

all_sprites = pygame.sprite.Group()
players = pygame.sprite.Group()
viruses = pygame.sprite.Group()
bullets = pygame.sprite.Group()
particles = pygame.sprite.Group()
powerups = pygame.sprite.Group()
ui_effects = pygame.sprite.Group()

p1 = None
p2 = None
stars = [Star() for _ in range(80)]

def spawn_floating_text(text, x, y, color, size=30):
    ft = FloatingText(text, x, y, color, size)
    all_sprites.add(ft); ui_effects.add(ft)

def spawn_particles(x, y, color, count=10):
    for _ in range(count):
        p = Particle(x, y, color)
        all_sprites.add(p); particles.add(p)

def reset_game():
    # GLOBAL OYUNCULARI UNUTMUŞUZ, EKLENDİ!
    global all_sprites, players, viruses, bullets, particles, powerups, ui_effects
    global p1, p2, progress, level, max_progress
    
    all_sprites.empty(); players.empty(); viruses.empty()
    bullets.empty(); particles.empty(); powerups.empty(); ui_effects.empty()
    
    progress = 0
    level = 1
    max_progress = 100
    
    p1 = Player('WASD', CYAN, SCREEN_WIDTH // 3)
    p2 = Player('ARROWS', NEON_PINK, 2 * SCREEN_WIDTH // 3)
    
    players.add(p1); players.add(p2)
    all_sprites.add(p1); all_sprites.add(p2)

# --- ANA DÖNGÜ ---
running = True
while running:
    clock.tick(FPS)
    
    # 1. GİRİŞ
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
            
        if event.type == pygame.KEYDOWN:
            if game_state == STATE_MENU:
                if event.key == pygame.K_SPACE: game_state = STATE_HOWTO
            
            elif game_state == STATE_HOWTO:
                if event.key == pygame.K_SPACE: reset_game(); game_state = STATE_PLAYING

            elif game_state in [STATE_GAMEOVER, STATE_WIN]:
                if event.key == pygame.K_SPACE: reset_game(); game_state = STATE_PLAYING
                elif event.key == pygame.K_ESCAPE: game_state = STATE_MENU
            
            elif game_state == STATE_LEVEL_UP:
                if event.key == pygame.K_SPACE: game_state = STATE_PLAYING

    # 2. UPDATE
    if game_state == STATE_PLAYING:
        players.update(); bullets.update(); viruses.update()
        powerups.update(); particles.update(); ui_effects.update()
        for s in stars: s.update()
        
        # --- LEVEL SİSTEMİ ---
        if progress >= max_progress:
            level += 1
            progress = 0
            max_progress = int(max_progress * 1.2) 
            game_state = STATE_LEVEL_UP
            viruses.empty()
            bullets.empty()
            powerups.empty()

        # Virüs Spawn 
        spawn_timer += 1
        spawn_rate = max(10, 60 - (level * 5)) 
        if spawn_timer > spawn_rate:
            spawn_timer = 0
            v = Virus(level)
            all_sprites.add(v); viruses.add(v)

        # Powerup Spawn
        if random.randint(0, 400) == 0:
            force = 'L' if any(p.is_dead for p in players) and random.random() < 0.6 else None
            pu = PowerUp(force)
            all_sprites.add(pu); powerups.add(pu)

        # KAYBETME KONTROLÜ
        if p1.is_dead and p2.is_dead:
            game_state = STATE_GAMEOVER
            game_over_text = f"REACHED LEVEL {level}"

        # ÇARPIŞMALAR
        
        hits = pygame.sprite.groupcollide(viruses, bullets, True, True)
        for v, bullet_list in hits.items():
            shooter = bullet_list[0].owner
            shooter.score += 100
            
            progress += 10 
            if progress > max_progress: progress = max_progress
            
            if v.rect.y > SCREEN_HEIGHT - 150:
                shooter.score += 50
                spawn_floating_text("CLOSE CALL!", v.rect.x, v.rect.y, YELLOW)
            
            spawn_particles(v.rect.centerx, v.rect.centery, v.color)

        for p in players:
            if not p.is_dead:
                hits = pygame.sprite.spritecollide(p, viruses, True)
                for v in hits:
                    if p.take_damage():
                        spawn_floating_text("-1 HEART", p.rect.centerx, p.rect.y - 40, NEON_RED)
                        spawn_particles(p.rect.centerx, p.rect.centery, NEON_RED, 20)
                
                phits = pygame.sprite.spritecollide(p, powerups, True)
                for pu in phits:
                    friend = p2 if p == p1 else p1
                    msg = p.activate_powerup(pu.type, friend)
                    spawn_floating_text(msg, p.rect.centerx, p.rect.y - 50, pu.color)

        for v in viruses:
            if v.rect.top > SCREEN_HEIGHT:
                progress -= 15 
                if progress < 0: progress = 0
                spawn_floating_text("MISSED!", v.rect.x, SCREEN_HEIGHT - 30, (100, 100, 100))

    # 3. ÇİZİM
    screen.fill(BG_COLOR)
    for s in stars: s.draw(screen)

    if game_state == STATE_MENU:
        t1 = font_big.render("NEON CYBER", True, CYAN)
        t2 = font_big.render("DEFENDERS", True, NEON_PINK)
        screen.blit(t1, (SCREEN_WIDTH//2 - 180, 150))
        screen.blit(t2, (SCREEN_WIDTH//2 - 160, 210))
        
        info = font_medium.render("CO-OP ARCADE MODE", True, YELLOW)
        screen.blit(info, (SCREEN_WIDTH//2 - 140, 350))
        
        start = font_pixel.render("PRESS [SPACE]", True, WHITE)
        screen.blit(start, (SCREEN_WIDTH//2 - 150, 500))

    elif game_state == STATE_HOWTO:
        head = font_bold.render("NASIL OYNANIR?", True, YELLOW)
        screen.blit(head, (SCREEN_WIDTH//2 - 160, 50))
        
        l1 = font_medium.render("- Birlikte calis, Virusleri yok et!", True, WHITE)
        l2 = font_medium.render("- Ustteki mavi bar dolunca LEVEL atlanir.", True, WHITE)
        l3 = font_medium.render("- Virus kacirirsaniz bar azalir!", True, NEON_RED)
        l4 = font_medium.render("- Can (Kalp) sadece carpisinca gider.", True, NEON_PINK)
        
        screen.blit(l1, (100, 150)); screen.blit(l2, (100, 200))
        screen.blit(l3, (100, 250)); screen.blit(l4, (100, 300))
        
        # Kontroller
        pygame.draw.rect(screen, (30,30,50), (100, 400, 350, 150), border_radius=10)
        screen.blit(font_medium.render("P1: WASD + SPACE", True, CYAN), (120, 450))
        
        pygame.draw.rect(screen, (30,30,50), (550, 400, 350, 150), border_radius=10)
        screen.blit(font_medium.render("P2: YON TUSLARI + ENTER", True, NEON_PINK), (570, 450))
        
        cont = font_pixel.render("[SPACE] BASLA", True, NEON_RED)
        screen.blit(cont, (SCREEN_WIDTH//2 - 150, 600))

    elif game_state == STATE_PLAYING:
        # LEVEL BAR
        pygame.draw.rect(screen, BAR_BG, (0, 0, SCREEN_WIDTH, 30))
        fill_width = int((progress / max_progress) * SCREEN_WIDTH)
        pygame.draw.rect(screen, BAR_FILL, (0, 0, fill_width, 30))
        
        lvl_txt = font_medium.render(f"LEVEL {level}", True, WHITE)
        screen.blit(lvl_txt, (SCREEN_WIDTH//2 - 50, 5))

        all_sprites.draw(screen)
        ui_effects.draw(screen)

        # UI
        if not p1.is_dead:
            for i in range(p1.lives): draw_heart(screen, 30 + i*25, 60, CYAN)
            s1 = font_small.render(f"P1: {p1.score}", True, WHITE)
            screen.blit(s1, (30, 80))
        else:
            dt = font_small.render("P1 DEAD", True, (100,100,100))
            screen.blit(dt, (30, 60))

        if not p2.is_dead:
            for i in range(p2.lives): draw_heart(screen, SCREEN_WIDTH - 140 + i*25, 60, NEON_PINK)
            s2 = font_small.render(f"P2: {p2.score}", True, WHITE)
            screen.blit(s2, (SCREEN_WIDTH - 140, 80))
        else:
            dt2 = font_small.render("P2 DEAD", True, (100,100,100))
            screen.blit(dt2, (SCREEN_WIDTH - 140, 60))

    elif game_state == STATE_LEVEL_UP:
        txt = font_big.render(f"LEVEL {level} COMPLETED!", True, YELLOW)
        screen.blit(txt, (SCREEN_WIDTH//2 - 250, 300))
        sub = font_pixel.render("NEXT WAVE INCOMING...", True, WHITE)
        screen.blit(sub, (SCREEN_WIDTH//2 - 220, 400))
        cont = font_small.render("PRESS [SPACE] TO CONTINUE", True, CYAN)
        screen.blit(cont, (SCREEN_WIDTH//2 - 120, 500))

    elif game_state in [STATE_GAMEOVER, STATE_WIN]:
        # HATA DÜZELTME: STATE_WIN tanımlı olduğu için artık hata vermez
        t = font_big.render("GAME OVER", True, NEON_RED)
        screen.blit(t, (SCREEN_WIDTH//2 - 150, 200))
        
        info = font_medium.render(game_over_text, True, WHITE)
        screen.blit(info, (SCREEN_WIDTH//2 - 100, 300))
        
        sc = font_small.render(f"P1: {p1.score} | P2: {p2.score}", True, WHITE)
        screen.blit(sc, (SCREEN_WIDTH//2 - 80, 350))

        rst = font_pixel.render("[SPACE] TRY AGAIN", True, WHITE)
        screen.blit(rst, (SCREEN_WIDTH//2 - 180, 500))

    pygame.display.flip()

pygame.quit()
sys.exit()