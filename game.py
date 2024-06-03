import pygame
import os
import pytmx
from pytmx.util_pygame import load_pygame

pygame.init()
screen = pygame.display.set_mode((1200, 800))
clock = pygame.time.Clock()

bg_image = pygame.image.load("assets/Background/sky.png").convert_alpha()

tmx_data = load_pygame("map.tmx")
SCALE_FACTOR = 3

class Character(pygame.sprite.Sprite):
    def __init__(self, x, y, group):
        super().__init__(group)
        self.flip = False

        self.idle_animation = self.load_animation('assets/MainCharacters/Kuro/Idle', 4)
        self.run_animation = self.load_animation('assets/MainCharacters/Kuro/Run', 6)
        self.jump_animation = self.load_animation('assets/MainCharacters/Kuro/Jump', 2)
        self.attack_animation = self.load_animation('assets/MainCharacters/Kuro/Attack', 4)

        self.current_frame = 0
        self.animation_time = 0
        self.current_animation = self.idle_animation
        self.animation_speed = 100

        self.image = self.current_animation[self.current_frame]
        self.rect = self.image.get_rect(topleft=(x, y))
        self.hitbox = self.rect.inflate(-self.rect.width * 0.3, -self.rect.height * 0.1)

        self.vel_y = 0
        self.jump = False
        self.attacking = False

    def load_animation(self, path, frame_count):
        frames = [pygame.image.load(os.path.join(path, f'{i}.png')).convert_alpha() for i in range(frame_count)]
        return [pygame.transform.scale(frame, (115, 115)) for frame in frames]

    def update_animation(self, dt):
        self.animation_time += dt
        if self.animation_time >= self.animation_speed:
            self.animation_time = 0
            self.current_frame = (self.current_frame + 1) % len(self.current_animation)
        frame = self.current_animation[self.current_frame]
        if self.flip:
            frame = pygame.transform.flip(frame, True, False)
        self.image = frame
        self.rect.size = self.image.get_size()
        self.hitbox = self.rect.inflate(-self.rect.width * 0.3, -self.rect.height * 0.1)

    def change_animation(self, new_animation):
        if self.current_animation != new_animation:
            self.current_animation = new_animation
            self.current_frame = 0
            self.animation_time = 0

    def collision_test(rect, tiles):
        return [tile for tile in tiles if rect.colliderect(tile)]
    
    def move(rect, movement, tiles):
        collision_types = {'top': False, 'bottom': False, 'right': False, 'left': False}
        rect.x += movement[0]
        for tile in Character.collision_test(rect, tiles):
            if movement[0] > 0:
                rect.right = tile.left
                collision_types['right'] = True
            elif movement[0] < 0:
                rect.left = tile.right
                collision_types['left'] = True
        rect.y += movement[1]
        for tile in Character.collision_test(rect, tiles):
            if movement[1] > 0:
                rect.bottom = tile.top
                collision_types['bottom'] = True
            elif movement[1] < 0:
                rect.top = tile.bottom
                collision_types['top'] = True
        return rect, collision_types

    def update(self, dt, tile_rects):
        self.update_animation(dt)
        player_movement = [0, 0]
        keys = pygame.key.get_pressed()
        if not self.attacking:
            if keys[pygame.K_a]:
                player_movement[0] -= 6
                self.flip = True
            if keys[pygame.K_d]:
                player_movement[0] += 6
                self.flip = False
            if keys[pygame.K_w] or keys[pygame.K_SPACE]:
                if not self.jump:
                    self.vel_y = -15
                    self.jump = True
            if keys[pygame.K_k]:
                self.attacking = True
                self.change_animation(self.attack_animation)
            elif player_movement[0] != 0:
                self.change_animation(self.run_animation)
            else:
                self.change_animation(self.idle_animation)
        else:
            if self.current_frame == len(self.attack_animation) - 1:
                self.attacking = False

        player_movement[1] += self.vel_y
        self.vel_y += 0.6
        if self.vel_y > 9:
            self.vel_y = 9

        self.hitbox, collisions = Character.move(self.hitbox, player_movement, tile_rects)
        self.rect.center = self.hitbox.center

        if collisions['bottom']:
            self.vel_y = 0
            self.jump = False
        elif collisions['top']:
            self.vel_y = 1
            self.jump = True
        else:
            self.jump = True

class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.math.Vector2()
        self.half_w = self.display_surface.get_size()[0] // 2
        self.half_h = self.display_surface.get_size()[1] // 2

    def center_target_camera(self, target):
        self.offset.x = target.rect.centerx - self.half_w
        self.offset.y = target.rect.centery - self.half_h

    def custom_draw(self, player):
        self.center_target_camera(player)
        for sprite in sorted(self.sprites(), key=lambda sprite: sprite.rect.centery):
            offset_pos = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_pos)

def load_tmx_map(filename):
    return pytmx.load_pygame(filename, pixelalpha=True)

def draw_tmx_map(surface, tmx_data, camera):
    tile_rects = []
    for layer in tmx_data.visible_layers:
        if isinstance(layer, pytmx.TiledTileLayer):
            for x, y, gid in layer:
                tile = tmx_data.get_tile_image_by_gid(gid)
                if tile:
                    tile = pygame.transform.scale(tile, (tile.get_width() * SCALE_FACTOR, tile.get_height() * SCALE_FACTOR))
                    tile_pos = pygame.Rect(x * tmx_data.tilewidth * SCALE_FACTOR, y * tmx_data.tileheight * SCALE_FACTOR, tmx_data.tilewidth * SCALE_FACTOR, tmx_data.tileheight * SCALE_FACTOR)
                    surface.blit(tile, tile_pos.topleft - camera.offset)
                    tile_rects.append(tile_pos)
    return tile_rects

def draw_bg():
    scaled_bg = pygame.transform.scale(bg_image, (1200, 800))
    screen.blit(scaled_bg, (0, 0))

camera_group = CameraGroup()
player = Character(700, 1700, camera_group)
camera_group.add(player)

run = True
while run:
    dt = clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    screen.fill((0, 0, 0))
    draw_bg()
    tile_rects = draw_tmx_map(screen, tmx_data, camera_group)
    player.update(dt, tile_rects)
    camera_group.custom_draw(player)
    pygame.display.flip()

pygame.quit()
