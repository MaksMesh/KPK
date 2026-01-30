import arcade
from arcade.gui import UIManager, UITextureButton, UIMessageBox
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout
from pyglet.graphics import Batch
import os


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = 'KPK'


def get_shards():
    try:
        with open('data/data.txt') as file:
            return int(file.readline().rstrip('\n'))
    except Exception:
        try:
            os.mkdir('data')
        except FileExistsError:
            pass

        with open('data/data.txt', 'w') as file:
            file.writelines(['0\n'] * 6)

        return 0


def get_attrs(native=True):
    try:
        with open('data/data.txt') as file:
            fin = [int(i) for i in file.read().split('\n')[1:6]]

            if len(fin) != 5:
                raise Exception

            if native:
                return fin
            else:
                fin[0] = 1 + fin[0] * 0.1
                fin[1] = 1 + fin[1] * 0.1
                fin[3] = 1 + fin[3] * 0.1

                if fin[2] == 0:
                    fin[2] = 1
                elif fin[2] == 3:
                    fin[2] = 2
                elif fin[2] == 5:
                    fin[2] = 3

                return fin
    except Exception:
        try:
            os.mkdir('data')
        except FileExistsError:
            pass

        with open('data/data.txt', 'w') as file:
            file.writelines(['0\n'] * 6)

        if native:
            return [0] * 5
        else:
            return [1] * 5


def write_to_file(data):
    try:
        os.mkdir('data')
    except FileExistsError:
        pass
    
    data = [str(i) + '\n' for i in data]

    with open('data/data.txt', 'w') as file:
        file.writelines(data)


class StartScreen(arcade.View):
    def __init__(self):
        super().__init__()
        self.batch = Batch()
        self.setup()

    def setup(self):
        game_name = 'Космические Похождения Колобка'

        self.phone_texture = arcade.load_texture('assets/images/gui/start_picture.png')
        self.phone_rect = arcade.Rect(0, self.width, 0, self.height, self.width, self.height, self.width / 2, self.height / 2)
        self.button_texture = arcade.load_texture('assets/images/gui/start_button.png')
        self.button_texture_hovered = arcade.load_texture('assets/images/gui/hovered_start_button.png')

        self.text = arcade.Text(game_name, 50, 530, arcade.color.WHITE, 36, batch=self.batch)

        self.manager = UIManager()
        self.manager.enable()

        self.anchor_layout = UIAnchorLayout(x=-250, y=100)
        self.box_layout = UIBoxLayout(vertical=True, space_between=20) 
    
        self.setup_widgets()
        
        self.anchor_layout.add(self.box_layout)
        self.manager.add(self.anchor_layout)

    def setup_widgets(self):
        self.start_button = UITextureButton(texture=self.button_texture, texture_hovered=self.button_texture_hovered, text='Старт')
        self.start_button.on_click = self.start_game
        self.box_layout.add(self.start_button)

        self.exit_button = UITextureButton(texture=self.button_texture, texture_hovered=self.button_texture_hovered, text='Выход')
        self.exit_button.on_click = lambda x: exit()
        self.box_layout.add(self.exit_button)

    def on_draw(self):
        self.clear()

        arcade.draw_texture_rect(self.phone_texture, self.phone_rect)
        self.batch.draw()
        self.manager.draw()

    def start_game(self, *args):
        game = StartLocation()
        game.setup()
        self.window.show_view(game)


class StartLocation(arcade.View):
    def __init__(self):
        super().__init__()
        
    def setup(self):
        self.tilemap = arcade.load_tilemap('assets/tilesets/start_tilemap.tmx', 0.75)

        self.base_tiles = self.tilemap.sprite_lists['base']
        self.collision_tiles = self.tilemap.sprite_lists['collision']
        self.start_tiles = self.tilemap.sprite_lists['start_tiles']
        self.upgrade_tiles = self.tilemap.sprite_lists['upgrade_tiles']

        self.world_width = int(self.tilemap.width * self.tilemap.tile_width * 0.75)
        self.world_height = int(self.tilemap.height * self.tilemap.tile_height * 0.75)

        self.star_sky_texture = arcade.load_texture('assets/tilesets/star_sky.png')
        self.phone_rect = arcade.Rect(0, self.world_width, 200, self.world_height + 200, self.world_width, self.world_height, self.world_width / 2, self.world_height / 2 + 100)

        self.player_list = arcade.SpriteList()
        self.player = arcade.Sprite('assets/images/player/players/default-player.png', 0.5, 875, 650)
        self.player_list.append(self.player)

        self.physics_engine = arcade.PhysicsEngineSimple(self.player, self.collision_tiles)

        self.world_camera = arcade.camera.Camera2D() 
        self.world_camera.position = self.player.position

        self.upgrade_pos = (1080, 804)
        self.start_pos = (864, 1200)

        self.keys = set()
        self.speed = 125
        self.stop_game = False

        self.manager = UIManager()
        self.manager.enable()

    def on_draw(self):
        self.clear()

        self.world_camera.use()
        arcade.draw_texture_rect(self.star_sky_texture, self.phone_rect)
        self.base_tiles.draw()
        self.start_tiles.draw()
        self.upgrade_tiles.draw()
        self.player_list.draw()

        self.manager.draw()

    def on_update(self, delta_time):
        if not self.stop_game:
            self.physics_engine.update()

            position = (self.player.center_x, self.player.center_y)
            self.world_camera.position = arcade.math.lerp_2d(self.world_camera.position, position, 0.12)

            move_x = move_y = 0

            if arcade.key.W in self.keys:
                move_y += self.speed
            if arcade.key.S in self.keys:
                move_y -= self.speed
            if arcade.key.D in self.keys:
                move_x += self.speed
            if arcade.key.A in self.keys:
                move_x -= self.speed

            self.player.center_x += move_x * delta_time
            self.player.center_y += move_y * delta_time

    def on_key_press(self, symbol, modifiers):
        self.keys.add(symbol)

        if not self.stop_game:
            if symbol == arcade.key.ESCAPE:
                self.world_camera.position = self.width / 2, self.height / 2
                self.window.show_view(StartScreen())
            elif symbol == arcade.key.Q:
                if arcade.math.get_distance(*self.player.position, *self.upgrade_pos) <= 100:
                    self.keys = set()
                    self.world_camera.position = self.width / 2, self.height / 2
                    self.window.show_view(UpgradeScreen(self))
                elif arcade.math.get_distance(*self.player.position, *self.start_pos) <= 100:
                    self.pre_start()

    def on_key_release(self, symbol, modifiers):
        self.keys.discard(symbol)

    def return_to_game(self):
        self.world_camera.position = self.player.position

    def pre_start(self):
        self.stop_game = True

        message_box = UIMessageBox(
            width=300, height=200,
            message_text="Начать игру?",
            buttons=("Да", "Нет")
        )
        message_box.on_action = self.make_choice_start
        self.manager.add(message_box)

    def make_choice_start(self, event):
        if event.action == 'Да':
            self.start()
        else:
            self.stop_game = False
    
    def start(self):
        mods = get_attrs(False)

        upgrade_shards = get_shards()
        modifiers = {}

        for key, value in zip(['damage', 'health', 'inventory', 'speed', 'lucky'], mods):
            modifiers[key] = value

        print(upgrade_shards, modifiers)


class UpgradeScreen(arcade.View):
    def __init__(self, game):
        super().__init__()
        self.upgrade_shards = get_shards()
        self.batch = Batch()
        self.game = game
        self.setup()

    def setup(self):
        self.bg = arcade.load_texture('assets/images/gui/upgrade_screen.png')
        self.bg_pos = arcade.Rect(0, self.width, 0, self.height, self.width, self.height, self.width / 2, self.height / 2)

        self.attrs = get_attrs()

        self.coords = ((140, 470), (140, 296), (140, 122), (524, 470), (524, 296))
        self.texts = []

        self.button_texture = arcade.load_texture('assets/images/gui/start_button.png')
        self.button_texture_hovered = arcade.load_texture('assets/images/gui/hovered_start_button.png')

        self.upgrade_shard_texture = arcade.load_texture('assets/images/items/upgrade_crystal.png')

        self.manager = UIManager()
        self.manager.enable()

        self.anchor_layout = UIAnchorLayout(x=-80, y=-45)
        self.box_layout = UIBoxLayout(vertical=True, space_between=140) 
    
        self.upgrade_damage_button = UITextureButton(texture=self.button_texture, texture_hovered=self.button_texture_hovered, text='Улучшить', scale=0.6)
        self.upgrade_damage_button.on_click = self.upgrade_damage
        self.box_layout.add(self.upgrade_damage_button)

        self.upgrade_health_button = UITextureButton(texture=self.button_texture, texture_hovered=self.button_texture_hovered, text='Улучшить', scale=0.6)
        self.upgrade_health_button.on_click = self.upgrade_health
        self.box_layout.add(self.upgrade_health_button)

        self.upgrade_backpack_button = UITextureButton(texture=self.button_texture, texture_hovered=self.button_texture_hovered, text='Улучшить', scale=0.6)
        self.upgrade_backpack_button.on_click = self.upgrade_backpack
        self.box_layout.add(self.upgrade_backpack_button)

        self.anchor_layout2 = UIAnchorLayout(x=310, y=45)
        self.box_layout2 = UIBoxLayout(vertical=True, space_between=140) 

        self.upgrade_speed_button = UITextureButton(texture=self.button_texture, texture_hovered=self.button_texture_hovered, text='Улучшить', scale=0.6)
        self.upgrade_speed_button.on_click = self.upgrade_speed
        self.box_layout2.add(self.upgrade_speed_button)

        self.upgrade_luck_button = UITextureButton(texture=self.button_texture, texture_hovered=self.button_texture_hovered, text='Улучшить', scale=0.6)
        self.upgrade_luck_button.on_click = self.upgrade_luck
        self.box_layout2.add(self.upgrade_luck_button)

        self.exit_button = UITextureButton(x=10, y=560, texture=self.button_texture, texture_hovered=self.button_texture_hovered, text='Назад', scale=0.4)
        self.exit_button.on_click = self.exit_act
        self.manager.add(self.exit_button)
        
        self.anchor_layout.add(self.box_layout)
        self.anchor_layout2.add(self.box_layout2)
        self.manager.add(self.anchor_layout)
        self.manager.add(self.anchor_layout2)

    def on_draw(self):
        self.clear()

        for (x, y), level in zip(self.coords, self.attrs):
            if level == 0:
                width = 0
            elif level == 1:
                width = 37
            elif level == 2:
                width = 86
            elif level == 3:
                width = 130
            elif level == 4:
                width = 186
            elif level == 5:
                width = 250
            
            height = 10

            arcade.draw_rect_filled(arcade.Rect(x, x + width, y, y + height, width, height, x + width / 2, y + height / 2), arcade.color.LIME_GREEN)

        arcade.draw_texture_rect(self.bg, self.bg_pos)

        curr_text = 0
        self.texts.clear()

        for x, y in self.coords:
            if self.attrs[curr_text] != 5:
                if curr_text != 2:
                    num = self.attrs[curr_text] + 1
                else:
                    if self.attrs[curr_text] == 0:
                        num = 2
                    else:
                        num = 5
            else:
                num = '?'

            x += 73
            y -= 50
            arcade.draw_texture_rect(self.upgrade_shard_texture, arcade.Rect(x, x + 30, y, y + 30, 30, 30, x + 15, y + 15), pixelated=True)
            curr_text += 1

            self.texts.append(arcade.Text(str(num), x - 5, y, font_size=25, anchor_x='right', batch=self.batch))

        x = 750
        y = 560

        arcade.draw_texture_rect(self.upgrade_shard_texture, arcade.Rect(x, x + 30, y, y + 30, 30, 30, x + 15, y + 15), pixelated=True)
        self.texts.append(arcade.Text(str(self.upgrade_shards), x - 5, y, font_size=25, anchor_x='right', batch=self.batch))

        self.manager.draw()
        self.batch.draw()

    def upgrade_damage(self, *args):
        summ = self.attrs[0] + 1

        if self.attrs[0] < 5:
            if self.upgrade_shards >= summ:
                self.attrs[0] += 1
                self.upgrade_shards -= summ

    def upgrade_health(self, *args):
        summ = self.attrs[1] + 1

        if self.attrs[1] < 5:
            if self.upgrade_shards >= summ:
                self.attrs[1] += 1
                self.upgrade_shards -= summ
    
    def upgrade_backpack(self, *args):
        if self.attrs[2] == 0:
            summ = 2
        else:
            summ = 5

        if self.attrs[2] < 5:
            if self.upgrade_shards >= summ:
                if self.attrs[2] == 0:
                    self.attrs[2] = 3
                else:
                    self.attrs[2] = 5
                self.upgrade_shards -= summ

    def upgrade_speed(self, *args):
        summ = self.attrs[3] + 1

        if self.attrs[3] < 5:
            if self.upgrade_shards >= summ:
                self.attrs[3] += 1
                self.upgrade_shards -= summ

    def upgrade_luck(self, *args):
        summ = self.attrs[4] + 1

        if self.attrs[4] < 5:
            if self.upgrade_shards >= summ:
                self.attrs[4] += 1
                self.upgrade_shards -= summ

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ESCAPE:
            self.exit_act()

    def exit_act(self, *args):
        write_to_file([self.upgrade_shards] + self.attrs)
        self.game.return_to_game()
        self.window.show_view(self.game)


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    view = StartScreen()
    window.show_view(view)
    arcade.run()


if __name__ == '__main__':
    main()