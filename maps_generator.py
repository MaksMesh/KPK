import arcade


SCREEN_WIDTH = 1050
SCREEN_HEIGHT = 700
SCREEN_TITLE = "Castle Tiles"
TILE_SCALING = 1.0
SPEED = 4


class GridGame(arcade.View):
    def __init__(self, map_name):
        super().__init__()
        self.world_camera = arcade.camera.Camera2D()
        self.gui_camera = arcade.camera.Camera2D()
        self.map_name = map_name
        self.tile_map = arcade.load_tilemap(self.map_name, scaling=TILE_SCALING)
        self.scene = arcade.Scene.from_tilemap(self.tile_map)

    def setup(self):
        pass

    def on_draw(self):
        self.clear()
        self.scene.draw()
