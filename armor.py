import arcade


class BaseArmor(arcade.Sprite):
    def __init__(self, texture, scale, health, player, level):
        super().__init__(texture, scale)
        self.health = health * player.modifiers.get('health', 1)
        self.player = player
        self.level = level

        self.name = ''

        self.apply_level()

    def apply_level(self):
        self.health *= self.level / 10 + 0.9

    def update(self, delta_time):
        self.position = self.player.position

    def apply_health(self):
        hp = self.player.max_health + self.health
        self.player.health = self.player.health / self.player.max_health * hp
        self.player.max_health = hp

    def unapply_health(self):
        hp = self.player.max_health - self.health
        self.player.health = self.player.health / self.player.max_health * hp
        self.player.max_health = hp

    def return_name(self):
        return self.name

    def return_desc(self):
        return f'Уровень: {self.level}\nЗдоровье: {self.health}'


class WoodenArmor(BaseArmor):
    def __init__(self, player, level):
        super().__init__('assets/images/armor/wooden_armor.png', player.scale, 10, player, level)
        self.rarity = 1
        self.name = 'Деревянная броня'


class IronArmor(BaseArmor):
    def __init__(self, player, level):
        super().__init__('assets/images/armor/iron_armor.png', player.scale, 13, player, level)
        self.rarity = 2
        self.name = 'Железная броня'


class DiamondArmor(BaseArmor):
    def __init__(self, player, level):
        super().__init__('assets/images/armor/diamond_armor.png', player.scale, 16, player, level)
        self.rarity = 3
        self.name = 'Алмазная броня'


class HolyArmor(BaseArmor):
    def __init__(self, player, level):
        super().__init__('assets/images/armor/holy_armor.png', player.scale, 20, player, level)
        self.rarity = 4
        self.name = 'Святая броня'


class MechaArmor(BaseArmor):
    def __init__(self, player, level):
        super().__init__('assets/images/armor/mecha_armor.png', player.scale, 25, player, level)
        self.rarity = 5
        self.name = 'Меха-броня'