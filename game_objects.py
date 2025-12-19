import pygame
import random
import math

# Colors - NEON PALETTE
COLORS = {
    'NEON_RED':    (255, 0, 85),
    'NEON_GREEN':  (57, 255, 20),
    'NEON_BLUE':   (0, 255, 255),  # Cyan
    'NEON_YELLOW': (255, 255, 0),
    'NEON_PURPLE': (188, 19, 254),
    'NEON_ORANGE': (255, 131, 0),
    'NEON_PINK':   (255, 0, 255),
}

COLOR_KEYS = list(COLORS.keys())

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.color = random.choice(list(COLORS.values()))
        # Digital spark physics
        speed = random.uniform(4, 12)
        angle = random.uniform(0, math.pi * 2)
        
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        
        self.size = random.uniform(2, 5)
        self.life = 255 

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 8 # Fast fizzle
        
        # No gravity, just direction inertia (Data bits)
        self.vx *= 0.95
        self.vy *= 0.95

    def draw(self, surface):
        if self.life > 0:
            # Draw square pixels
            s = pygame.Surface((int(self.size), int(self.size)))
            s.fill(self.color)
            s.set_alpha(self.life)
            surface.blit(s, (self.x, self.y))

class Ball:
    def __init__(self, color_name, r, g, b, radius):
        self.color_name = color_name
        self.base_color = (r, g, b)
        self.radius = radius
        # Positions
        self.x = 0
        self.y = 0
        self.target_x = 0
        self.target_y = 0
        
    def set_position(self, x, y):
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y

    def set_target(self, x, y):
        self.target_x = x
        self.target_y = y
        
    def update(self):
        # Easing
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        
        speed_factor = 0.25 # Faster, digital snap
        if abs(dx) < 0.5: self.x = self.target_x
        else: self.x += dx * speed_factor
            
        if abs(dy) < 0.5: self.y = self.target_y
        else: self.y += dy * speed_factor

    def draw(self, surface, is_selected=False):
        x, y = int(self.x), int(self.y)
        r = int(self.radius)
        if r <= 0: return 

        # PLASMA ORB LOOK
        
        # 1. Outer Glow (The Aura)
        # Large, faint, colored
        aura_r = r * 1.4
        aura_surf = pygame.Surface((aura_r*2, aura_r*2), pygame.SRCALPHA)
        pygame.draw.circle(aura_surf, (*self.base_color, 60), (aura_r, aura_r), aura_r)
        surface.blit(aura_surf, (x - aura_r, y - aura_r), special_flags=pygame.BLEND_RGBA_ADD)
        
        # 2. Middle Core (The Color)
        pygame.draw.circle(surface, self.base_color, (x, y), r)
        
        # 3. Inner White Hot Core (The Energy Source)
        # Small white center
        pygame.draw.circle(surface, (255, 255, 255), (x, y), r * 0.4)
        
        # 4. Selection Ring
        if is_selected:
            # Drawing a spinning bracket or ring?
            # Simple bright white ring
            pygame.draw.circle(surface, (255, 255, 255), (x, y), r * 1.1, width=2)


class Tube:
    def __init__(self, x, y, width, height, capacity=4):
        self.rect = pygame.Rect(x, y, width, height)
        self.balls = []
        self.capacity = capacity
        self.selected = False
        self.hovered = False
        self.pulse = 0
        
    def draw_back(self, surface):
        """Draws the containment field background"""
        # Faint scanlines
        s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        s.fill((0, 20, 40, 100)) # Dark blue-black bg
        
        # Draw scanlines
        for i in range(0, self.rect.height, 4):
            pygame.draw.line(s, (0, 255, 255, 30), (0, i), (self.rect.width, i))
            
        surface.blit(s, (self.rect.x, self.rect.y))

    def draw_front(self, surface):
        """Draws the laser borders"""
        
        # Laser Color
        color = (0, 255, 255) # Cyan default
        if self.selected:
            color = (255, 0, 255) # Magenta select
            
        # Outer Glow (Bloom)
        # Draw 3 rects with decreasing alpha/increasing size
        for i in range(3):
            alpha = 100 - (i * 30)
            offset = i * 2
            r = self.rect.inflate(offset, offset)
            # Use separate method to draw alpha rect border?
            # Pygame doesn't support alpha on draw.rect direct, need surface
            # But line drawing works? No, draw.line doesn't support alpha on main surf if no per-pixel alpha.
            # Assume main surf has no alpha channel usually.
            
            # Simple opaque lines look neon if bright enough against dark bg
            # Let's simple draw thick bright lines
            pass

        # For valid bloom, stick to simple thick lines for performance
        box_thickness = 2
        if self.selected:
             box_thickness = 4
             
        # Main Frame
        pygame.draw.rect(surface, color, self.rect, width=box_thickness)
        
        # Corner Accents (Cyberpunk markers)
        corner_len = 10
        # draw L shapes at corners
        # TopLeft
        pygame.draw.line(surface, (255, 255, 255), self.rect.topleft, (self.rect.left + corner_len, self.rect.top), 3)
        pygame.draw.line(surface, (255, 255, 255), self.rect.topleft, (self.rect.left, self.rect.top + corner_len), 3)
        
        # BottomRight
        pygame.draw.line(surface, (255, 255, 255), self.rect.bottomright, (self.rect.right - corner_len, self.rect.bottom), 3)
        pygame.draw.line(surface, (255, 255, 255), self.rect.bottomright, (self.rect.right, self.rect.bottom - corner_len), 3)


    def is_full(self):
        return len(self.balls) >= self.capacity

    def get_top_ball(self):
        if self.balls:
            return self.balls[-1]
        return None
    
    def can_receive(self, ball):
        if self.is_full():
            return False
        if not self.balls:
            return True
        return self.balls[-1].color_name == ball.color_name
