import random
import math
import arcade
from typing import List, Any, Optional

import main

player_coins = 100


class RouletteItem:
    def __init__(self, name: str, item_type: str, rarity: str, weight: float, color: arcade.color):
        self.name = name
        self.type = item_type
        self.rarity = rarity
        self.weight = weight
        self.color = color


class CaseCore:

    def __init__(self, center_x: float, center_y: float, radius: float, items: List[RouletteItem], player_coins):
        self.player_coins = player_coins
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.items = items

        # Рассчитываем углы и кумулятивные веса
        self._prepare_wheel_segments()

        # Состояние анимации
        self.is_spinning = False
        self.spin_speed = 0.0
        self.max_speed = 25.0  # Макс. угловая скорость (градусов/кадр)
        self.friction = 1  # Коэффициент замедления
        self.angle = 0.0  # Текущий угол поворота рулетки
        self.final_angle = 0.0  # Угол, на котором должна остановиться рулетка
        self.result_item: Optional[RouletteItem] = None

        # Звуки - используем существующие звуки из ресурсов arcade
        try:
            self.sound_spin = arcade.load_sound(":resources:sounds/coin1.wav")  # Звук запуска
            self.sound_click = arcade.load_sound(":resources:sounds/hit1.wav")  # Звук тика (щелчка)
            self.sound_win = arcade.load_sound(":resources:sounds/upgrade1.wav")  # Звук победы
            self.use_sounds = True
        except FileNotFoundError:
            # Если звуки не найдены, работаем без них
            self.use_sounds = False
            print("Звуки не найдены, рулетка будет работать без звука")

    def _prepare_wheel_segments(self):
        total_weight = sum(item.weight for item in self.items)
        self.segments = []
        current_angle = 0.0

        for item in self.items:
            # Доля предмета в общем весе = доля в 360 градусах
            sweep_angle = 360 * (item.weight / total_weight)
            self.segments.append({
                'item': item,
                'start_angle': current_angle,
                'end_angle': current_angle + sweep_angle,
                'mid_angle': current_angle + sweep_angle / 2
            })
            current_angle += sweep_angle

    def spin(self):
        if self.is_spinning:
            return

        self.is_spinning = True
        self.spin_speed = self.max_speed
        self.result_item = None

        # Случайно выбираем предмет на основе весов
        chosen_item = random.choices(self.items, weights=[i.weight for i in self.items])[0]

        # Находим сегмент этого предмета и определяем целевой угол для остановки.
        # Мы хотим, чтобы указатель остановился напротив этого сегмента.
        for seg in self.segments:
            if seg['item'] == chosen_item:
                # Целевой угол - середина сегмента, но с несколькими лишними оборотами для эффекта
                extra_rotations = random.randint(3, 5)  # Добавляем от 3 до 5 полных оборотов
                self.final_angle = 360 * extra_rotations - seg['mid_angle']
                self.result_item = chosen_item
                break

        # Проигрываем звук запуска
        if self.use_sounds:
            arcade.play_sound(self.sound_spin)

    def update(self, delta_time: float):
        if not self.is_spinning:
            return

        # Применяем вращение
        self.angle += self.spin_speed

        # Проигрываем щелчок при замедлении (каждые 45 градусов)
        if self.use_sounds and 1.0 < self.spin_speed < 5.0 and int(self.angle / 45) != int(
                (self.angle - self.spin_speed) / 45):
            arcade.play_sound(self.sound_click, volume=0.3)

        # Применяем "трение" для замедления
        self.spin_speed *= self.friction

        # Проверяем, не подошли ли мы к целевому углу и не замедлились ли достаточно
        target_angle_reached = self.angle >= self.final_angle
        print(target_angle_reached, self.spin_speed)
        if target_angle_reached:
            self.is_spinning = False
            self.spin_speed = 0.0
            # Фиксируем угол точно на целевом для красоты
            self.angle = self.final_angle % 360
            if self.result_item:
                # Проигрываем звук победы
                if self.use_sounds:
                    arcade.play_sound(self.sound_win)
                print(f"Поздравляем! Вы выиграли: {self.result_item.name} ({self.result_item.rarity})")
        if self.result_item.name == "1000 монет":
            self.player_coins += 1000

    def draw(self):
        # 1. Рисуем сегменты колеса
        for seg in self.segments:
            start_rad = math.radians(seg['start_angle'] + self.angle)
            end_rad = math.radians(seg['end_angle'] + self.angle)

            # Создаем список точек в правильном формате [(x1, y1), (x2, y2), ...]
            points = [(self.center_x, self.center_y)]  # Начинаем с центра

            # Генерируем точки дуги (идем от start_angle к end_angle)
            num_points = 20
            for i in range(num_points + 1):
                frac = i / num_points
                angle_rad = start_rad + (end_rad - start_rad) * frac
                x = self.center_x + self.radius * math.cos(angle_rad)
                y = self.center_y + self.radius * math.sin(angle_rad)
                points.append((x, y))

            # Рисуем сегмент
            arcade.draw_polygon_filled(points, seg['item'].color)

        # 2. Рисуем обводку и центральный круг
        arcade.draw_circle_outline(self.center_x, self.center_y, self.radius, arcade.color.BLACK, 5)
        arcade.draw_circle_filled(self.center_x, self.center_y, self.radius * 0.1, arcade.color.WHITE)
        arcade.draw_circle_outline(self.center_x, self.center_y, self.radius * 0.1, arcade.color.BLACK, 2)

        # 3. Рисуем указатель (треугольник сверху)
        pointer_height = self.radius * 1.15
        pointer_width = 20
        points = [
            (self.center_x, self.center_y + pointer_height),  # Острие
            (self.center_x - pointer_width, self.center_y + pointer_height - 30),  # Левое основание
            (self.center_x + pointer_width, self.center_y + pointer_height - 30),  # Правое основание
        ]
        arcade.draw_triangle_filled(points[0][0], points[0][1],
                                    points[1][0], points[1][1],
                                    points[2][0], points[2][1],
                                    arcade.color.RED)
        arcade.draw_triangle_outline(points[0][0], points[0][1],
                                     points[1][0], points[1][1],
                                     points[2][0], points[2][1],
                                     arcade.color.BLACK, 2)

        # 4. Если есть результат, показываем его под рулеткой
        if self.result_item and not self.is_spinning:
            # Определяем цвет текста в зависимости от редкости
            text_color = self.result_item.color
            # Делаем текст более контрастным для темных цветов
            r, g, b = text_color[0], text_color[1], text_color[2]
            brightness = (r + g + b) / 3
            if brightness < 128:
                text_color = arcade.color.WHITE

            result_text = f"ВЫ ВЫИГРАЛИ: {self.result_item.name}!"
            arcade.draw_text(result_text,
                             self.center_x, self.center_y - self.radius - 40,
                             text_color,
                             font_size=24, anchor_x="center",
                             bold=True)

    def get_result(self) -> Optional[RouletteItem]:
        if not self.is_spinning and self.result_item:
            return self.result_item
        return None


# Упрощенная версия для отладки (использует arcade.draw_arc_filled вместо polygon)
class SimpleCaseCore:

    def __init__(self, center_x: float, center_y: float, radius: float, items: List[RouletteItem], player_coins):
        self.player_coins = player_coins
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.items = items

        # Рассчитываем углы
        self._prepare_wheel_segments()

        # Состояние анимации
        self.is_spinning = False
        self.spin_speed = 0.0
        self.max_speed = 25.0
        self.friction = 1
        self.angle = 0.0
        self.final_angle = 0.0
        self.result_item: Optional[RouletteItem] = None

    def _prepare_wheel_segments(self):
        total_weight = sum(item.weight for item in self.items)
        self.segments = []
        current_angle = 0.0

        for item in self.items:
            sweep_angle = 360 * (item.weight / total_weight)
            self.segments.append({
                'item': item,
                'start_angle': current_angle,
                'end_angle': current_angle + sweep_angle,
                'mid_angle': current_angle + sweep_angle / 2
            })
            current_angle += sweep_angle

    def spin(self):
        if self.is_spinning:
            return

        self.is_spinning = True
        self.spin_speed = self.max_speed
        self.result_item = None

        chosen_item = random.choices(self.items, weights=[i.weight for i in self.items])[0]

        for seg in self.segments:
            if seg['item'] == chosen_item:
                extra_rotations = random.randint(3, 5)
                self.final_angle = 360 * extra_rotations - seg['mid_angle']
                self.result_item = chosen_item
                break

    def update(self, delta_time: float):
        if not self.is_spinning:
            return

        self.angle += self.spin_speed

        target_angle_reached = self.angle > self.final_angle
        print(target_angle_reached)
        if target_angle_reached:
            self.is_spinning = False
            self.spin_speed = 0.0
            self.angle = self.final_angle % 360
            if self.result_item:
                print(f"Поздравляем! Вы выиграли: {self.result_item.name} ({self.result_item.rarity})")

    def draw(self):
        # Рисуем сегменты используя draw_arc_filled (более простой способ)
        for seg in self.segments:
            start_angle = seg['start_angle'] + self.angle
            end_angle = seg['end_angle'] + self.angle

            # Для корректной работы с отрицательными углами
            if end_angle < start_angle:
                end_angle += 360

            arcade.draw_arc_filled(self.center_x, self.center_y,
                                   self.radius * 2, self.radius * 2,
                                   seg['item'].color,
                                   start_angle, end_angle)

        # Обводка и центр
        arcade.draw_circle_outline(self.center_x, self.center_y, self.radius, arcade.color.BLACK, 5)
        arcade.draw_circle_filled(self.center_x, self.center_y, self.radius * 0.1, arcade.color.WHITE)

        # Указатель
        pointer_height = self.radius * 1.15
        pointer_width = 20
        arcade.draw_triangle_filled(
            self.center_x, self.center_y + pointer_height,
                           self.center_x - pointer_width, self.center_y + pointer_height - 30,
                           self.center_x + pointer_width, self.center_y + pointer_height - 30,
            arcade.color.RED
        )

    def get_result(self) -> Optional[RouletteItem]:
        if not self.is_spinning and self.result_item:
            return self.result_item
        return None


def create_loot_items() -> list:
    items = [
        # name, type, rarity, weight, color
        RouletteItem("Пистолет", "Оружие", "common", 40.0, arcade.color.LIGHT_GRAY),
        RouletteItem("Дробовик", "Оружие", "common", 35.0, arcade.color.GRAY),
        RouletteItem("Автомат", "Оружие", "rare", 15.0, arcade.color.SAE),
        RouletteItem("Снайперка", "Оружие", "epic", 6.0, arcade.color.AMETHYST),
        RouletteItem("Шлёпонец", "Оружие", "legendary", 3.0, arcade.color.GOLD),
        RouletteItem("Гранаты(x5)", "Боеприпасы", "common", 30.0, arcade.color.LIGHT_BLUE),
        RouletteItem("Аптечка", "Здоровье", "rare", 10.0, arcade.color.PASTEL_GREEN),
        RouletteItem("Броня", "Защита", "epic", 5.0, arcade.color.PASTEL_YELLOW),
        RouletteItem("1000 монет", "Валюта", "common", 25.0, arcade.color.PASTEL_ORANGE),
    ]
    return items


class CaseWheel(arcade.View):
    def __init__(self, player_coins):
        super().__init__()
        arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)

        # Создаем рулетку
        # Выберите одну из двух версий:

        # Версия 1: Полная версия с полигонами
        self.roulette = CaseCore(center_x=400, center_y=300, radius=200,
                                 items=create_loot_items(), player_coins=100)

        # Версия 2: Упрощенная версия (меньше ошибок)
        # self.roulette = SimpleRouletteWheel(center_x=400, center_y=300, radius=200,
        #                                   items=create_loot_items())

        # Параметры кнопки
        self.button_x = 400
        self.button_y = 100
        self.button_width = 150
        self.button_height = 50
        self.button_color = arcade.color.DARK_GREEN
        self.button_text = "КРУТИТЬ! (10 монет)"
        self.button_hover = False

        # Статистика игрока
        self.player_coins = player_coins

    def on_draw(self):
        self.clear()

        # Рисуем рулетку
        self.roulette.draw()

        # Рисуем кнопку
        button_color = self.button_color
        if self.button_hover:
            button_color = arcade.color.GREEN  # Подсветка при наведении

        arcade.draw_lbwh_rectangle_filled(self.button_x, self.button_y,
                                          self.button_width, self.button_height,
                                          button_color)

        # Обводка кнопки
        arcade.draw_lbwh_rectangle_outline(self.button_x, self.button_y,
                                           self.button_width, self.button_height,
                                           arcade.color.BLACK, 2)

        # Текст кнопки
        arcade.draw_text(self.button_text,
                         self.button_x,
                         self.button_y,
                         arcade.color.WHITE,
                         font_size=16,
                         anchor_x="center",
                         anchor_y="center",
                         bold=True)

        # Показываем количество монет
        arcade.draw_text(f"Монеты: {self.player_coins}",
                         20, self.height - 30,
                         arcade.color.GOLD,
                         font_size=18,
                         bold=True)

        # Инструкция
        arcade.draw_text("Нажмите на кнопку, чтобы крутить рулетку за 10 монет",
                         self.button_x, 50,
                         arcade.color.LIGHT_GRAY,
                         font_size=14,
                         anchor_x="center")

    def on_update(self, delta_time):
        # Обновляем анимацию рулетки
        self.roulette.update(delta_time)

    def on_mouse_motion(self, x, y, dx, dy):
        # Проверяем, находится ли курсор над кнопкой
        left = self.button_x - self.button_width / 2
        right = self.button_x + self.button_width / 2
        top = self.button_y + self.button_height / 2
        bottom = self.button_y - self.button_height / 2

        self.button_hover = (left <= x <= right and bottom <= y <= top)

    def on_mouse_press(self, x, y, button, modifiers):
        # Проверяем нажатие на кнопку
        if button == arcade.MOUSE_BUTTON_LEFT:
            # Проверяем, находится ли клик в пределах кнопки
            left = self.button_x - self.button_width / 2
            right = self.button_x + self.button_width / 2
            top = self.button_y + self.button_height / 2
            bottom = self.button_y - self.button_height / 2

            if (left <= x <= right and bottom <= y <= top and
                    not self.roulette.is_spinning):

                # Проверяем, хватает ли монет
                if self.player_coins >= 10:
                    self.player_coins -= 10
                    self.roulette.spin()
                    print(f"Потрачено 10 монет. Осталось: {self.player_coins}")
                else:
                    print("Недостаточно монет!")

    def on_key_press(self, symbol, modifiers):
        if symbol == 99:
            game_view = main.Game()
            self.window.show_view(game_view)

        if symbol == 98:
            self.player_coins += 10
            self.roulette = CaseCore(center_x=400, center_y=300, radius=200,
                                     items=create_loot_items(), player_coins=self.player_coins)
