import arcade
import arcade.particles
import math
import bullets
import random


def make_trail(texture, maintain=60):
    emit = arcade.particles.Emitter(
        center_xy=(0, 0),
        emit_controller=arcade.particles.EmitMaintainCount(maintain),
        particle_factory=lambda e: arcade.particles.FadeParticle(
            filename_or_texture=texture,
            change_xy=arcade.math.rand_in_circle((0.0, 0.0), 1.6),
            lifetime=random.uniform(0.35, 0.6),
            start_alpha=220, end_alpha=0,
            scale=random.uniform(0.25, 0.4),
        ),
    )
    return emit


def make_explosion(x, y, texture, count=80):
    return arcade.particles.Emitter(
        center_xy=(x, y),
        emit_controller=arcade.particles.EmitBurst(count),
        particle_factory=lambda e: arcade.particles.FadeParticle(
            filename_or_texture=texture,
            change_xy=arcade.math.rand_in_circle((0.0, 0.0), 5.0),
            lifetime=random.uniform(0.3, 0.6),
            start_alpha=255, end_alpha=0,
            scale=random.uniform(0.35, 0.6)
        ),
    )


class BasicSword(arcade.Sprite):
    def __init__(self, texture, scale, x, y, radius, damage, degrees, speed, reloading, player, level):
        super().__init__(texture, scale)
        self.x = x
        self.y = y
        self.damage = damage * player.modifiers.get('damage', 1)
        self.level = level

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

        self.name = ''

        self.apply_level()

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

    def apply_level(self):
        self.damage *= self.level / 10 + 0.9

    def return_name(self):
        return self.name

    def return_desc(self):
        return f'Уровень: {self.level}\nУрон: {self.damage}\nПерезарядка: {self.reloading_time}'

    def return_to_live(self):
        pass


class WoodenSword(BasicSword):
    def __init__(self, player, level):
        super().__init__('assets/images/weapons/swords/wooden_sword.png', 0.8, 50, 20, 65, 6, 90, 200, 1, player, level)
        self.rarity = 1
        self.name = 'Деревянный меч'


class IronSword(BasicSword):
    def __init__(self, player, level):
        super().__init__('assets/images/weapons/swords/iron_sword.png', 1, 50, 20, 70, 7, 140, 280, 0.7, player, level)
        self.rarity = 2
        self.name = 'Железный меч'


class DiamondSword(BasicSword):
    def __init__(self, player, level):
        super().__init__('assets/images/weapons/swords/sword.png', 1.2, 50, 45, 90, 9, 180, 360, 0.5, player, level)
        self.rarity = 3
        self.name = 'Алмазный меч'


class DarkSword(BasicSword):
    def __init__(self, player, level):
        super().__init__('assets/images/weapons/swords/dark_sword.png', 1.3, 60, 35, 80, 12, 220, 400, 0.3, player, level)
        self.rarity = 4
        self.name = 'Меч тьмы'


class ChaosSaber(BasicSword):
    def __init__(self, player, level):
        super().__init__('assets/images/weapons/swords/chaos_saber.png', 1.5, 50, 50, 110, 14, 260, 500, 0.25, player, level)
        self.rarity = 5
        self.name = 'Сабля хаоса'


class Pistol(arcade.Sprite):
    def __init__(self, texture, scale, x, y, r_d, bullet, reloading, throughing, player, level):
        super().__init__(texture, scale)
        self.x = x
        self.y = y
        self.r_d = r_d
        self.level = level

        self.bullet = bullet
        self.bullets_list = arcade.SpriteList()
        player.bullets_list.append(self.bullets_list)

        self.reloading_time = reloading
        self.time_left = 0
        self.attacking = False
        self.throughing = throughing

        self.player = player
        self.enemies_list = self.player.enemies_list
        
        self.source_texture = arcade.load_texture(texture)

        self.name = ''

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

    def apply_level(self):
        self.bullet.damage *= self.player.modifiers.get('damage', 1)
        self.bullet.damage *= self.level / 10 + 0.9

    def kill(self):
        super().kill()
        self.bullets_list.clear()

        try:
            del self.player.bullets_list[self.player.bullets_list.index(self.bullets_list)]
        except Exception:
            pass

    def return_name(self):
        return self.name

    def return_desc(self):
        return f'Уровень: {self.level}\nУрон: {self.bullet.damage}\nПерезарядка: {self.reloading_time}'

    def return_to_live(self):
        self.player.bullets_list.append(self.bullets_list)


class OldPistol(Pistol):
    def __init__(self, player, level):
        super().__init__('assets/images/weapons/pistols/pistol.png', 1.2, 50, 0, 60, bullets.NormalPistolBullet(), 0.75, 1, player, level)
        self.rarity = 1
        self.name = 'Старый пистолет'


class ModernPistol(Pistol):
    def __init__(self, player, level):
        super().__init__('assets/images/weapons/pistols/modern_pistol.png', 1.2, 50, 0, 60, bullets.ModernPistolBullet(), 0.5, 2, player, level)
        self.rarity = 2
        self.name = 'Современный пистолет'


class PrimitiveSniper(Pistol):
    def __init__(self, player, level):
        super().__init__('assets/images/weapons/pistols/primitive_sniper.png', 1.4, 55, 0, 60, bullets.PrimitiveSniperBullet(), 1, 3, player, level)
        self.rarity = 3
        self.name = 'Примитивная снайперка'


class Sniper(Pistol):
    def __init__(self, player, level):
        super().__init__('assets/images/weapons/pistols/sniper.png', 1.4, 55, 0, 60, bullets.SniperBullet(), 0.9, 5, player, level)
        self.rarity = 4
        self.name = 'Снайперка'


class SpreadingPistol(Pistol):
    def __init__(self, player, level):
        super().__init__('assets/images/weapons/pistols/spreading_pistol.png', 1.2, 55, 0, 60, bullets.SpreadingBullet(), 0.75, 1, player, level)
        self.rarity = 3
        self.name = 'Рассеивающий пистолет'

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

            targets = [(x, y), arcade.math.rotate_around_point((self.player.center_x, self.player.center_y), (x, y), 30), arcade.math.rotate_around_point((self.player.center_x, self.player.center_y), (x, y), -30)]

            for x, y in targets:
                bullet = self.bullet.shoot(self.player.center_x, self.player.center_y, x, y)
                bullet.position = self.position
                bullet.attacked = set()
                self.bullets_list.append(bullet)


class GoodSpreadingPistol(Pistol):
    def __init__(self, player, level):
        super().__init__('assets/images/weapons/pistols/good_spreading_pistol.png', 1.2, 55, 0, 60, bullets.GoodSpreadingBullet(), 0.75, 2, player, level)
        self.rarity = 4
        self.name = 'Усечённый дробовик'

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

            targets = [(x, y), arcade.math.rotate_around_point((self.player.center_x, self.player.center_y), (x, y), 30), arcade.math.rotate_around_point((self.player.center_x, self.player.center_y), (x, y), -30)]

            for x, y in targets:
                bullet = self.bullet.shoot(self.player.center_x, self.player.center_y, x, y)
                bullet.position = self.position
                bullet.attacked = set()
                self.bullets_list.append(bullet)


class Shotgun(Pistol):
    def __init__(self, player, level):
        super().__init__('assets/images/weapons/pistols/shotgun.png', 1.2, 55, 0, 60, bullets.InsaneSpreadingBullet(), 0.65, 3, player, level)
        self.rarity = 5
        self.name = 'Дробовик'

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

            targets = [(x, y), arcade.math.rotate_around_point((self.player.center_x, self.player.center_y), (x, y), 30), 
                       arcade.math.rotate_around_point((self.player.center_x, self.player.center_y), (x, y), -30),
                       arcade.math.rotate_around_point((self.player.center_x, self.player.center_y), (x, y), -60),
                       arcade.math.rotate_around_point((self.player.center_x, self.player.center_y), (x, y), 60)]

            for x, y in targets:
                bullet = self.bullet.shoot(self.player.center_x, self.player.center_y, x, y)
                bullet.position = self.position
                bullet.attacked = set()
                self.bullets_list.append(bullet)


class PistolBook(Pistol):
    def __init__(self, texture, scale, x, y, r_d, bullet, reloading, throughing, player, level):
        super().__init__(texture, scale, x, y, r_d, bullet, reloading, throughing, player, level)
        self.emitters = []

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
            bullet.emitter.center_x = bullet.center_x
            bullet.emitter.center_y = bullet.center_y

            enemies = arcade.check_for_collision_with_list(bullet, self.enemies_list)

            for enemy in enemies:
                if enemy in bullet.attacked:
                    continue

                enemy.hurt(bullet.get_damage())
                bullet.attacked.add(enemy)

        for e in self.emitters:
            e.lifetime -= delta_time

            if e.lifetime <= 0:
                self.player.emitters.remove(e)
                self.emitters.remove(e)

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
            bullet.emitter = make_trail(arcade.make_soft_circle_texture(20, self.bullet.color, 255, 50))
            bullet.emitter.lifetime = bullet.lifetime
            self.player.emitters.append(bullet.emitter)
            self.emitters.append(bullet.emitter)
            self.bullets_list.append(bullet)

    def kill(self):
        super().kill()

        for i in self.emitters:
            self.player.emitters.remove(i)

        self.emitters.clear()


class WaterBook(PistolBook):
    def __init__(self, player, level):
        super().__init__('assets/images/weapons/magic/water_book.png', 1.2, 45, 0, 50, bullets.WaterBullet(), 0.75, None, player, level)
        self.rarity = 1
        self.name = 'Книга воды'


class FireBook(PistolBook):
    def __init__(self, player, level):
        super().__init__('assets/images/weapons/magic/fire_book.png', 1.2, 45, 0, 50, bullets.FireBullet(), 0.65, None, player, level)
        self.rarity = 2
        self.name = 'Огненная книга'


class AreaBook(Pistol):
    def __init__(self, texture, scale, x, y, r_d, damage, radius, lifetime, reloading, color, player, level):
        self.magic_color = color
        self.radius = radius
        self.damage = damage
        self.particle_texture = arcade.make_circle_texture(10, color)
        self.lifetime = lifetime

        super().__init__(texture, scale, x, y, r_d, None, reloading, None, player, level)

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
            bullet.lifetime -= delta_time

            if bullet.lifetime <= 0:
                bullet.kill()
            else:
                for enemy in enemies:
                    if enemy in bullet.attacked:
                        continue

                    enemy.hurt(self.damage)
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

            bullet = arcade.SpriteCircle(self.radius, self.magic_color, False, x, y)
            bullet.lifetime = self.lifetime
            bullet.alpha = 100
            bullet.attacked = set()
            self.player.emitters.append(make_explosion(x, y, self.particle_texture, 40))
            self.bullets_list.append(bullet)

    def apply_level(self):
        self.damage *= self.player.modifiers.get('damage', 1)
        self.damage *= self.level / 10 + 0.9

    def return_desc(self):
        return f'Уровень: {self.level}\nУрон: {self.damage}\nПерезарядка: {self.reloading_time}'


class DarkBook(AreaBook):
    def __init__(self, player, level):
        super().__init__('assets/images/weapons/magic/dark_book.png', 1.2, 45, 0, 50, 6, 50, 0.5, 0.6, arcade.color.PURPLE, player, level)
        self.rarity = 3
        self.name = 'Книга тьмы'


class LightBook(AreaBook):
    def __init__(self, player, level):
        super().__init__('assets/images/weapons/magic/light_book.png', 1.2, 45, 0, 50, 8, 75, 0.65, 0.5, arcade.color.YELLOW, player, level)
        self.rarity = 4
        self.name = 'Книга света'


USUAL_RARITY_WEAPONS = [WoodenSword, OldPistol, WaterBook]
UNUSUAL_RARITY_WEAPONS = [IronSword, ModernPistol, FireBook]
RARE_RARITY_WEAPONS = [DiamondSword, PrimitiveSniper, SpreadingPistol, DarkBook]
EPIC_RARITY_WEAPONS = [DarkSword, Sniper, GoodSpreadingPistol, LightBook]
LEGENDARY_RARITY_WEAPONS = [ChaosSaber, Shotgun]

RARITY_TO_WEAPONS = {1: USUAL_RARITY_WEAPONS,
                     2: UNUSUAL_RARITY_WEAPONS,
                     3: RARE_RARITY_WEAPONS,
                     4: EPIC_RARITY_WEAPONS,
                     5: LEGENDARY_RARITY_WEAPONS}