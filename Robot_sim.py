import pygame
import json
import math

# Bộ lọc thử nghiệm import thư viện Serial hỗ trợ truyền nhận dữ liệu qua cáp USB
try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    print("[WARNING] Thư viện 'pyserial' chưa được cài đặt trên máy tính.")
    print("Vui lòng chạy lệnh: 'pip install pyserial' để kích hoạt telemetry qua cáp USB.")

# =========================================
# KHỞI TẠO HỆ THỐNG ĐỒ HỌA PYGAME
# =========================================
pygame.init()

# =========================================
# CẤU HÌNH ĐỒ HỌA TOÀN MÀN HÌNH (FULLSCREEN)
# =========================================
info = pygame.display.Info()
WIDTH = info.current_w
HEIGHT = info.current_h

# ĐỊNH NGHĨA BIẾN TOÀN CỤC: Tọa độ Y của nhóm nút bấm chính để tránh lỗi NameError
BUTTON_Y = HEIGHT - 180 

screen = pygame.display.set_mode(
    (WIDTH, HEIGHT),
    pygame.FULLSCREEN
)

pygame.display.set_caption("AGV ROBOT TELEMETRY & SIMULATOR")
clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 18)
big_font = pygame.font.SysFont("Arial", 30)
tab_font = pygame.font.SysFont("Arial", 15, bold=True)

# =========================================
# KẾT NỐI SERIAL RECEIVER (TỰ ĐỘNG DÒ HOẶC CHỈ ĐỊNH)
# =========================================
# Đặt thành "AUTO" để tự quét, hoặc đổi thành cổng COM cứng (Ví dụ: "COM3", "COM4")
SERIAL_PORT = "/dev/cu.usbserial-0001" 

ser = None
connected_status = False
last_packet_time = 0

def find_and_connect_serial():
    global ser, connected_status
    if not SERIAL_AVAILABLE:
        return
    if ser is not None and ser.is_open:
        return
    
    # 1. Thử kết nối cổng COM chỉ định trước
    if SERIAL_PORT != "AUTO":
        try:
            ser = serial.Serial(SERIAL_PORT, 115200, timeout=0.05)
            print(f"[SERIAL] Kết nối thành công tới cổng chỉ định: {SERIAL_PORT}")
            connected_status = True
            return
        except Exception as e:
            print(f"[WARNING] Không thể mở cổng chỉ định {SERIAL_PORT}: {e}. Đang tự động quét tìm cổng thay thế...")
    
    # 2. Quét tự động cổng COM khả dụng (Fallback Mode)
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        device_lower = p.device.lower()
        desc_lower = p.description.lower()
        if "usb" in device_lower or "ch34" in desc_lower or "cp21" in desc_lower or "ftdi" in desc_lower or "com" in device_lower or "usb" in desc_lower:
            try:
                ser = serial.Serial(p.device, 115200, timeout=0.05)
                print(f"[SERIAL] Tự động quét và kết nối thành công tới cổng: {p.device}")
                connected_status = True
                return
            except Exception as e:
                pass

if SERIAL_AVAILABLE:
    find_and_connect_serial()

# =========================================
# MÀU SẮC GIAO DIỆN (UI COLOR SCHEME)
# =========================================
BG = (8, 10, 15)
GRID = (22, 25, 35)
PANEL = (18, 20, 28)
TAB_ACTIVE = (0, 170, 255)
TAB_INACTIVE = (35, 38, 50)

WHITE = (240, 240, 240)
GREEN = (0, 255, 120)
BLUE = (0, 170, 255)
RED = (255, 80, 80)
ORANGE = (255, 180, 0)
GRAY = (50, 52, 60)
BLACK_LINE = (15, 15, 15)

# =========================================
# TRẠNG THÁI PHÂN TRANG (TAB SYSTEM)
# =========================================
current_tab = "CONTROL" # Mặc định hiển thị trang CONTROL chứa các nút bấm gốc

# =========================================
# CẤU HÌNH TỈ LỆ VẬT LÝ THỰC TẾ (SCALE SYSTEM)
# =========================================
MAP_REAL_SIZE_MM = 8000  # Kích thước thực tế của sân đấu: 8000x8000mm (8m x 8m)
ROBOT_REAL_SIZE_MM = 500  # Kích thước thực tế của Robot: 500x500mm (0.5m x 0.5m)

# Khung giới hạn hiển thị sân đấu (Dạng hình vuông để tương thích tỉ lệ thực tế)
MAP_WIDTH = min(WIDTH - 420, HEIGHT - 100)
MAP_HEIGHT = MAP_WIDTH
MAP_X = 50
MAP_Y = 50

# Hệ số quy đổi từ mm sang pixels hiển thị
SCALE_MM_TO_PX = MAP_WIDTH / MAP_REAL_SIZE_MM

# =========================================
# HỆ THỐNG TOẠ ĐỘ NODE BẢN ĐỒ GỐC (ẢO) VÀ QUY ĐỔI SANG MM THỰC TẾ
# =========================================
nodes = {
    "A": (170, 120),
    "B": (170, 250),
    "C": (170, 350),
    "D": (170, 470),
    "E": (170, 620),
    "F": (500, 120),
    "G": (500, 160),
    "H": (500, 260),
    "I": (500, 350),
    "J": (500, 450),
    "K": (500, 540),
    "L": (500, 620),
    "M": (830, 120),
    "N": (830, 250),
    "O": (830, 350),
    "P": (830, 470),
    "Q": (830, 620)
}

# Tạo danh sách toạ độ node thực tế (đơn vị mm) để tính toán mô phỏng vật lý chính xác
nodes_mm = {}
for name, (vx, vy) in nodes.items():
    # Co dãn toạ độ ảo (1000x700) sang đầy đủ phạm vi thực tế (8000x8000mm)
    nodes_mm[name] = (vx * 8.0, vy * (8000.0 / 700.0))

# =========================================
# TRẠNG THÁI ROBOT (LƯU TRỮ HOÀN TOÀN TRÊN KHÔNG GIAN MM THỰC TẾ)
# =========================================
robot_x = nodes_mm["A"][0] # Tọa độ X của robot (mm)
robot_y = nodes_mm["A"][1] # Tọa độ Y của robot (mm)
robot_yaw = 0.0
robot_roll = 0.0
robot_pitch = 0.0

# Dữ liệu từ 4 laser VL53L0X (đơn vị: cm nhận từ ESP32)
front_distance = 0
back_distance = 0
left_distance = 0
right_distance = 0

# Nhị phân trạng thái 32 mắt dò line
front_sensor = [0] * 8
back_sensor  = [0] * 8
left_sensor  = [0] * 8
right_sensor = [0] * 8

# Vận tốc thực tế của bánh xe (RPM) và Xung Encoders
motor_speeds = [0.0] * 4
motor_encs = [0] * 4

# Sức khỏe kết nối phần cứng chính từ ESP32 Master
health_tca  = False
health_mpu  = False
health_mega = False
health_line = False

# Sức khỏe kết nối riêng biệt của 4 cảm biến Laser ToF
health_vl53 = [False, False, False, False] # Mảng trạng thái kết nối [Front, Back, Left, Right]

# Biến bổ trợ thống kê
packet_count = 0
trail = []

robot_mode = "RED"
red_route = ["A", "B", "C", "I", "O", "P", "Q"]
blue_route = ["M", "N", "O", "I", "C", "D", "E"]
current_route = red_route
current_target_index = 0
robot_speed = 35.0 # Vận tốc chạy mô phỏng (mm/khung hình) ~ 2.1 m/s ở 60 FPS
robot_running = False
robot_pause = False

# =========================================
# VẼ LƯỚI KHÔNG GIAN (GRID MAP)
# =========================================
def draw_grid():
    for x in range(0, WIDTH - 400, 40):
        pygame.draw.line(screen, GRID, (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, 40):
        pygame.draw.line(screen, GRID, (0, y), (WIDTH - 400, y))

# =========================================
# VẼ SƠ ĐỒ SÂN ĐẤU ROBOCON GỐC VÀ CO GIÃN TỈ LỆ
# =========================================
def draw_map():
    border_color = (180, 120, 255)
    line_color = (0, 0, 0)
    node_color = (0, 255, 255)
    slope_color = (255, 105, 180)
    green_zone = (60, 220, 80)
    red_zone = (255, 80, 80)
    blue_zone = (70, 120, 255)
    map_fill = (45, 45, 55)

    # Vẽ nền sân thi đấu hình vuông đúng chuẩn 8x8m
    pygame.draw.rect(screen, map_fill, (MAP_X, MAP_Y, MAP_WIDTH, MAP_HEIGHT))
    pygame.draw.rect(screen, border_color, (MAP_X, MAP_Y, MAP_WIDTH, MAP_HEIGHT), 4)

    # Hàm P: Ánh xạ chuyển đổi toạ độ vẽ ảo (1000x700) sang màn hình Pygame (pixel) đúng tỉ lệ 8000x8000mm
    def P(x_v, y_v):
        x_mm = x_v * 8.0
        y_mm = y_v * (8000.0 / 700.0)
        return (MAP_X + int(x_mm * SCALE_MM_TO_PX), MAP_Y + int(y_mm * SCALE_MM_TO_PX))

    # Định nghĩa hàm helper vẽ đường thẳng cục bộ để sửa lỗi NameError
    def line(start_pos, end_pos):
        pygame.draw.line(screen, line_color, start_pos, end_pos, 6)

    # Cánh bên trái
    line(P(120, 80), P(120, 620))
    line(P(200, 80), P(200, 620))
    line(P(120, 180), P(200, 180))
    line(P(120, 280), P(200, 280))
    line(P(120, 420), P(200, 420))
    line(P(120, 520), P(200, 520))

    # Cánh bên phải
    line(P(800, 80), P(800, 620))
    line(P(880, 80), P(880, 620))
    line(P(800, 180), P(880, 180))
    line(P(800, 280), P(880, 280))
    line(P(800, 420), P(880, 420))
    line(P(800, 520), P(880, 520))

    # Khu vực trung tâm
    line(P(430, 80), P(430, 620))
    line(P(570, 80), P(570, 620))
    line(P(500, 80), P(500, 620))
    line(P(430, 80), P(570, 80))
    line(P(430, 620), P(570, 620))
    line(P(310, 160), P(690, 160))
    line(P(430, 260), P(570, 260))
    line(P(430, 450), P(570, 450))
    line(P(310, 540), P(690, 540))

    line(P(200, 350), P(800, 350))
    line(P(350, 160), P(430, 160))
    line(P(570, 160), P(650, 160))
    line(P(350, 540), P(430, 540))
    line(P(570, 540), P(650, 540))

    # Khung các vùng xuất phát & Khu vực đặc biệt
    pygame.draw.rect(screen, red_zone, (P(155, 30)[0], P(150, 7)[1], int(90 * 8 * SCALE_MM_TO_PX), int(75 * (8000/700) * SCALE_MM_TO_PX)), 4)
    pygame.draw.rect(screen, red_zone, (P(155, 610)[0], P(150, 620)[1], int(90 * 8 * SCALE_MM_TO_PX), int(75 * (8000/700) * SCALE_MM_TO_PX)), 4)
    pygame.draw.rect(screen, blue_zone, (P(755, 30)[0], P(760, 7)[1], int(90 * 8 * SCALE_MM_TO_PX), int(75 * (8000/700) * SCALE_MM_TO_PX)), 4)
    pygame.draw.rect(screen, blue_zone, (P(755, 610)[0], P(760, 620)[1], int(90 * 8 * SCALE_MM_TO_PX), int(75 * (8000/700) * SCALE_MM_TO_PX)), 4)

    for gx, gy in [(280, 130), (680, 130), (280, 510), (680, 510)]:
        pygame.draw.rect(screen, green_zone, (P(gx, gy)[0], P(gx, gy)[1], int(40 * 8 * SCALE_MM_TO_PX), int(60 * (8000/700) * SCALE_MM_TO_PX)), 4)

    for sxp, syp in [(260, 300), (680, 300)]:
        pygame.draw.rect(screen, slope_color, (P(sxp, syp)[0], P(sxp, syp)[1], int(60 * 8 * SCALE_MM_TO_PX), int(100 * (8000/700) * SCALE_MM_TO_PX)), 4)

    # Vẽ và dán nhãn các Nodes
    for name, pos in nodes_mm.items():
        scr_pos = (MAP_X + int(pos[0] * SCALE_MM_TO_PX), MAP_Y + int(pos[1] * SCALE_MM_TO_PX))
        pygame.draw.circle(screen, node_color, scr_pos, 10)
        txt = font.render(name, True, (10, 10, 10))
        txt_rect = txt.get_rect(center=scr_pos)
        screen.blit(txt, txt_rect)

# =========================================
# VẼ ROBOT VÀ CÁC TIA LASER KHỎANG CÁCH CHUẨN XÁC VẬT LÝ
# =========================================
def draw_robot(x, y, yaw):
    # Tính kích thước pixels hiển thị của Robot dựa trên kích thước thật 500x500mm
    robot_size_px = max(24, int(ROBOT_REAL_SIZE_MM * SCALE_MM_TO_PX))
    robot_surface = pygame.Surface((robot_size_px * 2, robot_size_px * 2), pygame.SRCALPHA)
    
    # Quy đổi tọa độ của robot sang pixels
    scr_x = MAP_X + int(x * SCALE_MM_TO_PX)
    scr_y = MAP_Y + int(y * SCALE_MM_TO_PX)

    # Thân robot (Sát với tỉ lệ thực tế)
    center_pt = robot_size_px
    body_w = int(robot_size_px * 0.7)
    body_h = int(robot_size_px * 0.9)
    
    # Thân chính (Chassis)
    pygame.draw.rect(robot_surface, (55, 60, 70), (center_pt - body_w//2, center_pt - body_h//2, body_w, body_h), border_radius=int(body_w * 0.15))
    pygame.draw.rect(robot_surface, BLUE, (center_pt - body_w//2, center_pt - body_h//2, body_w, body_h), 2, border_radius=int(body_w * 0.15))
    
    # Khoang vi điều khiển trung tâm
    pygame.draw.rect(robot_surface, (30, 32, 40), (center_pt - body_w//3, center_pt - body_h//4, (body_w*2)//3, body_h//2), border_radius=4)
    
    # Bánh xe Mecanum (4 bánh)
    wheel_w = max(4, int(robot_size_px * 0.15))
    wheel_h = max(8, int(robot_size_px * 0.35))
    
    wheel_offsets = [
        (center_pt - body_w//2 - wheel_w//2, center_pt - body_h//2),
        (center_pt + body_w//2 - wheel_w//2, center_pt - body_h//2),
        (center_pt - body_w//2 - wheel_w//2, center_pt + body_h//2 - wheel_h),
        (center_pt + body_w//2 - wheel_w//2, center_pt + body_h//2 - wheel_h)
    ]
    for wx, wy in wheel_offsets:
        pygame.draw.rect(robot_surface, (120, 120, 120), (wx, wy, wheel_w, wheel_h), border_radius=2)
        pygame.draw.rect(robot_surface, (40, 40, 40), (wx, wy, wheel_w, wheel_h), 1, border_radius=2)

    # Chỉ thị chiều mũi tên và cảm biến la bàn
    pygame.draw.circle(robot_surface, RED, (center_pt, center_pt), 4)
    pygame.draw.line(robot_surface, BLUE, (center_pt, center_pt), (center_pt, center_pt - body_h//2 + 5), 2)
    pygame.draw.polygon(robot_surface, BLUE, [(center_pt, center_pt - body_h//2), (center_pt - 4, center_pt - body_h//2 + 6), (center_pt + 4, center_pt - body_h//2 + 6)])

    # Xoay robot tương tác động góc la bàn thực tế
    rotated = pygame.transform.rotate(robot_surface, -yaw)
    rect = rotated.get_rect(center=(scr_x, scr_y))
    screen.blit(rotated, rect)

    # -------------------------------------
    # VẼ CÁC TIA LASER CHUẨN KÍCH THƯỚC CHUẨN VẬT LÝ VỚI SÂN (mm)
    # -------------------------------------
    if connected_status:
        yaw_rad = math.radians(yaw)
        
        # Bán kính bán vật lý của Robot (500mm / 2 = 250mm)
        ROBOT_RADIUS_MM = 250
        
        # 1. Tia FRONT
        f_len_px = (ROBOT_RADIUS_MM + front_distance * 10) * SCALE_MM_TO_PX
        fx = scr_x + math.sin(yaw_rad) * f_len_px
        fy = scr_y - math.cos(yaw_rad) * f_len_px
        pygame.draw.line(screen, RED, (scr_x, scr_y), (int(fx), int(fy)), 1)
        pygame.draw.circle(screen, RED, (int(fx), int(fy)), 4)
        
        # 2. Tia BACK
        b_len_px = (ROBOT_RADIUS_MM + back_distance * 10) * SCALE_MM_TO_PX
        bx = scr_x - math.sin(yaw_rad) * b_len_px
        by = scr_y + math.cos(yaw_rad) * b_len_px
        pygame.draw.line(screen, RED, (scr_x, scr_y), (int(bx), int(by)), 1)
        pygame.draw.circle(screen, RED, (int(bx), int(by)), 4)

        # 3. Tia LEFT
        l_len_px = (ROBOT_RADIUS_MM + left_distance * 10) * SCALE_MM_TO_PX
        lx = scr_x - math.cos(yaw_rad) * l_len_px
        ly = scr_y - math.sin(yaw_rad) * l_len_px
        pygame.draw.line(screen, RED, (scr_x, scr_y), (int(lx), int(ly)), 1)
        pygame.draw.circle(screen, RED, (int(lx), int(ly)), 4)

        # 4. Tia RIGHT
        r_len_px = (ROBOT_RADIUS_MM + right_distance * 10) * SCALE_MM_TO_PX
        rx = scr_x + math.cos(yaw_rad) * r_len_px
        ry = scr_y + math.sin(yaw_rad) * r_len_px
        pygame.draw.line(screen, RED, (scr_x, scr_y), (int(rx), int(ry)), 1)
        pygame.draw.circle(screen, RED, (int(rx), int(ry)), 4)

# =========================================
# CHỈ THỊ BÓNG LED DÒ LINE (SATELLITE BARS)
# =========================================
def draw_sensor_bar(data, x, y):
    for i, val in enumerate(data):
        color = GREEN if val else GRAY
        pygame.draw.circle(screen, color, (x + i * 26, y), 8)
        num_txt = font.render(str(i+1), True, (100, 100, 105))
        screen.blit(num_txt, (x - 4 + i * 26, y + 12))

# =========================================
# BẢNG ĐIỀU KHIỂN ĐA TRANG (TABBED RIGHT PANEL)
# =========================================
def draw_panel():
    panel_x = WIDTH - 360
    # Bo khung nền Panel chính
    pygame.draw.rect(screen, PANEL, (panel_x, 20, 340, HEIGHT - 40), border_radius=20)

    # -------------------------------------
    # THIẾT KẾ TAB HEADER (CLICKABLE TABS)
    # -------------------------------------
    tabs = ["CONTROL", "SENSORS", "HARDWARE"]
    tab_start_x = panel_x + 15
    tab_y = 35

    for i, tab_name in enumerate(tabs):
        tab_rect = pygame.Rect(tab_start_x + i * 105, tab_y, 100, 35)
        bg_color = TAB_ACTIVE if current_tab == tab_name else TAB_INACTIVE
        pygame.draw.rect(screen, bg_color, tab_rect, border_radius=6)
        
        txt_color = BLACK_LINE if current_tab == tab_name else WHITE
        txt = tab_font.render(tab_name, True, txt_color)
        txt_rect = txt.get_rect(center=tab_rect.center)
        screen.blit(txt, txt_rect)

    pygame.draw.line(screen, GRAY, (panel_x + 15, 82), (panel_x + 325, 82), 1)

    # -------------------------------------
    # TRANG 1: ĐIỀU KHIỂN CHẠY VÀ SÂN ĐẤU GỐC
    # -------------------------------------
    if current_tab == "CONTROL":
        # Connection status indicator
        conn_color = GREEN if connected_status else RED
        conn_text  = "USB TELEMETRY: ONLINE" if connected_status else "USB TELEMETRY: OFFLINE"
        pygame.draw.circle(screen, conn_color, (panel_x + 35, 115), 6)
        status = font.render(conn_text, True, conn_color)
        screen.blit(status, (panel_x + 50, 106))

        # Đèn báo kết nối hệ thống vi điều khiển chính
        pygame.draw.line(screen, GRAY, (panel_x + 15, 135), (panel_x + 325, 135), 1)
        sys_title = font.render("SYS HEALTH:", True, BLUE)
        screen.blit(sys_title, (panel_x + 25, 142))

        h_labels = [("TCA", health_tca), ("IMU", health_mpu), ("MEGA", health_mega), ("LINE", health_line)]
        for i, (name, state) in enumerate(h_labels):
            h_color = GREEN if state else RED
            pygame.draw.circle(screen, h_color, (panel_x + 35 + i * 75, 175), 5)
            h_txt = font.render(name, True, h_color)
            screen.blit(h_txt, (panel_x + 45 + i * 75, 166))

        # Đèn báo kết nối riêng rẽ của 4 cảm biến Laser ToF (Tránh đè chữ)
        pygame.draw.line(screen, GRAY, (panel_x + 15, 195), (panel_x + 325, 195), 1)
        vl_title = font.render("VL53 SENSORS:", True, BLUE)
        screen.blit(vl_title, (panel_x + 25, 202))

        vl_labels = [("FRONT", health_vl53[0]), ("BACK", health_vl53[1]), ("LEFT", health_vl53[2]), ("RIGHT", health_vl53[3])]
        for i, (name, state) in enumerate(vl_labels):
            h_color = GREEN if state else RED
            pygame.draw.circle(screen, h_color, (panel_x + 35 + i * 75, 235), 5)
            h_txt = font.render(name, True, h_color)
            screen.blit(h_txt, (panel_x + 45 + i * 75, 226))

        # Tiêu đề bảng điều khiển mô phỏng gốc
        sim_info_y = 265
        pygame.draw.line(screen, GRAY, (panel_x + 15, sim_info_y - 10), (panel_x + 325, sim_info_y - 10), 1)
        
        sim_title = big_font.render("SIMULATION CTRL", True, WHITE)
        screen.blit(sim_title, (panel_x + 30, sim_info_y))

        # Các nút bấm gốc (Đã đồng bộ hóa toạ độ Y theo biến toàn cục BUTTON_Y chống đè chéo)
        buttons = [
            ("START", GREEN),
            ("PAUSE", ORANGE),
            ("STOP", RED)
        ]
        for i, (name, color) in enumerate(buttons):
            btn_rect = pygame.Rect(panel_x + 30, BUTTON_Y + i * 50, 120, 35)
            pygame.draw.rect(screen, color, btn_rect, border_radius=8)
            txt = font.render(name, True, BLACK_LINE)
            txt_rect = txt.get_rect(center=btn_rect.center)
            screen.blit(txt, txt_rect)

        # Trực quan hóa cấu hình chọn Sân RED / BLUE
        pygame.draw.rect(screen, RED, (panel_x + 180, BUTTON_Y, 120, 35), border_radius=8)
        txt_red = font.render("RED FIELD", True, WHITE)
        screen.blit(txt_red, (panel_x + 201, BUTTON_Y + 8))

        pygame.draw.rect(screen, BLUE, (panel_x + 180, BUTTON_Y + 50, 120, 35), border_radius=8)
        txt_blue = font.render("BLUE FIELD", True, WHITE)
        screen.blit(txt_blue, (panel_x + 198, BUTTON_Y + 58))

        # Dải hiển thị trạng thái sân đang chạy
        mode_text = font.render(f"ACTIVE FIELD: {robot_mode}", True, WHITE)
        screen.blit(mode_text, (panel_x + 180, BUTTON_Y + 108))

        # Target Node hiển thị
        if current_target_index < len(current_route):
            target = current_route[current_target_index]
            txt_tar = big_font.render(f"TARGET: Node {target}", True, GREEN)
            screen.blit(txt_tar, (panel_x + 30, HEIGHT - 85))

    # -------------------------------------
    # TRANG 2: THEO DÕI 32 MẮT DÒ LINE (SENSORS)
    # -------------------------------------
    elif current_tab == "SENSORS":
        sensor_title = big_font.render("32-CH LINE DETECT", True, BLUE)
        screen.blit(sensor_title, (panel_x + 30, 105))

        labels = [
            ("MẶT TRƯỚC (FRONT - F1..F8)", front_sensor),
            ("MẶT SAU (BACK - B1..B8)", back_sensor),
            ("MẶT TRÁI (LEFT - L1..L8)", left_sensor),
            ("MẶT PHẢI (RIGHT - R1..R8)", right_sensor)
        ]

        sy = 160
        for i, (name, data) in enumerate(labels):
            txt = font.render(name, True, WHITE)
            screen.blit(txt, (panel_x + 30, sy + i * 95))
            
            box_rect = pygame.Rect(panel_x + 20, sy + 25 + i * 95, 300, 45)
            pygame.draw.rect(screen, BG, box_rect, border_radius=10)
            pygame.draw.rect(screen, GRAY, box_rect, 1, border_radius=10)
            
            draw_sensor_bar(data, panel_x + 40, sy + 45 + i * 95)

    # -------------------------------------
    # TRANG 3: THÔNG SỐ ĐO KHÔNG GIAN (HARDWARE)
    # -------------------------------------
    elif current_tab == "HARDWARE":
        hw_title = big_font.render("HARDWARE STATUS", True, ORANGE)
        screen.blit(hw_title, (panel_x + 30, 105))

        # 1. Khung hiển thị IMU La bàn số
        imu_y = 155
        pygame.draw.rect(screen, BG, (panel_x + 20, imu_y, 300, 100), border_radius=10)
        pygame.draw.rect(screen, GRAY, (panel_x + 20, imu_y, 300, 100), 1, border_radius=10)
        
        imu_title = font.render("IMU YAW / ROLL / PITCH", True, BLUE)
        screen.blit(imu_title, (panel_x + 35, imu_y + 10))
        
        txt_yaw = font.render(f"Yaw Góc Quay : {robot_yaw:.2f}°", True, WHITE)
        screen.blit(txt_yaw, (panel_x + 35, imu_y + 35))
        
        txt_rp = font.render(f"Roll: {robot_roll:.1f}°   |   Pitch: {robot_pitch:.1f}°", True, WHITE)
        screen.blit(txt_rp, (panel_x + 35, imu_y + 65))

        # 2. Khung hiển thị cảm biến laser VL53L0X
        laser_y = 275
        pygame.draw.rect(screen, BG, (panel_x + 20, laser_y, 300, 115), border_radius=10)
        pygame.draw.rect(screen, GRAY, (panel_x + 20, laser_y, 300, 115), 1, border_radius=10)
        
        laser_title = font.render("VL53L0X LASER DISTANCE (cm)", True, BLUE)
        screen.blit(laser_title, (panel_x + 35, laser_y + 10))
        
        txt_lf = font.render(f"Trước (F) : {front_distance:<5} |  Sau (B) : {back_distance}", True, WHITE)
        screen.blit(txt_lf, (panel_x + 35, laser_y + 40))
        
        txt_lr = font.render(f"Trái  (L) : {left_distance:<5} |  Phải (R) : {right_distance}", True, WHITE)
        screen.blit(txt_lr, (panel_x + 35, laser_y + 75))

        # 3. Khung hiển thị tốc độ vòng quay bánh xe RPM thực tế
        rpm_y = 410
        pygame.draw.rect(screen, BG, (panel_x + 20, rpm_y, 300, 105), border_radius=10)
        pygame.draw.rect(screen, GRAY, (panel_x + 20, rpm_y, 300, 105), 1, border_radius=10)
        
        motor_title = font.render("MOTOR REAL-TIME SPEED (RPM)", True, BLUE)
        screen.blit(motor_title, (panel_x + 35, rpm_y + 10))
        
        txt_m12 = font.render(f"Bánh Trước: FL: {motor_speeds[0]:.1f}  | FR: {motor_speeds[1]:.1f}", True, WHITE)
        screen.blit(txt_m12, (panel_x + 35, rpm_y + 40))
        
        txt_m34 = font.render(f"Bánh Sau   : RL: {motor_speeds[2]:.1f}  | RR: {motor_speeds[3]:.1f}", True, WHITE)
        screen.blit(txt_m34, (panel_x + 35, rpm_y + 70))

        # 4. Gói tin nhận được
        pkt_text = font.render(f"Gói tin Telemetry đã nhận: {packet_count}", True, GRAY)
        screen.blit(pkt_text, (panel_x + 30, HEIGHT - 55))

# =========================================
# ĐIỀU HƯỚNG MÔ PHỎNG TỰ ĐỘNG GỐC (AUTO NAV)
# =========================================
def auto_navigation():
    global robot_x, robot_y, robot_yaw, current_target_index

    if not robot_running or robot_pause:
        return

    if current_target_index >= len(current_route):
        return

    target_name = current_route[current_target_index]
    tx, ty = nodes_mm[target_name] # Tọa độ mục tiêu thực tế (mm)

    dx = tx - robot_x
    dy = ty - robot_y
    distance = math.sqrt(dx*dx + dy*dy)

    # Chạm đích khi khoảng cách nhỏ hơn 40mm (4cm)
    if distance < 40:
        current_target_index += 1
        return

    dx /= distance
    dy /= distance

    # Di chuyển robot mượt mà trong không gian thực (mm)
    robot_x += dx * robot_speed
    robot_y += dy * robot_speed
    
    # Chỉ giả lập hướng xoay khi xe không kết nối trực tiếp với robot thật
    if not connected_status:
        robot_yaw = math.degrees(math.atan2(dx, -dy))

# =========================================
# VÒNG LẶP CHẠY CHÍNH (MAIN PROGRAM LOOP)
# =========================================
running = True

while running:
    clock.tick(60)

    # Tự động quét tìm kết nối USB Serial nếu bị lỏng dây cáp
    if SERIAL_AVAILABLE and not connected_status:
        find_and_connect_serial()

    # =====================================
    # ĐỌC GIẢI MÃ CHUỖI TELEMETRY NHẬN TỪ USB SERIAL
    # =====================================
    if SERIAL_AVAILABLE and ser is not None and ser.is_open:
        try:
            while ser.in_waiting > 0:
                line_data = ser.readline().decode('utf-8', errors='ignore').strip()
                # Chỉ xử lý các chuỗi JSON hợp lệ được bắt đầu bằng { và kết thúc bằng }
                if line_data.startswith('{') and line_data.endswith('}'):
                    msg = json.loads(line_data)

                    # Đồng bộ hóa góc quay vật lý của IMU thực tế
                    robot_yaw   = msg["yaw"]
                    robot_roll  = msg.get("roll", 0.0)
                    robot_pitch = msg.get("pitch", 0.0)

                    # Cập nhật giá trị khoảng cách của 4 mắt laser ToF
                    front_distance = msg["front_distance"]
                    back_distance  = msg["back_distance"]
                    left_distance  = msg.get("left_distance", 0)
                    right_distance = msg.get("right_distance", 0)

                    # Cập nhật trạng thái logic của 32 mắt dò line
                    front_sensor = msg["front"]
                    back_sensor  = msg["back"]
                    left_sensor  = msg["left"]
                    right_sensor = msg["right"]

                    # Cập nhật RPM thực tế của bánh Mecanum và Xung Encoders
                    motor_speeds = msg.get("speed", [0.0]*4)
                    motor_encs   = msg.get("enc", [0]*4)

                    # Cập nhật trạng thái sống/chết của các linh kiện trên robot
                    health_data = msg.get("health", {})
                    health_tca  = health_data.get("tca", False)
                    health_mpu  = health_data.get("mpu", False)
                    health_mega = health_data.get("mega", False)
                    health_line = health_data.get("line", False)
                    health_vl53[0] = health_data.get("vl53_f", False)
                    health_vl53[1] = health_data.get("vl53_b", False)
                    health_vl53[2] = health_data.get("vl53_l", False)
                    health_vl53[3] = health_data.get("vl53_r", False)

                    # Thêm tọa độ vết di chuyển thực tế (mép bánh xe)
                    trail.append((robot_x, robot_y))
                    if len(trail) > 1000:
                        trail.pop(0)

                    packet_count += 1
                    connected_status = True
                    last_packet_time = pygame.time.get_ticks()

        except Exception as e:
            pass

    # Nếu quá 1.5 giây không có tín hiệu phản hồi từ robot, tự động ngắt kết nối COM để chờ dò lại
    if SERIAL_AVAILABLE and connected_status and (pygame.time.get_ticks() - last_packet_time > 1500):
        connected_status = False
        try:
            if ser:
                ser.close()
            ser = None
        except:
            pass

    # =====================================
    # XỬ LÝ SỰ KIỆN CLICK CHUỘT / BÀN PHÍM
    # =====================================
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            panel_x = WIDTH - 360

            # ---------------------------------
            # SỰ KIỆN CLICK CHUYỂN TAB HEADER
            # ---------------------------------
            tab_y = 35
            if tab_y <= my <= tab_y + 35:
                # Tab 1: CONTROL
                if panel_x + 15 <= mx <= panel_x + 115:
                    current_tab = "CONTROL"
                # Tab 2: SENSORS
                elif panel_x + 120 <= mx <= panel_x + 220:
                    current_tab = "SENSORS"
                # Tab 3: HARDWARE
                elif panel_x + 225 <= mx <= panel_x + 325:
                    current_tab = "HARDWARE"

            # ---------------------------------
            # SỰ KIỆN CLICK BUTTONS GỐC (Chỉ cho phép khi ở Tab CONTROL)
            # ---------------------------------
            if current_tab == "CONTROL":
                # START BUTTON CLICK
                if panel_x + 30 <= mx <= panel_x + 150:
                    if BUTTON_Y <= my <= BUTTON_Y + 35:
                        robot_running = True
                        robot_pause = False

                # PAUSE BUTTON CLICK
                if panel_x + 30 <= mx <= panel_x + 150:
                    if BUTTON_Y + 50 <= my <= BUTTON_Y + 85:
                        robot_pause = not robot_pause

                # STOP BUTTON CLICK (Sử dụng thống nhất biến BUTTON_Y toàn cục)
                if panel_x + 30 <= mx <= panel_x + 150:
                    if BUTTON_Y + 100 <= my <= BUTTON_Y + 135:
                        robot_running = False
                        current_target_index = 0
                        if robot_mode == "RED":
                            robot_x, robot_y = nodes_mm["A"]
                        else:
                            robot_x, robot_y = nodes_mm["M"]

                # RED FIELD SELECTION (Đồng bộ nút bấm sang biến toàn cục BUTTON_Y)
                if panel_x + 180 <= mx <= panel_x + 300:
                    if BUTTON_Y <= my <= BUTTON_Y + 35:
                        robot_mode = "RED"
                        current_route = red_route
                        robot_x, robot_y = nodes_mm["A"]
                        current_target_index = 0

                # BLUE FIELD SELECTION (Sử dụng BUTTON_Y + 50 thống nhất)
                if panel_x + 180 <= mx <= panel_x + 300:
                    if BUTTON_Y + 50 <= my <= BUTTON_Y + 85:
                        robot_mode = "BLUE"
                        current_route = blue_route
                        robot_x, robot_y = nodes_mm["M"]
                        current_target_index = 0

    # Chạy thuật toán di chuyển mô phỏng tự hành
    auto_navigation()

    # =====================================
    # RENDER ĐỒ HỌA MÀN HÌNH
    # =====================================
    screen.fill(BG)
    draw_grid()
    draw_map()

    # Vẽ vệt di chuyển (Trail) của AGV chuyển đổi từ mm sang pixel hiển thị
    for p in trail:
        screen_tx = MAP_X + int(p[0] * SCALE_MM_TO_PX)
        screen_ty = MAP_Y + int(p[1] * SCALE_MM_TO_PX)
        pygame.draw.circle(screen, GREEN, (screen_tx, screen_ty), 2)

    # Convert tọa độ thực tế mm của robot sang tọa độ Pixel hiển thị
    screen_robot_x = MAP_X + int(robot_x * SCALE_MM_TO_PX)
    screen_robot_y = MAP_Y + int(robot_y * SCALE_MM_TO_PX)

    # Vẽ robot bám theo góc xoay Yaw IMU vật lý thực tế
    draw_robot(robot_x, robot_y, robot_yaw)

    # Vẽ panel thông số đa trang chống đè chữ
    draw_panel()

    pygame.display.flip()

pygame.quit()