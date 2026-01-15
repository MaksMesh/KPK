import arcade
import math


class BasicEnemy(arcade.Sprite):
    def __init__(self, texture, scale, center_x, center_y, damage, health, speed, active, player):
        super().__init__(texture, scale, center_x, center_y)
        self.damage = damage
        self.health = health
        self.speed = speed
        self.active = active
        self.player = player

    def update(self, delta_time):
        x, y = self.get_move()
        self.physics_engines[0].apply_force(self, (x, y))

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


class Enemy(BasicEnemy):
    def __init__(self, x, y, active, player):
        super().__init__('assets/images/enemies/basic_enemy.png', 0.33, x, y, 3, 8, 3000, active, player)