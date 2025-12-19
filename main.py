import sys
import random
import asyncio
from game_objects import Ball, Tube, COLORS, COLOR_KEYS

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 1000, 700
BACKGROUND_COLOR = (18, 18, 18)  # Deep Dark Grey
HEADER_HEIGHT = 100

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Ball Sort Puzzle")
font = pygame.font.SysFont("Segoe UI", 36, bold=True)

# Game State
# Additional imports for particles
from game_objects import Particle

# Game State
tubes = []
particles = []
selected_tube = None
is_won = False

def create_level(num_tubes=5):
    global tubes, is_won, particles
    is_won = False
    tubes = []
    particles = []
    
    # Simple logic: N tubes total, N-2 are full, 2 are empty.
    # Each full tube has 4 balls.
    # Total balls = (num_tubes - 2) * 4
    
    num_full_tubes = num_tubes - 2
    colors_needed = num_full_tubes
    
    # Select colors
    level_colors = COLOR_KEYS[:colors_needed]
    
    # Create pool of balls
    ball_pool = []
    for c_name in level_colors:
        rgb = COLORS[c_name]
        for _ in range(4): # 4 balls per color
            ball_pool.append((c_name, rgb))
            
    # Shuffle
    random.shuffle(ball_pool)
    
    # Calculate Layout
    calculate_layout(num_tubes)
    
    # Fill tubes
    ball_idx = 0
    for i in range(num_full_tubes):
        for _ in range(4):
            c_name, rgb = ball_pool[ball_idx]
            # Init with dummy vals, update_ball_positions fixes it
            b = Ball(c_name, rgb[0], rgb[1], rgb[2], 10)
            tubes[i].balls.append(b)
            ball_idx += 1
            
    update_ball_positions()

def calculate_layout(num_tubes):
    global tubes
    w, h = screen.get_width(), screen.get_height()
    
    # --- STRICT LAYOUT CALCULATION ---
    # Goal: 4 balls fit PERFECTLY in height.
    # Tube Width: Fixed or responsive? Responsive but capped.
    
    # Responsive width
    max_tube_width = 100
    min_gap = 20
    
    # Total available width for tubes
    content_width_percentage = 0.8
    available_w = w * content_width_percentage
    
    # (N * tube_w) + ((N-1) * gap) = available
    # Let gap = tube_w * 0.4
    # (N + (N-1)*0.4) * tube_w = available
    
    factor = num_tubes + (num_tubes - 1) * 0.4
    tube_width = available_w / factor
    tube_width = min(max_tube_width, tube_width)
    
    tube_gap = tube_width * 0.4
    
    # Calculate Heights based on Ball Radius
    # ball diameter = tube_width - padding
    padding = 16 
    ball_diameter = tube_width - padding
    ball_radius = ball_diameter / 2
    
    # Tube Height needs to hold 4 balls + some top clearance
    # height = 4 * diameter + top_padding + bottom_padding
    tube_height = (ball_diameter * 4) + ball_radius # Extra space at top
    
    start_x = (w - (num_tubes * tube_width + (num_tubes - 1) * tube_gap)) // 2
    start_y = (h - tube_height) // 2 + 40 # Offset for title
    
    # Re-create or Update Tubes
    if not tubes:
        for i in range(num_tubes):
            x = start_x + i * (tube_width + tube_gap)
            t = Tube(x, start_y, tube_width, tube_height)
            tubes.append(t)
    else:
        # Just update rects if tubes exist
         for i, t in enumerate(tubes):
             t.rect.x = start_x + i * (tube_width + tube_gap)
             t.rect.y = start_y
             t.rect.width = tube_width
             t.rect.height = tube_height

    # Update global ball radius
    for t in tubes:
        for b in t.balls:
            b.radius = int(ball_radius)
            
    # Save the strictly calculated ball diameter for positioning
    calculate_layout.ball_diameter = ball_diameter
    calculate_layout.padding = padding

def update_ball_positions():
    # Use calculated diameter from layout
    if not hasattr(calculate_layout, 'ball_diameter'):
        return # Not ready
        
    ball_diameter = calculate_layout.ball_diameter
    padding = calculate_layout.padding
    
    for t in tubes:
        # Balls stack from bottom
        # Bottom Y = t.rect.bottom - (padding/2) - radius
        # But we can just use diameter stacking
        
        base_y = t.rect.bottom - (padding / 2) - (ball_diameter / 2)
        
        for i, b in enumerate(t.balls):
            target_x = t.rect.centerx
            target_y = base_y - (i * ball_diameter)
            
            # Lift if selected
            if t == selected_tube and i == len(t.balls) - 1:
                target_y = t.rect.top - 50
                
            b.set_target(target_x, target_y)

def check_win():
    global is_won
    # Check if all tubes are either empty or full of same color
    for t in tubes:
        if not t.balls:
            continue
        if len(t.balls) != 4:
            return False
        first_color = t.balls[0].color_name
        for b in t.balls:
            if b.color_name != first_color:
                return False
    is_won = True
    trigger_win_effects()

def trigger_win_effects():
    # Spawn confetti
    for _ in range(100):
        # Spawn from left and right edges
        x = random.choice([0, WIDTH])
        y = random.randint(HEIGHT//2, HEIGHT)
        p = Particle(x, y)
        # shoot towards center
        p.vx = random.uniform(5, 15) if x == 0 else random.uniform(-15, -5)
        p.vy = random.uniform(-15, -5)
        particles.append(p)

def handle_click(pos):
    global selected_tube
    
    clicked_tube = None
    for t in tubes:
        if t.rect.collidepoint(pos):
            clicked_tube = t
            break
         # Floating area check
        if selected_tube == t and t.balls:
             # loose hit box
             if abs(pos[0] - t.rect.centerx) < t.rect.width and pos[1] < t.rect.top + 100:
                 clicked_tube = t

    if not clicked_tube:
        selected_tube = None
        update_ball_positions()
        return

    if selected_tube is None:
        if clicked_tube.balls:
            selected_tube = clicked_tube
            update_ball_positions()
    else:
        if clicked_tube == selected_tube:
            selected_tube = None
            update_ball_positions()
        else:
            ball_to_move = selected_tube.get_top_ball()
            if clicked_tube.can_receive(ball_to_move):
                selected_tube.balls.pop()
                clicked_tube.balls.append(ball_to_move)
                selected_tube = None
                update_ball_positions()
                check_win()
            else:
                selected_tube = None
                update_ball_positions()

# Helper for Cyber Gradient
def draw_cyber_background(surface):
    w, h = surface.get_size()
    
    # 1. Deep Space Black
    surface.fill((5, 5, 10))
    
    # 2. Retro Grid (Perspective)
    # Horizontal lines get closer together towards horizon (vanish point)
    # Vertical lines fan out? Or just simple floor grid.
    
    horizon_y = h * 0.4
    
    grid_color = (60, 20, 80) # Dark Purple
    
    # Floor Grid
    # Draw vertical lines fanning out
    center_x = w // 2
    num_v_lines = 12
    for i in range(num_v_lines + 1):
        offset = (i - num_v_lines/2) * (w * 1.5 / num_v_lines)
        # bottom point
        p1 = (center_x + offset, h)
        # horizon point
        p2 = (center_x + offset * 0.1, horizon_y)
        pygame.draw.line(surface, grid_color, p1, p2, 2)
        
    # Horizontal lines - exponential spacing
    num_h_lines = 10
    total_dist = h - horizon_y
    for i in range(num_h_lines):
        # Power function for perspective spacing
        ratio = (i / num_h_lines) ** 2
        y = horizon_y + ratio * total_dist
        pygame.draw.line(surface, grid_color, (0, y), (w, y), 2)
        
    # Top Gradient (Stars or just fade)
    # Simple star field
    if not hasattr(draw_cyber_background, "stars"):
         draw_cyber_background.stars = [(random.randint(0, w), random.randint(0, int(horizon_y))) for _ in range(30)]
    
    for sx, sy in draw_cyber_background.stars:
        pygame.draw.circle(surface, (200, 200, 255), (sx, sy), 1)

def draw_win_screen(surface):
    # Dim background
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))
    
    # Text - Digital Glitch Style
    # Main 'SYSTEM ACCESSED' or 'LEVEL CLEARED'
    
    # Neon Green Text
    win_font = pygame.font.SysFont("consolas", 60, bold=True)
    text = win_font.render(">> SYSTEM HACKED", True, (0, 255, 0))
    
    # Glitch Shadow
    shadow = win_font.render(">> SYSTEM HACKED", True, (255, 0, 255))
    surface.blit(shadow, (WIDTH//2 - text.get_width()//2 + 4, HEIGHT//2 - 50 + 2))
    surface.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 50))
    
    sub_font = pygame.font.SysFont("consolas", 30)
    sub = sub_font.render("[PRESS R TO REBOOT]", True, (0, 255, 255))
    surface.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 20))


async def main():
    global screen, is_won
    clock = pygame.time.Clock()
    running = True

    # Font setup
    global font
    font = pygame.font.SysFont("consolas", 36, bold=True)

    create_level()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                calculate_layout(len(tubes))
                update_ball_positions()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if not is_won:
                    handle_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    create_level()

        # Update
        for t in tubes:
            for b in t.balls:
                b.update()
        
        if is_won:
            for p in particles:
                p.update() 
            if len(particles) > 0 and particles[0].life <= 0:
                 particles.pop(0)

        # Draw
        draw_cyber_background(screen)
        
        # Title
        title_text = ">> BALL_SORT.EXE"
        title_surf = font.render(title_text, True, (0, 255, 255))
        title_shadow = font.render(title_text, True, (255, 0, 255))
        
        title_x = screen.get_width()//2 - title_surf.get_width()//2
        screen.blit(title_shadow, (title_x + 3, 30))
        screen.blit(title_surf, (title_x, 30))

        # Layer 1: Tube Backs
        for t in tubes:
            t.draw_back(screen)

        # Layer 2: Balls
        for t in tubes:
            is_selected_tube = (t == selected_tube)
            for i, b in enumerate(t.balls):
                # Pass selected state to top ball if tube is selected
                ball_selected = is_selected_tube and (i == len(t.balls) - 1)
                b.draw(screen, is_selected=ball_selected)

        # Layer 3: Tube Fronts (Laser Frames)
        for t in tubes:
            t.draw_front(screen)
            
        # Layer 4: Win UI & Particles
        if is_won:
            draw_win_screen(screen)
            for p in particles:
                p.draw(screen)

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    asyncio.run(main())
