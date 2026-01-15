import arcade
import weapons
import enemies


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = 'KPK'


class Player(arcade.Sprite):
    def __init__(self, texture, x, y, scale, weapons_list, modifiers={}):
        super().__init__(texture, scale, x, y)
        self.modifiers = modifiers
        self.weapon = None
        self.health = 10
        self.weapons_list = weapons_list

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
        self.weapons_list.append(self.weapon)


class Game(arcade.View):
    def __init__(self):
        super().__init__()

        self.player_list = arcade.SpriteList()
        self.walls = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()
        self.weapons_list = arcade.SpriteList()

        self.physics_engine = arcade.PymunkPhysicsEngine(damping=0)

        self.setup()

    def setup(self):
        arcade.set_background_color(arcade.color.SKY_BLUE)

        self.player = Player('assets/images/player/players/default-player.png', 400, 100, 0.5, self.weapons_list, {})
        self.player.set_weapon(weapons.DarkSword(self.player, self.enemy_list))
        self.player_list.append(self.player)

        self.enemy = enemies.Enemy(300, 500, True, self.player)
        self.enemy_list.append(self.enemy)


        self.keys = set()
  
        self.physics_engine.add_sprite_list(self.player_list, 1, 0, moment_of_inertia=arcade.PymunkPhysicsEngine.MOMENT_INF, collision_type='player')
        self.physics_engine.add_sprite_list(self.enemy_list, 1, 0, moment_of_inertia=arcade.PymunkPhysicsEngine.MOMENT_INF, collision_type='enemy')

    def on_update(self, delta_time):
        self.player.update(delta_time, self.keys)
        self.enemy_list.update(delta_time)
        self.physics_engine.step(delta_time)

    def on_draw(self):
        self.clear()
        self.player_list.draw()
        self.enemy_list.draw()
        self.weapons_list.draw()

    def on_key_press(self, symbol, modifiers):
        print(symbol)
        self.keys.add(symbol)

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