import tkinter as tk
import math
import json
import os
import raylibpy as rl
from raylibpy import Vector2, Vector3
from tkinter import colorchooser, filedialog
import numpy as np
import shutil
import pygame
import filecmp

# Initialize pygame mixer
pygame.mixer.init()

# Try importing PIL for image scaling
try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None

# ------------------------------------------------------------------------------
# Portable Media Directory System
# ------------------------------------------------------------------------------
MEDIA_DIR = "media"
if not os.path.exists(MEDIA_DIR):
    os.makedirs(MEDIA_DIR)

def get_media_path(filename):
    """Returns the proper media path, ensuring it's in the media directory"""
    if filename is None:
        return None
    # If already in media dir, return as-is
    if filename.startswith(MEDIA_DIR + os.sep) or filename.startswith("media/"):
        return filename
    # Otherwise, return path in media dir
    return os.path.join(MEDIA_DIR, os.path.basename(filename))

def copy_to_media(src_path):
    """Copy a file to the media directory and return the media path"""
    if src_path is None or not os.path.exists(src_path):
        return None
        
    filename = os.path.basename(src_path)
    dest_path = get_media_path(filename)
    
    try:
        # Only copy if not already in media dir or if different
        if not os.path.exists(dest_path) or not filecmp.cmp(src_path, dest_path, shallow=False):
            shutil.copy2(src_path, dest_path)
        return dest_path
    except Exception as e:
        print(f"Error copying {src_path} to media directory:", e)
        return src_path  # Fallback to original path if copy fails

def load_asset(path):
    """Get the proper path for an asset, ensuring it's in the media directory"""
    if path is None:
        return None
        
    # First try to find in media directory
    media_path = get_media_path(path)
    if os.path.exists(media_path):
        return media_path
        
    # If not found, try original path
    if os.path.exists(path):
        # Attempt to copy to media dir for future use
        return copy_to_media(path)
        
    return None

# ------------------------------------------------------------------------------
# Game Configuration
# ------------------------------------------------------------------------------
ROWS = 20
COLS = 20
CELL_SIZE = 40

# Initialize grid
grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]

# Global variables
sky_color_hex = "#87CEEB"
sun_color_hex = "#FFFF00"

# Texture variables
wall_texture_img = None
ground_texture_img = None
wall_texture_path = None
ground_texture_path = None

# Handgun variables
handgun_idle_img = None
handgun_shoot_img = None
handgun_idle_path = None
handgun_shoot_path = None
handgun_shoot_sound = None
handgun_shoot_sound_path = None

# Enemy variables
enemy_idle_img = None
enemy_shot_img = None
enemy_idle_path = None
enemy_shot_path = None
enemy_model_path = None

# Main menu variables
main_menu_title_var = None
main_menu_button1_var = None
main_menu_button2_var = None
main_menu_button3_var = None
main_menu_alignment = None
main_menu_bg_mode = None
main_menu_bg_color = None
main_menu_bg_image_path = None
main_menu_title_color = None
main_menu_button1_color = None
main_menu_button2_color = None
main_menu_button3_color = None

# Win message variables
win_message_var = None
win_message_color_var = None

# ------------------------------------------------------------------------------
# Utility Functions
# ------------------------------------------------------------------------------
def hex_to_color(color_str):
    """Convert hex color string to Raylib Color"""
    if color_str.startswith("#"):
        try:
            hex_str = color_str.lstrip('#')
            r = int(hex_str[0:2], 16)
            g = int(hex_str[2:4], 16)
            b = int(hex_str[4:6], 16)
            return rl.Color(r, g, b, 255)
        except Exception as e:
            print("Error parsing hex color:", color_str, e)
            return rl.Color(255, 255, 255, 255)
    else:
        try:
            rgb_tuple = root.winfo_rgb(color_str)
            r = int(rgb_tuple[0] / 65535 * 255)
            g = int(rgb_tuple[1] / 65535 * 255)
            b = int(rgb_tuple[2] / 65535 * 255)
            return rl.Color(r, g, b, 255)
        except Exception as e:
            print("Error converting color name:", color_str, e)
            return rl.Color(255, 255, 255, 255)

def redraw_grid():
    """Redraw the grid canvas"""
    canvas.delete("all")
    for i in range(ROWS):
        for j in range(COLS):
            x1 = j * CELL_SIZE
            y1 = i * CELL_SIZE
            x2 = x1 + CELL_SIZE
            y2 = y1 + CELL_SIZE
            cell_val = grid[i][j]
            
            if cell_val == 0:  # Ground
                if ground_texture_img is not None:
                    canvas.create_image(x1, y1, anchor='nw', image=ground_texture_img)
                else:
                    canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="black")
            elif cell_val == 1:  # Wall
                if wall_texture_img is not None:
                    canvas.create_image(x1, y1, anchor='nw', image=wall_texture_img)
                else:
                    canvas.create_rectangle(x1, y1, x2, y2, fill="gray", outline="black")
            elif cell_val == 2:  # Spawn
                if ground_texture_img is not None:
                    canvas.create_image(x1, y1, anchor='nw', image=ground_texture_img)
                canvas.create_rectangle(x1, y1, x2, y2, fill="green", outline="black")
            elif cell_val == 3:  # Enemy
                if enemy_idle_img is not None:
                    canvas.create_image(x1, y1, anchor='nw', image=enemy_idle_img)
                else:
                    canvas.create_oval(x1, y1, x2, y2, fill="red", outline="black")

def canvas_click(event):
    """Handle canvas click events"""
    col = event.x // CELL_SIZE
    row = event.y // CELL_SIZE
    if row < 0 or row >= ROWS or col < 0 or col >= COLS:
        return
        
    mode = mode_var.get()
    if mode == "wall":
        grid[row][col] = 1
    elif mode == "ground":
        grid[row][col] = 0
    elif mode == "spawn":
        # Clear existing spawn point
        for i in range(ROWS):
            for j in range(COLS):
                if grid[i][j] == 2:
                    grid[i][j] = 0
        grid[row][col] = 2
    elif mode == "enemy":
        grid[row][col] = 3
        
    redraw_grid()

def ray_intersect_sphere(ray_origin, ray_dir, sphere_center, sphere_radius):
    """Check if ray intersects with sphere"""
    L = Vector3(sphere_center.x - ray_origin.x,
                sphere_center.y - ray_origin.y,
                sphere_center.z - ray_origin.z)
    t_ca = L.x * ray_dir.x + L.y * ray_dir.y + L.z * ray_dir.z
    if t_ca < 0:
        return False
    d2 = (L.x**2 + L.y**2 + L.z**2) - t_ca**2
    return d2 <= sphere_radius**2

# ------------------------------------------------------------------------------
# Game Preview Function
# ------------------------------------------------------------------------------
def preview():
    """Run the game preview"""
    global game_name_var, shot_delay_var
    
    # Find spawn position
    spawn_found = False
    spawn_row, spawn_col = 0, 0
    for i in range(ROWS):
        for j in range(COLS):
            if grid[i][j] == 2:
                spawn_row, spawn_col = i, j
                spawn_found = True
                break
        if spawn_found:
            break
            
    if not spawn_found:
        spawn_row = ROWS // 2
        spawn_col = COLS // 2

    # Initialize window
    screen_width = int(800 * 1.5)
    screen_height = int(600 * 1.5)
    title = game_name_var.get().strip() or "Preview"
    rl.init_window(screen_width, screen_height, title)
    rl.init_audio_device()
    rl.enable_cursor()
    rl.set_target_fps(60)

    # Load assets through media system
    wall_model_path = load_asset("wall.obj") or "wall.obj"
    model = rl.load_model(wall_model_path)

    wall_tex = rl.load_texture(load_asset(wall_texture_path)) if wall_texture_path else None
    ground_tex = rl.load_texture(load_asset(ground_texture_path)) if ground_texture_path else None
    bg_texture = rl.load_texture(load_asset(main_menu_bg_image_path)) if main_menu_bg_image_path and main_menu_bg_mode.get() == "image" else None
    handgun_idle_tex = rl.load_texture(load_asset(handgun_idle_path)) if handgun_idle_path else None
    handgun_shoot_tex = rl.load_texture(load_asset(handgun_shoot_path)) if handgun_shoot_path else None
    enemy_model = rl.load_model(load_asset(enemy_model_path)) if enemy_model_path else None
    enemy_idle_tex = rl.load_texture(load_asset(enemy_idle_path)) if enemy_idle_path else None
    enemy_shot_tex = rl.load_texture(load_asset(enemy_shot_path)) if enemy_shot_path else None

    # Load sound
    sound_path = load_asset(handgun_shoot_sound_path) if handgun_shoot_sound_path else None
    handgun_shoot_sound = pygame.mixer.Sound(sound_path) if sound_path else None

    # Create enemies
    enemies = []
    for i in range(ROWS):
        for j in range(COLS):
            if grid[i][j] == 3:
                enemies.append({
                    'pos': Vector3(j + 0.5, 0, i + 0.5),
                    'hit_count': 0,
                    'state': 'idle',
                    'state_timer': 0.0
                })

    # Game settings
    cooldown_duration = shot_delay_var.get()
    shoot_display_duration = 0.15
    last_shot_time = -cooldown_duration
    shot_display_timer = 0.0

    player_radius = 0.3
    player_height = 1.8
    base_speed = 3.0
    run_multiplier = 2.0
    jump_impulse = 5.0
    gravity = 9.8
    mouse_sensitivity = 0.005

    camera_pos = Vector3(spawn_col + 0.5, 0, spawn_row + 0.5)
    camera_vel = Vector3(0, 0, 0)
    yaw = 0.0
    pitch = 0.0

    game_state = "menu"
    cursor_locked = False

    # Main game loop
    while not rl.window_should_close():
        dt = rl.get_frame_time()
        current_time = rl.get_time()

        # Shooting logic
        if rl.is_mouse_button_pressed(rl.MOUSE_LEFT_BUTTON) and (current_time - last_shot_time >= cooldown_duration):
            last_shot_time = current_time
            shot_display_timer = shoot_display_duration
            if handgun_shoot_sound:
                handgun_shoot_sound.play()

        if shot_display_timer > 0:
            shot_display_timer -= dt

        # Game state management
        if game_state == "menu":
            if cursor_locked:
                rl.enable_cursor()
                cursor_locked = False

            # Draw menu
            rl.begin_drawing()
            if main_menu_bg_mode.get() == "color":
                rl.clear_background(hex_to_color(main_menu_bg_color.get()))
            elif main_menu_bg_mode.get() == "image" and bg_texture:
                rl.clear_background(rl.RAYWHITE)
                rl.draw_texture(bg_texture, 0, 0, rl.WHITE)
            else:
                rl.clear_background(rl.RAYWHITE)
            
            # Menu text and buttons
            title_text = main_menu_title_var.get() or "My Game"
            button1_text = main_menu_button1_var.get() or "Start Game"
            button2_text = main_menu_button2_var.get() or "Options"
            button3_text = main_menu_button3_var.get() or "Exit"

            align = main_menu_alignment.get()
            title_font_size = 40
            title_width = rl.measure_text(title_text, title_font_size)
            
            if align == "left":
                title_x = 50
                button_x = 50
            elif align == "right":
                title_x = screen_width - title_width - 50
                button_x = screen_width - 200 - 50
            else:
                title_x = (screen_width - title_width) // 2
                button_x = (screen_width - 200) // 2

            rl.draw_text(title_text, title_x, screen_height // 4, title_font_size, hex_to_color(main_menu_title_color.get()))

            button_width = 200
            button_height = 50
            button_spacing = 20
            
            btn1_y = screen_height // 2 - button_height - button_spacing
            btn2_y = screen_height // 2
            btn3_y = screen_height // 2 + button_height + button_spacing

            # Draw buttons
            rl.draw_rectangle(button_x, btn1_y, button_width, button_height, rl.LIGHTGRAY)
            btn1_text_width = rl.measure_text(button1_text, 20)
            rl.draw_text(button1_text, 
                         button_x + (button_width - btn1_text_width) // 2,
                         btn1_y + (button_height - 20) // 2, 
                         20, hex_to_color(main_menu_button1_color.get()))

            rl.draw_rectangle(button_x, btn2_y, button_width, button_height, rl.LIGHTGRAY)
            btn2_text_width = rl.measure_text(button2_text, 20)
            rl.draw_text(button2_text, 
                         button_x + (button_width - btn2_text_width) // 2,
                         btn2_y + (button_height - 20) // 2, 
                         20, hex_to_color(main_menu_button2_color.get()))

            rl.draw_rectangle(button_x, btn3_y, button_width, button_height, rl.LIGHTGRAY)
            btn3_text_width = rl.measure_text(button3_text, 20)
            rl.draw_text(button3_text, 
                         button_x + (button_width - btn3_text_width) // 2,
                         btn3_y + (button_height - 20) // 2, 
                         20, hex_to_color(main_menu_button3_color.get()))

            # Check button clicks
            if rl.is_mouse_button_pressed(rl.MOUSE_LEFT_BUTTON):
                mouse_pos = rl.get_mouse_position()
                if (button_x <= mouse_pos.x <= button_x + button_width):
                    if btn1_y <= mouse_pos.y <= btn1_y + button_height:
                        game_state = "game"
                        rl.disable_cursor()
                        cursor_locked = True
                    elif btn2_y <= mouse_pos.y <= btn2_y + button_height:
                        print("Options selected (not implemented)")
                    elif btn3_y <= mouse_pos.y <= btn3_y + button_height:
                        break

            rl.end_drawing()

        elif game_state == "game":
            # Handle input
            if rl.is_key_pressed(rl.KeyboardKey.KEY_ESCAPE):
                game_state = "menu"
                rl.enable_cursor()
                cursor_locked = False

            # Camera movement
            mouse_delta = rl.get_mouse_delta()
            yaw -= mouse_delta.x * mouse_sensitivity
            pitch -= mouse_delta.y * mouse_sensitivity
            pitch = max(min(pitch, 1.4), -1.4)
            
            # Calculate movement vectors
            forward = Vector3(math.sin(yaw) * math.cos(pitch),
                             math.sin(pitch),
                             math.cos(yaw) * math.cos(pitch))
            forward = rl.vector3_normalize(forward)
            
            up = Vector3(0, 1, 0)
            right = rl.vector3_cross_product(forward, up)
            right = rl.vector3_normalize(right)

            # Movement input
            move = Vector3(0, 0, 0)
            if rl.is_key_down(rl.KeyboardKey.KEY_W):
                move = rl.vector3_add(move, forward)
            if rl.is_key_down(rl.KeyboardKey.KEY_S):
                move = rl.vector3_subtract(move, forward)
            if rl.is_key_down(rl.KeyboardKey.KEY_A):
                move = rl.vector3_subtract(move, right)
            if rl.is_key_down(rl.KeyboardKey.KEY_D):
                move = rl.vector3_add(move, right)
                
            if rl.vector3_length(move) > 0:
                move = rl.vector3_normalize(move)
                
            speed = base_speed * (run_multiplier if rl.is_key_down(rl.KeyboardKey.KEY_LEFT_SHIFT) else 1.0)
            move = rl.vector3_scale(move, speed)
            
            camera_vel.x = move.x
            camera_vel.z = move.z

            # Jumping
            if rl.is_key_pressed(rl.KeyboardKey.KEY_SPACE) and (camera_pos.y <= 0.05):
                camera_vel.y = jump_impulse
            camera_vel.y -= gravity * dt

            # Update position
            camera_pos = rl.vector3_add(camera_pos, rl.vector3_scale(camera_vel, dt))
            if camera_pos.y < 0:
                camera_pos.y = 0
                camera_vel.y = 0

            # Collision detection
            walls = [(i, j) for i in range(ROWS) for j in range(COLS) if grid[i][j] == 1]
            if walls:
                walls_np = np.array(walls)
                px, pz = camera_pos.x, camera_pos.z
                
                closest_x = np.maximum(walls_np[:,1], np.minimum(px, walls_np[:,1] + 1))
                closest_z = np.maximum(walls_np[:,0], np.minimum(pz, walls_np[:,0] + 1))
                
                dx = px - closest_x
                dz = pz - closest_z
                distances = np.sqrt(dx * dx + dz * dz)
                
                collision_indices = np.where(distances < player_radius)[0]
                if collision_indices.size > 0:
                    correction_factor = 0.5 if camera_pos.y > 0.05 else 1.0
                    distances_fixed = np.where(distances == 0, 0.001, distances)
                    
                    penetration = player_radius - distances[collision_indices]
                    corr_x = np.sum((dx[collision_indices] / distances_fixed[collision_indices]) * penetration * correction_factor)
                    corr_z = np.sum((dz[collision_indices] / distances_fixed[collision_indices]) * penetration * correction_factor)
                    
                    camera_pos.x += corr_x
                    camera_pos.z += corr_z

            # Shooting enemies
            if rl.is_mouse_button_pressed(rl.MOUSE_LEFT_BUTTON) and (current_time - last_shot_time < 0.1):
                ray_origin = Vector3(camera_pos.x, camera_pos.y + player_height * 0.5, camera_pos.z)
                for enemy in enemies[:]:
                    if ray_intersect_sphere(ray_origin, forward, enemy['pos'], 0.5):
                        enemy['hit_count'] += 1
                        enemy['state'] = 'shot'
                        enemy['state_timer'] = 0.5
                        if enemy['hit_count'] >= 2:
                            enemies.remove(enemy)

            # Update enemy states
            for enemy in enemies:
                if enemy['state'] == 'shot':
                    enemy['state_timer'] -= dt
                    if enemy['state_timer'] <= 0:
                        enemy['state'] = 'idle'

            # Setup camera
            eye_level = player_height * 0.5
            camera = rl.Camera3D(
                position=Vector3(camera_pos.x, camera_pos.y + eye_level, camera_pos.z),
                target=Vector3(camera_pos.x + forward.x, camera_pos.y + forward.y + eye_level, camera_pos.z + forward.z),
                up=up,
                fovy=60.0,
                projection=rl.CameraProjection.CAMERA_PERSPECTIVE
            )

            # Draw 3D scene
            rl.begin_drawing()
            rl.clear_background(hex_to_color(sky_color_hex))
            
            rl.begin_mode3d(camera)
            
            # Draw sun
            sun_position = Vector3(COLS * 1.5, 10, -COLS * 0.5)
            center = Vector3(COLS / 2, 0, ROWS / 2)
            light_dir = rl.vector3_normalize(rl.vector3_subtract(center, sun_position))
            
            shader = model.materials[0].shader
            lightPosLoc = rl.get_shader_location(shader, "light.position")
            if lightPosLoc != -1:
                rl.set_shader_value(shader, lightPosLoc, [light_dir.x, light_dir.y, light_dir.z], rl.SHADER_UNIFORM_VEC3)
            
            rl.draw_sphere(sun_position, 1.0, hex_to_color(sun_color_hex))

            # Draw ground and walls
            for i in range(ROWS):
                for j in range(COLS):
                    pos = Vector3(j + 0.5, 0.05, i + 0.5)
                    scale = Vector3(1.0, 0.1, 1.0)
                    
                    if grid[i][j] != 1:
                        if ground_tex:
                            model.materials[0].maps[rl.MATERIAL_MAP_DIFFUSE].texture = ground_tex
                        rl.draw_model_ex(model, pos, Vector3(0, 1, 0), 0.0, scale, rl.WHITE)
                    else:
                        pos.y = 0.5
                        scale.y = 1.0
                        if wall_tex:
                            model.materials[0].maps[rl.MATERIAL_MAP_DIFFUSE].texture = wall_tex
                        rl.draw_model_ex(model, pos, Vector3(0, 1, 0), 0.0, scale, rl.WHITE)

            # Draw spawn point
            rl.draw_cube(Vector3(spawn_col + 0.5, 0.5, spawn_row + 0.5), 0.5, 0.5, 0.5, rl.GREEN)

            # Draw enemies
            for enemy in enemies:
                if enemy_model:
                    enemy_angle = math.degrees(math.atan2(camera_pos.x - enemy['pos'].x, 
                                                       camera_pos.z - enemy['pos'].z)) + 180
                    
                    if enemy['state'] == 'shot' and enemy_shot_tex:
                        enemy_model.materials[0].maps[rl.MATERIAL_MAP_DIFFUSE].texture = enemy_shot_tex
                    elif enemy_idle_tex:
                        enemy_model.materials[0].maps[rl.MATERIAL_MAP_DIFFUSE].texture = enemy_idle_tex
                        
                    rl.draw_model_ex(
                        enemy_model, 
                        Vector3(enemy['pos'].x, 0.5, enemy['pos'].z),
                        Vector3(0, 1, 0), 
                        enemy_angle, 
                        Vector3(1.0, 1.0, 1.0), 
                        rl.WHITE
                    )
                else:
                    rl.draw_cube(Vector3(enemy['pos'].x, 0.5, enemy['pos'].z), 1.0, 1.0, 1.0, rl.RED)

            rl.end_mode3d()

            # Draw HUD
            handgun_x = (screen_width - 416) // 2
            handgun_y = screen_height - 416
            
            if shot_display_timer > 0 and handgun_shoot_tex:
                rl.draw_texture(handgun_shoot_tex, handgun_x, handgun_y, rl.WHITE)
            elif handgun_idle_tex:
                rl.draw_texture(handgun_idle_tex, handgun_x, handgun_y, rl.WHITE)

            # Draw FPS and controls
            fps = rl.get_fps()
            rl.draw_text(f"FPS: {fps}", screen_width - 100, 10, 20, rl.MAROON)
            rl.draw_text("WASD: Move | SHIFT: Run | SPACE: Jump | ESC: Menu", 
                         10, 10, 20, rl.MAROON)
            
            # Draw win message if all enemies defeated
            if not enemies:
                win_text = win_message_var.get() or "YOU WIN!"
                font_size = 50
                text_width = rl.measure_text(win_text, font_size)
                win_color = hex_to_color(win_message_color_var.get()) if win_message_color_var else rl.GREEN
                rl.draw_text(win_text, 
                            (screen_width - text_width) // 2,
                            (screen_height - font_size) // 2,
                            font_size, win_color)
            
            rl.end_drawing()

    # Clean up
    rl.unload_model(model)
    if wall_tex: rl.unload_texture(wall_tex)
    if ground_tex: rl.unload_texture(ground_tex)
    if bg_texture: rl.unload_texture(bg_texture)
    if handgun_idle_tex: rl.unload_texture(handgun_idle_tex)
    if handgun_shoot_tex: rl.unload_texture(handgun_shoot_tex)
    if enemy_idle_tex: rl.unload_texture(enemy_idle_tex)
    if enemy_shot_tex: rl.unload_texture(enemy_shot_tex)
    if enemy_model: rl.unload_model(enemy_model)
    
    rl.close_audio_device()
    rl.close_window()

# ------------------------------------------------------------------------------
# Asset Selection Functions
# ------------------------------------------------------------------------------
def choose_sky_color():
    global sky_color_hex
    color = colorchooser.askcolor(title="Choose Sky Color", initialcolor=sky_color_hex)
    if color[1]:
        sky_color_hex = color[1]

def choose_sun_color():
    global sun_color_hex
    color = colorchooser.askcolor(title="Choose Sun Color", initialcolor=sun_color_hex)
    if color[1]:
        sun_color_hex = color[1]

def choose_wall_texture():
    global wall_texture_img, wall_texture_path
    file_path = filedialog.askopenfilename(
        filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"), ("All Files", "*.*")],
        title="Choose Wall Texture"
    )
    if file_path:
        wall_texture_path = copy_to_media(file_path)
        try:
            if Image:
                img = Image.open(wall_texture_path)
                img = img.resize((CELL_SIZE, CELL_SIZE), Image.Resampling.LANCZOS)
                wall_texture_img = ImageTk.PhotoImage(img)
            else:
                wall_texture_img = tk.PhotoImage(file=wall_texture_path)
            redraw_grid()
        except Exception as e:
            print("Error loading wall texture:", e)
            wall_texture_img = None

def choose_ground_texture():
    global ground_texture_img, ground_texture_path
    file_path = filedialog.askopenfilename(
        filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"), ("All Files", "*.*")],
        title="Choose Ground Texture"
    )
    if file_path:
        ground_texture_path = copy_to_media(file_path)
        try:
            if Image:
                img = Image.open(ground_texture_path)
                img = img.resize((CELL_SIZE, CELL_SIZE), Image.Resampling.LANCZOS)
                ground_texture_img = ImageTk.PhotoImage(img)
            else:
                ground_texture_img = tk.PhotoImage(file=ground_texture_path)
            redraw_grid()
        except Exception as e:
            print("Error loading ground texture:", e)
            ground_texture_img = None

def choose_handgun_idle_image():
    global handgun_idle_img, handgun_idle_path
    file_path = filedialog.askopenfilename(
        filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"), ("All Files", "*.*")],
        title="Choose Handgun Idle Image (416x416)"
    )
    if file_path:
        handgun_idle_path = copy_to_media(file_path)
        try:
            if Image:
                img = Image.open(handgun_idle_path)
                img = img.resize((416, 416), Image.Resampling.LANCZOS)
                handgun_idle_img = ImageTk.PhotoImage(img)
            else:
                handgun_idle_img = tk.PhotoImage(file=handgun_idle_path)
        except Exception as e:
            print("Error loading handgun idle image:", e)
            handgun_idle_img = None

def choose_handgun_shoot_image():
    global handgun_shoot_img, handgun_shoot_path
    file_path = filedialog.askopenfilename(
        filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"), ("All Files", "*.*")],
        title="Choose Handgun Shoot Image (416x416)"
    )
    if file_path:
        handgun_shoot_path = copy_to_media(file_path)
        try:
            if Image:
                img = Image.open(handgun_shoot_path)
                img = img.resize((416, 416), Image.Resampling.LANCZOS)
                handgun_shoot_img = ImageTk.PhotoImage(img)
            else:
                handgun_shoot_img = tk.PhotoImage(file=handgun_shoot_path)
        except Exception as e:
            print("Error loading handgun shoot image:", e)
            handgun_shoot_img = None

def choose_handgun_shoot_sound():
    global handgun_shoot_sound, handgun_shoot_sound_path
    file_path = filedialog.askopenfilename(
        filetypes=[("Audio Files", "*.wav;*.ogg;*.mp3"), ("All Files", "*.*")],
        title="Choose Handgun Shoot Sound"
    )
    if file_path:
        handgun_shoot_sound_path = copy_to_media(file_path)
        try:
            handgun_shoot_sound = pygame.mixer.Sound(handgun_shoot_sound_path)
        except Exception as e:
            print("Error loading handgun shoot sound:", e)
            handgun_shoot_sound = None

def choose_enemy_idle_image():
    global enemy_idle_img, enemy_idle_path
    file_path = filedialog.askopenfilename(
        filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"), ("All Files", "*.*")],
        title="Choose Enemy Idle Image"
    )
    if file_path:
        enemy_idle_path = copy_to_media(file_path)
        try:
            if Image:
                img = Image.open(enemy_idle_path)
                img = img.resize((CELL_SIZE, CELL_SIZE), Image.Resampling.LANCZOS)
                enemy_idle_img = ImageTk.PhotoImage(img)
            else:
                enemy_idle_img = tk.PhotoImage(file=enemy_idle_path)
            redraw_grid()
        except Exception as e:
            print("Error loading enemy idle image:", e)
            enemy_idle_img = None

def choose_enemy_shot_image():
    global enemy_shot_img, enemy_shot_path
    file_path = filedialog.askopenfilename(
        filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"), ("All Files", "*.*")],
        title="Choose Enemy Shot Image"
    )
    if file_path:
        enemy_shot_path = copy_to_media(file_path)
        try:
            if Image:
                img = Image.open(enemy_shot_path)
                img = img.resize((CELL_SIZE, CELL_SIZE), Image.Resampling.LANCZOS)
                enemy_shot_img = ImageTk.PhotoImage(img)
            else:
                enemy_shot_img = tk.PhotoImage(file=enemy_shot_path)
            redraw_grid()
        except Exception as e:
            print("Error loading enemy shot image:", e)
            enemy_shot_img = None

def choose_enemy_model():
    global enemy_model_path
    file_path = filedialog.askopenfilename(
        filetypes=[("3D Model Files", "*.obj"), ("All Files", "*.*")],
        title="Choose Enemy Model (.obj)"
    )
    if file_path:
        enemy_model_path = copy_to_media(file_path)

def choose_main_menu_bg_image():
    global main_menu_bg_image_path
    file_path = filedialog.askopenfilename(
        filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"), ("All Files", "*.*")],
        title="Choose Main Menu Background Image"
    )
    if file_path:
        main_menu_bg_image_path = copy_to_media(file_path)

def choose_win_message_color():
    color = colorchooser.askcolor(title="Choose Win Message Color", initialcolor=win_message_color_var.get())
    if color[1]:
        win_message_color_var.set(color[1])

# ------------------------------------------------------------------------------
# File Operations
# ------------------------------------------------------------------------------
def save_map():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
        title="Save Map"
    )
    if file_path:
        try:
            def get_portable_path(path):
                if not path:
                    return None
                if path.startswith(MEDIA_DIR + os.sep) or path.startswith("media/"):
                    return os.path.basename(path)
                return path

            data = {
                "grid": grid,
                "sky_color": sky_color_hex,
                "sun_color": sun_color_hex,
                "wall_texture": get_portable_path(wall_texture_path),
                "ground_texture": get_portable_path(ground_texture_path),
                "handgun_idle_texture": get_portable_path(handgun_idle_path),
                "handgun_shoot_texture": get_portable_path(handgun_shoot_path),
                "handgun_shoot_sound": get_portable_path(handgun_shoot_sound_path),
                "enemy_idle_texture": get_portable_path(enemy_idle_path),
                "enemy_shot_texture": get_portable_path(enemy_shot_path),
                "enemy_model": get_portable_path(enemy_model_path),
                "game_name": game_name_var.get(),
                "shot_delay": shot_delay_var.get(),
                "win_message_text": win_message_var.get(),
                "win_message_color": win_message_color_var.get(),
                "main_menu_title": main_menu_title_var.get(),
                "main_menu_buttons": [
                    main_menu_button1_var.get(),
                    main_menu_button2_var.get(),
                    main_menu_button3_var.get()
                ],
                "main_menu_alignment": main_menu_alignment.get(),
                "main_menu_bg_mode": main_menu_bg_mode.get(),
                "main_menu_bg_color": main_menu_bg_color.get(),
                "main_menu_bg_image": get_portable_path(main_menu_bg_image_path),
                "main_menu_title_color": main_menu_title_color.get(),
                "main_menu_button1_color": main_menu_button1_color.get(),
                "main_menu_button2_color": main_menu_button2_color.get(),
                "main_menu_button3_color": main_menu_button3_color.get()
            }

            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print("Error saving map:", e)

def load_map():
    global grid, sky_color_hex, sun_color_hex
    global wall_texture_path, ground_texture_path, wall_texture_img, ground_texture_img
    global handgun_idle_path, handgun_shoot_path, handgun_idle_img, handgun_shoot_img
    global handgun_shoot_sound, handgun_shoot_sound_path
    global enemy_idle_path, enemy_shot_path, enemy_idle_img, enemy_shot_img, enemy_model_path
    global game_name_var, shot_delay_var, win_message_var, win_message_color_var
    global main_menu_title_var, main_menu_button1_var, main_menu_button2_var, main_menu_button3_var
    global main_menu_alignment, main_menu_bg_mode, main_menu_bg_color, main_menu_bg_image_path
    global main_menu_title_color, main_menu_button1_color, main_menu_button2_color, main_menu_button3_color

    file_path = filedialog.askopenfilename(
        defaultextension=".json",
        filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
        title="Load Map"
    )
    if file_path:
        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            if "grid" in data and "sky_color" in data:
                # Load basic data
                grid[:] = data["grid"]
                sky_color_hex = data["sky_color"]
                sun_color_hex = data.get("sun_color", "#FFFF00")
                game_name_var.set(data.get("game_name", "Preview"))
                shot_delay_var.set(data.get("shot_delay", 2.2))
                win_message_var.set(data.get("win_message_text", "YOU WIN!"))
                win_message_color_var.set(data.get("win_message_color", "#00FF00"))

                # Load main menu settings
                main_menu_title_var.set(data.get("main_menu_title", "My Game"))
                buttons = data.get("main_menu_buttons", ["Start Game", "Options", "Exit"])
                if len(buttons) >= 3:
                    main_menu_button1_var.set(buttons[0])
                    main_menu_button2_var.set(buttons[1])
                    main_menu_button3_var.set(buttons[2])
                main_menu_alignment.set(data.get("main_menu_alignment", "middle"))
                main_menu_bg_mode.set(data.get("main_menu_bg_mode", "color"))
                main_menu_bg_color.set(data.get("main_menu_bg_color", "#FFFFFF"))
                main_menu_title_color.set(data.get("main_menu_title_color", "blue"))
                main_menu_button1_color.set(data.get("main_menu_button1_color", "black"))
                main_menu_button2_color.set(data.get("main_menu_button2_color", "black"))
                main_menu_button3_color.set(data.get("main_menu_button3_color", "black"))

                # Load all assets (copy to media dir if needed)
                def load_asset_path(path):
                    if not path:
                        return None
                    # First try to find in media dir
                    media_path = get_media_path(path)
                    if os.path.exists(media_path):
                        return media_path
                    # Then try original path (and copy to media)
                    if os.path.exists(path):
                        return copy_to_media(path)
                    return None

                wall_texture_path = load_asset_path(data.get("wall_texture"))
                ground_texture_path = load_asset_path(data.get("ground_texture"))
                handgun_idle_path = load_asset_path(data.get("handgun_idle_texture"))
                handgun_shoot_path = load_asset_path(data.get("handgun_shoot_texture"))
                handgun_shoot_sound_path = load_asset_path(data.get("handgun_shoot_sound"))
                enemy_idle_path = load_asset_path(data.get("enemy_idle_texture"))
                enemy_shot_path = load_asset_path(data.get("enemy_shot_texture"))
                enemy_model_path = load_asset_path(data.get("enemy_model"))
                main_menu_bg_image_path = load_asset_path(data.get("main_menu_bg_image"))

                # Reload all textures
                def reload_texture(path, cell_size=None):
                    if not path:
                        return None
                    try:
                        if Image:
                            img = Image.open(path)
                            if cell_size:
                                img = img.resize((cell_size, cell_size), Image.Resampling.LANCZOS)
                            return ImageTk.PhotoImage(img)
                        return tk.PhotoImage(file=path)
                    except Exception as e:
                        print(f"Error loading texture {path}:", e)
                        return None

                wall_texture_img = reload_texture(wall_texture_path, CELL_SIZE)
                ground_texture_img = reload_texture(ground_texture_path, CELL_SIZE)
                handgun_idle_img = reload_texture(handgun_idle_path, 416)
                handgun_shoot_img = reload_texture(handgun_shoot_path, 416)
                enemy_idle_img = reload_texture(enemy_idle_path, CELL_SIZE)
                enemy_shot_img = reload_texture(enemy_shot_path, CELL_SIZE)

                # Reload sound
                if handgun_shoot_sound_path:
                    try:
                        handgun_shoot_sound = pygame.mixer.Sound(handgun_shoot_sound_path)
                    except Exception as e:
                        print("Error loading handgun sound:", e)
                        handgun_shoot_sound = None

                redraw_grid()
            else:
                print("Invalid map file format")
        except Exception as e:
            print("Error loading map:", e)

def save_main_menu():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
        title="Save Main Menu"
    )
    if file_path:
        try:
            config = {
                "title": main_menu_title_var.get(),
                "buttons": [
                    main_menu_button1_var.get(),
                    main_menu_button2_var.get(),
                    main_menu_button3_var.get()
                ],
                "alignment": main_menu_alignment.get(),
                "bg_mode": main_menu_bg_mode.get(),
                "bg_color": main_menu_bg_color.get(),
                "bg_image": os.path.basename(main_menu_bg_image_path) if main_menu_bg_image_path else None,
                "title_color": main_menu_title_color.get(),
                "button1_color": main_menu_button1_color.get(),
                "button2_color": main_menu_button2_color.get(),
                "button3_color": main_menu_button3_color.get()
            }
            with open(file_path, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print("Error saving main menu:", e)

def load_main_menu():
    global main_menu_bg_image_path
    file_path = filedialog.askopenfilename(
        defaultextension=".json",
        filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
        title="Load Main Menu"
    )
    if file_path:
        try:
            with open(file_path, "r") as f:
                config = json.load(f)

            if "title" in config and "buttons" in config:
                main_menu_title_var.set(config["title"])
                buttons = config["buttons"]
                if len(buttons) >= 3:
                    main_menu_button1_var.set(buttons[0])
                    main_menu_button2_var.set(buttons[1])
                    main_menu_button3_var.set(buttons[2])
                
                main_menu_alignment.set(config.get("alignment", "middle"))
                main_menu_bg_mode.set(config.get("bg_mode", "color"))
                main_menu_bg_color.set(config.get("bg_color", "#FFFFFF"))
                
                bg_image = config.get("bg_image")
                if bg_image:
                    main_menu_bg_image_path = get_media_path(bg_image)
                else:
                    main_menu_bg_image_path = None
                    
                main_menu_title_color.set(config.get("title_color", "blue"))
                main_menu_button1_color.set(config.get("button1_color", "black"))
                main_menu_button2_color.set(config.get("button2_color", "black"))
                main_menu_button3_color.set(config.get("button3_color", "black"))
        except Exception as e:
            print("Error loading main menu:", e)

# ------------------------------------------------------------------------------
# Main Menu Color Pickers
# ------------------------------------------------------------------------------
def choose_main_menu_bg_color():
    color = colorchooser.askcolor(title="Choose Background Color", initialcolor=main_menu_bg_color.get())
    if color[1]:
        main_menu_bg_color.set(color[1])

def choose_main_menu_title_color():
    color = colorchooser.askcolor(title="Choose Title Color", initialcolor=main_menu_title_color.get())
    if color[1]:
        main_menu_title_color.set(color[1])

def choose_main_menu_button1_color():
    color = colorchooser.askcolor(title="Choose Button 1 Color", initialcolor=main_menu_button1_color.get())
    if color[1]:
        main_menu_button1_color.set(color[1])

def choose_main_menu_button2_color():
    color = colorchooser.askcolor(title="Choose Button 2 Color", initialcolor=main_menu_button2_color.get())
    if color[1]:
        main_menu_button2_color.set(color[1])

def choose_main_menu_button3_color():
    color = colorchooser.askcolor(title="Choose Button 3 Color", initialcolor=main_menu_button3_color.get())
    if color[1]:
        main_menu_button3_color.set(color[1])

# ------------------------------------------------------------------------------
# UI Setup
# ------------------------------------------------------------------------------
root = tk.Tk()
root.title("Ray Engine Editor")

# Create main frame
main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True)

# Left panel - Main Menu Editor
main_menu_frame = tk.Frame(main_frame, width=200, bg="lightgray")
main_menu_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

tk.Label(main_menu_frame, text="Main Menu Editor", bg="lightgray", font=("Arial", 14, "bold")).pack(pady=5)

# Initialize main menu variables
main_menu_title_var = tk.StringVar(value="My Game")
main_menu_button1_var = tk.StringVar(value="Start Game")
main_menu_button2_var = tk.StringVar(value="Options")
main_menu_button3_var = tk.StringVar(value="Exit")
main_menu_alignment = tk.StringVar(value="middle")
main_menu_bg_mode = tk.StringVar(value="color")
main_menu_bg_color = tk.StringVar(value="#FFFFFF")
main_menu_title_color = tk.StringVar(value="blue")
main_menu_button1_color = tk.StringVar(value="black")
main_menu_button2_color = tk.StringVar(value="black")
main_menu_button3_color = tk.StringVar(value="black")

# Main menu UI elements
tk.Label(main_menu_frame, text="Title:", bg="lightgray").pack(anchor='w', padx=5)
tk.Entry(main_menu_frame, textvariable=main_menu_title_var).pack(fill=tk.X, padx=5, pady=2)

tk.Label(main_menu_frame, text="Button 1:", bg="lightgray").pack(anchor='w', padx=5)
tk.Entry(main_menu_frame, textvariable=main_menu_button1_var).pack(fill=tk.X, padx=5, pady=2)

tk.Label(main_menu_frame, text="Button 2:", bg="lightgray").pack(anchor='w', padx=5)
tk.Entry(main_menu_frame, textvariable=main_menu_button2_var).pack(fill=tk.X, padx=5, pady=2)

tk.Label(main_menu_frame, text="Button 3:", bg="lightgray").pack(anchor='w', padx=5)
tk.Entry(main_menu_frame, textvariable=main_menu_button3_var).pack(fill=tk.X, padx=5, pady=2)

tk.Label(main_menu_frame, text="Alignment:", bg="lightgray").pack(anchor='w', padx=5)
tk.Radiobutton(main_menu_frame, text="Left", variable=main_menu_alignment, value="left", bg="lightgray").pack(anchor='w', padx=10)
tk.Radiobutton(main_menu_frame, text="Middle", variable=main_menu_alignment, value="middle", bg="lightgray").pack(anchor='w', padx=10)
tk.Radiobutton(main_menu_frame, text="Right", variable=main_menu_alignment, value="right", bg="lightgray").pack(anchor='w', padx=10)

tk.Label(main_menu_frame, text="Background Mode:", bg="lightgray").pack(anchor='w', padx=5)
tk.Radiobutton(main_menu_frame, text="Color", variable=main_menu_bg_mode, value="color", bg="lightgray").pack(anchor='w', padx=10)
tk.Radiobutton(main_menu_frame, text="Image", variable=main_menu_bg_mode, value="image", bg="lightgray").pack(anchor='w', padx=10)

tk.Button(main_menu_frame, text="Choose Background Color", command=choose_main_menu_bg_color).pack(pady=5, padx=5, anchor='w')
tk.Button(main_menu_frame, text="Choose Background Image", command=choose_main_menu_bg_image).pack(pady=5, padx=5, anchor='w')
tk.Label(main_menu_frame, text="(Recommended: 1200x900)", bg="lightgray").pack(anchor='w', padx=5)

tk.Label(main_menu_frame, text="Title Font Color:", bg="lightgray").pack(anchor='w', padx=5)
tk.Button(main_menu_frame, text="Choose Title Color", command=choose_main_menu_title_color).pack(pady=5, padx=5, anchor='w')

tk.Label(main_menu_frame, text="Button 1 Font Color:", bg="lightgray").pack(anchor='w', padx=5)
tk.Button(main_menu_frame, text="Choose Button 1 Color", command=choose_main_menu_button1_color).pack(pady=5, padx=5, anchor='w')

tk.Label(main_menu_frame, text="Button 2 Font Color:", bg="lightgray").pack(anchor='w', padx=5)
tk.Button(main_menu_frame, text="Choose Button 2 Color", command=choose_main_menu_button2_color).pack(pady=5, padx=5, anchor='w')

tk.Label(main_menu_frame, text="Button 3 Font Color:", bg="lightgray").pack(anchor='w', padx=5)
tk.Button(main_menu_frame, text="Choose Button 3 Color", command=choose_main_menu_button3_color).pack(pady=5, padx=5, anchor='w')

tk.Button(main_menu_frame, text="Save Main Menu", command=save_main_menu).pack(pady=5, padx=5, anchor='w')
tk.Button(main_menu_frame, text="Load Main Menu", command=load_main_menu).pack(pady=5, padx=5, anchor='w')

# Center panel - Map Canvas
canvas_frame = tk.Frame(main_frame)
canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

canvas = tk.Canvas(canvas_frame, width=COLS * CELL_SIZE, height=ROWS * CELL_SIZE, bg="white")
canvas.pack(fill=tk.BOTH, expand=True)
canvas.bind("<Button-1>", canvas_click)

# Right panel - Map Controls
control_frame = tk.Frame(main_frame)
control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

tk.Label(control_frame, text="Map Editor Controls").pack(anchor='nw')

mode_var = tk.StringVar(value="wall")
tk.Radiobutton(control_frame, text="Wall", variable=mode_var, value="wall").pack(anchor='nw')
tk.Radiobutton(control_frame, text="Ground", variable=mode_var, value="ground").pack(anchor='nw')
tk.Radiobutton(control_frame, text="Spawn", variable=mode_var, value="spawn").pack(anchor='nw')
tk.Radiobutton(control_frame, text="Enemy", variable=mode_var, value="enemy").pack(anchor='nw')

# Game settings
tk.Label(control_frame, text="Game Name:").pack(anchor='nw', pady=(10, 0))
game_name_var = tk.StringVar(value="Preview")
tk.Entry(control_frame, textvariable=game_name_var).pack(fill=tk.X, padx=5, pady=2)

tk.Label(control_frame, text="Shot Delay (s):").pack(anchor='nw', pady=(10, 0))
shot_delay_var = tk.DoubleVar(value=2.2)
tk.Entry(control_frame, textvariable=shot_delay_var).pack(fill=tk.X, padx=5, pady=2)

# Win message
tk.Label(control_frame, text="Win Message:").pack(anchor='nw', pady=(10, 0))
win_message_var = tk.StringVar(value="YOU WIN!")
tk.Entry(control_frame, textvariable=win_message_var).pack(fill=tk.X, padx=5, pady=2)

tk.Label(control_frame, text="Win Message Color:").pack(anchor='nw', pady=(10, 0))
win_message_color_var = tk.StringVar(value="#00FF00")
tk.Entry(control_frame, textvariable=win_message_color_var).pack(fill=tk.X, padx=5, pady=2)
tk.Button(control_frame, text="Choose Color", command=choose_win_message_color).pack(pady=5, anchor='nw')

# Environment controls
tk.Button(control_frame, text="Choose Sky Color", command=choose_sky_color).pack(pady=5, anchor='nw')
tk.Button(control_frame, text="Choose Sun Color", command=choose_sun_color).pack(pady=5, anchor='nw')

# Texture controls
tk.Button(control_frame, text="Choose Wall Texture", command=choose_wall_texture).pack(pady=5, anchor='nw')
tk.Button(control_frame, text="Choose Ground Texture", command=choose_ground_texture).pack(pady=5, anchor='nw')

# Handgun controls
tk.Button(control_frame, text="Choose Handgun Idle", command=choose_handgun_idle_image).pack(pady=5, anchor='nw')
tk.Button(control_frame, text="Choose Handgun Shoot", command=choose_handgun_shoot_image).pack(pady=5, anchor='nw')
tk.Button(control_frame, text="Choose Shoot Sound", command=choose_handgun_shoot_sound).pack(pady=5, anchor='nw')

# Enemy controls
tk.Button(control_frame, text="Choose Enemy Idle", command=choose_enemy_idle_image).pack(pady=5, anchor='nw')
tk.Button(control_frame, text="Choose Enemy Shot", command=choose_enemy_shot_image).pack(pady=5, anchor='nw')
tk.Button(control_frame, text="Choose Enemy Model", command=choose_enemy_model).pack(pady=5, anchor='nw')

# File operations
tk.Button(control_frame, text="Test Preview", command=preview).pack(pady=5, anchor='nw')
tk.Button(control_frame, text="Save Map", command=save_map).pack(pady=5, anchor='nw')
tk.Button(control_frame, text="Load Map", command=load_map).pack(pady=5, anchor='nw')

# Initialize UI
redraw_grid()
root.mainloop()
