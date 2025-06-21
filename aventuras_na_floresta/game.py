import pgzrun
import random
import math
from pygame.rect import Rect

WIDTH = 800
HEIGHT = 480
TITLE = "Aventuras na Floresta"

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (40, 135, 50)
BROWN = (139, 69, 19)
BLUE = (0, 0, 200)
RED = (200, 0, 0)

GAME_STATE_MENU = 0
GAME_STATE_PLAYING = 1
GAME_STATE_GAME_OVER = 2
GAME_STATE_WIN = 3

music_on = True

class Animation:
    def __init__(self, image_names, frame_duration):
        self.images = image_names
        self.frame_duration = frame_duration
        self.current_frame_index = 0
        self.frame_counter = 0
    def get_current_image(self):
        return self.images[self.current_frame_index]
    def update(self):
        self.frame_counter += 1
        if self.frame_counter >= self.frame_duration:
            self.frame_counter = 0
            self.current_frame_index = (self.current_frame_index + 1) % len(self.images)
    def reset(self):
        self.current_frame_index = 0
        self.frame_counter = 0

class Player(Actor):
    _next_id = 0  # Variável de classe para gerar IDs únicos
    
    def __init__(self, x, y):
        Player._next_id += 1
        self.player_id = Player._next_id
        self.idle_animations = Animation(['player_idle_1', 'player_idle_2'], 15)
        self.run_animations = Animation(['player_run_1', 'player_run_2'], 6)
        self.jump_image = 'player_jump'
        self.crouch_image = 'player_duck'
        self.attack_image = 'player_attack'
        self.current_animation = self.idle_animations
        super().__init__(self.current_animation.get_current_image(), (x, y))
        self.speed = 3
        self.jump_force = -9
        self.gravity = 0.4
        self.vy = 0
        self.on_ground = False
        self.facing_right = True
        self.crouching = False
        self.attacking = False
        self.attack_timer = 0
        self.attack_duration = 20
        self.attack_cooldown = 0
        self.attack_cooldown_duration = 30
        self.previous_y = self.y
        self.image = self.current_animation.get_current_image()
        self.height = 40
    def update(self, platforms):
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.attacking:
            self.attack_timer += 1
            if self.attack_timer > self.attack_duration:
                self.attacking = False
                self.attack_timer = 0
        
        if keyboard.down and self.on_ground:
            self.crouching = True
        elif not keyboard.down:
            self.crouching = False
        
        dx = 0
        current_speed = 2 if self.crouching else 3
        
        if not self.attacking:
            if keyboard.left:
                dx = -current_speed
                self.facing_right = False
            elif keyboard.right:
                dx = +current_speed
                self.facing_right = True
        
        self.x += dx
        
        # Colisão horizontal
        for platform in platforms:
            if self.colliderect(platform):
                if dx > 0:
                    self.right = platform.left
                elif dx < 0:
                    self.left = platform.right
        
        self.vy += self.gravity
        self.y += self.vy
        self.on_ground = False
        
        # Colisão vertical com o chão
        for platform in platforms:
            if self.colliderect(platform):
                if self.vy > 0 and self.bottom > platform.top and self.bottom <= platform.top + 25:
                    self.bottom = platform.top
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0 and self.top < platform.bottom and self.top > platform.top and not self.on_ground:
                    self.top = platform.bottom
                    self.vy = 0
        
        # Verificação adicional para garantir que não atravesse o chão
        if self.bottom > HEIGHT - 40 and self.vy > 0:
            self.bottom = HEIGHT - 40
            self.vy = 0
            self.on_ground = True
        
        # Limites da tela
        if self.left < 20:
            self.left = 20
        if self.right > WIDTH - 20:
            self.right = WIDTH - 20
        
        # Atualização da imagem baseada no estado
        base_image_name = ""
        if self.attacking:
            base_image_name = self.attack_image
        elif not self.on_ground:
            base_image_name = self.jump_image
        elif self.crouching:
            base_image_name = self.crouch_image
        else:
            if dx != 0:
                self.run_animations.update()
                base_image_name = self.run_animations.get_current_image()
            else:
                self.idle_animations.update()
                base_image_name = self.idle_animations.get_current_image()
        
        if not base_image_name:
            base_image_name = self.idle_animations.get_current_image()
        
        # Aplicar flip se necessário
        if not self.facing_right:
            if not base_image_name.endswith("_flipped"):
                self.image = base_image_name + "_flipped"
            else:
                self.image = base_image_name
        else:
            if base_image_name.endswith("_flipped"):
                self.image = base_image_name[:-8]
            else:
                self.image = base_image_name
        
        # Ajustar altura quando agachado
        if self.crouching:
            self.height = 25
        else:
            self.height = 40
    def jump(self):
        if self.on_ground and not self.crouching and not self.attacking:
            sounds.jump.play()
            self.vy = self.jump_force
            self.on_ground = False
    def attack(self):
        if not self.attacking and self.attack_cooldown == 0:
            self.attacking = True
            self.attack_cooldown = self.attack_cooldown_duration
            sounds.hit.play()

class Enemy(Actor):
    def __init__(self, x, y, patrol_range_left, patrol_range_right):
        self.walk_animations = Animation(['enemy_walk_1', 'enemy_walk_2'], 12)
        self.die_animations = Animation(['enemy_die_1'], 30)
        super().__init__(self.walk_animations.get_current_image(), (x, y))
        self.speed = 1
        self.direction = 1
        self.patrol_range_left = patrol_range_left
        self.patrol_range_right = patrol_range_right
        self.is_dying = False
        self.death_timer = 0
        self.enemy_type = "enemy"
    def update(self):
        if self.is_dying:
            self.death_timer += 1
            if self.death_timer > 60:
                return True
            return False
        self.x += self.speed * self.direction
        if self.x > self.patrol_range_right or self.x < self.patrol_range_left:
            self.direction *= -1
        self.walk_animations.update()
        base_image_name = self.walk_animations.get_current_image()
        if self.direction == -1:
            self.image = base_image_name + "_flipped"
        else:
            self.image = base_image_name
        return False
    def die(self):
        self.is_dying = True
        self.death_timer = 0
        self.image = "enemy_die_1"
        if self.direction == -1:
            self.image += "_flipped"

class Spiky(Actor):
    def __init__(self, x, y, patrol_range_left, patrol_range_right):
        self.idle_animations = Animation(['spiky_idle_1', 'spiky_idle_2'], 15)
        self.die_animations = Animation(['spiky_die_1'], 30)
        super().__init__(self.idle_animations.get_current_image(), (x, y))
        self.speed = 0.5
        self.direction = 1
        self.patrol_range_left = patrol_range_left
        self.patrol_range_right = patrol_range_right
        self.is_dying = False
        self.death_timer = 0
        self.enemy_type = "spiky"
    def update(self):
        if self.is_dying:
            self.death_timer += 1
            if self.death_timer > 60:
                return True
            return False
        self.x += self.speed * self.direction
        if self.x > self.patrol_range_right or self.x < self.patrol_range_left:
            self.direction *= -1
        self.idle_animations.update()
        base_image_name = self.idle_animations.get_current_image()
        self.image = base_image_name
        return False
    def die(self):
        self.is_dying = True
        self.death_timer = 0
        self.image = "spiky_die_1"

class Platform(Rect):
    def __init__(self, x, y, width, height):
        super().__init__((x, y), (width, height))

class Game:
    def __init__(self):
        self.current_state = GAME_STATE_MENU
        self.background = Actor('background', (WIDTH // 2, HEIGHT // 2))
        button_width, button_height = 200, 50
        self.start_button = Rect((WIDTH//2 - button_width//2, 200), (button_width, button_height))
        self.music_button = Rect((WIDTH//2 - button_width//2, 260), (button_width, button_height))
        self.exit_button = Rect((WIDTH//2 - button_width//2, 320), (button_width, button_height))
        self.player = None
        self.platforms = []
        self.enemies = []
        self.game_over_timer = 0
        if music_on:
            music.play('background_music')
            music.set_volume(0.3)
    def load_level_1(self):
        if self.current_state == GAME_STATE_MENU or self.player is None:
            self.player = Player(100, HEIGHT - 120)
        else:
            return
        
        self.platforms = [
            Platform(0, HEIGHT - 40, WIDTH, 40),
        ]
        
        self.enemies = [
            Enemy(300, HEIGHT - 60, 250, 350),
            Enemy(600, HEIGHT - 60, 550, 650),
            Spiky(150, HEIGHT - 60, 100, 200),
            Spiky(500, HEIGHT - 60, 450, 550),
        ]
    def reset_game(self):
        self.current_state = GAME_STATE_MENU
        self.load_level_1()
        if music_on and not music.is_playing('background_music'):
            music.play('background_music')
            music.set_volume(0.3)
    def update(self):
        global music_on
        if self.current_state == GAME_STATE_PLAYING:
            self.player.update(self.platforms)
            enemies_to_remove = []
            for enemy in self.enemies:
                if enemy.update():
                    enemies_to_remove.append(enemy)
            for enemy in enemies_to_remove:
                self.enemies.remove(enemy)
            if self.player.attacking:
                for enemy in self.enemies[:]:
                    if not enemy.is_dying:
                        player_attack_range = 50
                        if self.player.facing_right:
                            attack_x = self.player.x + player_attack_range
                        else:
                            attack_x = self.player.x - player_attack_range
                        
                        distance_x = abs(attack_x - enemy.x)
                        distance_y = abs(self.player.y - enemy.y)
                        
                        if distance_x < 40 and distance_y < 40:
                            enemy.die()
                            break
            living_enemies = [enemy for enemy in self.enemies if not enemy.is_dying]
            if len(living_enemies) == 0 and len(self.enemies) > 0:
                all_dead = True
                for enemy in self.enemies:
                    if enemy.death_timer < 30:
                        all_dead = False
                        break
                if all_dead:
                    self.current_state = GAME_STATE_WIN
                    self.game_over_timer = 0
                    music.stop()
                    music.play('game_win')
                    music.set_volume(0.5)
            if not self.player.attacking:
                for enemy in self.enemies:
                    if not enemy.is_dying:
                        distance_x = abs(self.player.x - enemy.x)
                        distance_y = abs(self.player.y - enemy.y)
                        
                        if distance_x < 30 and distance_y < 30:
                            sounds.hit.play()
                            self.current_state = GAME_STATE_GAME_OVER
                            self.game_over_timer = 0
                            music.stop()
                            music.play('game_over')
                            music.set_volume(0.5)
                            break
        elif self.current_state == GAME_STATE_GAME_OVER:
            self.game_over_timer += 1
            if self.game_over_timer > 120:
                self.reset_game()
        elif self.current_state == GAME_STATE_WIN:
            self.game_over_timer += 1
            if self.game_over_timer > 180:
                self.reset_game()
    def draw(self):
        screen.clear()
        self.background.draw()
        if self.current_state == GAME_STATE_MENU:
            screen.draw.text("Aventuras na Floresta", center=(WIDTH // 2, 100), color=WHITE, fontsize=60, owidth=1.5, ocolor=BLACK)
            screen.draw.filled_rect(self.start_button, BLUE)
            screen.draw.text("Iniciar Jogo", center=self.start_button.center, color=WHITE, fontsize=30)
            screen.draw.filled_rect(self.music_button, BLUE)
            music_text = "Música: ON" if music_on else "Música: OFF"
            screen.draw.text(music_text, center=self.music_button.center, color=WHITE, fontsize=30)
            screen.draw.filled_rect(self.exit_button, BLUE)
            screen.draw.text("Sair", center=self.exit_button.center, color=WHITE, fontsize=30)
        elif self.current_state == GAME_STATE_PLAYING:
            for platform in self.platforms:
                screen.draw.filled_rect(Rect(platform.x, platform.y, platform.width, 8), GREEN)
                screen.draw.filled_rect(Rect(platform.x, platform.y + 8, platform.width, platform.height - 8), BROWN)
            self.player.draw()
            for enemy in self.enemies:
                enemy.draw()
            
            # Seta indicativa para seguir à direita
            arrow_x = self.player.x + 50
            arrow_y = self.player.y - 60
            if arrow_x < WIDTH - 100:
                screen.draw.text("→", center=(arrow_x, arrow_y), color=WHITE, fontsize=40, owidth=2, ocolor=BLACK)
                screen.draw.text("SIGA", center=(arrow_x, arrow_y + 25), color=WHITE, fontsize=16, owidth=1, ocolor=BLACK)
            
            controls = [
                "CONTROLS:",
                "A/D or ←/→: Move",
                "SPACE or ↑: Jump",
                "↓: Crouch",
                "R or ENTER: Attack"
            ]
            y_offset = HEIGHT - 120
            for i, control in enumerate(controls):
                color = WHITE if i == 0 else (200, 200, 200)
                fontsize = 20 if i == 0 else 16
                screen.draw.text(control, topleft=(WIDTH - 200, y_offset + i * 20), color=color, fontsize=fontsize)
        elif self.current_state == GAME_STATE_GAME_OVER:
            screen.draw.text("GAME OVER", center=(WIDTH // 2, HEIGHT // 2), color=RED, fontsize=80, owidth=1.5, ocolor=WHITE)
        elif self.current_state == GAME_STATE_WIN:
            screen.draw.text("VICTORY!", center=(WIDTH // 2, HEIGHT // 2 - 50), color=GREEN, fontsize=80, owidth=1.5, ocolor=WHITE)
            screen.draw.text("You defeated all enemies!", center=(WIDTH // 2, HEIGHT // 2 + 50), color=WHITE, fontsize=40, owidth=1.5, ocolor=BLACK)
game = Game()
def update():
    game.update()
def draw():
    game.draw()
def on_key_down(key):
    if game.current_state == GAME_STATE_PLAYING:
        if key == keys.SPACE or key == keys.UP:
            game.player.jump()
        elif key == keys.R or key == keys.RETURN:
            game.player.attack()
def on_mouse_down(pos):
    global music_on
    if game.current_state == GAME_STATE_MENU:
        if game.start_button.collidepoint(pos):
            game.current_state = GAME_STATE_PLAYING
            game.load_level_1()
            if music_on:
                music.play('background_music')
        elif game.music_button.collidepoint(pos):
            music_on = not music_on
            if music_on:
                music.play('background_music')
                music.set_volume(0.3)
            else:
                music.stop()
        elif game.exit_button.collidepoint(pos):
            exit()
pgzrun.go()