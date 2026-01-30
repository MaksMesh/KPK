import json
import math
import random
import arcade


class StarNode:
    def __init__(self, level_id, x, y, name, unlocked=False, completed=False):
        self.level_id = level_id
        self.position = (x, y)
        self.name = name
        self.unlocked = unlocked
        self.completed = completed
        self.connections = []

    def add_connection(self, node):
        if node not in self.connections:
            self.connections.append(node)


class LevelGraph:
    def __init__(self):
        self.nodes = {}
        self.start_node = None
        self.current_node = None
        self.all_completed = False
        self.last_visited_id = 1

    def add_node(self, level_id, x, y, name, unlocked=False, completed=False):
        node = StarNode(level_id, x, y, name, unlocked, completed)
        self.nodes[level_id] = node
        if level_id == 1:
            node.unlocked = True
            self.start_node = node
            if not self.current_node:
                self.current_node = node
        return node

    def connect_nodes(self, level_id1, level_id2):
        node1 = self.nodes.get(level_id1)
        node2 = self.nodes.get(level_id2)
        if node1 and node2:
            node1.add_connection(node2)
            node2.add_connection(node1)

    def unlock_node(self, level_id):
        node = self.nodes.get(level_id)
        if node:
            node.unlocked = True

    def complete_node(self, level_id):
        node = self.nodes.get(level_id)
        if node:
            node.completed = True
            node.unlocked = False

    def get_accessible_nodes(self):
        if not self.current_node:
            return []
        return [node for node in self.current_node.connections if node.unlocked and not node.completed]

    def move_to_node(self, level_id):
        target = self.nodes.get(level_id)
        if target and target.unlocked and not target.completed:
            self.current_node = target
            self.last_visited_id = level_id
            return True
        return False

    def check_all_completed(self):
        if not self.nodes:
            return False
        for node in self.nodes.values():
            if not node.completed:
                return False
        self.all_completed = True
        return True

    def save_to_file(self, filename):
        data = {
            'nodes': [],
            'connections': [],
            'current_node_id': self.last_visited_id,
            'last_visited_id': self.last_visited_id
        }

        for node in self.nodes.values():
            data['nodes'].append({
                'id': node.level_id,
                'x': node.position[0],
                'y': node.position[1],
                'name': node.name,
                'unlocked': node.unlocked,
                'completed': node.completed
            })

        for node in self.nodes.values():
            for connection in node.connections:
                if connection.level_id > node.level_id:
                    data['connections'].append([node.level_id, connection.level_id])

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    def load_from_file(self, filename):
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


            last_visited_id = data.get('last_visited_id', 1)
            if last_visited_id in self.nodes:
                self.current_node = self.nodes[last_visited_id]
                self.last_visited_id = last_visited_id

            if self.current_node:
                for node in self.current_node.connections:
                    if not node.completed:
                        self.unlock_node(node.level_id)

        except Exception as e:
            print(f"Ошибка загрузки графа: {e}")
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
    def __init__(self, game_instance=None, is_level_comp=False, completed_node_id=None):
        super().__init__()
        self.window.set_mouse_visible(True)
        self.game = game_instance
        self.level_graph = LevelGraph()
        self.level_data = {
            "money": 100,
            "modifiers": {},
            "weapons": [],
            "armor": None,
            "level": 1,
            "map_path": "maps/planet_1.tmx",
            "level_id": 1
        }

        if game_instance and hasattr(game_instance, 'player'):
            self.level_data["money"] = game_instance.player.money
            self.level_data["modifiers"] = game_instance.player.modifiers.copy()

            for i, weapon in enumerate(game_instance.player.inventory):
                if weapon:
                    self.level_data["weapons"].append({
                        "type": weapon.__class__,
                        "level": weapon.level,
                        "slot": i
                    })

            if game_instance.player.armor:
                self.level_data["armor"] = {
                    "type": game_instance.player.armor.__class__,
                    "level": game_instance.player.armor.level
                }

        try:
            self.level_graph.load_from_file('assets/levels/level_graph.json')
        except:
            self.level_graph.create_default_graph()
            self.level_graph.save_to_file('assets/levels/level_graph.json')

        if completed_node_id is not None:
            self.level_graph.complete_node(completed_node_id)
            completed_node = self.level_graph.nodes.get(completed_node_id)
            if completed_node:
                for node in completed_node.connections:
                    if not node.completed:
                        self.level_graph.unlock_node(node.level_id)

        self.level_graph.save_to_file('assets/levels/level_graph.json')

        if self.level_graph.check_all_completed():
            self.generate_random_graph()

        self.spaceship_texture = arcade.load_texture('assets/images/ui/spaceship.png')
        self.star_locked_texture = arcade.load_texture('assets/images/ui/star_locked.png')
        self.star_unlocked_texture = arcade.load_texture('assets/images/ui/star_unlocked.png')
        self.star_hover_texture = arcade.load_texture('assets/images/ui/star_hover.png')
        self.star_current_texture = arcade.load_texture('assets/images/ui/star_current.png')
        self.star_completed_texture = self.create_darkened_texture(self.star_locked_texture)

        self.selected_node = None
        self.hovered_node = None

        if self.level_graph.current_node:
            self.spaceship_position = self.level_graph.current_node.position
            self.selected_node = self.level_graph.current_node
        else:
            self.spaceship_position = (400, 300)

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

    def create_darkened_texture(self, texture):
        from PIL import ImageEnhance
        image = texture.image
        enhancer = ImageEnhance.Brightness(image)
        darkened_image = enhancer.enhance(0.3)
        return arcade.Texture(darkened_image)

    def generate_random_graph(self):
        self.level_graph = LevelGraph()
        base_x, base_y = 400, 300
        self.level_graph.add_node(1, base_x, base_y, "Стартовая база", True, False)
        planet_names = ["Марс", "Венера", "Меркурий", "Юпитер", "Сатурн", "Уран", "Нептун", "Плутон", "Церера", "Эрида",
                        "Татуин", "Альдераан", "Эндор", "Джакку", "Корусант"]
        random.shuffle(planet_names)
        planet_types = ["пустынная", "ледяная", "горная", "водная", "лесная", "вулканическая", "газовая",
                        "металлическая", "болотистая", "радиоактивная"]
        random.shuffle(planet_types)
        num_planets = random.randint(4, 7)
        nodes = [self.level_graph.nodes[1]]
        used_names = set()

        for i in range(2, num_planets + 2):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(150, 350)
            x = base_x + distance * math.cos(angle)
            y = base_y + distance * math.sin(angle)

            while True:
                base_name = random.choice(planet_names)
                planet_type = random.choice(planet_types)
                name = f"{base_name} ({planet_type})"
                if name not in used_names:
                    used_names.add(name)
                    break

            if i == 2:
                unlocked = True
            else:
                unlocked = False

            self.level_graph.add_node(i, x, y, name, unlocked, False)
            nodes.append(self.level_graph.nodes[i])

        for i in range(len(nodes)):
            connections = random.randint(1, 3)
            possible_connections = [j for j in range(len(nodes)) if j != i]
            random.shuffle(possible_connections)
            for j in range(min(connections, len(possible_connections))):
                target_idx = possible_connections[j]
                self.level_graph.connect_nodes(nodes[i].level_id, nodes[target_idx].level_id)

        self.level_graph.current_node = self.level_graph.nodes[1]
        self.level_graph.save_to_file('assets/levels/level_graph.json')

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
                status = "Зачищено"
            elif node.unlocked:
                color = arcade.color.WHITE
                status = "Доступно для высадки" if node != self.selected_node else "Текущий"
            else:
                color = arcade.color.GRAY
                status = "Заблокирован"

            arcade.draw_text(node.name, node.position[0], node.position[1] - 30, color, 12, anchor_x="center")
            arcade.draw_text(status, node.position[0], node.position[1] - 50, color, 10, anchor_x="center")

        ship_x, ship_y = self.spaceship_position
        rect = arcade.rect.XYWH(ship_x, ship_y, self.spaceship_texture.width * 0.1, self.spaceship_texture.height * 0.1)
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
                    ship_x + dx / distance * move_distance, ship_y + dy / distance * move_distance)
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
            self.selected_node = closest_node
            self.spaceship_target = closest_node
            self.selected_info_text = None
            self.selected_warning_text = None

    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE and self.selected_node:
            if not self.selected_node.completed:
                if self.level_graph.move_to_node(self.selected_node.level_id):
                    self.level_data["level"] += 1
                    self.level_data["map_path"] = self.generate_random_map()
                    self.level_data["level_id"] = self.selected_node.level_id

                    self.level_graph.save_to_file('assets/levels/level_graph.json')

                    from main import Game
                    game_view = Game()
                    game_view.start_level(self.level_data)
                    self.window.show_view(game_view)
                else:
                    self.selected_info_text = arcade.Text(f"Ошибка: нельзя высадиться на {self.selected_node.name}",
                                                          400, 50, arcade.color.RED, 24, anchor_x="center")
            else:
                self.selected_warning_text = arcade.Text("Высадка невозможна на пройденный уровень", 400, 25,
                                                         arcade.color.RED, 16, anchor_x="center")
        elif key == arcade.key.ESCAPE:
            if self.game:
                self.window.show_view(self.game)

    def generate_random_map(self):
        map_templates = ["maps/planet_1.tmx", "maps/planet_2.tmx", "maps/planet_3.tmx", "maps/planet_4.tmx",
                         "maps/planet_5.tmx"]
        import os
        existing_maps = []
        for map_file in map_templates:
            if os.path.exists(map_file):
                existing_maps.append(map_file)

        if existing_maps:
            return random.choice(existing_maps)
        else:
            return "maps/planet_1.tmx"