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


class BoomBulletBase(BulletBase):
    def __init__(self, texture, scale, x1, y1, x2, y2, first_damage, second_damage, first_lifetime, second_lifetime, radius, speed):
        super().__init__(texture, scale, x1, y1, x2, y2, None, None, speed)
        self.angle = arcade.math.get_angle_degrees(x1, y1, x2, y2)

        self.target_radians = self.radians + math.radians(90)

        self.first_damage = first_damage
        self.second_damage = second_damage
        self.first_lifetime = first_lifetime
        self.second_lifetime = second_lifetime
        self.speed = speed
        self.targets_damaged = 0
        self.second_phase_texture = arcade.make_circle_texture(radius * 2, (100, 51, 78))

        self.want_boom = False

        self.phase = 1

    def update(self, delta_time):
        if self.phase == 1:
            self.center_x += math.sin(self.target_radians) * self.speed * delta_time
            self.center_y += math.cos(self.target_radians) * self.speed * delta_time
            self.angle += 720 * delta_time

            self.first_lifetime -= delta_time

            if self.first_lifetime <= 0:
                self.phase = 2
                self.attacked = set()
                self.want_boom = True
                self.texture = self.second_phase_texture
                self.sync_hit_box_to_texture()
                self.alpha = 150
                self.scale = 1
        else:
            self.second_lifetime -= delta_time

            if self.second_lifetime <= 0:
                self.kill()

    def get_damage(self):
        if self.phase == 1:
            return self.first_damage
        else:
            return self.second_damage


class SlipperBulletBase(BoomBulletBase):
    def __init__(self, x1, y1, x2, y2, damage_mod=1):
        lifetime = arcade.math.get_distance(x1, y1, x2, y2) / 300 - 0.15
        super().__init__('assets/images/weapons/magic/slipper.png', 1.75, x1, y1, x2, y2, 12 * damage_mod, 10 * damage_mod, lifetime, 0.75, 80, 300)


class Bullet:
    def __init__(self, texture, scale, damage, lifetime, speed):
        self.texture = texture
        self.scale = scale
        self.damage = damage
        self.lifetime = lifetime
        self.speed = speed
        self.color = (0, 0, 0)

    def shoot(self, x1, y1, x2, y2):
        return BulletBase(self.texture, self.scale, x1, y1, x2, y2, self.damage, self.lifetime, self.speed)


class NormalPistolBullet(Bullet):
    def __init__(self):
        super().__init__('assets/images/bullets/pistol_bullet.png', 1, 3, 1, 200)


class ModernPistolBullet(Bullet):
    def __init__(self):
        super().__init__('assets/images/bullets/pistol_bullet.png', 1.5, 4, 1.5, 250)


class PrimitiveSniperBullet(Bullet):
    def __init__(self):
        super().__init__('assets/images/bullets/upgraded_bullet.png', 1.5, 8, 1.5, 500)


class SniperBullet(Bullet):
    def __init__(self):
        super().__init__('assets/images/bullets/insane_bullet.png', 1.5, 13, 1.5, 650)


class SpreadingBullet(Bullet):
    def __init__(self):
        super().__init__('assets/images/bullets/upgraded_bullet.png', 1.75, 3, 1.25, 250)


class GoodSpreadingBullet(Bullet):
    def __init__(self):
        super().__init__('assets/images/bullets/upgraded_bullet.png', 1.75, 4, 1.5, 275)


class InsaneSpreadingBullet(Bullet):
    def __init__(self):
        super().__init__('assets/images/bullets/insane_bullet.png', 2, 5, 1.5, 300)


class WaterBullet(Bullet):
    def __init__(self):
        super().__init__(arcade.make_soft_circle_texture(20, arcade.color.BLUE, 255, 50), 1, 3, 1.75, 125)
        self.color = arcade.color.BLUE


class FireBullet(Bullet):
    def __init__(self):
        super().__init__(arcade.make_soft_circle_texture(20, arcade.color.RED, 255, 150), 1.2, 4, 2, 175)
        self.color = arcade.color.ORANGE


class SlipperBullet:
    def __init__(self, damage_mod=1):
        self.damage_mod = damage_mod
        self.first_damage = 12 * damage_mod
        self.second_damage = 10 * damage_mod

    def shoot(self, x1, y1, x2, y2):
        return SlipperBulletBase(x1, y1, x2, y2, self.damage_mod)


class NormalEnemyBullet(Bullet):
    def __init__(self):
        super().__init__('assets/images/bullets/pistol_bullet.png', 1.3, 3, 1.5, 200)


class GoodEnemyBullet(Bullet):
    def __init__(self):
        super().__init__('assets/images/bullets/pistol_bullet.png', 1.5, 5, 1.75, 250)


class ShotgunEnemyBullet(Bullet):
    def __init__(self):
        super().__init__('assets/images/bullets/insane_bullet.png', 1.5, 4, 1.5, 300)