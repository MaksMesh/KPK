import arcade
import math


class BasicSword(arcade.Sprite):
    def __init__(self, texture, scale, x, y, radius, damage, degrees, speed, reloading, player, enemies_list):
        super().__init__(texture, scale)
        self.x = x
        self.y = y
        self.damage = damage

        self.degrees = degrees
        self.speed = speed
        self.rotate_to = None
        self.radius = radius

        self.reloading_time = reloading
        self.time_left = 0
        self.attacking = False
        self.hitted = set()

        self.player = player
        self.enemies_list = enemies_list

    def update(self, delta_time):
        if not self.attacking:
            self.center_x = self.player.center_x + self.x
            self.center_y = self.player.center_y + self.y
        else:
            self.center_x = self.player.center_x + self.radius * math.sin(self.radians)
            self.center_y = self.player.center_y + self.radius * math.cos(self.radians)

            self.check_for_hit()

            prev = self.rotate_to - self.angle
            self.angle += self.speed * delta_time
            now = self.rotate_to - self.angle

            if (prev > 0 and now < 0) or (prev < 0 and now > 0):
                self.end_attack()
        
        if self.time_left > 0:
            self.time_left -= delta_time
        
    def attack(self, x, y):
        if not self.attacking and self.time_left <= 0:
            self.attacking = True
            middle = arcade.math.get_angle_degrees(self.player.center_x, self.player.center_y, x, y) + 90
            
            start = middle - self.degrees / 2
            end = middle + self.degrees / 2

            self.position = self.player.position
            self.angle = start
            self.rotate_to = end

    def end_attack(self):
        self.center_x = self.player.center_x + self.x
        self.center_y = self.player.center_y + self.y
        self.angle = 0
        self.attacking = False
        self.time_left = self.reloading_time
        self.hitted.clear()

    def check_for_hit(self):
        for i in arcade.check_for_collision_with_list(self, self.enemies_list):
            if i not in self.hitted:
                i.hurt(self.damage)
                self.hitted.add(i)


class WoodenSword(BasicSword):
    def __init__(self, player, enemies_list):
        super().__init__('assets/images/weapons/swords/wooden_sword.png', 0.8, 50, 20, 65, 4, 90, 200, 1, player, enemies_list)


class IronSword(BasicSword):
    def __init__(self, player, enemies_list):
        super().__init__('assets/images/weapons/swords/iron_sword.png', 1, 50, 20, 70, 7, 140, 280, 0.7, player, enemies_list)


class DiamondSword(BasicSword):
    def __init__(self, player, enemies_list):
        super().__init__('assets/images/weapons/swords/sword.png', 1.2, 50, -15, 40, 9, 180, 360, 0.5, player, enemies_list)


class DarkSword(BasicSword):
    def __init__(self, player, enemies_list):
        super().__init__('assets/images/weapons/swords/dark_sword.png', 1.3, 60, 35, 80, 13, 220, 400, 0.3, player, enemies_list)