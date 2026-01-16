import arcade
import math
import bullets


class BasicSword(arcade.Sprite):
    def __init__(self, texture, scale, x, y, radius, damage, degrees, speed, reloading, player):
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
        self.enemies_list = self.player.enemies_list

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
    def __init__(self, player):
        super().__init__('assets/images/weapons/swords/wooden_sword.png', 0.8, 50, 20, 65, 4, 90, 200, 1, player)


class IronSword(BasicSword):
    def __init__(self, player):
        super().__init__('assets/images/weapons/swords/iron_sword.png', 1, 50, 20, 70, 7, 140, 280, 0.7, player)


class DiamondSword(BasicSword):
    def __init__(self, player):
        super().__init__('assets/images/weapons/swords/sword.png', 1.2, 50, -15, 40, 9, 180, 360, 0.5, player)


class DarkSword(BasicSword):
    def __init__(self, player):
        super().__init__('assets/images/weapons/swords/dark_sword.png', 1.3, 60, 35, 80, 13, 220, 400, 0.3, player)


class Pistol(arcade.Sprite):
    def __init__(self, texture, scale, x, y, r_d, bullet, reloading, throughing, player, level):
        super().__init__(texture, scale)
        self.x = x
        self.y = y
        self.r_d = r_d
        self.level = level

        self.bullet = bullet
        self.bullets_list = arcade.SpriteList()

        self.reloading_time = reloading
        self.time_left = 0
        self.attacking = False
        self.throughing = throughing

        self.player = player
        self.enemies_list = self.player.enemies_list
        
        self.source_texture = arcade.load_texture(texture)

        self.apply_level()

    def update(self, delta_time):
        if not self.attacking:
            self.angle = 0
            self.texture = self.source_texture
            self.center_x = self.player.center_x + self.x
            self.center_y = self.player.center_y + self.y
        else:
            self.center_x = self.player.center_x + self.r_d * math.sin(self.radians + math.radians(90))
            self.center_y = self.player.center_y + self.r_d * math.cos(self.radians + math.radians(90))

        for bullet in self.bullets_list.sprite_list:
            enemies = arcade.check_for_collision_with_list(bullet, self.enemies_list)

            for enemy in enemies:
                if enemy in bullet.attacked:
                    continue

                enemy.hurt(bullet.get_damage())

                bullet.targets_damaged += 1

                if bullet.targets_damaged >= self.throughing:
                    bullet.kill()
                    break

                bullet.attacked.add(enemy)

        self.bullets_list.update(delta_time)

        if self.time_left > 0:
            self.time_left -= delta_time
        else:
            self.attacking = False

    def attack(self, x, y):
        if self.time_left <= 0:
            self.attacking = True

            self.angle = arcade.math.get_angle_degrees(self.player.center_x, self.player.center_y, x, y)

            if -90 < self.angle < 90:
                self.texture = self.source_texture
            else:
                self.texture = self.source_texture.flip_vertically()

            self.center_x = self.player.center_x + self.r_d * math.sin(self.radians + math.radians(90))
            self.center_y = self.player.center_y + self.r_d * math.cos(self.radians + math.radians(90))

            self.time_left = self.reloading_time

            bullet = self.bullet.shoot(self.player.center_x, self.player.center_y, x, y)
            bullet.position = self.position
            bullet.attacked = set()
            self.bullets_list.append(bullet)
            self.player.bullets_list.append(bullet)

    def apply_level(self):
        self.bullet.damage *= self.level / 10 + 0.9


class OldPistol(Pistol):
    def __init__(self, player, level):
        super().__init__('assets/images/weapons/pistols/pistol.png', 1.2, 50, 0, 60, bullets.NormalPistolBullet(), 0.75, 1, player, level)


class OldPistol(Pistol):
    def __init__(self, player, level):
        super().__init__('assets/images/weapons/pistols/modern_pistol.png', 1.2, 50, 0, 60, bullets.ModernPistolBullet(), 0.5, 2, player, level)