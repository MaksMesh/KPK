import json
import math

import arcade


class StarNode:
    def __init__(self, level_id: int, x: float, y: float, name: str, unlocked: bool = False, completed: bool = False):
        self.level_id = level_id
        self.position = (x, y)
        self.name = name
        self.unlocked = unlocked
        self.completed = completed
        self.connections = []

    def add_connection(self, node):
        if node not in self.connections:
            self.connections.append(node)

    def __repr__(self):
        return f"StarNode({self.level_id}, {self.name})"


class LevelGraph:
    def __init__(self):
        self.nodes = {}
        self.start_node = None
        self.current_node = None

    def add_node(self, level_id: int, x: float, y: float, name: str, unlocked: bool = False, completed: bool = False):
        node = StarNode(level_id, x, y, name, unlocked, completed)
        self.nodes[level_id] = node
        if level_id == 1:
            node.unlocked = True
            self.start_node = node
            self.current_node = node
        return node

    def connect_nodes(self, level_id1: int, level_id2: int):
        node1 = self.nodes.get(level_id1)
        node2 = self.nodes.get(level_id2)
        if node1 and node2:
            node1.add_connection(node2)
            node2.add_connection(node1)

    def unlock_node(self, level_id: int):
        node = self.nodes.get(level_id)
        if node:
            node.unlocked = True

    def complete_node(self, level_id: int):
        node = self.nodes.get(level_id)
        if node:
            node.completed = True
            node.unlocked = False

    def get_accessible_nodes(self):
        if not self.current_node:
            return []
        return [node for node in self.current_node.connections if node.unlocked and not node.completed]

    def move_to_node(self, level_id: int):
        target = self.nodes.get(level_id)
        if target and target.unlocked and not target.completed and target in self.get_accessible_nodes():
            self.current_node = target
            return True
        return False

    def load_from_file(self, filename: str):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)

            for node_data in data['nodes']:
                self.add_node(
                    node_data['id'],
                    node_data['x'],
                    node_data['y'],
                    node_data['name'],
                    node_data.get('unlocked', False),
                    node_data.get('completed', False)
                )

            for connection in data['connections']:
                self.connect_nodes(connection[0], connection[1])

            start_id = data.get('start_id', 1)
            self.current_node = self.nodes.get(start_id)

        except Exception as e:
            print(f"Error loading level graph: {e}")
            self.create_default_graph()

    def create_default_graph(self):
        self.add_node(1, 400, 300, "Земля", True, False)
        self.add_node(2, 600, 400, "Планета верх", False, False)
        self.add_node(3, 600, 200, "Планета низ", False, False)
        self.add_node(4, 800, 450, "Планета 1", False, False)
        self.add_node(5, 800, 150, "Планета 2", False, False)
        self.add_node(6, 1000, 300, "Планета Железяка", False, False)

        self.connect_nodes(1, 2)
        self.connect_nodes(1, 3)
        self.connect_nodes(2, 4)
        self.connect_nodes(3, 5)
        self.connect_nodes(4, 6)
        self.connect_nodes(5, 6)


class LevelTransitionView(arcade.View):
    def __init__(self, game_instance, is_level_comp: bool):
        super().__init__()
        self.window.set_mouse_visible(True)
        self.game = game_instance
        self.level_graph = LevelGraph()
        self.maps = {"Планета верх": "maps/planet_1.tmx",
                     "Планета низ": "maps/planet_2.tmx",
                     "Планета 1": "maps/planet_3.tmx",
                     "Планета 2": "maps/planet_4.tmx",
                     "Планета Железяка": "maps/planet_5.tmx"}

        try:
            self.level_graph.load_from_file('assets/levels/level_graph.json')
        except:
            self.level_graph.create_default_graph()

        self.spaceship_texture = arcade.load_texture('assets/images/ui/spaceship.png')
        self.star_locked_texture = arcade.load_texture('assets/images/ui/star_locked.png')
        self.star_unlocked_texture = arcade.load_texture('assets/images/ui/star_unlocked.png')
        self.star_hover_texture = arcade.load_texture('assets/images/ui/star_hover.png')
        self.star_current_texture = arcade.load_texture('assets/images/ui/star_current.png')

        self.star_completed_texture = self.create_darkened_texture(self.star_locked_texture)

        self.selected_node = None
        self.hovered_node = None
        self.spaceship_position = self.level_graph.current_node.position if self.level_graph.current_node else (
            400, 300)
        self.spaceship_target = None
        self.spaceship_speed = 200

        self.camera = arcade.camera.Camera2D()
        self.camera.position = self.spaceship_position

        self.title_text = arcade.Text("Карта Галактики", 400, 550, arcade.color.GOLD, 36, anchor_x="center")
        self.hint_text = arcade.Text("Кликните на звезду для перелета", 400, 500, arcade.color.LIGHT_GRAY, 20,
                                     anchor_x="center")
        self.landing_hint = arcade.Text("Нажмите ПРОБЕЛ чтобы начать высадку", 400, 70, arcade.color.LIGHT_GRAY, 20,
                                        anchor_x="center")

        self.selected_info_text = None
        self.selected_warning_text = None

        if is_level_comp:
            self.complete_current_level()

    def create_darkened_texture(self, texture):
        from PIL import ImageEnhance
        image = texture.image
        enhancer = ImageEnhance.Brightness(image)
        darkened_image = enhancer.enhance(0.3)
        return arcade.Texture(darkened_image)

    def complete_current_level(self):
        if self.level_graph.current_node:
            current_id = self.level_graph.current_node.level_id
            self.level_graph.complete_node(current_id)

            for node in self.level_graph.current_node.connections:
                self.level_graph.unlock_node(node.level_id)

    def on_draw(self):
        self.clear(arcade.color.DARK_SLATE_GRAY)

        self.camera.use()

        for node in self.level_graph.nodes.values():
            for connection in node.connections:
                if connection.level_id > node.level_id:
                    start_x, start_y = node.position
                    end_x, end_y = connection.position

                    if node.completed or connection.completed:
                        color = arcade.color.DARK_GRAY
                    elif node.unlocked and connection.unlocked:
                        color = arcade.color.GOLD
                    else:
                        color = arcade.color.LIGHT_GRAY

                    arcade.draw_line(start_x, start_y, end_x, end_y, color, 2)

        for node in self.level_graph.nodes.values():
            if node.completed:
                texture = self.star_completed_texture
            elif node == self.selected_node and node.unlocked and not node.completed:
                texture = self.star_current_texture
            elif node == self.hovered_node and node.unlocked and not node.completed:
                texture = self.star_hover_texture
            elif node.unlocked and not node.completed:
                texture = self.star_unlocked_texture
            else:
                texture = self.star_locked_texture

            rect = arcade.rect.XYWH(node.position[0], node.position[1], 40, 40)
            arcade.draw_texture_rect(texture, rect)

            if node.completed:
                color = arcade.color.DARK_GRAY
                status = ("Зачищено")
            elif node.unlocked:
                color = arcade.color.WHITE
                status = "Доступно для высадки" if node != self.selected_node else "Текущий"
            else:
                color = arcade.color.GRAY
                status = "Заблокирован"

            arcade.draw_text(
                node.name,
                node.position[0], node.position[1] - 30,
                color, 12, anchor_x="center"
            )

            arcade.draw_text(
                status,
                node.position[0], node.position[1] - 50,
                color, 10, anchor_x="center"
            )

        ship_x, ship_y = self.spaceship_position
        rect = arcade.rect.XYWH(ship_x, ship_y,
                                self.spaceship_texture.width * 0.1,
                                self.spaceship_texture.height * 0.1)
        arcade.draw_texture_rect(self.spaceship_texture, rect)

        arcade.camera.Camera2D().use()

        self.title_text.draw()
        self.hint_text.draw()
        self.landing_hint.draw()

        if self.selected_info_text:
            self.selected_info_text.draw()
        if self.selected_warning_text:
            self.selected_warning_text.draw()

    def on_update(self, delta_time):
        if self.spaceship_target:
            target_x, target_y = self.spaceship_target.position
            ship_x, ship_y = self.spaceship_position

            dx = target_x - ship_x
            dy = target_y - ship_y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance > 5:
                move_distance = self.spaceship_speed * delta_time
                if move_distance > distance:
                    self.spaceship_position = (target_x, target_y)
                    self.selected_node = self.spaceship_target
                else:
                    self.spaceship_position = (
                        ship_x + dx / distance * move_distance,
                        ship_y + dy / distance * move_distance
                    )
            else:
                self.spaceship_position = (target_x, target_y)
                self.selected_node = self.spaceship_target

        self.camera.position = self.spaceship_position

    def on_mouse_motion(self, x, y, dx, dy):
        self.hovered_node = None

        world_x = x + (self.camera.position[0] - 400)
        world_y = y + (self.camera.position[1] - 300)

        for node in self.level_graph.nodes.values():
            if node.completed or not node.unlocked:
                continue

            distance = math.sqrt((world_x - node.position[0]) ** 2 + (world_y - node.position[1]) ** 2)
            if distance < 25:
                self.hovered_node = node
                break

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        closest_node = None
        min_distance = float('inf')

        world_x = x + (self.camera.position[0] - 400)
        world_y = y + (self.camera.position[1] - 300)

        for node in self.level_graph.nodes.values():
            if not node.unlocked:
                continue

            distance = math.sqrt((world_x - node.position[0]) ** 2 + (world_y - node.position[1]) ** 2)
            if distance < 25 and distance < min_distance:
                min_distance = distance
                closest_node = node

        if closest_node:
            self.spaceship_target = closest_node
            self.selected_info_text = None
            self.selected_warning_text = None

    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE and self.selected_node:
            if not self.selected_node.completed:
                if self.level_graph.move_to_node(self.selected_node.level_id):
                    import maps_generator
                    maps_generator_view = maps_generator.GridGame(self.maps[self.selected_node.name])
                    self.window.show_view(maps_generator_view)
                    # self.window.show_view(self.game)
                    self.game.start_level(self.selected_node.level_id)
                else:
                    self.selected_info_text = arcade.Text(
                        f"Ошибка: нельзя высадиться на {self.selected_node.name}",
                        400, 50, arcade.color.RED, 24, anchor_x="center"
                    )
            else:
                self.selected_warning_text = arcade.Text(
                    "Высадка невозможна на пройденный уровень",
                    400, 25, arcade.color.RED, 16, anchor_x="center"
                )
        elif key == arcade.key.ESCAPE:
            self.window.show_view(self.game)
