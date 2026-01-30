import os

import arcade
from pyglet.graphics import Batch

import armor
import enemies
import items
import weapons

if not os.path.exists('assets/levels'):
    os.makedirs('assets/levels')

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = 'KPK'


class Player(arcade.Sprite):
    def __init__(self, texture, x, y, scale, slots, money, weapons_list, armor_list, bullets_list, enemies_list,
                 items_list, emitters, modifiers={}):
        super().__init__(texture, scale, x, y)
        self.modifiers = modifiers
        self.weapon = None
        self.armor = None
        self.max_health = 10 * modifiers.get('health', 1)
        self.health = self.max_health
        self.weapons_list = weapons_list
        self.bullets_list = bullets_list
        self.enemies_list = enemies_list
        self.emitters = emitters
        self.items_list = items_list
        self.armor_list = armor_list
        self.speed = 300
        self.money = money

        self.inventory = [None] * slots
        self.curr_slot = 0
        self.change_x = 0
        self.change_y = 0

    def update(self, delta_time, keys):
        self.change_x = 0
        self.change_y = 0

        if arcade.key.W in keys:
            self.change_y += self.speed
        if arcade.key.S in keys:
            self.change_y -= self.speed
        if arcade.key.D in keys:
            self.change_x += self.speed
        if arcade.key.A in keys:
            self.change_x -= self.speed

        self.center_x += self.change_x * delta_time
        self.center_y += self.change_y * delta_time

        self.center_x = max(30, min(SCREEN_WIDTH - 30, self.center_x))
        self.center_y = max(30, min(SCREEN_HEIGHT - 30, self.center_y))

        if self.weapon is not None:
            self.weapon.update(delta_time)

        if self.armor is not None:
            self.armor.update(delta_time)

    def attack(self, x, y):
        if self.weapon is not None:
            self.weapon.attack(x, y)

    def set_weapon(self, weapon):
        if self.weapon is not None:
            self.weapon.kill()

        self.weapon = weapon

        if self.weapon is not None:
            self.weapon.return_to_live()
            self.weapons_list.append(self.weapon)

    def hurt(self, damage):
        if self.health > 0:
            self.health -= damage

            if self.health <= 0:
                self.kill()
                self.health = 0

    def heal(self, health):
        self.health = min([self.max_health, self.health + health])

    def kill(self):
        super().kill()

        if self.weapon is not None:
            self.weapon.kill()

        if self.armor is not None:
            self.armor.kill()

    def next_item(self):
        if self.health > 0:
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

    def get_item(self):
        itemss = sorted(self.items_list.sprite_list, key=lambda x: x.get_distance())

        if itemss:
            if itemss[0].get_distance() <= 100:
                return itemss[0]

    def drop_item(self):
        if self.health > 0:
            if self.inventory[self.curr_slot] is not None:
                self.items_list.append(
                    items.WeaponItem(self.inventory[self.curr_slot].__class__, self.center_x, self.center_y, self,
                                     self.inventory[self.curr_slot].level))
                self.set_weapon_slot(None, self.curr_slot)

    def set_armor(self, armor):
        if self.armor is not None:
            self.armor.unapply_health()
            self.armor.kill()

        self.armor = armor

        if self.armor is not None:
            self.armor.apply_health()
            self.armor_list.append(armor)

    def drop_armor(self):
        if self.health > 0:
            if self.armor is not None:
                self.items_list.append(
                    items.ArmorItem(self.armor.__class__, self.center_x, self.center_y, self, self.armor.level))
                self.set_armor(None)


class Game(arcade.View):
    def __init__(self):
        super().__init__()

        self.current_level_id = 1

        self.player_list = arcade.SpriteList()
        self.walls = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList(True)
        self.weapons_list = arcade.SpriteList()
        self.bullets_list = []
        self.items_list = arcade.SpriteList()
        self.armor_list = arcade.SpriteList()

        self.emitters = []

        self.batch = Batch()

        self.health_bar_texture = arcade.load_texture('assets/images/gui/health_bar.png')
        self.slot_texture = arcade.load_texture('assets/images/gui/slot.png')
        self.gui_rarities = [arcade.load_texture('assets/images/gui/usual_item_gui.png'),
                             arcade.load_texture('assets/images/gui/unusual_item_gui.png'),
                             arcade.load_texture('assets/images/gui/rare_item_gui.png'),
                             arcade.load_texture('assets/images/gui/epic_item_gui.png'),
                             arcade.load_texture('assets/images/gui/legendary_item_gui.png')]
        self.texts = []

        self.showing_item = None
        self.chosen_item = None

        self.isLevelComp = False
        self.level_completion_timer = 0
        self.level_completion_triggered = False

        self.setup()

    def setup(self):
        arcade.set_background_color(arcade.color.SKY_BLUE)

        self.player = Player('assets/images/player/players/default-player.png', 400, 100, 0.5, 2, 100,
                             self.weapons_list, self.armor_list, self.bullets_list, self.enemy_list, self.items_list,
                             self.emitters, {'damage': 2, 'health': 2, 'speed': 1.5})
        self.player.set_weapon_slot(weapons.Slipper(self.player, 1), 0)
        self.player.set_weapon_slot(weapons.DarkBook(self.player, 1), 1)

        self.player.set_armor(armor.HolyArmor(self.player, 1))
        self.player_list.append(self.player)

        enemy = enemies.ShotgunEnemy(300, 500, True, self.player, (255, 102, 0), 1)
        self.enemy_list.append(enemy)

        item = items.ArmorItem(armor.MechaArmor, 100, 100, self.player, 1)
        self.items_list.append(item)

        item = items.BoughtWeapon(weapons.WaterBook, 200, 100, self.player, 2, 50)
        self.items_list.append(item)

        item = items.Chest(300, 300, 2, self.player, 5)
        self.items_list.append(item)

        self.keys = set()

    def on_update(self, delta_time):
        if self.showing_item is None:
            self.enemy_list.update(delta_time)

            emitters_copy = self.emitters.copy()
            for e in emitters_copy:
                e.update(delta_time)
            for e in emitters_copy:
                if e.can_reap():
                    self.emitters.remove(e)

            self.player_list.update(delta_time, self.keys)

        if not self.enemy_list.sprite_list and not self.level_completion_triggered:
            self.level_completion_triggered = True
            self.level_completion_timer = 10.0

        if self.level_completion_timer > 0:
            self.level_completion_timer -= delta_time
            if self.level_completion_timer <= 0:
                self.toggle_level_completion()

    def on_draw(self):
        self.clear()

        for e in self.emitters:
            e.draw()

        self.items_list.draw()
        self.player_list.draw()
        self.armor_list.draw()
        self.enemy_list.draw()

        for i in self.bullets_list:
            i.draw()

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

            if self.player.inventory[i] is not None:
                try:
                    texture = self.player.inventory[i].source_texture
                except AttributeError:
                    texture = self.player.inventory[i].texture

                arcade.draw_texture_rect(texture, rect)

            if i == self.player.curr_slot:
                rect_f = rect

        arcade.draw_rect_outline(rect_f, arcade.color.SEA_BLUE, 3)

        self.hp_text = arcade.Text(f'{round(self.player.health)}/{round(self.player.max_health)}', 675, 35,
                                   arcade.color.WHITE, 20, anchor_x='center', anchor_y='center', batch=self.batch)

        if self.showing_item is not None:
            self.draw_item()

    def on_key_press(self, symbol, modifiers):
        self.keys.add(symbol)

        if self.showing_item is None:
            if symbol == arcade.key.E:
                self.player.next_item()
            elif symbol == arcade.key.Q:
                item = self.player.get_item()

                if item is not None:
                    if type(item) is items.WeaponItem:
                        if self.player.inventory[self.player.curr_slot] is None:
                            self.chosen_item = item
                            self.showing_item = item.weapon(self.player, item.level)
                    elif type(item) is items.ArmorItem:
                        if self.player.armor is None:
                            self.chosen_item = item
                            self.showing_item = item.armor(self.player, item.level)
                    elif type(item) is items.BoughtWeapon:
                        if self.player.inventory[self.player.curr_slot] is None:
                            self.chosen_item = item
                            self.showing_item = item.weapon(self.player, item.level)
                    elif type(item) is items.BoughtArmor:
                        if self.player.armor is None:
                            self.chosen_item = item
                            self.showing_item = item.armor(self.player, item.level)
                    else:
                        item.activate()
            elif symbol == arcade.key.Z:
                self.player.drop_item()
            elif symbol == arcade.key.X:
                self.player.drop_armor()
        else:
            if symbol == arcade.key.ENTER:
                if type(self.chosen_item) is items.WeaponItem:
                    self.player.set_weapon_slot(self.showing_item, self.player.curr_slot)

                    self.chosen_item.kill()
                    self.showing_item = None
                    self.chosen_item = None
                    self.texts.clear()
                elif type(self.chosen_item) is items.ArmorItem:
                    self.player.set_armor(self.showing_item)

                    self.chosen_item.kill()
                    self.showing_item = None
                    self.chosen_item = None
                    self.texts.clear()
                elif type(self.chosen_item) is items.BoughtWeapon:
                    if self.player.money >= self.chosen_item.money:
                        self.player.money -= self.chosen_item.money
                        self.player.set_weapon_slot(self.showing_item, self.player.curr_slot)

                        self.chosen_item.kill()
                        self.showing_item = None
                        self.chosen_item = None
                        self.texts.clear()
                elif type(self.chosen_item) is items.BoughtArmor:
                    if self.player.money >= self.chosen_item.money:
                        self.player.money -= self.chosen_item.money
                        self.player.set_armor(self.showing_item)

                        self.chosen_item.kill()
                        self.showing_item = None
                        self.chosen_item = None
                        self.texts.clear()

            elif symbol == arcade.key.Q:
                self.showing_item = None
                self.chosen_item = None
                self.texts.clear()
        if symbol == arcade.key.Y:
            self.toggle_level_completion()

        if symbol == arcade.key.U:
            import upgrade
            game_view = upgrade.UpgradeWheel()
            self.window.show_view(game_view)

        if symbol == arcade.key.C:
            import case
            game_view = case.CaseWheel(100)
            self.window.show_view(game_view)

    def start_level(self, level_data):
        import random

        self.current_level_id = level_data.get("level_id", 1)

        self.keys = set()
        self.enemy_list.clear()
        self.items_list.clear()

        self.player.weapons_list = self.weapons_list
        self.player.bullets_list = self.bullets_list
        self.player.enemies_list = self.enemy_list
        self.player.items_list = self.items_list
        self.player.armor_list = self.armor_list

        self.player.center_x = 400
        self.player.center_y = 100

        map_path = level_data.get("map_path", "maps/planet_1.tmx")
        try:
            tile_map = arcade.load_tilemap(map_path)
            self.walls = tile_map.sprite_lists.get("Walls", arcade.SpriteList())
        except Exception as e:
            self.walls = arcade.SpriteList()
            for x in range(0, 800, 64):
                wall = arcade.SpriteSolidColor(64, 64, arcade.color.GRAY)
                wall.center_x = x
                wall.center_y = 32
                self.walls.append(wall)

        self.player.money = level_data.get("money", self.player.money)
        self.player.modifiers = level_data.get("modifiers", self.player.modifiers)

        for weapon_data in level_data.get("weapons", []):
            weapon_type = weapon_data["type"]
            level = weapon_data["level"]
            weapon = weapon_type(self.player, level)
            slot = weapon_data["slot"]
            self.player.set_weapon_slot(weapon, slot)

        if level_data.get("armor"):
            armor_data = level_data["armor"]
            armor_type = armor_data["type"]
            level = armor_data["level"]
            armor_instance = armor_type(self.player, level)
            self.player.set_armor(armor_instance)

        self.player.max_health = 10 * self.player.modifiers.get('health', 1)
        self.player.health = min(self.player.health, self.player.max_health)
        self.player.speed = 300

        enemy_count = 3
        for _ in range(enemy_count):
            x = random.randint(100, 700)
            y = random.randint(300, 500)
            enemy_type = random.choice(
                [enemies.ShotgunEnemy, enemies.ShootingEnemy, enemies.Enemy, enemies.FastEnemy, enemies.SlowEnemy])
            enemy = enemy_type(x, y, True, self.player,
                               (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)),
                               level_data.get("level", 1))
            self.enemy_list.append(enemy)

        item_count = random.randint(2, 4)
        for _ in range(item_count):
            x = random.randint(50, 750)
            y = random.randint(100, 400)
            item_type = random.choice([items.Chest, items.WeaponItem, items.ArmorItem])

            if item_type == items.Chest:
                level = random.randint(1, 5)
                cost = random.randint(1, 3)
                item = items.Chest(x, y, level, self.player, cost)
            else:
                weapon_or_armor = random.choice(
                    [weapons.DarkBook, weapons.WaterBook, armor.HolyArmor, armor.MechaArmor])
                level = random.randint(1, 5)
                item = item_type(weapon_or_armor, x, y, self.player, level)

            self.items_list.append(item)

    def toggle_level_completion(self):
        from test_main import LevelTransitionView
        level_transition_view = LevelTransitionView(self, True, self.current_level_id)
        self.window.show_view(level_transition_view)

    def on_key_release(self, symbol, modifiers):
        self.keys.discard(symbol)

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.player.attack(x, y)

    def draw_item(self):
        texture = self.gui_rarities[self.showing_item.rarity - 1]

        rect = arcade.Rect(250, 550, 200, 400, 300, 200, 400, 300)
        arcade.draw_texture_rect(texture, rect)

        try:
            texture = self.showing_item.source_texture
        except AttributeError:
            texture = self.showing_item.texture

        rect = arcade.Rect(265, 315, 335, 385, 50, 50, 290, 360)
        arcade.draw_texture_rect(texture, rect)

        self.texts = [
            arcade.Text(self.showing_item.return_name(), 320, 380, font_size=13, anchor_x='left', anchor_y='center',
                        batch=self.batch)]
        texts = self.showing_item.return_desc().split('\n')

        for i in range(len(texts)):
            self.texts.append(arcade.Text(texts[i], 265, 310 - 20 * i, font_size=10, batch=self.batch))

        if type(self.chosen_item) is items.BoughtWeapon or type(self.chosen_item) is items.BoughtArmor:
            text_y = 100
            self.texts.append(
                arcade.Text(f'Цена предмета: {self.chosen_item.money}', 400, 150, font_size=20, anchor_x='center',
                            anchor_y='center', batch=self.batch))
            self.texts.append(
                arcade.Text(f'Баланс: {self.player.money}', 10, 580, font_size=20, anchor_y='center', batch=self.batch))
        else:
            text_y = 150

        self.texts.append(
            arcade.Text('ENTER чтобы подтвердить и Q чтобы выйти', 400, text_y, font_size=20, anchor_x='center',
                        anchor_y='center', batch=self.batch))


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    view = Game()
    window.show_view(view)
    arcade.run()


if __name__ == '__main__':
    main()
