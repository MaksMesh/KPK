import arcade
import math


class BulletBase(arcade.Sprite):
    def __init__(self, texture, scale, x1, y1, x2, y2, damage, lifetime, speed):
        super().__init__(texture, scale, x1, y1)
        self.angle = arcade.math.get_angle_degrees(x1, y1, x2, y2)

        self.damage = damage
        self.lifetime = lifetime
        self.speed = speed
        self.targets_damaged = 0

    def update(self, delta_time):
        self.center_x += math.sin(self.radians + math.radians(90)) * self.speed * delta_time
        self.center_y += math.cos(self.radians + math.radians(90)) * self.speed * delta_time

        self.lifetime -= delta_time

        if self.lifetime <= 0:
            self.kill()

    def get_damage(self):
        return self.damage


class Bullet:
    def __init__(self, texture, scale, damage, lifetime, speed):
        self.texture = texture
        self.scale = scale
        self.damage = damage
        self.lifetime = lifetime
        self.speed = speed

    def shoot(self, x1, y1, x2, y2):
        return BulletBase(self.texture, self.scale, x1, y1, x2, y2, self.damage, self.lifetime, self.speed)


class NormalPistolBullet(Bullet):
    def __init__(self):
        super().__init__('assets/images/bullets/pistol_bullet.png', 1, 3, 1, 200)


class ModernPistolBullet(Bullet):
    def __init__(self):
        super().__init__('assets/images/bullets/pistol_bullet.png', 1.5, 4, 1.5, 250)