import os
import math  # Добавлен импорт для математических операций

import arcade
from pyglet.graphics import Batch
from pyglet.image import load as load_image

import armor
import enemies
import items
import weapons
import random

from arcade.gui import UIManager, UITextureButton, UIMessageBox
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout

if not os.path.exists('assets/levels'):
    os.makedirs('assets/levels')

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = 'KPK'


def get_shards():
    try:
        with open('data/data.txt') as file:
            return int(file.readline().rstrip('\n'))
    except Exception:
        try:
            os.mkdir('data')
        except FileExistsError:
            pass

        with open('data/data.txt', 'w') as file:
            file.writelines(['0\n'] * 6)

        return 0


def get_attrs(native=True):
    try:
        with open('data/data.txt') as file:
            fin = [int(i) for i in file.read().split('\n')[1:6]]

            if len(fin) != 5:
                raise Exception

            if native:
                return fin
            else:
                fin[0] = 1 + fin[0] * 0.1
                fin[1] = 1 + fin[1] * 0.1
                fin[3] = 1 + fin[3] * 0.1

                if fin[2] == 0:
                    fin[2] = 1
                elif fin[2] == 3:
                    fin[2] = 2
                elif fin[2] == 5:
                    fin[2] = 3

                return fin
    except Exception:
        try:
            os.mkdir('data')
        except FileExistsError:
            pass

        with open('data/data.txt', 'w') as file:
            file.writelines(['0\n'] * 6)

        if native:
            return [0] * 5
        else:
            return [1] * 5


def write_to_file(data):
    try:
        os.mkdir('data')
    except FileExistsError:
        pass

    data = [str(i) + '\n' for i in data]

    with open('data/data.txt', 'w') as file:
        file.writelines(data)


class VirtualJoystick:
    def __init__(self, center_x, center_y, outer_radius=60, inner_radius=30):
        self.center_x = center_x
        self.center_y = center_y
        self.outer_radius = outer_radius
        self.inner_radius = inner_radius
        self.inner_x = center_x
        self.inner_y = center_y
        self.is_active = False
        self.dx = 0
        self.dy = 0

    def draw(self):
        # Draw outer circle
        arcade.draw_circle_filled(self.center_x, self.center_y,
                                  self.outer_radius, (100, 100, 100, 150))
        arcade.draw_circle_outline(self.center_x, self.center_y,
                                   self.outer_radius, (200, 200, 200, 200), 2)

        # Draw inner circle
        arcade.draw_circle_filled(self.inner_x, self.inner_y,
                                  self.inner_radius, (150, 150, 150, 200))
        arcade.draw_circle_outline(self.inner_x, self.inner_y,
                                   self.inner_radius, (255, 255, 255, 255), 2)

    def activate(self, x, y):
        if arcade.math.get_distance(x, y, self.center_x, self.center_y) <= self.outer_radius:
            self.is_active = True
            self.update_position(x, y)
            return True
        return False

    def update_position(self, x, y):
        if self.is_active:
            # Calculate distance from center
            dx = x - self.center_x
            dy = y - self.center_y
            distance = arcade.math.get_distance(x, y, self.center_x, self.center_y)

            # Limit to outer radius
            if distance > self.outer_radius:
                angle = math.atan2(dy, dx)
                dx = math.cos(angle) * self.outer_radius
                dy = math.sin(angle) * self.outer_radius
                self.inner_x = self.center_x + dx
                self.inner_y = self.center_y + dy
            else:
                self.inner_x = x
                self.inner_y = y

            # Normalize values to -1 to 1 range
            self.dx = dx / self.outer_radius
            self.dy = dy / self.outer_radius

    def deactivate(self):
        self.is_active = False
        self.inner_x = self.center_x
        self.inner_y = self.center_y
        self.dx = 0
        self.dy = 0

    def get_vector(self):
        return (self.dx, self.dy)


class TouchButton:
    def __init__(self, x, y, width, height, text, color=(100, 100, 100, 200),
                 pressed_color=(150, 150, 150, 200), text_color=arcade.color.WHITE):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.color = color
        self.pressed_color = pressed_color
        self.text_color = text_color
        self.is_pressed = False
        self.was_pressed = False

    def draw(self):
        color = self.pressed_color if self.is_pressed else self.color

        # Draw button background
        arcade.draw_lbwh_rectangle_filled(self.x, self.y, self.width, self.height, color)
        arcade.draw_lbwh_rectangle_outline(self.x, self.y, self.width, self.height,
                                           arcade.color.WHITE, 2)

        # Draw text
        arcade.draw_text(self.text, self.x, self.y, self.text_color,
                         font_size=self.height // 2, anchor_x='center',
                         anchor_y='center', bold=True)

    def check_press(self, x, y):
        left = self.x - self.width / 2
        right = self.x + self.width / 2
        bottom = self.y - self.height / 2
        top = self.y + self.height / 2

        if left <= x <= right and bottom <= y <= top:
            self.is_pressed = True
            return True
        return False

    def check_release(self):
        if self.is_pressed and not self.was_pressed:
            self.was_pressed = True
            return True
        self.was_pressed = self.is_pressed
        return False

    def reset(self):
        self.is_pressed = False
        self.was_pressed = False


class MobileControls:
    def __init__(self, game_view):
        self.game_view = game_view
        self.show_controls = True

        # Создаем джойстики согласно схеме
        # MVJ в левом нижнем углу, SHJ в правом нижнем углу
        self.move_joystick = VirtualJoystick(100, 100)  # MVJ - левый нижний угол
        self.shoot_joystick = VirtualJoystick(SCREEN_WIDTH - 100, 100)  # SHJ - правый нижний угол

        # Размеры кнопок согласно схеме 5x5
        button_size = 50
        button_spacing = 5

        # Рассчитываем позиции для сетки 5x5
        grid_width = SCREEN_WIDTH
        grid_height = 200  # Высота области с кнопками
        grid_y_start = 200  # Отступ снизу

        # Ширина одной ячейки в сетке
        cell_width = grid_width // 5

        # Создаем кнопки согласно схеме:
        # Строка 1: [Esc, пусто, пусто, пусто, E]
        # Строка 2: [Q, пусто, пусто, пусто, Y]
        # Строка 3: [Z, пусто, пусто, пусто, X]
        # Строка 4: [MVJ, SET, SPACE, ENTER, SHJ]

        # Строка 1 (верхняя)
        esc_x = cell_width * 0.5  # Колонка 1
        e_x = cell_width * 4.5  # Колонка 5
        row1_y = grid_y_start + grid_height - button_size - button_spacing

        self.esc_button = TouchButton(esc_x, row1_y, button_size, button_size, "Esc")
        self.e_button = TouchButton(e_x, row1_y, button_size, button_size, "E")

        # Строка 2
        q_x = cell_width * 0.5  # Колонка 1
        y_x = cell_width * 4.5  # Колонка 5
        row2_y = row1_y - button_size - button_spacing * 2

        self.q_button = TouchButton(q_x, row2_y, button_size, button_size, "Q")
        self.y_button = TouchButton(y_x, row2_y, button_size, button_size, "Y")

        # Строка 3
        z_x = cell_width * 0.5  # Колонка 1
        x_x = cell_width * 4.5  # Колонка 5
        row3_y = row2_y - button_size - button_spacing * 2

        self.z_button = TouchButton(z_x, row3_y, button_size, button_size, "Z")
        self.x_button = TouchButton(x_x, row3_y, button_size, button_size, "X")

        # Строка 4 (нижняя - с джойстиками и спец кнопками)
        set_x = cell_width * 1.5  # Колонка 2 - SET
        space_x = cell_width * 2.5  # Колонка 3 - SPACE
        enter_x = cell_width * 3.5  # Колонка 4 - ENTER
        row4_y = row3_y - button_size - button_spacing * 2

        # Создаем специальные кнопки для строки 4
        self.settings_button = TouchButton(set_x, row4_y, button_size, button_size, "⚙",
                                           text_color=arcade.color.WHITE)
        self.space_button = TouchButton(space_x, row4_y, button_size, button_size, "Space")
        self.enter_button = TouchButton(enter_x, row4_y, button_size, button_size, "Enter")

        self.buttons = [
            self.q_button, self.e_button, self.y_button,
            self.z_button, self.x_button, self.esc_button,
            self.enter_button, self.space_button
        ]

        # Settings panel
        self.show_settings = False
        self.settings_panel = None

    def draw(self):
        if not self.show_controls:
            return

        # Draw joysticks (в их оригинальных позициях, не в сетке)
        self.move_joystick.draw()
        self.shoot_joystick.draw()

        # Draw buttons
        for button in self.buttons:
            button.draw()

        # Draw settings button
        self.settings_button.draw()

        # Draw settings panel if open
        if self.show_settings and self.settings_panel:
            self.settings_panel.draw()

    def on_update(self, delta_time):
        if not self.show_controls:
            return

        # Handle movement from joystick
        if self.move_joystick.is_active:
            dx, dy = self.move_joystick.get_vector()

            # Convert to key presses - безопасно обрабатываем разные типы вьюх
            if hasattr(self.game_view, 'keys'):
                if abs(dx) > 0.2 or abs(dy) > 0.2:
                    if dx > 0.2 and arcade.key.D not in self.game_view.keys:
                        self.game_view.keys.add(arcade.key.D)
                    elif dx < -0.2 and arcade.key.A not in self.game_view.keys:
                        self.game_view.keys.add(arcade.key.A)
                    else:
                        self.game_view.keys.discard(arcade.key.D)
                        self.game_view.keys.discard(arcade.key.A)

                    if dy > 0.2 and arcade.key.W not in self.game_view.keys:
                        self.game_view.keys.add(arcade.key.W)
                    elif dy < -0.2 and arcade.key.S not in self.game_view.keys:
                        self.game_view.keys.add(arcade.key.S)
                    else:
                        self.game_view.keys.discard(arcade.key.W)
                        self.game_view.keys.discard(arcade.key.S)

        # Handle shooting from joystick - только для Game класса
        if self.shoot_joystick.is_active and isinstance(self.game_view, Game):
            dx, dy = self.shoot_joystick.get_vector()
            if abs(dx) > 0.2 or abs(dy) > 0.2:
                # Calculate target position for shooting
                player = self.game_view.player
                target_x = player.center_x + dx * 500
                target_y = player.center_y + dy * 500
                player.attack(target_x, target_y)

        # Handle button presses - безопасно для разных вьюх
        if self.q_button.check_release():
            # Для Game класса
            if isinstance(self.game_view, Game):
                if not getattr(self.game_view, 'game_over', False):
                    if getattr(self.game_view, 'showing_item', None) is None:
                        item = self.game_view.player.get_item()
                        if item is not None:
                            # Simulate Q key press
                            self.game_view.on_key_press(arcade.key.Q, 0)
                    else:
                        # Если показывается предмет, Q для выхода
                        self.game_view.on_key_press(arcade.key.Q, 0)
            # Для других вьюх
            elif hasattr(self.game_view, 'on_key_press'):
                self.game_view.on_key_press(arcade.key.Q, 0)

        if self.e_button.check_release():
            if isinstance(self.game_view, Game):
                if not getattr(self.game_view, 'game_over', False):
                    if getattr(self.game_view, 'showing_item', None) is None:
                        self.game_view.player.next_item()
            elif hasattr(self.game_view, 'on_key_press'):
                self.game_view.on_key_press(arcade.key.E, 0)

        if self.y_button.check_release():
            if isinstance(self.game_view, Game):
                if not getattr(self.game_view, 'game_over', False):
                    if getattr(self.game_view, 'showing_item', None) is None:
                        if not self.game_view.enemy_list.sprite_list:
                            self.game_view.toggle_level_completion()
            elif hasattr(self.game_view, 'on_key_press'):
                self.game_view.on_key_press(arcade.key.Y, 0)

        if self.z_button.check_release():
            if isinstance(self.game_view, Game):
                if not getattr(self.game_view, 'game_over', False):
                    if getattr(self.game_view, 'showing_item', None) is None:
                        self.game_view.player.drop_item()
            elif hasattr(self.game_view, 'on_key_press'):
                self.game_view.on_key_press(arcade.key.Z, 0)

        if self.x_button.check_release():
            if isinstance(self.game_view, Game):
                if not getattr(self.game_view, 'game_over', False):
                    if getattr(self.game_view, 'showing_item', None) is None:
                        self.game_view.player.drop_armor()
            elif hasattr(self.game_view, 'on_key_press'):
                self.game_view.on_key_press(arcade.key.X, 0)

        if self.esc_button.check_release():
            if hasattr(self.game_view, 'on_key_press'):
                self.game_view.on_key_press(arcade.key.ESCAPE, 0)

        if self.enter_button.check_release():
            if hasattr(self.game_view, 'on_key_press'):
                self.game_view.on_key_press(arcade.key.ENTER, 0)

        if self.space_button.check_release():
            if hasattr(self.game_view, 'on_key_press'):
                self.game_view.on_key_press(arcade.key.SPACE, 0)

        if self.settings_button.check_release():
            self.toggle_settings()

    def on_touch_down(self, x, y):
        if not self.show_controls:
            return False

        # Check joysticks first (они перекрывают кнопки MVJ/SHJ)
        if self.move_joystick.activate(x, y):
            return True
        if self.shoot_joystick.activate(x, y):
            return True

        # Check settings button
        if self.settings_button.check_press(x, y):
            return True

        # Check other buttons
        for button in self.buttons:
            if button.check_press(x, y):
                return True

        # Check settings panel if open
        if self.show_settings and self.settings_panel:
            return self.settings_panel.on_touch_down(x, y)

        return False

    def on_touch_move(self, x, y):
        if not self.show_controls:
            return

        # Update joystick positions
        self.move_joystick.update_position(x, y)
        self.shoot_joystick.update_position(x, y)

        # Update settings panel if open
        if self.show_settings and self.settings_panel:
            self.settings_panel.on_touch_move(x, y)

    def on_touch_up(self, x, y):
        if not self.show_controls:
            return

        # Deactivate joysticks
        self.move_joystick.deactivate()
        self.shoot_joystick.deactivate()

        # Reset all buttons
        for button in self.buttons:
            button.reset()
        self.settings_button.reset()

        # Reset movement keys when joystick is released
        if hasattr(self.game_view, 'keys'):
            self.game_view.keys.discard(arcade.key.W)
            self.game_view.keys.discard(arcade.key.S)
            self.game_view.keys.discard(arcade.key.A)
            self.game_view.keys.discard(arcade.key.D)

        # Update settings panel if open
        if self.show_settings and self.settings_panel:
            self.settings_panel.on_touch_up(x, y)

    def toggle_settings(self):
        self.show_settings = not self.show_settings
        if self.show_settings:
            self.create_settings_panel()

    def create_settings_panel(self):
        # Create a simple settings panel for control visibility
        panel_width = 300
        panel_height = 200

        class SettingsPanel:
            def __init__(self, controls):
                self.controls = controls
                self.x = SCREEN_WIDTH // 2
                self.y = SCREEN_HEIGHT // 2
                self.width = panel_width
                self.height = panel_height

                # Close button
                self.close_button = TouchButton(self.x + panel_width // 2 - 30,
                                                self.y + panel_height // 2 - 30,
                                                50, 30, "X",
                                                color=(200, 50, 50, 200))

                # Toggle button
                self.toggle_button = TouchButton(self.x, self.y,
                                                 panel_width - 60, 40,
                                                 "Скрыть контролы" if controls.show_controls else "Показать контролы",
                                                 color=(50, 150, 50, 200))

            def draw(self):
                # Draw background
                arcade.draw_lbwh_rectangle_filled(self.x, self.y, self.width, self.height,
                                                  (50, 50, 50, 230))
                arcade.draw_lbwh_rectangle_outline(self.x, self.y, self.width, self.height,
                                                   arcade.color.WHITE, 3)

                # Draw title
                arcade.draw_text("Настройки", self.x, self.y + panel_height // 2 - 20,
                                 arcade.color.WHITE, 20, anchor_x='center')

                # Draw buttons
                self.close_button.draw()
                self.toggle_button.draw()

            def on_touch_down(self, x, y):
                if self.close_button.check_press(x, y):
                    return True
                if self.toggle_button.check_press(x, y):
                    return True
                return False

            def on_touch_move(self, x, y):
                pass

            def on_touch_up(self, x, y):
                if self.close_button.check_release():
                    self.controls.show_settings = False
                    return True
                if self.toggle_button.check_release():
                    self.controls.show_controls = not self.controls.show_controls
                    self.toggle_button.text = "Скрыть контролы" if self.controls.show_controls else "Показать контролы"
                    return True
                return False

        self.settings_panel = SettingsPanel(self)


class StartScreen(arcade.View):
    def __init__(self):
        super().__init__()
        self.batch = Batch()
        self.mobile_controls = MobileControls(self)  # Добавлено
        self.setup()

    def setup(self):
        game_name = 'KPK'

        self.phone_texture = arcade.load_texture('assets/images/gui/start_picture.png')
        self.phone_rect = arcade.Rect(0, self.width, 0, self.height, self.width, self.height, self.width / 2,
                                      self.height / 2)
        self.button_texture = arcade.load_texture('assets/images/gui/start_button.png')
        self.button_texture_hovered = arcade.load_texture('assets/images/gui/hovered_start_button.png')

        self.text = arcade.Text(game_name, SCREEN_WIDTH / 2, 530, arcade.color.WHITE, 40, batch=self.batch,
                                align="center")

        self.manager = UIManager()
        self.manager.enable()

        self.anchor_layout = UIAnchorLayout(x=150, y=100)
        self.box_layout = UIBoxLayout(horizontal=True, space_between=20)

        self.setup_widgets()

        self.anchor_layout.add(self.box_layout)
        self.manager.add(self.anchor_layout)

    def setup_widgets(self):
        self.start_button = UITextureButton(texture=self.button_texture, texture_hovered=self.button_texture_hovered,
                                            text='Старт')
        self.start_button.on_click = self.start_game
        self.box_layout.add(self.start_button)

    def on_draw(self):
        self.clear()

        arcade.draw_texture_rect(self.phone_texture, self.phone_rect)
        self.batch.draw()
        self.manager.draw()

        # Draw mobile controls
        if self.mobile_controls:
            self.mobile_controls.draw()

    def start_game(self, *args):
        game = StartLocation()
        game.setup()
        self.manager.disable()
        self.window.show_view(game)

    def on_update(self, delta_time):
        if self.mobile_controls:
            self.mobile_controls.on_update(delta_time)

    # Touch events for mobile controls
    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            if self.mobile_controls and self.mobile_controls.on_touch_down(x, y):
                return

    def on_mouse_motion(self, x, y, dx, dy):
        if self.mobile_controls:
            self.mobile_controls.on_touch_move(x, y)

    def on_mouse_release(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            if self.mobile_controls:
                self.mobile_controls.on_touch_up(x, y)


class StartLocation(arcade.View):
    def __init__(self):
        super().__init__()
        self.batch = Batch()
        self.mobile_controls = None
        self.keys = set()  # Добавлено для поддержки управления

    def setup(self):
        self.tilemap = arcade.load_tilemap('assets/tilesets/start_tilemap.tmx', 0.75)

        self.base_tiles = self.tilemap.sprite_lists['base']
        self.collision_tiles = self.tilemap.sprite_lists['collision']
        self.start_tiles = self.tilemap.sprite_lists['start_tiles']
        self.upgrade_tiles = self.tilemap.sprite_lists['upgrade_tiles']

        self.world_width = int(self.tilemap.width * self.tilemap.tile_width * 0.75)
        self.world_height = int(self.tilemap.height * self.tilemap.tile_height * 0.75)

        self.star_sky_texture = arcade.load_texture('assets/tilesets/star_sky.png')
        self.phone_rect = arcade.Rect(0, self.world_width, 200, self.world_height + 200, self.world_width,
                                      self.world_height, self.world_width / 2, self.world_height / 2 + 100)

        self.player_list = arcade.SpriteList()
        self.player = arcade.Sprite('assets/images/player/players/default-player.png', 0.5, 875, 650)
        self.player_list.append(self.player)

        self.text = arcade.Text('Нажмите Q, чтобы взаимодействовать.', self.player.center_x, self.player.center_y + 70,
                                font_size=18, anchor_x='center',
                                anchor_y='center', batch=self.batch)

        self.physics_engine = arcade.PhysicsEngineSimple(self.player, self.collision_tiles)

        self.world_camera = arcade.camera.Camera2D()
        self.world_camera.position = self.player.position

        self.music = arcade.load_sound('assets/music/menu.mp3')
        self.music_player = self.music.play(1, loop=True)

        self.upgrade_pos = (1080, 804)
        self.start_pos = (864, 1200)

        self.keys = set()
        self.speed = 125
        self.stop_game = False

        self.manager = UIManager()
        self.manager.enable()

        # Initialize mobile controls
        self.mobile_controls = MobileControls(self)

    def on_draw(self):
        self.clear()

        self.world_camera.use()
        arcade.draw_texture_rect(self.star_sky_texture, self.phone_rect)
        self.base_tiles.draw()
        self.start_tiles.draw()
        self.upgrade_tiles.draw()
        self.batch.draw()
        self.player_list.draw()

        self.manager.draw()

        # Draw mobile controls on GUI camera
        self.gui_camera = arcade.camera.Camera2D()
        self.gui_camera.use()
        if self.mobile_controls:
            self.mobile_controls.draw()

    def on_update(self, delta_time):
        if not self.stop_game:
            self.physics_engine.update()

            position = (self.player.center_x, self.player.center_y)
            self.world_camera.position = arcade.math.lerp_2d(self.world_camera.position, position, 0.12)

            move_x = move_y = 0

            if arcade.key.W in self.keys:
                move_y += self.speed
            if arcade.key.S in self.keys:
                move_y -= self.speed
            if arcade.key.D in self.keys:
                move_x += self.speed
            if arcade.key.A in self.keys:
                move_x -= self.speed

            self.player.center_x += move_x * delta_time
            self.player.center_y += move_y * delta_time

        # Update mobile controls
        if self.mobile_controls:
            self.mobile_controls.on_update(delta_time)

    def on_key_press(self, symbol, modifiers):
        self.keys.add(symbol)

        if not self.stop_game:
            if symbol == arcade.key.ESCAPE:
                arcade.stop_sound(self.music_player)
                self.world_camera.position = self.width / 2, self.height / 2
                game = StartScreen()
                self.manager.disable()
                self.window.show_view(game)
            elif symbol == arcade.key.Q:
                if arcade.math.get_distance(*self.player.position, *self.upgrade_pos) <= 100:
                    self.keys = set()
                    self.world_camera.position = self.width / 2, self.height / 2
                    self.window.show_view(UpgradeScreen(self))
                elif arcade.math.get_distance(*self.player.position, *self.start_pos) <= 100:
                    self.pre_start()

    def on_key_release(self, symbol, modifiers):
        self.keys.discard(symbol)

    def return_to_game(self):
        self.world_camera.position = self.player.position

    def pre_start(self):
        self.stop_game = True

        message_box = UIMessageBox(
            width=300, height=200,
            message_text="Начать игру?",
            buttons=("Да", "Нет")
        )
        message_box.on_action = self.make_choice_start
        self.manager.add(message_box)

    def make_choice_start(self, event):
        if event.action == 'Да':
            self.start()
        else:
            self.stop_game = False

    def start(self):
        arcade.stop_sound(self.music_player)
        mods = get_attrs(False)

        upgrade_shards = get_shards()
        modifiers = {}

        for key, value in zip(['damage', 'health', 'inventory', 'speed', 'lucky'], mods):
            modifiers[key] = value

        color = arcade.color.BLACK.from_iterable(
            (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        mapp = random.choice(["map1.tmx", "map2.tmx"])

        game = Game(mapp, 0, upgrade_shards, modifiers, [(weapons.OldPistol, 5)], (None, 1), 20, 1, color)
        self.window.show_view(game)

    # Touch events for mobile controls
    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            if self.mobile_controls:
                if self.mobile_controls.on_touch_down(x, y):
                    return

    def on_mouse_motion(self, x, y, dx, dy):
        if self.mobile_controls:
            self.mobile_controls.on_touch_move(x, y)

    def on_mouse_release(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            if self.mobile_controls:
                self.mobile_controls.on_touch_up(x, y)


class UpgradeScreen(arcade.View):
    def __init__(self, game):
        super().__init__()
        self.upgrade_shards = get_shards()
        self.batch = Batch()
        self.game = game
        self.mobile_controls = None
        self.setup()

    def setup(self):
        self.bg = arcade.load_texture('assets/images/gui/upgrade_screen.png')
        self.bg_pos = arcade.Rect(0, self.width, 0, self.height, self.width, self.height, self.width / 2,
                                  self.height / 2)

        self.attrs = get_attrs()

        self.coords = ((140, 470), (140, 296), (140, 122), (524, 470), (524, 296))
        self.texts = []

        self.button_texture = arcade.load_texture('assets/images/gui/start_button.png')
        self.button_texture_hovered = arcade.load_texture('assets/images/gui/hovered_start_button.png')

        self.upgrade_shard_texture = arcade.load_texture('assets/images/items/upgrade_crystal.png')

        self.manager = UIManager()
        self.manager.enable()

        self.anchor_layout = UIAnchorLayout(x=-80, y=-45)
        self.box_layout = UIBoxLayout(vertical=True, space_between=140)

        self.upgrade_damage_button = UITextureButton(texture=self.button_texture,
                                                     texture_hovered=self.button_texture_hovered, text='Улучшить',
                                                     scale=0.6)
        self.upgrade_damage_button.on_click = self.upgrade_damage
        self.box_layout.add(self.upgrade_damage_button)

        self.upgrade_health_button = UITextureButton(texture=self.button_texture,
                                                     texture_hovered=self.button_texture_hovered, text='Улучшить',
                                                     scale=0.6)
        self.upgrade_health_button.on_click = self.upgrade_health
        self.box_layout.add(self.upgrade_health_button)

        self.upgrade_backpack_button = UITextureButton(texture=self.button_texture,
                                                       texture_hovered=self.button_texture_hovered, text='Улучшить',
                                                       scale=0.6)
        self.upgrade_backpack_button.on_click = self.upgrade_backpack
        self.box_layout.add(self.upgrade_backpack_button)

        self.anchor_layout2 = UIAnchorLayout(x=310, y=45)
        self.box_layout2 = UIBoxLayout(vertical=True, space_between=140)

        self.upgrade_speed_button = UITextureButton(texture=self.button_texture,
                                                    texture_hovered=self.button_texture_hovered, text='Улучшить',
                                                    scale=0.6)
        self.upgrade_speed_button.on_click = self.upgrade_speed
        self.box_layout2.add(self.upgrade_speed_button)

        self.upgrade_luck_button = UITextureButton(texture=self.button_texture,
                                                   texture_hovered=self.button_texture_hovered, text='Улучшить',
                                                   scale=0.6)
        self.upgrade_luck_button.on_click = self.upgrade_luck
        self.box_layout2.add(self.upgrade_luck_button)

        self.exit_button = UITextureButton(x=10, y=560, texture=self.button_texture,
                                           texture_hovered=self.button_texture_hovered, text='Назад', scale=0.4)
        self.exit_button.on_click = self.exit_act
        self.manager.add(self.exit_button)

        self.anchor_layout.add(self.box_layout)
        self.anchor_layout2.add(self.box_layout2)
        self.manager.add(self.anchor_layout)
        self.manager.add(self.anchor_layout2)

        # Initialize mobile controls
        self.mobile_controls = MobileControls(self)

    def on_draw(self):
        self.clear()

        for (x, y), level in zip(self.coords, self.attrs):
            if level == 0:
                width = 0
            elif level == 1:
                width = 37
            elif level == 2:
                width = 86
            elif level == 3:
                width = 130
            elif level == 4:
                width = 186
            elif level == 5:
                width = 250

            height = 10

            arcade.draw_rect_filled(
                arcade.Rect(x, x + width, y, y + height, width, height, x + width / 2, y + height / 2),
                arcade.color.LIME_GREEN)

        arcade.draw_texture_rect(self.bg, self.bg_pos)

        curr_text = 0
        self.texts.clear()

        for x, y in self.coords:
            if self.attrs[curr_text] != 5:
                if curr_text != 2:
                    num = self.attrs[curr_text] + 1
                else:
                    if self.attrs[curr_text] == 0:
                        num = 2
                    else:
                        num = 5
            else:
                num = '?'

            x += 73
            y -= 50
            arcade.draw_texture_rect(self.upgrade_shard_texture,
                                     arcade.Rect(x, x + 30, y, y + 30, 30, 30, x + 15, y + 15), pixelated=True)
            curr_text += 1

            self.texts.append(arcade.Text(str(num), x - 5, y, font_size=25, anchor_x='right', batch=self.batch))

        x = 750
        y = 560

        arcade.draw_texture_rect(self.upgrade_shard_texture, arcade.Rect(x, x + 30, y, y + 30, 30, 30, x + 15, y + 15),
                                 pixelated=True)
        self.texts.append(
            arcade.Text(str(self.upgrade_shards), x - 5, y, font_size=25, anchor_x='right', batch=self.batch))

        self.manager.draw()
        self.batch.draw()

        # Draw mobile controls
        if self.mobile_controls:
            self.mobile_controls.draw()

    def on_update(self, delta_time):
        if self.mobile_controls:
            self.mobile_controls.on_update(delta_time)

    def upgrade_damage(self, *args):
        summ = self.attrs[0] + 1

        if self.attrs[0] < 5:
            if self.upgrade_shards >= summ:
                self.attrs[0] += 1
                self.upgrade_shards -= summ

    def upgrade_health(self, *args):
        summ = self.attrs[1] + 1

        if self.attrs[1] < 5:
            if self.upgrade_shards >= summ:
                self.attrs[1] += 1
                self.upgrade_shards -= summ

    def upgrade_backpack(self, *args):
        if self.attrs[2] == 0:
            summ = 2
        else:
            summ = 5

        if self.attrs[2] < 5:
            if self.upgrade_shards >= summ:
                if self.attrs[2] == 0:
                    self.attrs[2] = 3
                else:
                    self.attrs[2] = 5
                self.upgrade_shards -= summ

    def upgrade_speed(self, *args):
        summ = self.attrs[3] + 1

        if self.attrs[3] < 5:
            if self.upgrade_shards >= summ:
                self.attrs[3] += 1
                self.upgrade_shards -= summ

    def upgrade_luck(self, *args):
        summ = self.attrs[4] + 1

        if self.attrs[4] < 5:
            if self.upgrade_shards >= summ:
                self.attrs[4] += 1
                self.upgrade_shards -= summ

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ESCAPE:
            self.exit_act()

    def exit_act(self, *args):
        write_to_file([self.upgrade_shards] + self.attrs)
        self.game.return_to_game()
        self.manager.disable()
        self.window.show_view(self.game)

    # Touch events for mobile controls
    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            if self.mobile_controls:
                self.mobile_controls.on_touch_down(x, y)

    def on_mouse_motion(self, x, y, dx, dy):
        if self.mobile_controls:
            self.mobile_controls.on_touch_move(x, y)

    def on_mouse_release(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            if self.mobile_controls:
                self.mobile_controls.on_touch_up(x, y)


class Player(arcade.Sprite):
    def __init__(self, texture, x, y, scale, money, upgrade_crystals, weapons_list, armor_list, bullets_list,
                 enemies_list, items_list, emitters, modifiers={}):
        super().__init__(texture, scale, x, y)
        self.modifiers = modifiers
        self.weapon = None
        self.armor = None
        self.max_health = 10 * modifiers.get('health', 1)
        self.health = self.max_health
        self.weapons_list = weapons_list
        self.bullets_list = bullets_list
        self.enemies_list = enemies_list
        self.emitters = emitters
        self.items_list = items_list
        self.armor_list = armor_list
        self.speed = 6500 * modifiers.get('speed', 1)
        self.money = money
        self.upgrade_crystals = upgrade_crystals

        self.inventory = [None] * modifiers.get('inventory', 1)
        self.curr_slot = 0

    def update(self, delta_time, keys):
        move_x = move_y = 0

        if arcade.key.W in keys:
            move_y += self.speed
        if arcade.key.S in keys:
            move_y -= self.speed
        if arcade.key.D in keys:
            move_x += self.speed
        if arcade.key.A in keys:
            move_x -= self.speed

        self.physics_engines[0].apply_force(self, (move_x, move_y))

        if self.weapon is not None:
            self.weapon.update(delta_time)

        if self.armor is not None:
            self.armor.update(delta_time)

    def attack(self, x, y):
        if self.weapon is not None:
            self.weapon.attack(x, y)

    def set_weapon(self, weapon):
        if self.weapon is not None:
            self.weapon.kill()

        self.weapon = weapon

        if self.weapon is not None:
            self.weapon.return_to_live()
            self.weapons_list.append(self.weapon)

    def hurt(self, damage):
        if self.health > 0:
            self.health -= damage

            if self.health <= 0:
                self.kill()
                self.health = 0

    def heal(self, health):
        self.health = min([self.max_health, self.health + health])

    def kill(self):
        super().kill()

        if self.weapon is not None:
            self.weapon.kill()

        if self.armor is not None:
            self.armor.kill()

    def next_item(self):
        if self.health > 0:
            self.curr_slot += 1
            self.curr_slot %= len(self.inventory)

            try:
                for bullet in self.weapon.bullets_list.sprite_list:
                    bullet.kill()
            except AttributeError:
                pass

            self.set_weapon(self.inventory[self.curr_slot])

    def set_weapon_slot(self, weapon, slot):
        self.inventory[slot] = weapon

        if slot == self.curr_slot:
            self.set_weapon(weapon)

    def get_item(self):
        itemss = sorted(self.items_list.sprite_list, key=lambda x: x.get_distance())

        if itemss:
            if itemss[0].get_distance() <= 100:
                return itemss[0]

    def drop_item(self):
        if self.health > 0:
            if self.inventory[self.curr_slot] is not None:
                self.items_list.append(
                    items.WeaponItem(self.inventory[self.curr_slot].__class__, self.center_x, self.center_y, self,
                                     self.inventory[self.curr_slot].level))
                self.set_weapon_slot(None, self.curr_slot)

    def set_armor(self, armor):
        if self.armor is not None:
            self.armor.unapply_health()
            self.armor.kill()

        self.armor = armor

        if self.armor is not None:
            self.armor.apply_health()
            self.armor_list.append(armor)

    def drop_armor(self):
        if self.health > 0:
            if self.armor is not None:
                self.items_list.append(
                    items.ArmorItem(self.armor.__class__, self.center_x, self.center_y, self, self.armor.level))
                self.set_armor(None)


class Game(arcade.View):
    def __init__(self, map_name, money, upgrade_crystals, modifiers, weapons, armor, hp, level, color, level_id=1):
        super().__init__()

        self.current_level_id = level_id

        self.player_list = arcade.SpriteList()
        self.walls = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList(True)
        self.weapons_list = arcade.SpriteList()
        self.bullets_list = []
        self.items_list = arcade.SpriteList()
        self.armor_list = arcade.SpriteList()
        self.walls_list = arcade.SpriteList()
        self.phone_list = arcade.SpriteList()
        self.join_triggers = arcade.SpriteList()

        self.emitters = []

        self.batch = Batch()
        self.hint_batch = Batch()

        self.physics_engine = arcade.PymunkPhysicsEngine(damping=0)

        self.health_bar_texture = arcade.load_texture('assets/images/gui/health_bar.png')
        self.slot_texture = arcade.load_texture('assets/images/gui/slot.png')
        self.gui_rarities = [arcade.load_texture('assets/images/gui/usual_item_gui.png'),
                             arcade.load_texture('assets/images/gui/unusual_item_gui.png'),
                             arcade.load_texture('assets/images/gui/rare_item_gui.png'),
                             arcade.load_texture('assets/images/gui/epic_item_gui.png'),
                             arcade.load_texture('assets/images/gui/legendary_item_gui.png')]
        self.texts = []

        self.showing_item = None
        self.chosen_item = None

        self.color = color
        self.level = level

        self.world_camera = arcade.Camera2D()
        self.gui_camera = arcade.Camera2D()

        self.game_over = False

        # Initialize mobile controls
        self.mobile_controls = MobileControls(self)

        self.setup_map(map_name, money, upgrade_crystals, modifiers, weapons, armor, hp)

    def on_update(self, delta_time):
        if self.showing_item is None and not self.game_over:
            self.enemy_list.update(delta_time)

            emitters_copy = self.emitters.copy()
            for e in emitters_copy:
                e.update(delta_time)
            for e in emitters_copy:
                if e.can_reap():
                    self.emitters.remove(e)

            self.physics_engine.step(delta_time)
            self.player_list.update(delta_time, self.keys)

            position = (self.player.center_x, self.player.center_y)
            self.world_camera.position = arcade.math.lerp_2d(self.world_camera.position, position, 0.12)

            self.check_join_triggers()

            if self.player.health <= 0:
                self.game_over = True
                self.game_over_text = arcade.Text('Игра окончена! Нажмите ESC для выхода.', self.width / 2,
                                                  self.height / 3 * 2, font_size=27, anchor_x='center',
                                                  anchor_y='center', batch=self.batch)

        # Update mobile controls
        if self.mobile_controls:
            self.mobile_controls.on_update(delta_time)

    def check_join_triggers(self):
        for i in arcade.check_for_collision_with_list(self.player, self.join_triggers):
            room = i.room

            for enemy in self.enemy_list.sprite_list:
                try:
                    if enemy.room == room:
                        enemy.active = True
                except Exception:
                    continue

    def on_draw(self):
        self.clear()

        self.world_camera.use()
        self.phone_list.draw()
        self.walls_list.draw()
        self.hint_batch.draw()

        for e in self.emitters:
            e.draw()

        self.items_list.draw()
        self.player_list.draw()
        self.armor_list.draw()
        self.enemy_list.draw()

        for i in self.bullets_list:
            i.draw()

        self.weapons_list.draw()

        self.gui_camera.use()
        self.draw_gui()
        self.batch.draw()

        # Draw mobile controls
        if self.mobile_controls:
            self.mobile_controls.draw()

    def draw_gui(self):
        rect = arcade.Rect(550, SCREEN_WIDTH, 0, 70, 250, 70, 675, 35)
        arcade.draw_texture_rect(self.health_bar_texture, rect)

        hp_width = 210 * (self.player.health / self.player.max_health)

        rect = arcade.Rect(570, SCREEN_WIDTH - 230 + hp_width, 23, 56, hp_width, 33, 570 + hp_width / 2, 35)
        arcade.draw_rect_filled(rect, arcade.color.RED)

        for i in range(len(self.player.inventory)):
            rect = arcade.Rect(i * 70, i * 70 + 70, 0, 70, 70, 70, i * 70 + 35, 35)
            arcade.draw_texture_rect(self.slot_texture, rect)

            if self.player.inventory[i] is not None:
                try:
                    texture = self.player.inventory[i].source_texture
                except AttributeError:
                    texture = self.player.inventory[i].texture

                arcade.draw_texture_rect(texture, rect)

            if i == self.player.curr_slot:
                rect_f = rect

        arcade.draw_rect_outline(rect_f, arcade.color.SEA_BLUE, 3)

        self.hp_text = arcade.Text(f'{round(self.player.health)}/{round(self.player.max_health)}', 675, 35,
                                   arcade.color.WHITE, 20, anchor_x='center', anchor_y='center', batch=self.batch)

        if self.showing_item is not None:
            self.draw_item()

    def on_key_press(self, symbol, modifiers):
        self.keys.add(symbol)

        if self.showing_item is None and not self.game_over:
            if symbol == arcade.key.E:
                self.player.next_item()
            elif symbol == arcade.key.Q:
                item = self.player.get_item()

                if item is not None:
                    if type(item) is items.WeaponItem:
                        if self.player.inventory[self.player.curr_slot] is None:
                            self.chosen_item = item
                            self.showing_item = item.weapon(self.player, item.level)
                    elif type(item) is items.ArmorItem:
                        if self.player.armor is None:
                            self.chosen_item = item
                            self.showing_item = item.armor(self.player, item.level)
                    elif type(item) is items.BoughtWeapon:
                        if self.player.inventory[self.player.curr_slot] is None:
                            self.chosen_item = item
                            self.showing_item = item.weapon(self.player, item.level)
                    elif type(item) is items.BoughtArmor:
                        if self.player.armor is None:
                            self.chosen_item = item
                            self.showing_item = item.armor(self.player, item.level)
                    else:
                        item.activate()
            elif symbol == arcade.key.Z:
                self.player.drop_item()
            elif symbol == arcade.key.X:
                self.player.drop_armor()
            elif symbol == arcade.key.ESCAPE:
                self.keys = set()
                self.window.show_view(PauseView(self, self.player.money, self.player.upgrade_crystals))
            elif symbol == arcade.key.Y:
                if not self.enemy_list.sprite_list:
                    self.toggle_level_completion()
        elif not self.game_over:
            if symbol == arcade.key.ENTER:
                if type(self.chosen_item) is items.WeaponItem:
                    self.player.set_weapon_slot(self.showing_item, self.player.curr_slot)

                    self.chosen_item.kill()
                    self.showing_item = None
                    self.chosen_item = None
                    self.texts.clear()
                elif type(self.chosen_item) is items.ArmorItem:
                    self.player.set_armor(self.showing_item)

                    self.chosen_item.kill()
                    self.showing_item = None
                    self.chosen_item = None
                    self.texts.clear()
                elif type(self.chosen_item) is items.BoughtWeapon:
                    if self.player.money >= self.chosen_item.money:
                        self.player.money -= self.chosen_item.money
                        self.player.set_weapon_slot(self.showing_item, self.player.curr_slot)

                        self.chosen_item.kill()
                        self.showing_item = None
                        self.chosen_item = None
                        self.texts.clear()
                elif type(self.chosen_item) is items.BoughtArmor:
                    if self.player.money >= self.chosen_item.money:
                        self.player.money -= self.chosen_item.money
                        self.player.set_armor(self.showing_item)

                        self.chosen_item.kill()
                        self.showing_item = None
                        self.chosen_item = None
                        self.texts.clear()

            elif symbol == arcade.key.Q:
                self.showing_item = None
                self.chosen_item = None
                self.texts.clear()
        else:
            if symbol == arcade.key.ESCAPE:
                attrs = get_attrs()
                write_to_file([self.player.upgrade_crystals] + attrs)
                arcade.stop_sound(self.music_player)
                self.window.show_view(StartScreen())

    def toggle_level_completion(self):
        from planet_generation import LevelTransitionView
        arcade.stop_sound(self.music_player)
        level_transition_view = LevelTransitionView(self, True, self.current_level_id, self.level)
        self.window.show_view(level_transition_view)

    def on_key_release(self, symbol, modifiers):
        self.keys.discard(symbol)

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            # Check mobile controls first
            if self.mobile_controls and self.mobile_controls.on_touch_down(x, y):
                return

            # Original mouse press logic for shooting
            if self.showing_item is None and not self.game_over:
                self.player.attack(x + self.world_camera.position[0] - self.width / 2,
                                   y + self.world_camera.position[1] - self.height / 2)

    def on_mouse_motion(self, x, y, dx, dy):
        if self.mobile_controls:
            self.mobile_controls.on_touch_move(x, y)

    def on_mouse_release(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            if self.mobile_controls:
                self.mobile_controls.on_touch_up(x, y)

    def draw_item(self):
        texture = self.gui_rarities[self.showing_item.rarity - 1]

        rect = arcade.Rect(250, 550, 200, 400, 300, 200, 400, 300)
        arcade.draw_texture_rect(texture, rect)

        try:
            texture = self.showing_item.source_texture
        except AttributeError:
            texture = self.showing_item.texture

        rect = arcade.Rect(265, 315, 335, 385, 50, 50, 290, 360)
        arcade.draw_texture_rect(texture, rect)

        self.texts = [
            arcade.Text(self.showing_item.return_name(), 320, 380, font_size=13, anchor_x='left', anchor_y='center',
                        batch=self.batch)]
        texts = self.showing_item.return_desc().split('\n')

        for i in range(len(texts)):
            self.texts.append(arcade.Text(texts[i], 265, 310 - 20 * i, font_size=10, batch=self.batch))

        if type(self.chosen_item) is items.BoughtWeapon or type(self.chosen_item) is items.BoughtArmor:
            text_y = 100
            self.texts.append(
                arcade.Text(f'Цена предмета: {self.chosen_item.money}', 400, 150, font_size=20, anchor_x='center',
                            anchor_y='center', batch=self.batch))
            self.texts.append(
                arcade.Text(f'Баланс: {self.player.money}', 10, 580, font_size=20, anchor_y='center', batch=self.batch))
        else:
            text_y = 150

        self.texts.append(
            arcade.Text('ENTER чтобы подтвердить и Q чтобы выйти', 400, text_y, font_size=20, anchor_x='center',
                        anchor_y='center', batch=self.batch))

    def setup_map(self, map_name, money, upgrade_crystals, modifiers, weapons_now, armor_now, hp):
        self.tilemap = arcade.load_tilemap('assets/tilesets/maps/' + map_name)
        self.walls_list = self.tilemap.sprite_lists['walls']
        self.phone_list = self.tilemap.sprite_lists['floor']
        player_pos = self.tilemap.sprite_lists['player'].sprite_list[0].position
        try:
            enemies_list = self.tilemap.sprite_lists['enemies'].sprite_list
        except Exception:
            enemies_list = []
        chests_list = self.tilemap.sprite_lists['chests']
        try:
            join_triggers = self.tilemap.object_lists['join_triggers']
        except Exception:
            join_triggers = []
        try:
            shop_items = self.tilemap.sprite_lists['shop_items']
        except Exception:
            shop_items = []
        try:
            boss = self.tilemap.sprite_lists['boss'].sprite_list[0]
        except Exception:
            boss = False
        try:
            boss_angles = self.tilemap.sprite_lists['boss_angles'].sprite_list
        except Exception:
            boss_angles = []

        normal_enemy_texture = self.tilemap.sprite_lists['normal_enemy_texture'].sprite_list[0].texture

        self.player = Player('assets/images/player/players/default-player.png', player_pos[0], player_pos[1], 0.5,
                             money, upgrade_crystals, self.weapons_list, self.armor_list, self.bullets_list,
                             self.enemy_list, self.items_list, self.emitters, modifiers)
        self.physics_engine.add_sprite_list(self.walls_list, body_type=arcade.PymunkPhysicsEngine.STATIC)
        self.world_camera.position = self.player.position

        for i in enemies_list:
            if i.texture == normal_enemy_texture:
                enemy = random.choice(enemies.NORMAL_ENEMIES)(*i.position, False, self.player, self.color, self.level)
                enemy.room = i.properties['room']
                self.enemy_list.append(enemy)
            else:
                enemy = random.choice(enemies.ELITE_ENEMIES)(*i.position, False, self.player, self.color, self.level)
                enemy.room = i.properties['room']
                self.enemy_list.append(enemy)

        for i in chests_list.sprite_list:
            self.items_list.append(items.Chest(*i.position, 2, self.player, self.level))

        walls_color = (min([self.color.r + 5, 255]), min([self.color.g + 5, 255]), min([self.color.b + 5, 255]))
        bg_color = (self.color.r // 4, self.color.g // 4, self.color.b // 4)

        self.phone_list.color = self.color
        self.walls_list.color = walls_color
        arcade.set_background_color(bg_color)

        for i in join_triggers:
            trigger = arcade.Sprite(i)

            for key, value in i.properties.items():
                setattr(trigger, key, value)

            x = [j[0] for j in i.shape]
            x = sum(x) / len(x)

            y = [j[1] for j in i.shape]
            y = sum(y) / len(y)

            trigger.center_x = x
            trigger.center_y = y

            self.join_triggers.append(trigger)

        for i in shop_items:
            min_level = max([self.level - 2, 1])
            max_level = min([self.level + 2, 100])
            level = random.randint(min_level, max_level)

            if random.randint(0, 1):
                rarity = random.randint(1, 5)
                price = round((rarity * 100 + 10 * level) * random.uniform(0.95, 1.05))
                item = items.BoughtWeapon(random.choice(weapons.RARITY_TO_WEAPONS[rarity]), *i.position, self.player,
                                          level, price)
            else:
                rarity = random.randint(1, 5)
                price = round((rarity * 100 + 10 * level) * random.uniform(0.95, 1.05))
                item = items.BoughtArmor(random.choice(armor.RARITY_TO_ARMOR[rarity]), *i.position, self.player, level,
                                         price)

            self.items_list.append(item)

        if boss:
            angles = [i.position for i in boss_angles]
            x1, y1 = min([i[0] for i in angles]), min([i[1] for i in angles])
            x2, y2 = max([i[0] for i in angles]), max([i[1] for i in angles])

            bosss = random.choice(enemies.BOSSES)(boss.center_x, boss.center_y, False, self.player, self.color,
                                                  self.level, x1, y1, x2, y2)
            bosss.room = boss.properties['room']
            self.enemy_list.append(bosss)

        for num, (i, level) in enumerate(weapons_now):
            if i is None:
                continue

            self.player.set_weapon_slot(i(self.player, level), num)

        if armor_now[0] is not None:
            self.player.set_armor(armor_now[0](self.player, armor_now[1]))

        self.player.health = hp
        self.player_list.append(self.player)

        self.keys = set()

        self.physics_engine.add_sprite_list(self.player_list, 1, 0,
                                            moment_of_inertia=arcade.PymunkPhysicsEngine.MOMENT_INF,
                                            collision_type='player')
        self.physics_engine.add_sprite_list(self.enemy_list, 1, 0,
                                            moment_of_inertia=arcade.PymunkPhysicsEngine.MOMENT_INF,
                                            collision_type='enemy')

        self.music = arcade.load_sound(f'assets/music/music{random.randint(1, 3)}.mp3')
        self.music_player = self.music.play(1, loop=True)

        if self.level == 1:
            self.hint_text1 = arcade.Text('Y чтобы покинуть планету, когда все враги мертвы.', self.player.center_x,
                                          self.player.center_y + 80, font_size=18,
                                          anchor_x='center', anchor_y='center', batch=self.hint_batch)
            self.hint_text2 = arcade.Text('Остальное управление в ESC.', self.player.center_x,
                                          self.player.center_y + 50, font_size=18,
                                          anchor_x='center', anchor_y='center', batch=self.hint_batch)

    def get_player_weapons(self):
        fin = []
        for i in self.player.inventory:
            if i is None:
                fin.append((None, 1))
            else:
                fin.append((i.__class__, i.level))

        return fin

    def get_player_armor(self):
        if self.player.armor is not None:
            return (self.player.armor.__class__, self.player.armor.level)
        else:
            return (None, 1)


class PauseView(arcade.View):
    def __init__(self, game, money, upgrade_shards):
        super().__init__()
        self.game = game
        self.batch = Batch()
        self.bg = arcade.load_texture('assets/images/gui/pause.png')
        self.bg_pos = arcade.Rect(0, self.width, 0, self.height, self.width, self.height, self.width / 2,
                                  self.height / 2)

        self.money_texture = arcade.load_texture('assets/images/items/money.png')
        self.upgrade_texture = arcade.load_texture('assets/images/items/upgrade_crystal.png')

        self.money_pos = arcade.Rect(760, 790, 560, 590, 30, 30, 775, 575)
        self.upgrade_pos = arcade.Rect(760, 790, 520, 550, 30, 30, 775, 535)

        self.money_text = arcade.Text(str(money), 755, 575, font_size=15, anchor_x='right', anchor_y='center',
                                      batch=self.batch)
        self.upgrade_text = arcade.Text(str(upgrade_shards), 755, 535, font_size=15, anchor_x='right',
                                        anchor_y='center', batch=self.batch)

        # Initialize mobile controls
        self.mobile_controls = MobileControls(self)

        self.setup_gui()

    def setup_gui(self):
        self.button_texture = arcade.load_texture('assets/images/gui/start_button.png')
        self.button_texture_hovered = arcade.load_texture('assets/images/gui/hovered_start_button.png')

        self.manager = UIManager()
        self.manager.enable()

        self.anchor_layout = UIAnchorLayout(x=0, y=-200)
        self.box_layout = UIBoxLayout(vertical=True, space_between=20)

        self.start_button = UITextureButton(texture=self.button_texture, texture_hovered=self.button_texture_hovered,
                                            text='Вернуться к игре')
        self.start_button.on_click = self.return_to_game
        self.box_layout.add(self.start_button)

        self.exit_button = UITextureButton(texture=self.button_texture, texture_hovered=self.button_texture_hovered,
                                           text='Выход')
        self.exit_button.on_click = self.exit_game
        self.box_layout.add(self.exit_button)

        self.anchor_layout.add(self.box_layout)
        self.manager.add(self.anchor_layout)

    def on_update(self, delta_time):
        if self.mobile_controls:
            self.mobile_controls.on_update(delta_time)

    def on_draw(self):
        arcade.draw_texture_rect(self.bg, self.bg_pos)

        arcade.draw_texture_rect(self.money_texture, self.money_pos)
        arcade.draw_texture_rect(self.upgrade_texture, self.upgrade_pos)

        self.batch.draw()
        self.manager.draw()

        # Draw mobile controls
        if self.mobile_controls:
            self.mobile_controls.draw()

    def on_key_press(self, symbol, mods):
        if symbol == arcade.key.ESCAPE:
            self.return_to_game()

    def return_to_game(self, *args):
        self.manager.disable()
        self.window.show_view(self.game)

    def exit_game(self, *args):
        attrs = get_attrs()
        write_to_file([self.game.player.upgrade_crystals] + attrs)
        arcade.exit()

    # Touch events for mobile controls
    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            if self.mobile_controls:
                self.mobile_controls.on_touch_down(x, y)

    def on_mouse_motion(self, x, y, dx, dy):
        if self.mobile_controls:
            self.mobile_controls.on_touch_move(x, y)

    def on_mouse_release(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            if self.mobile_controls:
                self.mobile_controls.on_touch_up(x, y)


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.set_icon(load_image('assets/images/enemies/basic_enemy.png'))
    view = StartScreen()
    window.show_view(view)
    arcade.run()


if __name__ == '__main__':
    main()
