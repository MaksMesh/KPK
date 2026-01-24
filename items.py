import arcade


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