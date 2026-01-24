import arcade
import random
import math
import main
import sqlite3

WIDTH = 800
HEIGHT = 600
TITLE = "Upgrade Wheel"

class UpgradeWheel(arcade.View):
    def __init__(self):
        super().__init__()
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

        self.con = sqlite3.connect("weapons.sqlite")
        self.cur = self.con.cursor()

        self.chance = 30
        self.rotation = 0
        self.target_angle = 0
        self.spinning = False
        self.speed = 0
        self.result = None
        self.win_angle = self.chance * 3.6
        self.stop_angle = 0

        self.end = 270 + (self.win_angle / 2)
        self.start = (self.end - self.win_angle)
        self.First = False

    def setup(self):
        pass

    def on_draw(self):
        self.clear()

        center_x = WIDTH // 2
        center_y = HEIGHT // 2

        # print(self.stop_angle)
        # print(self.end, self.start)

        if self.end >= self.stop_angle >= self.start:
            self.result = "WIN"
        else:
            self.result = "LOSE"

        # LOSE сектор
        arcade.draw_arc_filled(
            center_x, center_y,
            300, 300,
            arcade.color.RED,
            0, 360
        )

        # WIN сектор
        arcade.draw_arc_filled(
            center_x, center_y,
            300, 300,
            arcade.color.GREEN,
            self.start, self.end
        )

        # обводка
        arcade.draw_circle_outline(
            center_x, center_y,
            150,
            arcade.color.WHITE,
            3
        )

        arcade.draw_circle_filled(
            center_x, center_y,
            100,
            arcade.color.DARK_SLATE_GRAY
        )

        arcade.draw_circle_outline(
            center_x, center_y,
            103,
            arcade.color.WHITE,
            3
        )

        angle = math.radians(self.rotation - 90)
        radius = 170

        px = (center_x + math.cos(angle) * radius)
        py = (center_y + math.sin(angle) * radius)

        dir_angle = math.atan2(center_y - py, center_x - px)

        size = 18

        tip_x = px + math.cos(dir_angle) * size
        tip_y = py + math.sin(dir_angle) * size

        left_x = px + math.cos(dir_angle + 2.5) * size
        left_y = py + math.sin(dir_angle + 2.5) * size

        right_x = px + math.cos(dir_angle - 2.5) * size
        right_y = py + math.sin(dir_angle - 2.5) * size

        arcade.draw_triangle_filled(
            tip_x, tip_y,
            left_x, left_y,
            right_x, right_y,
            arcade.color.YELLOW
        )

        arcade.draw_text(
            f"Chance: {self.chance}%",
            center_x, center_y,
            arcade.color.WHITE, 20, anchor_x="center", anchor_y="center"
        )

    def on_update(self, delta_time):
        if not self.spinning:
            return

        self.rotation += self.speed
        self.speed *= 0.99  # плавное торможение

        # если следующим шагом перелетим цель
        if self.rotation >= self.target_angle:
            self.rotation = self.target_angle
            self.spinning = False
            self.speed = 0

            final_angle = self.rotation % 360

            if self.start <= final_angle <= self.end:
                self.result = "WIN"
            else:
                self.result = "LOSE"

            print("STOP:", final_angle)
            print("RESULT:", self.result)

        if self.speed <= 0.5 and self.First:
            arcade.draw_text(
                self.result,
                WIDTH // 2 - 50, 50,
                arcade.color.YELLOW, 40
            )

    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE and not self.spinning:
            self.result = None
            self.spinning = True

            self.win_angle = self.chance * 3.6
            self.end = 270 + (self.win_angle / 2)
            self.start = self.end - self.win_angle

            print(self.start, self.end)

            self.stop_angle = random.uniform(0, 360) + 270
            self.target_angle = 360 * 5 + self.stop_angle

            self.speed = 35  # стартовая скорость

            self.rotation = 0

            self.First = True
        if key == arcade.key.U:
            game_view = main.Game()
            self.window.show_view(game_view)
        if key == arcade.key.C:
            self.speed = 35

