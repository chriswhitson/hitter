import asyncio
import math
import random
from dataclasses import dataclass

import pygame

WIDTH, HEIGHT = 1280, 720
FPS = 60

WHITE = (246, 246, 246)
WALL = (0, 0, 0)
PLAYER_GREEN = (40, 170, 60)
SHADOW_COLOR = (195, 195, 195)
YELLOW = (255, 214, 0)
ORANGE = (255, 136, 0)
RED = (220, 40, 40)
GREY = (135, 135, 135)
PURPLE = (134, 86, 180)
BLUE = (65, 110, 220)

DIFFICULTY_COLORS = {"grey": GREY, "purple": PURPLE, "blue": BLUE}
DIFFICULTY_RANGE = {"grey": 250, "purple": 320, "blue": 390}


@dataclass
class Projectile:
    pos: pygame.Vector2
    vel: pygame.Vector2
    owner: str
    life: float
    kind: str


class Enemy:
    def __init__(self, pos, patrol, difficulty):
        self.pos = pygame.Vector2(pos)
        self.patrol = [pygame.Vector2(p) for p in patrol]
        self.patrol_index = 0
        self.vel = pygame.Vector2(1, 0)
        self.speed = {"grey": 105, "purple": 120, "blue": 140}[difficulty]
        self.color_name = difficulty
        self.base_color = DIFFICULTY_COLORS[difficulty]
        self.vision_range = DIFFICULTY_RANGE[difficulty]
        self.vision_angle = 70
        self.alertness = 0.2
        self.state = "patrol"
        self.fire_cd = random.uniform(0.4, 1.0)
        self.body_alive = True
        self.target = None

    def alert_color(self):
        if self.alertness < 0.33:
            return YELLOW
        if self.alertness < 0.66:
            return ORANGE
        return RED


class Camera:
    def __init__(self, pos, facing, cone=60, view_range=320):
        self.pos = pygame.Vector2(pos)
        self.facing = pygame.Vector2(facing).normalize()
        self.cone = cone
        self.view_range = view_range
        self.active = True


class Player:
    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)
        self.speed = 200
        self.health = 100
        self.has_goal = False
        self.disguise = None
        self.keys = set()
        self.ammo = 36
        self.daggers = 7
        self.fire_cd = 0
        self.throw_cd = 0
        self.leaning = False
        self.lean_normal = pygame.Vector2(0, 0)


class Level:
    def __init__(self, data):
        self.spawn = pygame.Vector2(data["spawn"])
        self.goal = pygame.Vector2(data["goal"])
        self.escape = pygame.Rect(data["escape"])
        self.walls = [pygame.Rect(r) for r in data["walls"]]
        self.shadows = [pygame.Rect(r) for r in data.get("shadows", [])]
        self.gates = [dict(rect=pygame.Rect(g["rect"]), color=g["color"], open=g.get("open", False), key=g.get("key"), button=g.get("button")) for g in data.get("gates", [])]
        self.keys = [dict(id=k["id"], rect=pygame.Rect(k["rect"]), taken=False) for k in data.get("keys", [])]
        self.buttons = [dict(id=b["id"], rect=pygame.Rect(b["rect"])) for b in data.get("buttons", [])]
        self.cameras = [Camera(c["pos"], c["facing"], c.get("cone", 60), c.get("range", 320)) for c in data.get("cameras", [])]
        self.enemies = [Enemy(e["pos"], e["patrol"], e["difficulty"]) for e in data["enemies"]]


LEVELS = [
    {
        "spawn": (120, 620),
        "goal": (1130, 100),
        "escape": (40, 40, 90, 90),
        "walls": [
            (0, 0, 1280, 20), (0, 700, 1280, 20), (0, 0, 20, 720), (1260, 0, 20, 720),
            (220, 220, 20, 500), (220, 220, 350, 20), (560, 100, 20, 420),
            (370, 510, 560, 20), (910, 190, 20, 340), (940, 190, 280, 20),
            (730, 320, 20, 200), (750, 320, 170, 20),
        ],
        "shadows": [(30, 510, 200, 170), (380, 530, 300, 160), (1010, 40, 200, 130)],
        "gates": [
            {"rect": (560, 500, 20, 70), "color": "grey", "key": "k1"},
            {"rect": (910, 450, 20, 60), "color": "purple", "button": "b1"},
        ],
        "keys": [{"id": "k1", "rect": (70, 550, 24, 24)}],
        "buttons": [{"id": "b1", "rect": (780, 590, 30, 30)}],
        "cameras": [
            {"pos": (650, 250), "facing": (0, 1), "cone": 55, "range": 280},
            {"pos": (1060, 280), "facing": (-1, 0), "cone": 50, "range": 240},
        ],
        "enemies": [
            {"pos": (300, 610), "difficulty": "grey", "patrol": [(300, 610), (500, 610), (500, 390), (300, 390)]},
            {"pos": (670, 440), "difficulty": "purple", "patrol": [(670, 440), (870, 440), (870, 260), (670, 260)]},
            {"pos": (1040, 120), "difficulty": "blue", "patrol": [(1040, 120), (1170, 120), (1170, 300), (1040, 300)]},
        ],
    },
    {
        "spawn": (90, 650),
        "goal": (1160, 90),
        "escape": (40, 40, 90, 90),
        "walls": [
            (0, 0, 1280, 20), (0, 700, 1280, 20), (0, 0, 20, 720), (1260, 0, 20, 720),
            (180, 120, 20, 600), (180, 120, 350, 20), (530, 120, 20, 420),
            (350, 300, 500, 20), (840, 120, 20, 420), (860, 520, 340, 20),
            (980, 200, 20, 340), (640, 540, 20, 160),
        ],
        "shadows": [(20, 540, 220, 160), (560, 560, 260, 140), (1060, 20, 170, 120)],
        "gates": [
            {"rect": (530, 500, 20, 60), "color": "grey", "key": "k2"},
            {"rect": (980, 510, 20, 60), "color": "blue", "button": "b2"},
            {"rect": (850, 260, 20, 60), "color": "purple"},
        ],
        "keys": [{"id": "k2", "rect": (260, 160, 24, 24)}],
        "buttons": [{"id": "b2", "rect": (710, 610, 30, 30)}],
        "cameras": [
            {"pos": (300, 200), "facing": (1, 0), "cone": 60, "range": 260},
            {"pos": (930, 360), "facing": (-1, 0), "cone": 60, "range": 300},
            {"pos": (1140, 260), "facing": (0, 1), "cone": 50, "range": 230},
        ],
        "enemies": [
            {"pos": (260, 600), "difficulty": "grey", "patrol": [(260, 600), (430, 600), (430, 420), (260, 420)]},
            {"pos": (590, 420), "difficulty": "purple", "patrol": [(590, 420), (800, 420), (800, 180), (590, 180)]},
            {"pos": (1040, 580), "difficulty": "blue", "patrol": [(1040, 580), (1180, 580), (1180, 360), (1040, 360)]},
            {"pos": (1100, 130), "difficulty": "blue", "patrol": [(1100, 130), (1180, 130), (1180, 260), (1100, 260)]},
        ],
    },
]


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Hitter: Abstract Extraction")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 20)
        self.big_font = pygame.font.SysFont("arial", 38)
        self.floor = self.generate_floor_texture()
        self.level_index = 0
        self.level = Level(LEVELS[self.level_index])
        self.player = Player(self.level.spawn)
        self.projectiles = []
        self.alert_pos = None
        self.alert_timer = 0.0
        self.won = False
        self.lose = False
        self.mobile_controls = self.build_mobile_controls()
        self.mobile_pressed = set()
        self.pointer_controls = {}

    def build_mobile_controls(self):
        left = {
            "up": pygame.Rect(86, HEIGHT - 194, 72, 72),
            "down": pygame.Rect(86, HEIGHT - 94, 72, 72),
            "left": pygame.Rect(20, HEIGHT - 128, 72, 72),
            "right": pygame.Rect(152, HEIGHT - 128, 72, 72),
        }
        right = {
            "shoot": pygame.Rect(WIDTH - 220, HEIGHT - 144, 84, 84),
            "dagger": pygame.Rect(WIDTH - 124, HEIGHT - 204, 72, 72),
            "disguise": pygame.Rect(WIDTH - 116, HEIGHT - 102, 72, 72),
        }
        return {**left, **right}

    def control_at_point(self, pos):
        for name, rect in self.mobile_controls.items():
            if rect.collidepoint(pos):
                return name
        return None

    def auto_aim_direction(self):
        best = None
        best_dist = float("inf")
        for enemy in self.level.enemies:
            if not enemy.body_alive:
                continue
            dist = (enemy.pos - self.player.pos).length_squared()
            if dist < best_dist:
                best_dist = dist
                best = enemy.pos
        if best is not None:
            return best - self.player.pos
        return pygame.Vector2(0, -1)

    def generate_floor_texture(self):
        surface = pygame.Surface((WIDTH, HEIGHT))
        surface.fill(WHITE)
        for _ in range(8500):
            x = random.randrange(0, WIDTH)
            y = random.randrange(0, HEIGHT)
            shade = random.randrange(236, 247)
            surface.set_at((x, y), (shade, shade, shade))
        return surface

    def player_rect(self, pos=None):
        p = self.player.pos if pos is None else pos
        return pygame.Rect(p.x - 12, p.y - 12, 24, 24)

    def entity_blockers(self):
        blockers = list(self.level.walls)
        for gate in self.level.gates:
            if gate["open"]:
                continue
            if self.player.disguise == gate["color"]:
                continue
            blockers.append(gate["rect"])
        return blockers

    def line_blocked(self, start, end):
        for rect in self.level.walls:
            if rect.clipline(start, end):
                return True
        return False

    def in_shadow(self, point):
        return any(s.collidepoint(point.x, point.y) for s in self.level.shadows)

    def wall_contact_normal(self):
        rect = self.player_rect()
        threshold = 8
        best_gap = threshold + 1
        best_normal = None
        for wall in self.entity_blockers():
            overlap_y = min(rect.bottom, wall.bottom) - max(rect.top, wall.top)
            if overlap_y > 4:
                left_gap = abs(rect.left - wall.right)
                if left_gap <= threshold and left_gap < best_gap:
                    best_gap = left_gap
                    best_normal = pygame.Vector2(1, 0)
                right_gap = abs(rect.right - wall.left)
                if right_gap <= threshold and right_gap < best_gap:
                    best_gap = right_gap
                    best_normal = pygame.Vector2(-1, 0)

            overlap_x = min(rect.right, wall.right) - max(rect.left, wall.left)
            if overlap_x > 4:
                top_gap = abs(rect.top - wall.bottom)
                if top_gap <= threshold and top_gap < best_gap:
                    best_gap = top_gap
                    best_normal = pygame.Vector2(0, 1)
                bottom_gap = abs(rect.bottom - wall.top)
                if bottom_gap <= threshold and bottom_gap < best_gap:
                    best_gap = bottom_gap
                    best_normal = pygame.Vector2(0, -1)
        return best_normal

    def player_visibility_multiplier(self):
        visibility = 1.0
        if self.in_shadow(self.player.pos):
            visibility *= 0.55
        if self.player.leaning:
            visibility *= 0.45
        return visibility

    def set_alert(self, pos):
        self.alert_pos = pygame.Vector2(pos)
        self.alert_timer = 4.5
        for enemy in self.level.enemies:
            if not enemy.body_alive:
                continue
            enemy.state = "combat"
            enemy.target = pygame.Vector2(pos)
            enemy.alertness = 1.0

    def angle_in_cone(self, source, facing, target, cone_degrees):
        to_target = target - source
        if to_target.length_squared() <= 1:
            return True
        to_target = to_target.normalize()
        facing_n = facing.normalize() if facing.length_squared() else pygame.Vector2(1, 0)
        angle = math.degrees(math.acos(max(-1, min(1, facing_n.dot(to_target)))))
        return angle <= cone_degrees / 2

    def move_with_collisions(self, mover_rect, delta):
        blockers = self.entity_blockers()
        rect = mover_rect.copy()
        rect.x += int(delta.x)
        for b in blockers:
            if rect.colliderect(b):
                if delta.x > 0:
                    rect.right = b.left
                elif delta.x < 0:
                    rect.left = b.right
        rect.y += int(delta.y)
        for b in blockers:
            if rect.colliderect(b):
                if delta.y > 0:
                    rect.bottom = b.top
                elif delta.y < 0:
                    rect.top = b.bottom
        return rect

    def update_player(self, dt):
        keys = pygame.key.get_pressed()
        move = pygame.Vector2(0, 0)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            move.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            move.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            move.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            move.x += 1
        if "up" in self.mobile_pressed:
            move.y -= 1
        if "down" in self.mobile_pressed:
            move.y += 1
        if "left" in self.mobile_pressed:
            move.x -= 1
        if "right" in self.mobile_pressed:
            move.x += 1
        if move.length_squared() > 0:
            move = move.normalize() * self.player.speed * dt

        new_rect = self.move_with_collisions(self.player_rect(), move)
        self.player.pos.update(new_rect.centerx, new_rect.centery)

        wall_normal = self.wall_contact_normal()
        if wall_normal is not None:
            self.player.leaning = True
            self.player.lean_normal = wall_normal
        else:
            self.player.leaning = False
            self.player.lean_normal = pygame.Vector2(0, 0)

        for key in self.level.keys:
            if not key["taken"] and key["rect"].colliderect(self.player_rect()):
                key["taken"] = True
                self.player.keys.add(key["id"])

        active_buttons = {b["id"] for b in self.level.buttons if b["rect"].colliderect(self.player_rect())}
        for gate in self.level.gates:
            gate["open"] = ((gate.get("key") in self.player.keys if gate.get("key") else False) or
                            (gate.get("button") in active_buttons if gate.get("button") else False))

        if (self.player.pos - self.level.goal).length() < 20:
            self.player.has_goal = True

        if self.player.has_goal and self.level.escape.colliderect(self.player_rect()):
            self.level_index += 1
            if self.level_index >= len(LEVELS):
                self.won = True
                return
            self.level = Level(LEVELS[self.level_index])
            self.player = Player(self.level.spawn)
            self.projectiles.clear()
            self.alert_pos = None
            self.alert_timer = 0
            self.mobile_pressed.clear()
            self.pointer_controls.clear()

    def spawn_player_shot(self, kind, direction):
        if direction.length_squared() == 0:
            return
        direction = direction.normalize()
        speed = 520 if kind == "bullet" else 390
        self.projectiles.append(Projectile(self.player.pos.copy(), direction * speed, "player", 1.8, kind))

    def update_enemy(self, enemy, dt):
        if not enemy.body_alive:
            return

        enemy.fire_cd = max(0.0, enemy.fire_cd - dt)

        player_detect_range = enemy.vision_range * self.player_visibility_multiplier()
        if self.player.disguise == enemy.color_name:
            player_detect_range *= 0.2

        sees_player = False
        dist = (self.player.pos - enemy.pos).length()
        if dist <= player_detect_range:
            in_cone = self.angle_in_cone(enemy.pos, enemy.vel, self.player.pos, enemy.vision_angle)
            if in_cone and not self.line_blocked(enemy.pos, self.player.pos):
                if self.player.disguise != enemy.color_name or dist < 64:
                    sees_player = True

        if sees_player:
            self.set_alert(self.player.pos)

        if self.alert_timer > 0:
            if enemy.state != "combat":
                enemy.state = "investigate"
                enemy.target = self.alert_pos.copy() if self.alert_pos is not None else None
                enemy.alertness = max(enemy.alertness, 0.5)

        if enemy.state == "combat":
            enemy.alertness = 1.0
            enemy.target = self.player.pos.copy() if sees_player else (self.alert_pos.copy() if self.alert_pos is not None else None)
            if enemy.target is not None:
                delta = enemy.target - enemy.pos
                if delta.length_squared() > 2:
                    enemy.vel = delta.normalize()
                    step = enemy.vel * enemy.speed * dt
                    rect = pygame.Rect(enemy.pos.x - 12, enemy.pos.y - 12, 24, 24)
                    moved = self.move_with_collisions(rect, step)
                    enemy.pos.update(moved.centerx, moved.centery)
            if dist < enemy.vision_range * 1.1 and not self.line_blocked(enemy.pos, self.player.pos) and enemy.fire_cd <= 0:
                shot_dir = (self.player.pos - enemy.pos)
                if shot_dir.length_squared() > 0:
                    self.projectiles.append(Projectile(enemy.pos.copy(), shot_dir.normalize() * 430, "enemy", 2.2, "bullet"))
                enemy.fire_cd = random.uniform(0.7, 1.2)
            if self.alert_timer <= 0 and not sees_player:
                enemy.state = "investigate"
                enemy.target = self.player.pos.copy()

        elif enemy.state == "investigate":
            enemy.alertness = max(0.45, enemy.alertness - dt * 0.2)
            target = enemy.target if enemy.target is not None else enemy.patrol[enemy.patrol_index]
            delta = target - enemy.pos
            if delta.length_squared() < 14:
                enemy.state = "patrol"
            else:
                enemy.vel = delta.normalize()
                rect = pygame.Rect(enemy.pos.x - 12, enemy.pos.y - 12, 24, 24)
                moved = self.move_with_collisions(rect, enemy.vel * enemy.speed * dt)
                enemy.pos.update(moved.centerx, moved.centery)

        else:
            enemy.alertness = max(0.2, enemy.alertness - dt * 0.4)
            target = enemy.patrol[enemy.patrol_index]
            delta = target - enemy.pos
            if delta.length_squared() < 16:
                enemy.patrol_index = (enemy.patrol_index + 1) % len(enemy.patrol)
            else:
                enemy.vel = delta.normalize()
                rect = pygame.Rect(enemy.pos.x - 12, enemy.pos.y - 12, 24, 24)
                moved = self.move_with_collisions(rect, enemy.vel * enemy.speed * dt)
                enemy.pos.update(moved.centerx, moved.centery)

    def update_cameras(self):
        for cam in self.level.cameras:
            if not cam.active:
                continue
            to_player = self.player.pos - cam.pos
            if to_player.length() > cam.view_range * self.player_visibility_multiplier():
                continue
            if self.angle_in_cone(cam.pos, cam.facing, self.player.pos, cam.cone) and not self.line_blocked(cam.pos, self.player.pos):
                self.set_alert(self.player.pos)

    def update_projectiles(self, dt):
        for proj in list(self.projectiles):
            proj.life -= dt
            if proj.life <= 0:
                self.projectiles.remove(proj)
                continue
            proj.pos += proj.vel * dt

            if proj.pos.x < 0 or proj.pos.x > WIDTH or proj.pos.y < 0 or proj.pos.y > HEIGHT:
                self.projectiles.remove(proj)
                continue

            hit_wall = False
            for wall in self.level.walls:
                if wall.collidepoint(proj.pos.x, proj.pos.y):
                    hit_wall = True
                    break
            if hit_wall:
                self.projectiles.remove(proj)
                continue

            if proj.owner == "player":
                for cam in self.level.cameras:
                    if cam.active and pygame.Rect(cam.pos.x - 8, cam.pos.y - 8, 16, 16).collidepoint(proj.pos.x, proj.pos.y):
                        cam.active = False
                        if proj in self.projectiles:
                            self.projectiles.remove(proj)
                        break
                for enemy in self.level.enemies:
                    if enemy.body_alive and pygame.Rect(enemy.pos.x - 12, enemy.pos.y - 12, 24, 24).collidepoint(proj.pos.x, proj.pos.y):
                        enemy.body_alive = False
                        enemy.state = "down"
                        enemy.alertness = 0.0
                        if proj in self.projectiles:
                            self.projectiles.remove(proj)
                        break
            else:
                if self.player_rect().collidepoint(proj.pos.x, proj.pos.y):
                    self.player.health -= 20
                    self.projectiles.remove(proj)
                    if self.player.health <= 0:
                        self.lose = True

    def pickup_disguise(self):
        for enemy in self.level.enemies:
            if enemy.body_alive:
                continue
            if (enemy.pos - self.player.pos).length() < 34:
                self.player.disguise = enemy.color_name
                return

    def draw_cone(self, pos, facing, fov, view_range, color, alpha):
        cone_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        angle = math.atan2(facing.y, facing.x)
        left = angle - math.radians(fov / 2)
        right = angle + math.radians(fov / 2)
        left_pt = (pos.x + math.cos(left) * view_range, pos.y + math.sin(left) * view_range)
        right_pt = (pos.x + math.cos(right) * view_range, pos.y + math.sin(right) * view_range)
        pygame.draw.polygon(cone_surface, (*color, alpha), [(pos.x, pos.y), left_pt, right_pt])
        self.screen.blit(cone_surface, (0, 0))

    def draw_player(self):
        color = PLAYER_GREEN if self.player.disguise is None else DIFFICULTY_COLORS[self.player.disguise]
        if self.player.leaning:
            direction = self.player.lean_normal.normalize() if self.player.lean_normal.length_squared() else pygame.Vector2(0, -1)
            side = pygame.Vector2(-direction.y, direction.x)
            nose = self.player.pos + direction * 12
            back = self.player.pos - direction * 10
            flank = back + side * 12
            pygame.draw.polygon(self.screen, color, [nose, back, flank])
        else:
            body = pygame.Rect(self.player.pos.x - 13, self.player.pos.y - 2, 26, 20)
            pygame.draw.rect(self.screen, color, body)
            pygame.draw.circle(self.screen, color, (int(self.player.pos.x), int(self.player.pos.y - 2)), 13)

    def draw_enemy(self, enemy):
        if enemy.body_alive:
            self.draw_cone(enemy.pos, enemy.vel, enemy.vision_angle, enemy.vision_range, enemy.base_color, 36)
            direction = enemy.vel.normalize() if enemy.vel.length_squared() else pygame.Vector2(1, 0)
            side = pygame.Vector2(-direction.y, direction.x)
            nose = enemy.pos + direction * 14
            back_left = enemy.pos - direction * 10 + side * 10
            back_right = enemy.pos - direction * 10 - side * 10
            pygame.draw.polygon(self.screen, enemy.base_color, [nose, back_left, back_right])
            pygame.draw.polygon(self.screen, enemy.alert_color(), [nose, back_left, back_right], 3)
        else:
            pygame.draw.circle(self.screen, enemy.base_color, (int(enemy.pos.x), int(enemy.pos.y)), 10)

    def draw(self):
        self.screen.blit(self.floor, (0, 0))

        for s in self.level.shadows:
            pygame.draw.rect(self.screen, SHADOW_COLOR, s)

        for wall in self.level.walls:
            pygame.draw.rect(self.screen, WALL, wall)

        for gate in self.level.gates:
            if gate["open"]:
                pygame.draw.rect(self.screen, (205, 205, 205), gate["rect"], 2)
            else:
                pygame.draw.rect(self.screen, DIFFICULTY_COLORS[gate["color"]], gate["rect"])

        for key in self.level.keys:
            if not key["taken"]:
                pygame.draw.rect(self.screen, (250, 210, 20), key["rect"])

        for button in self.level.buttons:
            color = (170, 230, 170) if button["rect"].colliderect(self.player_rect()) else (80, 180, 80)
            pygame.draw.rect(self.screen, color, button["rect"])

        for cam in self.level.cameras:
            if cam.active:
                self.draw_cone(cam.pos, cam.facing, cam.cone, cam.view_range, (120, 120, 120), 45)
                pygame.draw.rect(self.screen, (40, 40, 40), (cam.pos.x - 8, cam.pos.y - 8, 16, 16))
            else:
                pygame.draw.rect(self.screen, (100, 100, 100), (cam.pos.x - 8, cam.pos.y - 8, 16, 16))

        for enemy in self.level.enemies:
            self.draw_enemy(enemy)

        goal_color = (255, 215, 80) if not self.player.has_goal else (180, 160, 60)
        pygame.draw.circle(self.screen, goal_color, (int(self.level.goal.x), int(self.level.goal.y)), 12)
        pygame.draw.rect(self.screen, (60, 170, 200), self.level.escape, 2)

        for proj in self.projectiles:
            c = (10, 10, 10) if proj.owner == "enemy" else ((20, 90, 20) if proj.kind == "bullet" else (50, 20, 80))
            pygame.draw.circle(self.screen, c, (int(proj.pos.x), int(proj.pos.y)), 4 if proj.kind == "bullet" else 5)

        self.draw_player()

        hud = [
            f"Level {self.level_index + 1}/{len(LEVELS)}",
            f"Health: {self.player.health}",
            f"Ammo: {self.player.ammo}",
            f"Daggers: {self.player.daggers}",
            f"Disguise: {self.player.disguise or 'none'}",
            "Goal: secured" if self.player.has_goal else "Goal: steal objective",
        ]
        for i, line in enumerate(hud):
            txt = self.font.render(line, True, (25, 25, 25))
            self.screen.blit(txt, (24, 20 + i * 24))

        tip = self.font.render("WASD move | auto-lean near walls | LMB shoot | RMB throw dagger | C steal colour", True, (40, 40, 40))
        self.screen.blit(tip, (24, HEIGHT - 34))
        touch_tip = self.font.render("Touch: D-pad move | SHOOT | DAGGER | COLOR", True, (40, 40, 40))
        self.screen.blit(touch_tip, (24, HEIGHT - 58))

        for name, rect in self.mobile_controls.items():
            pressed = name in self.mobile_pressed
            base = (55, 55, 55, 170) if not pressed else (20, 120, 45, 190)
            overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.ellipse(overlay, base, overlay.get_rect())
            self.screen.blit(overlay, rect.topleft)
            label = {
                "up": "U", "down": "D", "left": "L", "right": "R",
                "shoot": "SHOOT", "dagger": "DAG", "disguise": "CLR",
            }[name]
            txt = self.font.render(label, True, (245, 245, 245))
            self.screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

        if self.won:
            txt = self.big_font.render("Extraction complete.", True, (0, 0, 0))
            self.screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 30))
        if self.lose:
            txt = self.big_font.render("You were eliminated.", True, (120, 0, 0))
            self.screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 30))

    async def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_c:
                    self.pickup_disguise()
                if event.type == pygame.MOUSEBUTTONDOWN and not self.won and not self.lose:
                    mouse = pygame.Vector2(event.pos)
                    control = self.control_at_point(mouse)
                    if event.button == 1 and control is not None:
                        self.mobile_pressed.add(control)
                        self.pointer_controls[("mouse", event.button)] = control
                        if control == "shoot" and self.player.ammo > 0 and self.player.fire_cd <= 0:
                            self.spawn_player_shot("bullet", self.auto_aim_direction())
                            self.player.ammo -= 1
                            self.player.fire_cd = 0.16
                        elif control == "dagger" and self.player.daggers > 0 and self.player.throw_cd <= 0:
                            self.spawn_player_shot("dagger", self.auto_aim_direction())
                            self.player.daggers -= 1
                            self.player.throw_cd = 0.4
                        elif control == "disguise":
                            self.pickup_disguise()
                    else:
                        aim = mouse - self.player.pos
                        if event.button == 1 and self.player.ammo > 0 and self.player.fire_cd <= 0:
                            self.spawn_player_shot("bullet", aim)
                            self.player.ammo -= 1
                            self.player.fire_cd = 0.16
                        if event.button == 3 and self.player.daggers > 0 and self.player.throw_cd <= 0:
                            self.spawn_player_shot("dagger", aim)
                            self.player.daggers -= 1
                            self.player.throw_cd = 0.4
                if event.type == pygame.MOUSEBUTTONUP:
                    key = ("mouse", event.button)
                    control = self.pointer_controls.pop(key, None)
                    if control is not None:
                        self.mobile_pressed.discard(control)
                if event.type == pygame.FINGERDOWN and not self.won and not self.lose:
                    pos = (int(event.x * WIDTH), int(event.y * HEIGHT))
                    control = self.control_at_point(pos)
                    if control is not None:
                        self.mobile_pressed.add(control)
                        self.pointer_controls[("finger", event.finger_id)] = control
                        if control == "shoot" and self.player.ammo > 0 and self.player.fire_cd <= 0:
                            self.spawn_player_shot("bullet", self.auto_aim_direction())
                            self.player.ammo -= 1
                            self.player.fire_cd = 0.16
                        elif control == "dagger" and self.player.daggers > 0 and self.player.throw_cd <= 0:
                            self.spawn_player_shot("dagger", self.auto_aim_direction())
                            self.player.daggers -= 1
                            self.player.throw_cd = 0.4
                        elif control == "disguise":
                            self.pickup_disguise()
                    elif self.player.ammo > 0 and self.player.fire_cd <= 0:
                        self.spawn_player_shot("bullet", pygame.Vector2(pos) - self.player.pos)
                        self.player.ammo -= 1
                        self.player.fire_cd = 0.16
                if event.type in (pygame.FINGERUP, pygame.FINGERMOTION):
                    key = ("finger", event.finger_id)
                    current = self.pointer_controls.get(key)
                    if current is None:
                        continue
                    pos = (int(event.x * WIDTH), int(event.y * HEIGHT))
                    now_control = self.control_at_point(pos)
                    if event.type == pygame.FINGERUP:
                        self.mobile_pressed.discard(current)
                        self.pointer_controls.pop(key, None)
                    elif now_control != current:
                        self.mobile_pressed.discard(current)
                        if now_control is not None:
                            self.mobile_pressed.add(now_control)
                            self.pointer_controls[key] = now_control
                        else:
                            self.pointer_controls.pop(key, None)

            if not self.won and not self.lose:
                self.player.fire_cd = max(0.0, self.player.fire_cd - dt)
                self.player.throw_cd = max(0.0, self.player.throw_cd - dt)
                self.alert_timer = max(0.0, self.alert_timer - dt)
                if self.alert_timer <= 0:
                    self.alert_pos = None

                self.update_player(dt)
                for enemy in self.level.enemies:
                    self.update_enemy(enemy, dt)
                self.update_cameras()
                self.update_projectiles(dt)

            self.draw()
            pygame.display.flip()
            await asyncio.sleep(0)

        pygame.quit()


async def main():
    game = Game()
    await game.run()


if __name__ == "__main__":
    asyncio.run(main())
