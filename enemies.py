import arcade
import arcade.particles
import math
import bullets
import random


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


class BasicEnemy(arcade.Sprite):
    def __init__(self, texture, scale, center_x, center_y, damage, reload, health, speed, active, player, color, level):
        super().__init__(texture, scale, center_x, center_y)
        self.damage = damage
        self.reload = reload
        self.time_left = 0
        self.level = level

        self.health = health
        self.speed = speed
        self.active = active
        self.player = player
        self.color = color

        self.apply_level()

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
            self.player.emitters.append(make_explosion(self.center_x, self.center_y, arcade.make_circle_texture(10, self.color), 20))
        else:
            self.player.emitters.append(make_explosion(self.center_x, self.center_y, arcade.make_circle_texture(8, self.color), 5))

    def attack(self):
        if self.time_left <= 0:
            if arcade.check_for_collision(self, self.player):
                self.player.hurt(self.damage)
                self.time_left = self.reload

    def apply_level(self):
        self.damage *= self.level / 10 + 0.9
        self.health *= self.level / 10 + 0.9


class Enemy(BasicEnemy):
    def __init__(self, x, y, active, player, color, level):
        super().__init__('assets/images/enemies/enemy.png', 1, x, y, 3, 1, 8, 3000, active, player, color, level)


class FastEnemy(BasicEnemy):
    def __init__(self, x, y, active, player, color, level):
        super().__init__('assets/images/enemies/fast_enemy.png', 1, x, y, 2, 0.8, 5, 5000, active, player, color, level)


class SlowEnemy(BasicEnemy):
    def __init__(self, x, y, active, player, color, level):
        super().__init__('assets/images/enemies/slow_enemy.png', 1.2, x, y, 6, 1.2, 15, 1750, active, player, color, level)


class BasicShootingEnemy(BasicEnemy):
    def __init__(self, texture, scale, center_x, center_y, damage, reload, health, speed, x, y, r_d, distance, attack_distance, weapon_texture, weapon_scale, bullet, active, player, color, level):
        super().__init__(texture, scale, center_x, center_y, damage, reload, health, speed, active, player, color, level)
        self.x = x
        self.y = y
        self.r_d = r_d

        self.distance = distance
        self.attack_distance = attack_distance
        self.weapon = arcade.Sprite(weapon_texture, 1.2, center_x + x, center_y + y)
        self.source_texture = arcade.load_texture(weapon_texture)
        self.player.weapons_list.append(self.weapon)

        self.bullets_list = arcade.SpriteList()
        self.bullet = bullet
        self.attacking = False
        self.player.bullets_list.append(self.bullets_list)

        self.bullet.damage = self.damage

    def update(self, delta_time):
        distance = arcade.math.get_distance(*self.position, *self.player.position)

        x, y = self.get_move(distance)
        self.physics_engines[0].apply_force(self, (x, y))

        if distance <= self.attack_distance:
            self.attack()

        if not self.attacking:
            self.weapon.angle = 0
            self.weapon.texture = self.source_texture
            self.weapon.center_x = self.center_x + self.x
            self.weapon.center_y = self.center_y + self.y
        else:
            self.weapon.center_x = self.center_x + self.r_d * math.sin(self.weapon.radians + math.radians(90))
            self.weapon.center_y = self.center_y + self.r_d * math.cos(self.weapon.radians + math.radians(90))

        for bullet in self.bullets_list.sprite_list:
            if arcade.check_for_collision(bullet, self.player):
                self.player.hurt(bullet.get_damage())
                bullet.kill()

        self.bullets_list.update(delta_time)

        if self.time_left > 0:
            self.time_left -= delta_time
        else:
            self.attacking = False

    def get_move(self, distance):
        if self.active and distance > self.distance:
            angle = arcade.math.get_angle_radians(*self.position, *self.player.position)
            move_x = math.sin(angle) * self.speed
            move_y = math.cos(angle) * self.speed

            return move_x, move_y

        return 0, 0

    def attack(self):
        if self.time_left <= 0:
            self.time_left = self.reload
            self.attacking = True

            self.weapon.angle = arcade.math.get_angle_degrees(self.center_x, self.center_y, self.player.center_x, self.player.center_y)

            if -90 < self.weapon.angle < 90:
                self.weapon.texture = self.source_texture
            else:
                self.weapon.texture = self.source_texture.flip_vertically()

            self.weapon.center_x = self.center_x + self.r_d * math.sin(self.weapon.radians + math.radians(90))
            self.weapon.center_y = self.center_y + self.r_d * math.cos(self.weapon.radians + math.radians(90))

            bullet = self.bullet.shoot(self.center_x, self.center_y, self.player.center_x, self.player.center_y)
            bullet.position = self.weapon.position
            self.bullets_list.append(bullet)

    def kill(self):
        super().kill()
        self.weapon.kill()

        for i in self.bullets_list.sprite_list:
            i.remove_from_sprite_lists()
            i.kill()

        del self.player.bullets_list[self.player.bullets_list.index(self.bullets_list)]


class ShootingEnemy(BasicShootingEnemy):
    def __init__(self, x, y, active, player, color, level):
        super().__init__('assets/images/enemies/shooting_enemy.png', 1, x, y, 3, 1, 5, 3000, 50, 0, 60, 200, 400, 'assets/images/weapons/pistols/pistol.png', 1.2, bullets.NormalEnemyBullet(), active, player, color, level)


class GoodShootingEnemy(BasicShootingEnemy):
    def __init__(self, x, y, active, player, color, level):
        super().__init__('assets/images/enemies/good_shooting_enemy.png', 1, x, y, 5, 0.75, 8, 3000, 50, 0, 60, 200, 600, 'assets/images/weapons/pistols/modern_pistol.png', 1.5, bullets.GoodEnemyBullet(), active, player, color, level)


NORMAL_ENEMIES = [Enemy, FastEnemy, SlowEnemy, ShootingEnemy]
ELITE_ENEMIES = [GoodShootingEnemy]
BOSSES = []