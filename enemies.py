import arcade
import math


class BasicEnemy(arcade.Sprite):
    def __init__(self, texture, scale, center_x, center_y, damage, reload, health, speed, active, player, color):
        super().__init__(texture, scale, center_x, center_y)
        self.damage = damage
        self.reload = reload
        self.time_left = 0

        self.health = health
        self.speed = speed
        self.active = active
        self.player = player
        self.color = color

    def update(self, delta_time):
        x, y = self.get_move()
        self.physics_engines[0].apply_force(self, (x, y))

        if self.time_left > 0:
            self.time_left -= delta_time

        self.attack()

    def get_move(self):
        if self.active:
            angle = arcade.math.get_angle_radians(*self.position, *self.player.position)
            move_x = math.sin(angle) * self.speed
            move_y = math.cos(angle) * self.speed

            return move_x, move_y

        return 0, 0

    def hurt(self, damage):
        self.health -= damage

        if self.health <= 0:
            self.kill()

    def attack(self):
        if self.time_left <= 0:
            if arcade.check_for_collision(self, self.player):
                self.player.hurt(self.damage)
                self.time_left = self.reload


class Enemy(BasicEnemy):
    def __init__(self, x, y, active, player, color):
        super().__init__('assets/images/enemies/enemy.png', 1, x, y, 3, 1, 8, 3000, active, player, color)


class FastEnemy(BasicEnemy):
    def __init__(self, x, y, active, player, color):
        super().__init__('assets/images/enemies/fast_enemy.png', 1, x, y, 2, 0.8, 5, 5000, active, player, color)


class SlowEnemy(BasicEnemy):
    def __init__(self, x, y, active, player, color):
        super().__init__('assets/images/enemies/slow_enemy.png', 1.2, x, y, 6, 1.2, 15, 1750, active, player, color)