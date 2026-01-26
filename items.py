import arcade
import random
import weapons
import armor


class Item(arcade.Sprite):
    def __init__(self, texture, scale, x, y):
        super().__init__(texture, scale, x, y)

    def activate(self):
        pass


class WeaponItem(Item):
    def __init__(self, weapon, x, y, player, level):
        weaponex = weapon(player, 1)

        try:
            texture = weaponex.source_texture
        except AttributeError:
            texture = weaponex.texture

        super().__init__(texture, weaponex.scale, x, y)

        self.weapon = weapon
        self.player = player
        self.level = level

    def activate(self):
        if self.player.inventory[self.player.curr_slot] is None:
            self.player.set_weapon_slot(self.weapon(self.player, self.level), self.player.curr_slot)
            self.kill()

    def get_distance(self):
        return arcade.math.get_distance(*self.player.position, *self.position)


class ArmorItem(Item):
    def __init__(self, armor, x, y, player, level):
        armorex = armor(player, 1)

        try:
            texture = armorex.source_texture
        except AttributeError:
            texture = armorex.texture

        super().__init__(texture, armorex.scale, x, y)

        self.armor = armor
        self.player = player
        self.level = level

    def activate(self):
        if self.player.inventory[self.player.curr_slot] is None:
            self.player.set_armor(self.armor(self.player, self.level))
            self.kill()

    def get_distance(self):
        return arcade.math.get_distance(*self.player.position, *self.position)


class Chest(Item):
    def __init__(self, x, y, scale, player, level):
        super().__init__('assets/images/items/chest.png', scale, x, y)
        self.level = level
        self.player = player

    def activate(self):
        loot = self.get_loot()

        for i in loot:
            i.position = arcade.math.rand_in_circle((self.center_x, self.center_y), 100)
            self.player.items_list.append(i)

        self.kill()

    def get_loot(self):
        loot = []

        min_level = max([self.level - 2, 1])
        max_level = min([self.level + 2, 100])

        weaponss = random.randint(0, 2)
        armors = random.randint(0, 2)
        money_count = random.randint(1, 10 + self.player.modifiers.get('lucky', 0))

        for _ in range(weaponss):
            level = random.randint(min_level, max_level)

            rarity = random.random()
            lucky = self.player.modifiers.get('lucky', 0) * 0.01

            if rarity < 0.3 - lucky:
                rarity = 1
            elif rarity < 0.65 - lucky:
                rarity = 2
            elif rarity < 0.85 - lucky:
                rarity = 3
            elif rarity < 0.95 - lucky:
                rarity = 4
            else:
                rarity = 5

            loot.append(WeaponItem(random.choice(weapons.RARITY_TO_WEAPONS[rarity]), self.center_x, self.center_y, self.player, level))

        for _ in range(armors):
            level = random.randint(min_level, max_level)

            rarity = random.random()
            lucky = self.player.modifiers.get('lucky', 0) * 0.01

            if rarity < 0.3 - lucky:
                rarity = 1
            elif rarity < 0.65 - lucky:
                rarity = 2
            elif rarity < 0.85 - lucky:
                rarity = 3
            elif rarity < 0.95 - lucky:
                rarity = 4
            else:
                rarity = 5

            loot.append(ArmorItem(random.choice(armor.RARITY_TO_ARMOR[rarity]), self.center_x, self.center_y, self.player, level))

        for _ in range(money_count):
            loot.append(Money(1, self.center_x, self.center_y, self.player))

        loot.append(random.choice([Olyvie, Donut, Heart])(1.5, self.center_x, self.center_y, self.player))

        return loot

    def get_distance(self):
        return arcade.math.get_distance(*self.player.position, *self.position)


class BoughtWeapon(WeaponItem):
    def __init__(self, weapon, x, y, player, level, money):
        super().__init__(weapon, x, y, player, level)
        self.money = money
        self.color = arcade.color.YELLOW


class BoughtArmor(ArmorItem):
    def __init__(self, armor, x, y, player, level, money):
        super().__init__(armor, x, y, player, level)
        self.money = money
        self.color = arcade.color.YELLOW


class Money(Item):
    def __init__(self, scale, x, y, player):
        super().__init__('assets/images/items/money.png', scale, x, y)
        self.player = player

    def activate(self):
        self.player.money += 10
        self.kill()

    def get_distance(self):
        return arcade.math.get_distance(*self.player.position, *self.position)


class HealingItem(Item):
    def __init__(self, texture, scale, x, y, player):
        super().__init__(texture, scale, x, y)
        self.player = player

    def activate(self):
        self.player.heal(self.get_heal())
        self.kill()

    def get_distance(self):
        return arcade.math.get_distance(*self.player.position, *self.position)

    def get_heal(self):
        return 10


class Olyvie(HealingItem):
    def __init__(self, scale, x, y, player):
        super().__init__('assets/images/items/olyvie.png', scale, x, y, player)
    
    def get_heal(self):
        return self.player.max_health / 5


class Donut(HealingItem):
    def __init__(self, scale, x, y, player):
        super().__init__('assets/images/items/donut.png', scale, x, y, player)
    
    def get_heal(self):
        return self.player.max_health / 2


class Heart(HealingItem):
    def __init__(self, scale, x, y, player):
        super().__init__('assets/images/items/heart.png', scale, x, y, player)
    
    def get_heal(self):
        return self.player.max_health