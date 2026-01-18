import arcade
from pyglet.graphics import Batch
import weapons
import enemies


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = 'KPK'


class Player(arcade.Sprite):
    def __init__(self, texture, x, y, scale, slots, weapons_list, bullets_list, enemies_list, emitters, modifiers={}):
        super().__init__(texture, scale, x, y)
        self.modifiers = modifiers
        self.weapon = None
        self.max_health = 10
        self.health = self.max_health
        self.weapons_list = weapons_list
        self.bullets_list = bullets_list
        self.enemies_list = enemies_list
        self.emitters = emitters

        self.inventory = [None] * slots
        self.curr_slot = 0

    def update(self, delta_time, keys):
        move_x = move_y = 0
        speed = 5000

        if arcade.key.W in keys:
            move_y += speed
        if arcade.key.S in keys:
            move_y -= speed
        if arcade.key.D in keys:
            move_x += speed
        if arcade.key.A in keys:
            move_x -= speed

        self.physics_engines[0].apply_force(self, (move_x, move_y))

        if self.weapon is not None:
            self.weapon.update(delta_time)

    def attack(self, x, y):
        if self.weapon is not None:
            self.weapon.attack(x, y)

    def set_weapon(self, weapon):
        if self.weapon is not None:
            self.weapon.kill()

        self.weapon = weapon

        if self.weapon is not None:
            self.weapons_list.append(self.weapon)

    def hurt(self, damage):
        self.health -= damage

        if self.health <= 0:
            self.kill()
            self.health = 0

    def kill(self):
        super().kill()

        if self.weapon is not None:
            self.weapon.kill()

    def next_item(self):
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


class Game(arcade.View):
    def __init__(self):
        super().__init__()

        self.player_list = arcade.SpriteList()
        self.walls = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList(True)
        self.weapons_list = arcade.SpriteList()
        self.bullets_list = arcade.SpriteList()
        
        self.emitters = []

        self.batch = Batch()

        self.physics_engine = arcade.PymunkPhysicsEngine(damping=0)

        self.health_bar_texture = arcade.load_texture('assets/images/gui/health_bar.png')
        self.slot_texture = arcade.load_texture('assets/images/gui/slot.png')

        self.setup()

    def setup(self):
        arcade.set_background_color(arcade.color.SKY_BLUE)

        self.player = Player('assets/images/player/players/default-player.png', 400, 100, 0.5, 2, self.weapons_list, self.bullets_list, self.enemy_list, self.emitters, {})
        self.player.set_weapon_slot(weapons.ModernPistol(self.player, 1), 0)
        self.player.set_weapon_slot(weapons.DarkSword(self.player, 1), 1)
        self.player_list.append(self.player)

        for i in range(10):
            enemy = enemies.ShootingEnemy(300 + i, 500, True, self.player, (255, 102, 0), 1)
            self.enemy_list.append(enemy)

        self.keys = set()
  
        self.physics_engine.add_sprite_list(self.player_list, 1, 0, moment_of_inertia=arcade.PymunkPhysicsEngine.MOMENT_INF, collision_type='player')
        self.physics_engine.add_sprite_list(self.enemy_list, 1, 0, moment_of_inertia=arcade.PymunkPhysicsEngine.MOMENT_INF, collision_type='enemy')

    def on_update(self, delta_time):
        self.player_list.update(delta_time, self.keys)
        self.enemy_list.update(delta_time)

        emitters_copy = self.emitters.copy()
        for e in emitters_copy:
            e.update(delta_time)
        for e in emitters_copy:
            if e.can_reap():
                self.emitters.remove(e)

        self.physics_engine.step(delta_time)

    def on_draw(self):
        self.clear()

        for e in self.emitters:
            e.draw()

        self.player_list.draw()
        self.enemy_list.draw()
        self.bullets_list.draw()
        self.weapons_list.draw()

        self.draw_gui()
        self.batch.draw()

    def draw_gui(self):
        rect = arcade.Rect(550, SCREEN_WIDTH, 0, 70, 250, 70, 675, 35)
        arcade.draw_texture_rect(self.health_bar_texture, rect)

        hp_width = 210 * (self.player.health / self.player.max_health)

        rect = arcade.Rect(570, SCREEN_WIDTH - 230 + hp_width, 23, 56, hp_width, 33, 570 + hp_width / 2, 35)
        arcade.draw_rect_filled(rect, arcade.color.RED)

        for i in range(len(self.player.inventory)):
            rect = arcade.Rect(i * 70, i * 70 + 70, 0, 70, 70, 70, i * 70 + 35, 35)
            arcade.draw_texture_rect(self.slot_texture, rect)
            
            try:
                texture = self.player.inventory[i].source_texture
            except AttributeError:
                texture = self.player.inventory[i].texture

            arcade.draw_texture_rect(texture, rect)

            if i == self.player.curr_slot:
                rect_f = rect

        arcade.draw_rect_outline(rect_f, arcade.color.SEA_BLUE, 3)

        self.hp_text = arcade.Text(f'{round(self.player.health)}/{self.player.max_health}', 675, 35, arcade.color.WHITE, 20, anchor_x='center', anchor_y='center', batch=self.batch)

    def on_key_press(self, symbol, modifiers):
        self.keys.add(symbol)

        if symbol == arcade.key.E:
            self.player.next_item()

    def on_key_release(self, symbol, modifiers):
        self.keys.discard(symbol)

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.player.attack(x, y)


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    view = Game()
    window.show_view(view)
    arcade.run()


if __name__ == '__main__':
    main()