import pygame
import socket
import json
import math

# =========================================
# INIT
# =========================================
pygame.init()

# =========================================
# FULLSCREEN
# =========================================
info = pygame.display.Info()

WIDTH = info.current_w
HEIGHT = info.current_h

screen = pygame.display.set_mode(
    (WIDTH, HEIGHT),
    pygame.FULLSCREEN
)

pygame.display.set_caption("AGV ROBOT SIMULATOR")

clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 18)
big_font = pygame.font.SysFont("Arial", 30)

# =========================================
# UDP
# =========================================
UDP_IP = "0.0.0.0"
UDP_PORT = 4210

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.setblocking(False)

# =========================================
# COLORS
# =========================================
BG = (8, 10, 15)
GRID = (22, 25, 35)
PANEL = (18, 20, 28)

WHITE = (240,240,240)
GREEN = (0,255,120)
BLUE = (0,170,255)
RED = (255,80,80)
GRAY = (70,70,70)
BLACK_LINE = (15,15,15)

# =========================================
# ROBOT STATE
# =========================================
robot_x = 250
robot_y = 350
robot_yaw = 0

front_distance = 20
back_distance = 30

front_sensor = [0]*8
back_sensor = [0]*8
left_sensor = [0]*8
right_sensor = [0]*8

trail = []

packet_count = 0

# =========================================
# NODE SYSTEM
# =========================================

nodes = {

    # LEFT
    "A": (170,120),
    "B": (170,250),
    "C": (170,350),
    "D": (170,470),
    "E": (170,620),

    # CENTER
    "F": (500,120),
    "G": (500,160),
    "H": (500,260),
    "I": (500,350),
    "J": (500,450),
    "K": (500,540),
    "L": (500,620),

    # RIGHT
    "M": (830,120),
    "N": (830,250),
    "O": (830,350),
    "P": (830,470),
    "Q": (830,620)
}

# =========================================
# ROBOT MODE
# =========================================

robot_mode = "RED"

# =========================================
# ROUTES
# =========================================

red_route = [
    "A","B","C","I","O","P","Q"
]

blue_route = [
    "M","N","O","I","C","D","E"
]

current_route = red_route

current_target_index = 0

robot_speed = 2.0

robot_running = False
robot_pause = False

# =========================================
# GRID
# =========================================

def draw_grid():

    for x in range(0, WIDTH - 400, 40):

        pygame.draw.line(
            screen,
            GRID,
            (x,0),
            (x,HEIGHT)
        )

    for y in range(0, HEIGHT, 40):

        pygame.draw.line(
            screen,
            GRID,
            (0,y),
            (WIDTH - 400,y)
        )

# =========================================
# MAP
# =========================================
def draw_map():

    map_x = 50
    map_y = 50

    map_width = WIDTH - 500
    map_height = HEIGHT - 100

    # =====================================
    # COLORS
    # =====================================
    border_color = (180,120,255)

    line_color = (0,0,0)

    glow_color = (80,80,80)

    node_color = (0,255,255)

    slope_color = (255,105,180)

    green_zone = (60,220,80)

    red_zone = (255,80,80)

    blue_zone = (70,120,255)

    map_fill = (45,45,55)

    # =====================================
    # MAP BACKGROUND
    # =====================================
    pygame.draw.rect(
        screen,
        map_fill,
        (map_x,map_y,map_width,map_height)
    )

    # =====================================
    # BORDER
    # =====================================
    pygame.draw.rect(
        screen,
        border_color,
        (map_x,map_y,map_width,map_height),
        4
    )

    # =====================================
    # SCALE
    # =====================================
    sx = map_width / 1000
    sy = map_height / 700

    # =====================================
    # POSITION HELPER
    # =====================================
    def P(x,y):

        return (
            map_x + int(x*sx),
            map_y + int(y*sy)
        )

    # =====================================
    # LINE FUNCTION
    # =====================================
    def line(a,b):

        pygame.draw.line(
            screen,
            line_color,
            a,
            b,
            6
        )

    # =====================================
    # NODE FUNCTION
    # =====================================
    def node(pos):

        pygame.draw.circle(
            screen,
            node_color,
            pos,
            10
        )

    # =====================================
    # LEFT SIDE
    # =====================================

    # verticals
    line(P(120,80), P(120,620))
    line(P(200,80), P(200,620))

    # horizontals
    line(P(120,180), P(200,180))
    line(P(120,280), P(200,280))
    line(P(120,420), P(200,420))
    line(P(120,520), P(200,520))

    # =====================================
    # RIGHT SIDE
    # =====================================

    # verticals
    line(P(800,80), P(800,620))
    line(P(880,80), P(880,620))

    # horizontals
    line(P(800,180), P(880,180))
    line(P(800,280), P(880,280))
    line(P(800,420), P(880,420))
    line(P(800,520), P(880,520))

    # =====================================
    # CENTER RECTANGLE
    # =====================================

    # left
    line(P(430,80), P(430,620))

    # right
    line(P(570,80), P(570,620))

    # center
    line(P(500,80), P(500,620))

    # top close
    line(P(430,80), P(570,80))

    # bottom close
    line(P(430,620), P(570,620))

    # upper horizontal
    line(P(310,160), P(690,160))

    # upper middle
    line(P(430,260), P(570,260))

    # lower middle
    line(P(430,450), P(570,450))

    # lower horizontal
    line(P(310,540), P(690,540))

    # =====================================
    # MAIN HORIZONTAL CENTER
    # =====================================
    line(
        P(200,350),
        P(800,350)
    )

    # =====================================
    # UPPER CONNECTIONS
    # =====================================
    line(
        P(350,160),
        P(430,160)
    )

    line(
        P(570,160),
        P(650,160)
    )

    # =====================================
    # LOWER CONNECTIONS
    # =====================================
    line(
        P(350,540),
        P(430,540)
    )

    line(
        P(570,540),
        P(650,540)
    )

    # =====================================
    # LEFT NODES
    # =====================================
    left_nodes = [

        (120,80),
        (120,230),
        (120,350),
        (120,470),
        (120,620)
    ]

    # =====================================
    # RIGHT NODES
    # =====================================
    right_nodes = [

        (880,80),
        (880,230),
        (880,350),
        (880,470),
        (880,620)
    ]

    # =====================================
    # CENTER NODES
    # =====================================
    center_nodes = [

        (500,80),
        (500,160),
        (500,260),
        (500,350),
        (500,450),
        (500,540),
        (500,620)
    ]

    # draw left nodes
    for n in left_nodes:

        node(P(n[0], n[1]))

    # draw right nodes
    for n in right_nodes:

        node(P(n[0], n[1]))

    # draw center nodes
    for n in center_nodes:

        node(P(n[0], n[1]))

    # middle nodes
    node(P(200,350))
    node(P(800,350))

    # =====================================
    # START ZONES
    # =====================================

    # RED ZONES
    pygame.draw.rect(
        screen,
        red_zone,
        (
            P(155,30)[0],
            P(150,7)[1],
            int(90*sx),
            int(75*sy)
        ),
        4
    )

    pygame.draw.rect(
        screen,
        red_zone,
        (
            P(155,610)[0],
            P(150,620)[1],
            int(90*sx),
            int(75*sy)
        ),
        4
    )

    # BLUE ZONES
    pygame.draw.rect(
        screen,
        blue_zone,
        (
            P(755,30)[0],
            P(760,7)[1],
            int(90*sx),
            int(75*sy)
        ),
        4
    )

    pygame.draw.rect(
        screen,
        blue_zone,
        (
            P(755,610)[0],
            P(760,620)[1],
            int(90*sx),
            int(75*sy)
        ),
        4
    )

    # =====================================
    # GREEN ZONES
    # =====================================
    green_boxes = [

        # upper left
        (280,130),

        # upper right
        (680,130),

        # lower left
        (280,510),

        # lower right
        (680,510)
    ]

    for gx,gy in green_boxes:

        pygame.draw.rect(
            screen,
            green_zone,
            (
                P(gx,gy)[0],
                P(gx,gy)[1],
                int(40*sx),
                int(60*sy)
            ),
            4
        )

    # =====================================
    # SLOPES (PINK)
    # =====================================
    slopes = [

        # left slope
        (260,300),

        # right slope
        (680,300)
    ]

    for sxp,syp in slopes:

        pygame.draw.rect(
            screen,
            slope_color,
            (
                P(sxp,syp)[0],
                P(sxp,syp)[1],
                int(60*sx),
                int(100*sy)
            ),
            4
        )

    # =====================================
    # NODE LABELS
    # =====================================

    node_positions = {

        # LEFT
        "A": P(120,80),
        "B": P(120,230),
        "C": P(120,350),
        "D": P(120,470),
        "E": P(120,620),

        # CENTER
        "F": P(500,80),
        "G": P(500,160),
        "H": P(500,260),
        "I": P(500,350),
        "J": P(500,450),
        "K": P(500,540),
        "L": P(500,620),

        # RIGHT
        "M": P(880,80),
        "N": P(880,230),
        "O": P(880,350),
        "P": P(880,470),
        "Q": P(880,620),

        # MIDDLE
        "X": P(200,350),
        "Y": P(800,350)
    }

    for name, pos in node_positions.items():

        # NODE
        pygame.draw.circle(
            screen,
            node_color,
            pos,
            10
        )

        # TEXT
        txt = font.render(
            name,
            True,
            (10,10,10)
        )

        txt_rect = txt.get_rect(center=pos)

        screen.blit(txt, txt_rect)


# =========================================
# ROBOT
# =========================================
def draw_robot(x, y, yaw):

    # robot dài hơn
    robot_surface = pygame.Surface((50,65), pygame.SRCALPHA)

    # =====================================
    # SHADOW
    # =====================================
    pygame.draw.rect(
        robot_surface,
        (0,0,0,60),
        (8,10,34,45),
        border_radius=4
    )

    # =====================================
    # MAIN BODY
    # =====================================
    pygame.draw.rect(
        robot_surface,
        (55,60,70),
        (10,10,30,45),
        border_radius=3
    )

    # =====================================
    # TOP PANEL
    # =====================================
    pygame.draw.rect(
        robot_surface,
        (35,40,45),
        (15,16,20,32),
        border_radius=2
    )

    # =====================================
    # MECANUM WHEELS
    # =====================================
    wheel_positions = [

        (3,14),
        (41,14),

        (3,38),
        (41,38)
    ]

    for wx,wy in wheel_positions:

        # wheel body
        pygame.draw.rect(
            robot_surface,
            (85,85,85),
            (wx,wy,6,14),
            border_radius=1
        )

        # mecanum rollers
        for i in range(3):

            pygame.draw.line(
                robot_surface,
                (140,140,140),
                (wx, wy+i*4),
                (wx+6, wy+2+i*4),
                1
            )

    # =====================================
    # MPU6050
    # =====================================
    pygame.draw.circle(
        robot_surface,
        (255,80,80),
        (25,32),
        3
    )

    # =====================================
    # FRONT ARROW
    # =====================================
    pygame.draw.line(
        robot_surface,
        (0,255,255),
        (25,32),
        (25,14),
        2
    )

    pygame.draw.polygon(
        robot_surface,
        (0,255,255),
        [
            (25,10),
            (22,15),
            (28,15)
        ]
    )

    # =====================================
    # STATUS LEDS
    # =====================================
    pygame.draw.circle(
        robot_surface,
        (0,255,120),
        (18,32),
        2
    )

    pygame.draw.circle(
        robot_surface,
        (0,170,255),
        (32,32),
        2
    )

    # =====================================
    # ROTATE
    # =====================================
    rotated = pygame.transform.rotate(
        robot_surface,
        -yaw
    )

    rect = rotated.get_rect(
        center=(x,y)
    )

    screen.blit(rotated, rect)

# =========================================
# SENSOR BAR
# =========================================
def draw_sensor_bar(data, x, y):

    for i,val in enumerate(data):

        color = GREEN if val else GRAY

        pygame.draw.circle(
            screen,
            color,
            (x + i*26, y),
            8
        )

# =========================================
# PANEL
# =========================================
def draw_panel():

    panel_x = WIDTH - 360

    pygame.draw.rect(
        screen,
        PANEL,
        (panel_x,20,340,HEIGHT - 40),
        border_radius=20
    )

    title = big_font.render(
        "AGV ROBOT",
        True,
        WHITE
    )

    screen.blit(title, (panel_x + 30,40))

    sub = font.render(
        "ESP32 SIMULATION",
        True,
        BLUE
    )

    screen.blit(sub, (panel_x + 30,80))

    # status
    pygame.draw.circle(
        screen,
        GREEN,
        (panel_x + 35,125),
        7
    )

    status = font.render(
        "CONNECTED",
        True,
        GREEN
    )

    screen.blit(status, (panel_x + 50,115))

    # info
    info = [

        f"Yaw: {robot_yaw:.1f}°",
        f"Front Distance: {front_distance} cm",
        f"Back Distance: {back_distance} cm",
        f"Packets: {packet_count}"
    ]

    start_y = 180

    for i,text in enumerate(info):

        txt = font.render(
            text,
            True,
            WHITE
        )

        screen.blit(
            txt,
            (panel_x + 30, start_y + i*40)
        )

    # sensor labels
    labels = [

        ("FRONT", front_sensor),
        ("BACK", back_sensor),
        ("LEFT", left_sensor),
        ("RIGHT", right_sensor)
    ]

    sy = 380

    for i,(name,data) in enumerate(labels):

        txt = font.render(
            name,
            True,
            WHITE
        )

        screen.blit(
            txt,
            (panel_x + 30, sy + i*70)
        )

        draw_sensor_bar(
            data,
            panel_x + 40,
            sy + 30 + i*70
        )
     
    # =====================================
    # BUTTONS
    # =====================================

    button_y = HEIGHT - 260

    buttons = [

        ("START", GREEN),
        ("PAUSE", (255,200,0)),
        ("STOP", RED)
    ]

    for i,(name,color) in enumerate(buttons):

        pygame.draw.rect(
            screen,
            color,
            (
                panel_x + 30,
                button_y + i*60,
                120,
                40
            ),
            border_radius=10
        )

        txt = font.render(
            name,
            True,
            BLACK_LINE
        )

        screen.blit(
            txt,
            (
                panel_x + 60,
                button_y + 12 + i*60
            )
        )

    # =====================================
    # MODE
    # =====================================

    mode_text = font.render(
        f"MODE: {robot_mode}",
        True,
        WHITE
    )

    screen.blit(
        mode_text,
        (panel_x + 180, HEIGHT - 240)
    )

    # RED MODE BUTTON
    pygame.draw.rect(
        screen,
        (255,80,80),
        (panel_x + 180, HEIGHT - 200, 120, 40),
        border_radius=10
    )

    txt = font.render(
        "RED FIELD",
        True,
        WHITE
    )

    screen.blit(
        txt,
        (panel_x + 195, HEIGHT - 188)
    )

    # BLUE MODE BUTTON
    pygame.draw.rect(
        screen,
        (70,120,255),
        (panel_x + 180, HEIGHT - 145, 120, 40),
        border_radius=10
    )

    txt = font.render(
        "BLUE FIELD",
        True,
        WHITE
    )

    screen.blit(
        txt,
        (panel_x + 190, HEIGHT - 133)
    )

    # =====================================
    # CURRENT TARGET
    # =====================================

    if current_target_index < len(current_route):

        target = current_route[current_target_index]

        txt = font.render(
            f"TARGET NODE: {target}",
            True,
            GREEN
        )

        screen.blit(
            txt,
            (panel_x + 30, HEIGHT - 60)
        )

# =========================================
# AUTO NAVIGATION
# =========================================
def auto_navigation():

    global robot_x
    global robot_y
    global robot_yaw
    global current_target_index

    if not robot_running:
        return

    if robot_pause:
        return

    if current_target_index >= len(current_route):
        return

    target_name = current_route[current_target_index]

    tx, ty = nodes[target_name]

    dx = tx - robot_x
    dy = ty - robot_y

    distance = math.sqrt(dx*dx + dy*dy)

    # tới node
    if distance < 5:

        current_target_index += 1
        return

    dx /= distance
    dy /= distance

    robot_x += dx * robot_speed
    robot_y += dy * robot_speed

    robot_yaw = math.degrees(
        math.atan2(dx, -dy)
    )

# =========================================
# MAIN LOOP
# =========================================
running = True

while running:

    clock.tick(60)

    # =====================================
    # RECEIVE UDP
    # =====================================
    try:

        data, addr = sock.recvfrom(4096)

        msg = json.loads(data.decode())

        robot_x = msg["x"]
        robot_y = msg["y"]
        robot_yaw = msg["yaw"]

        front_distance = msg["front_distance"]
        back_distance = msg["back_distance"]

        front_sensor = msg["front"]
        back_sensor = msg["back"]
        left_sensor = msg["left"]
        right_sensor = msg["right"]

        trail.append((robot_x, robot_y))

        if len(trail) > 1000:
            trail.pop(0)

        packet_count += 1

    except:
        pass

    # =====================================
    # EVENTS
    # =====================================
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                running = False

   # =====================================
   # MOUSE
   # =====================================
    if event.type == pygame.MOUSEBUTTONDOWN:

       mx,my = pygame.mouse.get_pos()

       panel_x = WIDTH - 360

       # START
       if panel_x + 30 <= mx <= panel_x + 150:

           if HEIGHT - 260 <= my <= HEIGHT - 220:

               robot_running = True
               robot_pause = False

       # PAUSE
       if panel_x + 30 <= mx <= panel_x + 150:

           if HEIGHT - 200 <= my <= HEIGHT - 160:

               robot_pause = not robot_pause

       # STOP
       if panel_x + 30 <= mx <= panel_x + 150:

           if HEIGHT - 140 <= my <= HEIGHT - 100:

               robot_running = False
               current_target_index = 0

               if robot_mode == "RED":

                   robot_x, robot_y = nodes["A"]

               else:

                   robot_x, robot_y = nodes["M"]

       # RED MODE
       if panel_x + 180 <= mx <= panel_x + 300:

           if HEIGHT - 200 <= my <= HEIGHT - 160:

               robot_mode = "RED"

               current_route = red_route

               robot_x, robot_y = nodes["A"]

               current_target_index = 0

       # BLUE MODE
       if panel_x + 180 <= mx <= panel_x + 300:

           if HEIGHT - 145 <= my <= HEIGHT - 105:

               robot_mode = "BLUE"

               current_route = blue_route

               robot_x, robot_y = nodes["M"]

               current_target_index = 0
    # =====================================
    # AUTO NAVIGATION
    # =====================================
    auto_navigation()

    # =====================================
    # DRAW
    # =====================================
    screen.fill(BG)

    draw_grid()

    draw_map()

    # trail
    for p in trail:

        pygame.draw.circle(
            screen,
            GREEN,
            p,
            2
        )

    # robot
    draw_robot(
        robot_x,
        robot_y,
        robot_yaw
    )

    # right panel
    draw_panel()

    pygame.display.flip()

pygame.quit()