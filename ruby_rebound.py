#!/usr/bin/env python3
"""Ruby Rebound — neon brick-shatter arcade for ElbowOS. Python 3 + pygame."""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv

if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/RUBY_REBOUND_ElbowOS.mp4")
TITLE, HANDLE = "RUBY REBOUND", "x.com/ElbowOS"

BG = (8, 4, 18)
NEON_CYAN = (0, 255, 240)
NEON_MAG = (255, 40, 180)
NEON_GOLD = (255, 220, 40)
NEON_PINK = (255, 80, 160)
NEON_LIME = (80, 255, 100)
WHITE = (240, 245, 255)
PADDLE_C = (255, 60, 140)

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            self.screen = pygame.display.set_mode((W, H), pygame.HIDDEN)
        self.surf = pygame.Surface((W, H))
        self.font_lg = pygame.font.SysFont("dejavusans", 72, bold=True)
        self.font_md = pygame.font.SysFont("dejavusans", 48, bold=True)
        self.font_sm = pygame.font.SysFont("dejavusans", 32)
        self.reset()

    def reset(self):
        self.score = 0
        self.combo = 0
        self.lives = 3
        self.paddle = pygame.Rect(W//2 - 120, H - 180, 240, 28)
        self.ball = [W//2, H - 280, random.choice([-8, 8]), -12]
        self.bricks = []
        colors = [NEON_CYAN, NEON_MAG, NEON_GOLD, NEON_PINK, NEON_LIME]
        for row in range(8):
            for col in range(7):
                x = 60 + col * 140
                y = 280 + row * 70
                self.bricks.append([pygame.Rect(x, y, 120, 50), colors[row % len(colors)], True])
        self.particles = []
        self.orbs = []
        self.frame = 0
        self.dead = False

    def update(self, keys=None):
        if self.dead:
            return
        self.frame += 1
        # AI or human paddle
        if keys is None:  # autoplay
            target = self.ball[0] - self.paddle.w // 2
            self.paddle.x += max(-18, min(18, target - self.paddle.x))
        else:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.paddle.x -= 16
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.paddle.x += 16
        self.paddle.x = max(20, min(W - self.paddle.w - 20, self.paddle.x))

        # Ball
        self.ball[0] += self.ball[2]
        self.ball[1] += self.ball[3]
        if self.ball[0] < 20 or self.ball[0] > W - 20:
            self.ball[2] *= -1
        if self.ball[1] < 200:
            self.ball[3] *= -1
        # Paddle hit
        bx, by = self.ball[0], self.ball[1]
        if self.paddle.collidepoint(bx, by + 12) and self.ball[3] > 0:
            self.ball[3] = -abs(self.ball[3]) - 0.5
            self.ball[2] += (bx - self.paddle.centerx) * 0.15
            self.combo = 0

        # Bricks
        hit = False
        for b in self.bricks:
            if b[2] and b[0].collidepoint(bx, by):
                b[2] = False
                self.score += 50 + self.combo * 10
                self.combo += 1
                self.ball[3] *= -1
                self.ball[2] += random.uniform(-2, 2)
                hit = True
                for _ in range(12):
                    self.particles.append([bx, by, random.uniform(-4, 4), random.uniform(-6, 2), b[1], 18])
                if random.random() < 0.25:
                    self.orbs.append([bx, by, 0, 6, NEON_GOLD])
                break
        if not hit and self.ball[1] > H - 40:
            self.lives -= 1
            self.combo = 0
            if self.lives <= 0:
                self.dead = True
            else:
                self.ball = [self.paddle.centerx, self.paddle.top - 40, random.choice([-6, 6]), -11]

        # Particles & orbs
        for p in self.particles:
            p[0] += p[2]; p[1] += p[3]; p[5] -= 1
        self.particles = [p for p in self.particles if p[5] > 0]
        for o in self.orbs:
            o[1] += o[3]
            if self.paddle.collidepoint(o[0], o[1]):
                self.score += 100
                self.orbs.remove(o)
        self.orbs = [o for o in self.orbs if o[1] < H]

        # Speed up slightly
        spd = math.hypot(self.ball[2], self.ball[3])
        if spd < 14 and self.frame % 90 == 0:
            self.ball[2] *= 1.02
            self.ball[3] *= 1.02

    def draw(self, surf):
        surf.fill(BG)
        # Subtle grid
        for i in range(0, W, 60):
            pygame.draw.line(surf, (30, 20, 50), (i, 200), (i, H), 1)
        for i in range(200, H, 60):
            pygame.draw.line(surf, (30, 20, 50), (0, i), (W, i), 1)
        # Bricks
        for rect, col, alive in self.bricks:
            if alive:
                pygame.draw.rect(surf, col, rect, border_radius=8)
                pygame.draw.rect(surf, WHITE, rect, 3, border_radius=8)
        # Paddle
        pygame.draw.rect(surf, PADDLE_C, self.paddle, border_radius=12)
        pygame.draw.rect(surf, WHITE, self.paddle, 4, border_radius=12)
        # Ball
        pygame.draw.circle(surf, NEON_CYAN, (int(self.ball[0]), int(self.ball[1])), 16)
        pygame.draw.circle(surf, WHITE, (int(self.ball[0]), int(self.ball[1])), 16, 3)
        # Particles
        for x, y, _, _, col, life in self.particles:
            pygame.draw.circle(surf, col, (int(x), int(y)), max(2, life // 3))
        # Orbs
        for x, y, _, _, col in self.orbs:
            pygame.draw.circle(surf, col, (int(x), int(y)), 14)
        # UI
        title = self.font_lg.render(TITLE, True, NEON_GOLD)
        surf.blit(title, title.get_rect(center=(W//2, 90)))
        sc = self.font_md.render(f"SCORE {self.score}", True, NEON_CYAN)
        surf.blit(sc, sc.get_rect(center=(W//2, 170)))
        lv = self.font_sm.render(f"LIVES {self.lives}   COMBO x{self.combo}", True, NEON_PINK)
        surf.blit(lv, lv.get_rect(center=(W//2, H - 90)))
        handle = self.font_sm.render(HANDLE, True, WHITE)
        surf.blit(handle, handle.get_rect(center=(W//2, H - 40)))
        if self.dead:
            over = self.font_lg.render("GAME OVER", True, NEON_MAG)
            surf.blit(over, over.get_rect(center=(W//2, H//2)))

    def record(self):
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
            "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS),
            "-i", "-", "-an", "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart",
            OUT
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        frames = FPS * SECS
        for i in range(frames):
            self.update()
            self.draw(self.surf)
            # Convert surface to RGB bytes
            raw = pygame.image.tostring(self.surf, "RGB")
            proc.stdin.write(raw)
            if i % 30 == 0:
                print(f"frame {i}/{frames}")
        proc.stdin.close()
        err = proc.stderr.read().decode()
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1500:]}")
        print("wrote", OUT)
        pygame.quit()

    def play_interactive(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
                    self.reset()
            keys = pygame.key.get_pressed()
            self.update(keys)
            self.draw(self.screen)
            pygame.display.flip()
            clock.tick(FPS)
        pygame.quit()

def main():
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()

if __name__ == "__main__":
    main()
