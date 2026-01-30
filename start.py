import arcade
from arcade.gui import UIManager, UIFlatButton, UITextureButton, UILabel, UIInputText, UITextArea, UISlider, UIDropdown, UIMessageBox
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout
from pyglet.graphics import Batch


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = 'KPK'


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

        self.keys = set()
        self.speed = 125

    def on_draw(self):
        self.clear()

        self.world_camera.use()
        arcade.draw_texture_rect(self.star_sky_texture, self.phone_rect)
        self.base_tiles.draw()
        self.start_tiles.draw()
        self.upgrade_tiles.draw()
        self.player_list.draw()

    def on_update(self, delta_time):
        self.physics_engine.update()

        position = (
            self.player.center_x,
            self.player.center_y
        )
        self.world_camera.position = arcade.math.lerp_2d(  # Изменяем позицию камеры
            self.world_camera.position,
            position,
            0.12,  # Плавность следования камеры
        )

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

    def on_key_release(self, symbol, modifiers):
        self.keys.discard(symbol)


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    view = StartScreen()
    window.show_view(view)
    arcade.run()


if __name__ == '__main__':
    main()