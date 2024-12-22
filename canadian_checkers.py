import tkinter as tk
from tkinter import messagebox
from enum import Enum, auto
from PIL import Image, ImageTk
from pathlib import Path
from time import sleep
import json
import hashlib

# Определение типов шашек и сторон
class SideType(Enum):
    WHITE = auto()
    BLACK = auto()

    @staticmethod
    def opposite(side):
        if side == SideType.WHITE:
            return SideType.BLACK
        elif side == SideType.BLACK:
            return SideType.WHITE
        else:
            return None


class CheckerType(Enum):
    NONE = auto()
    WHITE_REGULAR = auto()
    BLACK_REGULAR = auto()
    WHITE_QUEEN = auto()
    BLACK_QUEEN = auto()


# Определение точки
class Point:
    def __init__(self, x: int = -1, y: int = -1):
        self.__x = x
        self.__y = y

    @property
    def x(self):
        return self.__x

    @property
    def y(self):
        return self.__y

    def __eq__(self, other):
        if isinstance(other, Point):
            return self.x == other.x and self.y == other.y
        return NotImplemented


# Определение движения
class Move:
    def __init__(self, from_x: int = -1, from_y: int = -1, to_x: int = -1, to_y: int = -1):
        self._from_x = from_x
        self._from_y = from_y
        self._to_x = to_x
        self._to_y = to_y

    @property
    def from_x(self):
        return self._from_x

    @property
    def from_y(self):
        return self._from_y

    @property
    def to_x(self):
        return self._to_x

    @property
    def to_y(self):
        return self._to_y

    def __str__(self):
        return f'{self._from_x}-{self._from_y} -> {self._to_x}-{self._to_y}'

    def __repr__(self):
        return f'{self._from_x}-{self._from_y} -> {self._to_x}-{self._to_y}'

    def __eq__(self, other):
        if isinstance(other, Move):
            return (
                    self._from_x == other._from_x and
                    self._from_y == other._from_y and
                    self._to_x == other._to_x and
                    self._to_y == other._to_y
            )
        return NotImplemented

# Определение шашки
class Checker:
    def __init__(self, type: CheckerType = CheckerType.NONE):
        self.__type = type

    @property
    def type(self):
        return self.__type

    def change_type(self, type: CheckerType):
        '''Изменение типа шашки'''
        self.__type = type


# Определение игровых констант
PLAYER_SIDE = SideType.WHITE
X_SIZE = Y_SIZE = 12
CELL_SIZE = 75
ANIMATION_SPEED = 4
MAX_PREDICTION_DEPTH = 3
BORDER_WIDTH = 2 * 2
FIELD_COLORS = ['#E7CFA9', '#927456']
HOVER_BORDER_COLOR = '#54b346'
SELECT_BORDER_COLOR = '#944444'
POSIBLE_MOVE_CIRCLE_COLOR = '#944444'

MOVE_OFFSETS = [
    Point(-1, -1),
    Point(1, -1),
    Point(-1, 1),
    Point(1, 1)
]

WHITE_CHECKERS = [CheckerType.WHITE_REGULAR, CheckerType.WHITE_QUEEN]
BLACK_CHECKERS = [CheckerType.BLACK_REGULAR, CheckerType.BLACK_QUEEN]


# Определение игрового поля
class Field:
    def __init__(self, x_size: int, y_size: int):
        self.__x_size = x_size
        self.__y_size = y_size
        self.generate()

    @property
    def x_size(self) -> int:
        return self.__x_size

    @property
    def y_size(self) -> int:
        return self.__y_size

    @property
    def size(self) -> int:
        return max(self.x_size, self.y_size)

    def generate(self):
        '''Генерация поля с шашками и задаёт количество всего'''
        self.checkers = [[Checker() for x in range(self.x_size)] for y in range(self.y_size)]
        for y in range(self.y_size):
            for x in range(self.x_size):
                if (y + x) % 2:
                    if (y < 5):
                        self.checkers[y][x].change_type(CheckerType.BLACK_REGULAR)
                    elif (y >= self.y_size - 5):
                        self.checkers[y][x].change_type(CheckerType.WHITE_REGULAR)

    def type_at(self, x: int, y: int) -> CheckerType:
        '''Получение типа шашки на поле по координатам'''
        return self.checkers[y][x].type

    def at(self, x: int, y: int) -> Checker:
        '''Получение шашки на поле по координатам'''
        return self.checkers[y][x]

    def is_within(self, x: int, y: int) -> bool:
        '''Определяет лежит ли точка в пределах поля'''
        return (0 <= x < self.x_size and 0 <= y < self.y_size)

    @property
    def white_checkers_count(self) -> int:
        '''Количество белых шашек на поле'''
        count = 0
        for row in self.checkers:
            for checker in row:
                if checker.type in WHITE_CHECKERS:
                    count += 1
        return count

    @property
    def black_checkers_count(self) -> int:
        '''Количество чёрных шашек на поле'''
        count = 0
        for row in self.checkers:
            for checker in row:
                if checker.type in BLACK_CHECKERS:
                    count += 1
        return count

    @property
    def white_score(self) -> int:
        '''Счёт белых'''
        score = 0
        for row in self.checkers:
            for checker in row:
                if checker.type == CheckerType.WHITE_REGULAR:
                    score += 1
                elif checker.type == CheckerType.WHITE_QUEEN:
                    score += 3
        return score

    @property
    def black_score(self) -> int:
        '''Счёт чёрных'''
        score = 0
        for row in self.checkers:
            for checker in row:
                if checker.type == CheckerType.BLACK_REGULAR:
                    score += 1
                elif checker.type == CheckerType.BLACK_QUEEN:
                    score += 3
        return score


# Определение игры
class Game:
    def __init__(self, canvas: tk.Canvas, x_field_size: int, y_field_size: int):
        self.canvas = canvas
        self.field = Field(x_field_size, y_field_size)

        self.current_player = SideType.WHITE

        self.hovered_cell = Point()
        self.selected_cell = Point()
        self.animated_cell = Point()

        self.is_animating = False

        self.white_points = 0
        self.black_points = 0

        self.init_images()

    def init_images(self):
        '''Инициализация изображений'''
        self.images = {
            CheckerType.WHITE_REGULAR: ImageTk.PhotoImage(
                Image.open(Path('assets', 'white-regular.png')).resize((CELL_SIZE, CELL_SIZE), Image.LANCZOS)),
            CheckerType.BLACK_REGULAR: ImageTk.PhotoImage(
                Image.open(Path('assets', 'black-regular.png')).resize((CELL_SIZE, CELL_SIZE), Image.LANCZOS)),
            CheckerType.WHITE_QUEEN: ImageTk.PhotoImage(
                Image.open(Path('assets', 'white-queen.png')).resize((CELL_SIZE, CELL_SIZE), Image.LANCZOS)),
            CheckerType.BLACK_QUEEN: ImageTk.PhotoImage(
                Image.open(Path('assets', 'black-queen.png')).resize((CELL_SIZE, CELL_SIZE), Image.LANCZOS)),
        }

    def animate_move(self, move: Move):
        '''Анимация перемещения шашки'''
        self.is_animating = True  # Устанавливаем флаг анимаци
        self.animated_cell = Point(move.from_x, move.from_y)
        self.draw()

        # Создание шашки для анимации
        animated_checker = self.canvas.create_image(move.from_x * CELL_SIZE, move.from_y * CELL_SIZE,
                                                      image=self.images.get(
                                                          self.field.type_at(move.from_x, move.from_y)), anchor='nw',
                                                      tag='animated_checker')

        # Вектора движения
        dx = 1 if move.from_x < move.to_x else -1
        dy = 1 if move.from_y < move.to_y else -1

        # Анимация
        for distance in range(abs(move.from_x - move.to_x)):
            for _ in range(100 // ANIMATION_SPEED):
                self.canvas.move(animated_checker, ANIMATION_SPEED / 100 * CELL_SIZE * dx,
                                   ANIMATION_SPEED / 100 * CELL_SIZE * dy)
                self.canvas.update()
                sleep(0.01)

        self.animated_cell = Point()
        self.is_animating = False

    def draw(self):
        '''Отрисовка сетки поля и шашек'''
        self.canvas.delete('all')
        self.draw_field_grid()
        self.draw_checkers()

    def draw_field_grid(self):
        '''Отрисовка сетки поля'''
        for y in range(self.field.y_size):
            for x in range(self.field.x_size):
                self.canvas.create_rectangle(x * CELL_SIZE, y * CELL_SIZE, x * CELL_SIZE + CELL_SIZE,
                                               y * CELL_SIZE + CELL_SIZE, fill=FIELD_COLORS[(y + x) % 2], width=0,
                                               tag='boards')

                # Отрисовка рамок у необходимых клеток
                if (x == self.selected_cell.x and y == self.selected_cell.y):
                    self.canvas.create_rectangle(x * CELL_SIZE + BORDER_WIDTH // 2, y * CELL_SIZE + BORDER_WIDTH // 2,
                                                   x * CELL_SIZE + CELL_SIZE - BORDER_WIDTH // 2,
                                                   y * CELL_SIZE + CELL_SIZE - BORDER_WIDTH // 2,
                                                   outline=SELECT_BORDER_COLOR, width=BORDER_WIDTH, tag='border')
                elif (x == self.hovered_cell.x and y == self.hovered_cell.y):
                    self.canvas.create_rectangle(x * CELL_SIZE + BORDER_WIDTH // 2, y * CELL_SIZE + BORDER_WIDTH // 2,
                                                   x * CELL_SIZE + CELL_SIZE - BORDER_WIDTH // 2,
                                                   y * CELL_SIZE + CELL_SIZE - BORDER_WIDTH // 2,
                                                   outline=HOVER_BORDER_COLOR, width=BORDER_WIDTH, tag='border')

                # Отрисовка возможных точек перемещения, если есть выбранная ячейка
                if (self.selected_cell):
                    self.draw_possible_moves()

    def draw_possible_moves(self):
        self.canvas.delete('posible_move_circle')

        # Получаем возможные ходы для текущего игрока
        player_moves_list = self.get_moves_list(self.current_player)

        # Отрисовываем возможные ходы для текущего игрока
        for move in player_moves_list:
            if (self.selected_cell.x == move.from_x and self.selected_cell.y == move.from_y):
                self.canvas.create_oval(move.to_x * CELL_SIZE + CELL_SIZE / 3,
                                          move.to_y * CELL_SIZE + CELL_SIZE / 3,
                                          move.to_x * CELL_SIZE + (CELL_SIZE - CELL_SIZE / 3),
                                          move.to_y * CELL_SIZE + (CELL_SIZE - CELL_SIZE / 3),
                                          fill=POSIBLE_MOVE_CIRCLE_COLOR, width=0,
                                          tag='posible_move_circle')

        # Получаем возможные ходы для противника
        opponent_moves_list = self.get_moves_list(SideType.opposite(self.current_player))

        # Отрисовываем возможные ходы для противника
        for move in opponent_moves_list:
            if (self.selected_cell.x == move.from_x and self.selected_cell.y == move.from_y):
                self.canvas.create_oval(move.to_x * CELL_SIZE + CELL_SIZE / 3,
                                          move.to_y * CELL_SIZE + CELL_SIZE / 3,
                                          move.to_x * CELL_SIZE + (CELL_SIZE - CELL_SIZE / 3),
                                          move.to_y * CELL_SIZE + (CELL_SIZE - CELL_SIZE / 3),
                                          fill=POSIBLE_MOVE_CIRCLE_COLOR, width=0,
                                          tag='posible_move_circle')
    def draw_checkers(self):
        '''Отрисовка шашек'''
        for y in range(self.field.y_size):
            for x in range(self.field.x_size):
                # Не отрисовывать пустые ячейки и анимируемую шашку
                if (self.field.type_at(x, y) != CheckerType.NONE and not (
                        x == self.animated_cell.x and y == self.animated_cell.y)):
                    self.canvas.create_image(x * CELL_SIZE, y * CELL_SIZE,
                                               image=self.images.get(self.field.type_at(x, y)), anchor='nw',
                                               tag='checkers')

    def mouse_move(self, event: tk.Event):
        '''Событие перемещения мышки'''
        x, y = (event.x) // CELL_SIZE, (event.y) // CELL_SIZE
        if (x != self.hovered_cell.x or y != self.hovered_cell.y):
            self.hovered_cell = Point(x, y)

        self.draw()

    def mouse_down(self, event: tk.Event):
        '''Событие нажатия мышки'''
        x, y = (event.x) // CELL_SIZE, (event.y) // CELL_SIZE

        # Если точка не внутри поля или идет анимация
        if not self.field.is_within(x, y) or self.is_animating:
            return

        # Определяем, какие шашки у текущего игрока
        if self.current_player == SideType.WHITE:
            player_checkers = WHITE_CHECKERS
        else:
            player_checkers = BLACK_CHECKERS

        # Получаем список всех обязательных ходов
        all_required_moves = []
        for check_y in range(self.field.y_size):
            for check_x in range(self.field.x_size):
                if self.field.type_at(check_x, check_y) in player_checkers:
                    moves = self.get_required_moves_list_for_checker(self.current_player, check_x, check_y)
                    all_required_moves.extend(moves)

        # Если есть обязательные ходы
        if all_required_moves:
            # Если уже есть выбранная шашка с обязательным ходом
            if self.selected_cell.x != -1:
                required_moves = self.get_required_moves_list_for_checker(
                    self.current_player, 
                    self.selected_cell.x, 
                    self.selected_cell.y
                )
                if required_moves:
                    # Можно ходить только этой шашкой
                    if x == self.selected_cell.x and y == self.selected_cell.y:
                        return
                    move = Move(self.selected_cell.x, self.selected_cell.y, x, y)
                    if move in required_moves:
                        self.handle_player_turn(move, x, y)
                    return
            
            # Если выбирается новая шашка
            if self.field.type_at(x, y) in player_checkers:
                moves = self.get_required_moves_list_for_checker(self.current_player, x, y)
                if moves:
                    self.selected_cell = Point(x, y)
                    self.draw()
            return

        # Если нет обязательных ходов
        if self.field.type_at(x, y) in player_checkers:
            self.selected_cell = Point(x, y)
            self.draw()
        elif self.selected_cell.x != -1:
            move = Move(self.selected_cell.x, self.selected_cell.y, x, y)
            if move in self.get_moves_list(self.current_player):
                self.handle_player_turn(move, x, y)

    def handle_move(self, move: Move, draw: bool = True) -> bool:
        '''Совершение хода'''
        if draw:
            self.animate_move(move)

        # Изменение позиции шашки
        self.field.at(move.to_x, move.to_y).change_type(self.field.type_at(move.from_x, move.from_y))
        self.field.at(move.from_x, move.from_y).change_type(CheckerType.NONE)

        # Вектора движения
        dx = -1 if move.from_x < move.to_x else 1
        dy = -1 if move.from_y < move.to_y else 1

        # Удаление съеденных шашек
        has_killed_checker = False
        x, y = move.to_x, move.to_y
        while x != move.from_x or y != move.from_y:
            x += dx
            y += dy
            if self.field.type_at(x, y) != CheckerType.NONE:
                # Подсчет очков в зависимости от типа съеденной шашки
                checker_type = self.field.type_at(x, y)
                if self.current_player == SideType.WHITE:
                    if checker_type == CheckerType.BLACK_REGULAR:
                        self.white_points += 1
                    elif checker_type == CheckerType.BLACK_QUEEN:
                        self.white_points += 3
                else:
                    if checker_type == CheckerType.WHITE_REGULAR:
                        self.black_points += 1
                    elif checker_type == CheckerType.WHITE_QUEEN:
                        self.black_points += 3
                self.field.at(x, y).change_type(CheckerType.NONE)
                has_killed_checker = True

        if draw:
            self.draw()
        return has_killed_checker

    def handle_player_turn(self, move: Move, x, y):
        '''Обработка хода игрока'''

        # Была ли убита шашка
        has_killed_checker = self.handle_move(move)

        # Проверяем достижение последней линии
        reached_end = (self.current_player == SideType.WHITE and y == 0) or \
                     (self.current_player == SideType.BLACK and y == self.field.y_size - 1)

        # Проверяем, есть ли обязательные ходы для текущей шашки
        required_moves_list = self.get_required_moves_list_for_checker(self.current_player, x, y)

        # Если есть обязательные ходы или достигнут край с возможностью взятия
        if (has_killed_checker and required_moves_list) or (reached_end and required_moves_list):
            # Игрок должен продолжать ходить той же шашкой
            self.selected_cell = Point(x, y)  # Оставить выбранной текущую ячейку
            self.draw()  # Перерисовать поле
        else:
            # Если нет обязательных ходов, проверяем на превращение в дамку
            if self.current_player == SideType.WHITE and y == 0 and self.field.type_at(x, y) == CheckerType.WHITE_REGULAR:
                self.field.at(x, y).change_type(CheckerType.WHITE_QUEEN)
            elif self.current_player == SideType.BLACK and y == self.field.y_size - 1 and self.field.type_at(x, y) == CheckerType.BLACK_REGULAR:
                self.field.at(x, y).change_type(CheckerType.BLACK_QUEEN)
            
            # Переключаем игрока
            self.current_player = SideType.opposite(self.current_player)  # Переключить игрока
            self.selected_cell = Point()  # Сбросить выбранную ячейку
            self.draw()  # Перерисовать поле
            self.check_for_game_over()

    def get_required_moves_list_for_checker(self, side: SideType, x: int, y: int) -> list[Move]:
        '''Получение списка обязательных ходов для конкретной шашки'''
        moves_list = []

        # Определение типов шашек
        if side == SideType.WHITE:
            friendly_checkers = WHITE_CHECKERS
            enemy_checkers = BLACK_CHECKERS
        elif side == SideType.BLACK:
            friendly_checkers = BLACK_CHECKERS
            enemy_checkers = WHITE_CHECKERS
        else:
            return moves_list

        # Для обычной шашки
        if self.field.type_at(x, y) == friendly_checkers[0]:
            for offset in MOVE_OFFSETS:
                if not self.field.is_within(x + offset.x * 2, y + offset.y * 2):
                    continue

                if self.field.type_at(x + offset.x, y + offset.y) in enemy_checkers and self.field.type_at(
                        x + offset.x * 2, y + offset.y * 2) == CheckerType.NONE:
                    moves_list.append(Move(x, y, x + offset.x * 2, y + offset.y * 2))

        # Для дамки
        elif self.field.type_at(x, y) == friendly_checkers[1]:
            for offset in MOVE_OFFSETS:
                if not self.field.is_within(x + offset.x * 2, y + offset.y * 2):
                    continue

                has_enemy_checker_on_way = False

                for shift in range(1, self.field.size):
                    if not self.field.is_within(x + offset.x * shift, y + offset.y * shift):
                        continue

                    # Если на пути не было вражеской шашки
                    if not has_enemy_checker_on_way:
                        if self.field.type_at(x + offset.x * shift, y + offset.y * shift) in enemy_checkers:
                            has_enemy_checker_on_way = True
                            continue
                        # Если на пути союзная шашка - то закончить цикл
                        elif self.field.type_at(x + offset.x * shift, y + offset.y * shift) in friendly_checkers:
                            break

                    # Если на пути была вражеская шашка
                    if has_enemy_checker_on_way:
                        if self.field.type_at(x + offset.x * shift, y + offset.y * shift) == CheckerType.NONE:
                            moves_list.append(Move(x, y, x + offset.x * shift, y + offset.y * shift))
                        else:
                            break

        return moves_list

    def check_for_game_over(self):
        '''Проверка на конец игры'''
        game_over = False

        white_moves_list = self.get_moves_list(SideType.WHITE)
        if not (white_moves_list):
            # Белые проиграли
            answer = tk.messagebox.showinfo('Конец игры', 'Чёрные выиграли')
            game_over = True

        black_moves_list = self.get_moves_list(SideType.BLACK)
        if not (black_moves_list):
            # Чёрные проиграли
            answer = tk.messagebox.showinfo('Конец игры', 'Белые выиграли')
            game_over = True

        if (game_over):
            # Новая игра
            self.__init__(self.canvas, self.field.x_size, self.field.y_size)

    def get_moves_list(self, side: SideType) -> list[Move]:
        '''Получение списка ходов'''
        moves_list = self.get_required_moves_list(side)
        if not (moves_list):
            moves_list = self.get_optional_moves_list(side)
        return moves_list
    
    def get_required_moves_list(self, side) :
        '''Получение списка обязательных ходов'''
        moves_list = []

        # Определение типов шашек
        if (side == SideType.WHITE):
            friendly_checkers = WHITE_CHECKERS
            enemy_checkers = BLACK_CHECKERS
        elif (side == SideType.BLACK):
            friendly_checkers = BLACK_CHECKERS
            enemy_checkers = WHITE_CHECKERS
        else:
            return moves_list

        for y in range(self.field.y_size):
            for x in range(self.field.x_size):

                # Для обычной шашки
                if (self.field.type_at(x, y) == friendly_checkers[0]):
                    for offset in MOVE_OFFSETS:
                        if not (self.field.is_within(x + offset.x * 2, y + offset.y * 2)): continue

                        if self.field.type_at(x + offset.x, y + offset.y) in enemy_checkers and self.field.type_at(
                                x + offset.x * 2, y + offset.y * 2) == CheckerType.NONE:
                            moves_list.append(Move(x, y, x + offset.x * 2, y + offset.y * 2))

                # Для дамки
                elif (self.field.type_at(x, y) == friendly_checkers[1]):
                    for offset in MOVE_OFFSETS:
                        if not (self.field.is_within(x + offset.x * 2, y + offset.y * 2)): continue

                        has_enemy_checker_on_way = False

                        for shift in range(1, self.field.size):
                            if not (self.field.is_within(x + offset.x * shift, y + offset.y * shift)): continue

                            # Если на пути не было вражеской шашки
                            if (not has_enemy_checker_on_way):
                                if (self.field.type_at(x + offset.x * shift, y + offset.y * shift) in enemy_checkers):
                                    has_enemy_checker_on_way = True
                                    continue
                                # Если на пути союзная шашка - то закончить цикл
                                elif (self.field.type_at(x + offset.x * shift,
                                                           y + offset.y * shift) in friendly_checkers):
                                    break

                            # Если на пути была вражеская шашка
                            if (has_enemy_checker_on_way):
                                if (self.field.type_at(x + offset.x * shift,
                                                         y + offset.y * shift) == CheckerType.NONE):
                                    moves_list.append(Move(x, y, x + offset.x * shift, y + offset.y * shift))
                                else:
                                    break

        return moves_list
    def get_optional_moves_list(self, side: SideType) -> list[Move]:
        '''Получение списка необязательных ходов'''
        moves_list = []

        # Определение типов шашек
        if (side == SideType.WHITE):
            friendly_checkers = WHITE_CHECKERS
        elif (side == SideType.BLACK):
            friendly_checkers = BLACK_CHECKERS
        else:
            return moves_list

        for y in range(self.field.y_size):
            for x in range(self.field.x_size):
                # Для обычной шашки
                if (self.field.type_at(x, y) == friendly_checkers[0]):
                    for offset in MOVE_OFFSETS[:2] if side == SideType.WHITE else MOVE_OFFSETS[2:]:
                        if not (self.field.is_within(x + offset.x, y + offset.y)): continue

                        if (self.field.type_at(x + offset.x, y + offset.y) == CheckerType.NONE):
                            moves_list.append(Move(x, y, x + offset.x, y + offset.y))

                # Для дамки
                elif (self.field.type_at(x, y) == friendly_checkers[1]):
                    for offset in MOVE_OFFSETS:
                        if not (self.field.is_within(x + offset.x, y + offset.y)): continue

                        for shift in range(1, self.field.size):
                            if not (self.field.is_within(x + offset.x * shift, y + offset.y * shift)): continue

                            if (self.field.type_at(x + offset.x * shift, y + offset.y * shift) == CheckerType.NONE):
                                moves_list.append(Move(x, y, x + offset.x * shift, y + offset.y * shift))
                            else:
                                break
        return moves_list

def check_user(username: str, password: str) -> bool:
    """Проверка существования пользователя"""
    try:
        with open('users.json', 'r') as file:
            users = json.load(file)
            
        # Хешируем введенный пароль
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Проверяем существование пользователя и правильность пароля
        if username in users and users[username] == hashed_password:
            return True
        return False
    except FileNotFoundError:
        return False

def register_user(username: str, password: str) -> bool:
    """Регистрация нового пользователя"""
    try:
        # Пытаемся загрузить существующих пользователей
        with open('users.json', 'r') as file:
            users = json.load(file)
    except FileNotFoundError:
        # Если файл не существует, создаем пустой словарь
        users = {}
    
    # Проверяем, не существует ли уже такой пользователь
    if username in users:
        return False
    
    # Хешируем пароль перед сохранением
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    # Добавляем нового пользователя
    users[username] = hashed_password
    
    # Сохраняем обновленный список пользователей
    with open('users.json', 'w') as file:
        json.dump(users, file)
    
    return True

def auth_gui():
    window = tk.Tk()
    window.title('Авторизация')
    
    # Устанавливаем размеры окна
    window_width = 400
    window_height = 500
    
    # Получаем размеры экрана
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    # Вычисляем координаты для центрирования окна
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    
    # Устанавливаем размеры и положение окна
    window.geometry(f'{window_width}x{window_height}+{x}+{y}')
    window.resizable(False, False)
    window.configure(bg='#2c3e50')

    # Создаем основной контейнер
    main_container = tk.Frame(window, bg='#2c3e50')
    main_container.pack(expand=True)

    # Общие стили
    font_header = ('Arial', 24, 'bold')
    font_entry = ('Arial', 12)
    font_label = ('Arial', 10)

    entry_style = {
        'bg': '#ecf0f1',
        'fg': '#2c3e50',
        'font': font_entry,
        'relief': tk.FLAT,
        'width': 25
    }

    button_style = {
        'font': font_entry,
        'relief': tk.FLAT,
        'cursor': 'hand2',
        'width': 20,  # Увеличенная ширина кнопок
        'height': 2
    }

    # Заголовок
    main_label = tk.Label(main_container, 
                         text='Авторизация', 
                         font=font_header,
                         bg='#2c3e50',
                         fg='#ecf0f1')
    main_label.pack(pady=(30, 20))

    # Контейнер для полей ввода
    entry_container = tk.Frame(main_container, bg='#2c3e50')
    entry_container.pack(pady=20)

    # Поля для ввода
    username_label = tk.Label(entry_container, 
                            text='Имя пользователя', 
                            font=font_label,
                            bg='#2c3e50',
                            fg='#ecf0f1')
    username_label.pack(pady=5)
    
    username_entry = tk.Entry(entry_container, **entry_style)
    username_entry.pack(pady=5)

    password_label = tk.Label(entry_container, 
                            text='Пароль', 
                            font=font_label,
                            bg='#2c3e50',
                            fg='#ecf0f1')
    password_label.pack(pady=5)

    password_entry = tk.Entry(entry_container, show="*", **entry_style)
    password_entry.pack(pady=5)

    # Контейнер для кнопок
    button_container = tk.Frame(main_container, bg='#2c3e50')
    button_container.pack(pady=30)

    # Кнопки
    send_btn = tk.Button(button_container, 
                        text='Войти', 
                        command=lambda: clicked(),
                        bg="#27ae60",  # Зеленый
                        fg="white",
                        activebackground="#219a52",
                        activeforeground="white",
                        **button_style)
    send_btn.pack(pady=10)

    reg_btn = tk.Button(button_container, 
                       text='Регистрация', 
                       command=lambda: open_registration(),
                       bg="#2980b9",  # Синий
                       fg="white",
                       activebackground="#2472a4",
                       activeforeground="white",
                       **button_style)
    reg_btn.pack(pady=10)

    exit_btn = tk.Button(button_container, 
                        text='Выход', 
                        command=lambda: exit_program(),
                        bg="#c0392b",  # Красный
                        fg="white",
                        activebackground="#a93226",
                        activeforeground="white",
                        **button_style)
    exit_btn.pack(pady=10)

    def clicked():
        username = username_entry.get()
        password = password_entry.get()

        # Проверяем, что поля не пустые
        if not username or not password:
            messagebox.showerror("Ошибка", "Заполните все поля")
            return

        if check_user(username, password):
            window.destroy()
            GameGui().draw_gui()
        else:
            messagebox.showerror("Ошибка", "Неверное имя пользователя или пароль")

    def exit_program():
        window.destroy()
    
    def open_registration():
        window.destroy()
        reg_gui()

    window.mainloop()

def reg_gui():
    window = tk.Tk()
    window.title('Регистрация')
    
    # Устанавливаем размеры окна
    window_width = 400
    window_height = 600  # Увеличена высота для нового поля
    
    # Получаем размеры экрана
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    # Вычисляем координаты для центрирования окна
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    
    # Устанавливаем размеры и положение окна
    window.geometry(f'{window_width}x{window_height}+{x}+{y}')
    window.resizable(False, False)
    window.configure(bg='#2c3e50')

    # Создаем основной контейнер
    main_container = tk.Frame(window, bg='#2c3e50')
    main_container.pack(expand=True)

    # Общие стили (такие же, как в auth_gui)
    font_header = ('Arial', 24, 'bold')
    font_entry = ('Arial', 12)
    font_label = ('Arial', 10)

    entry_style = {
        'bg': '#ecf0f1',
        'fg': '#2c3e50',
        'font': font_entry,
        'relief': tk.FLAT,
        'width': 25
    }

    button_style = {
        'font': font_entry,
        'relief': tk.FLAT,
        'cursor': 'hand2',
        'width': 20,  # Такая же ширина, как в auth_gui
        'height': 2
    }

    # Заголовок
    main_label = tk.Label(main_container, 
                         text='Регистрация', 
                         font=font_header,
                         bg='#2c3e50',
                         fg='#ecf0f1')
    main_label.pack(pady=(30, 20))

    # Контейнер для полей ввода
    entry_container = tk.Frame(main_container, bg='#2c3e50')
    entry_container.pack(pady=20)

    # Поля для ввода
    username_label = tk.Label(entry_container, 
                            text='Придумайте имя пользователя', 
                            font=font_label,
                            bg='#2c3e50',
                            fg='#ecf0f1')
    username_label.pack(pady=5)
    
    username_entry = tk.Entry(entry_container, **entry_style)
    username_entry.pack(pady=5)

    password_label = tk.Label(entry_container, 
                            text='Придумайте пароль', 
                            font=font_label,
                            bg='#2c3e50',
                            fg='#ecf0f1')
    password_label.pack(pady=5)

    password_entry = tk.Entry(entry_container, show="*", **entry_style)
    password_entry.pack(pady=5)

    # Новое поле для повторения пароля
    confirm_password_label = tk.Label(entry_container, 
                                    text='Повторите пароль', 
                                    font=font_label,
                                    bg='#2c3e50',
                                    fg='#ecf0f1')
    confirm_password_label.pack(pady=5)

    confirm_password_entry = tk.Entry(entry_container, show="*", **entry_style)
    confirm_password_entry.pack(pady=5)

    # Контейнер для кнопок
    button_container = tk.Frame(main_container, bg='#2c3e50')
    button_container.pack(pady=30)

    # Кнопки
    reg_btn = tk.Button(button_container, 
                       text='Зарегистрироваться', 
                       command=lambda: register(),
                       bg="#27ae60",
                       fg="white",
                       activebackground="#219a52",
                       activeforeground="white",
                       **button_style)
    reg_btn.pack(pady=10)

    back_btn = tk.Button(button_container, 
                        text='Назад', 
                        command=lambda: back_to_auth(),
                        bg="#2980b9",
                        fg="white",
                        activebackground="#2472a4",
                        activeforeground="white",
                        **button_style)
    back_btn.pack(pady=10)

    def register():
        username = username_entry.get()
        password = password_entry.get()
        confirm_password = confirm_password_entry.get()

        # Проверяем, что все поля заполнены
        if not username or not password or not confirm_password:
            messagebox.showerror("Ошибка", "Заполните все поля")
            return

        # Проверяем длину имени пользователя и пароля
        if len(username) < 3:
            messagebox.showerror("Ошибка", "Имя пользователя должно содержать минимум 3 символа")
            return

        if len(password) < 6:
            messagebox.showerror("Ошибка", "Пароль должен содержать минимум 6 символов")
            return

        # Проверяем совпадение паролей
        if password != confirm_password:
            messagebox.showerror("Ошибка", "Пароли не совпадают")
            return

        if register_user(username, password):
            messagebox.showinfo("Успех", "Регистрация успешна!")
            window.destroy()
            auth_gui()
        else:
            messagebox.showerror("Ошибка", "Пользователь с таким именем уже существует")

    def back_to_auth():
        window.destroy()
        auth_gui()

    window.mainloop()

class GameGui:
    def __init__(self):
        self.main_window = tk.Tk()
        self.main_window.title('Канадские шашки')
        self.main_window.attributes("-fullscreen", True)
        
        # Создаем фрейм-контейнер
        container = tk.Frame(self.main_window)
        container.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Создаем Canvas с адаптивным размером
        self.canvas = tk.Canvas(container)
        self.canvas.pack(side=tk.TOP, anchor=tk.N)
        
        # Функция для изменения размера canvas при изменении окна
        def resize_canvas(event=None):
            width = container.winfo_width() - 40  # Учитываем отступы
            height = container.winfo_height() - 40
            size = min(width, height)  # Квадратный canvas
            self.canvas.config(width=size, height=size)
        
        # Привязываем функцию изменения размера к изменению размера контейнера
        container.bind('<Configure>', resize_canvas)
        
        # Передаем canvas вместо main_window
        self.game = Game(self.canvas, X_SIZE, Y_SIZE)

    def exit_game(self):
        self.main_window.destroy()

    def show_rules(self):
        rules_window = tk.Toplevel(self.main_window)
        rules_window.title("Правила канадских шашек")
        rules_window.attributes('-fullscreen', True)
        
        # Создание основного контейнера с отступами
        main_frame = tk.Frame(rules_window, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=50, pady=30)
        
        # Создание верхней панели с заголовком и кнопкой закрытия
        top_frame = tk.Frame(main_frame, bg='#f0f0f0')
        top_frame.pack(fill='x', pady=(0, 20))
        
        # Заголовок (слева)
        title = tk.Label(top_frame, 
                        text="Правила канадских шашек", 
                        font=("Arial", 24, "bold"),
                        bg='#f0f0f0',
                        fg='#2c3e50')
        title.pack(side='left')

        # Кнопка закрытия (справа)
        close_button = tk.Button(
            top_frame,
            text="✕",
            command=lambda: on_closing(),
            font=("Arial", 16, "bold"),
            bg="#e74c3c",
            fg="white",
            width=3,
            height=1,
            relief=tk.FLAT,
            activebackground="#c0392b",
            activeforeground="white"
        )
        close_button.pack(side='right')

        # Создание фрейма для текста с прокруткой
        text_container = tk.Frame(main_frame, bg='#f0f0f0')
        text_container.pack(fill='both', expand=True)

        # Добавление прокрутки
        scrollbar = tk.Scrollbar(text_container)
        scrollbar.pack(side='right', fill='y')

        # Создание текстового виджета с правилами
        rules_text = tk.Text(text_container,
                            wrap=tk.WORD,
                            font=("Arial", 14),
                            padx=20,
                            pady=20,
                            bg='white',
                            fg='#2c3e50',
                            spacing1=10,  # Отступ перед абзацем
                            spacing2=2,   # Межстрочный интервал
                            spacing3=10)  # Отступ после абзаца
        rules_text.pack(fill='both', expand=True)

        # Привязка прокрутки к тексту
        scrollbar.config(command=rules_text.yview)
        rules_text.config(yscrollcommand=scrollbar.set)

        # Текст правил с форматированием
        rules_content = """
    ПРАВИЛА ИГРЫ В КАНАДСКИЕ ШАШКИ

    Основные положения:
    • Игра ведется на доске размером 12×12 клеток
    • Каждый игрок начинает с 30 шашками
    • Первый ход делают белые шашки

    Правила передвижения:
    1. Простая шашка ходит только вперед по диагонали на одну клетку.

    2. При достижении последней горизонтали простая шашка превращается в дамку.

    3. Дамка может ходить на любое количество клеток по диагонали как вперед, так и назад.

    Правила взятия:
    1. Взятие обязательно! Если есть возможность взять шашку противника, вы обязаны это сделать.

    2. При наличии нескольких вариантов взятия нужно выбрать тот, где будет взято наибольшее количество шашек противника.

    3. Взятие происходит через одну клетку по диагонали с перескоком через шашку противника.

    4. Взятые шашки снимаются с доски только после завершения полного хода.

    5. Простая шашка может бить как вперед, так и назад.

    Особые правила:
    • Если простая шашка во время взятия достигает последней горизонтали, но еще может продолжить взятие, она остается простой шашкой до завершения взятия.

    • "Турецкий удар" запрещен - нельзя дважды перепрыгивать через одну и ту же шашку противника.

    Окончание игры:
    Победа присуждается игроку, который:
    • Уничтожил все шашки противника
    • Или лишил их возможности хода ("запер")

    Подсчет очков:
    • За взятие простой шашки: 1 очко
    • За взятие дамки: 3 очка
        """

        # Вставка текста и установка режима "только для чтения"
        rules_text.insert('1.0', rules_content)
        rules_text.config(state='disabled')

        # Создание нижней панели с кнопкой
        bottom_frame = tk.Frame(main_frame, bg='#f0f0f0')
        bottom_frame.pack(fill='x', pady=(20, 0))

        # Кнопка закрытия
        close_button = tk.Button(
            bottom_frame,
            text="Закрыть правила",
            command=rules_window.destroy,
            font=("Arial", 12),
            bg="#e74c3c",
            fg="white",
            padx=20,
            pady=10,
            relief=tk.FLAT,
            activebackground="#c0392b",
            activeforeground="white"
        )
        close_button.pack(pady=10)

        # Обработчик события закрытия окна
        def on_closing():
            self.main_window.deiconify()  # Показываем главное окно
            rules_window.destroy()

           # Скрываем главное окно
        self.main_window.withdraw()
        
        # Привязываем обработчик к закрытию окна
        rules_window.protocol("WM_DELETE_WINDOW", on_closing)
        rules_window.bind('<Escape>', lambda e: on_closing())
    def start_game_man(self):
        self.main_window.destroy()
        self.start_game()
    def surrender(self):
        """Обработка сдачи игры"""
        # Показываем диалоговое окно с подтверждением
        answer = messagebox.askyesno(
            "Подтверждение", 
            "Вы действительно хотите сдаться?",
            icon='question'
        )
        
        # Если игрок подтвердил сдачу
        if answer:
            winner = "Чёрные" if self.game.current_player == SideType.WHITE else "Белые"
            messagebox.showinfo(
                "Конец игры", 
                f"{winner} выиграли!"
            )
            # Начинаем новую игру
            self.start_game_man()
    def start_game(self):
        # Создание окна игры
        self.main_window = tk.Tk()
        self.main_window.title('Канадские шашки')
        self.main_window.attributes("-fullscreen", True)
        self.main_window.configure(bg='#34495e')  # Темно-синий фон
        
        # Создаем фрейм-контейнер
        container = tk.Frame(self.main_window, bg='#34495e')
        container.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Создаем верхнюю панель
        top_frame = tk.Frame(container, bg='#34495e', height=50)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        top_frame.pack_propagate(False)

        # Информация о текущем ходе
        current_turn_var = tk.StringVar(value="Ход: Белые")
        current_turn = tk.Label(top_frame, 
                               textvariable=current_turn_var, 
                               font=("Arial", 18, "bold"),
                               bg='#34495e',
                               fg='#ecf0f1')
        current_turn.pack(pady=10)

        # Создаем нижний контейнер для доски и правой панели
        bottom_container = tk.Frame(container, bg='#34495e')
        bottom_container.pack(fill=tk.BOTH, expand=True)

        # Создаем фрейм для доски с белым фоном и рамкой
        game_frame = tk.Frame(bottom_container, 
                             bg='white',
                             highlightbackground='#2c3e50',
                             highlightthickness=2)
        game_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Создаем правую панель
        right_panel = tk.Frame(bottom_container, bg='#34495e', width=300)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        right_panel.pack_propagate(False)

        # Создаем Canvas с адаптивным размером
        main_canvas = tk.Canvas(game_frame)
        main_canvas.pack(expand=True)

        # Функция для изменения размера canvas
        def resize_canvas(event=None):
            # Получаем доступное пространство
            frame_width = game_frame.winfo_width()
            frame_height = game_frame.winfo_height()
            
            # Вычисляем размер стороны квадратного canvas
            size = min(frame_width, frame_height) - 40  # Отступ по 20 пикселей с каждой стороны
            
            # Обновляем размеры canvas
            main_canvas.config(width=size, height=size)
            
            # Обновляем размер ячейки
            global CELL_SIZE
            CELL_SIZE = size // 12  # Делим на количество клеток (12x12)
            
            # Перерисовываем игровое поле
            if hasattr(self, 'game'):
                self.game.init_images()  # Обновляем размеры изображений
                self.game.draw()  # Перерисовываем поле

        # Привязываем функцию к изменению размера фрейма
        game_frame.bind('<Configure>', resize_canvas)

        # Очки в правой панели
        score_frame = tk.Frame(right_panel, bg='#34495e')
        score_frame.pack(pady=20)

        score_style = {
            'font': ("Arial", 14),
            'bg': '#34495e',
            'fg': '#ecf0f1'
        }

        white_score_var = tk.StringVar(value="Очки белых: 0")
        black_score_var = tk.StringVar(value="Очки черных: 0")
        
        white_score = tk.Label(score_frame, textvariable=white_score_var, **score_style)
        white_score.pack(pady=5)
        
        black_score = tk.Label(score_frame, textvariable=black_score_var, **score_style)
        black_score.pack(pady=5)

        # Кнопки в правой панели
        buttons_frame = tk.Frame(right_panel, bg='#34495e')
        buttons_frame.pack(pady=20)

        button_style = {
            'font': ("Arial", 12),
            'width': 15,
            'relief': tk.FLAT,
            'cursor': 'hand2'
        }

        new_game_btn = tk.Button(buttons_frame, 
                                text="Новая игра", 
                                command=lambda: self.start_game_man(),
                                bg="#27ae60",
                                fg="white",
                                activebackground="#219a52",
                                **button_style)
        new_game_btn.pack(pady=5)

        surrender_btn = tk.Button(buttons_frame, 
                                text="Сдаться", 
                                command=lambda: self.surrender(),
                                bg="#2980b9",
                                fg="white",
                                activebackground="#2472a4",
                                **button_style)
        surrender_btn.pack(pady=5)

        exit_btn = tk.Button(buttons_frame, 
                            text="Выход", 
                            command=lambda: self.exit_game(),
                            bg="#c0392b",
                            fg="white",
                            activebackground="#a93226",
                            **button_style)
        exit_btn.pack(pady=5)

        # Создаем новую игру с новым canvas
        self.game = Game(main_canvas, X_SIZE, Y_SIZE)

        # Обновление информации об игре
        def update_game_info():
            current_turn_var.set(f"Ход: {'Белые' if self.game.current_player == SideType.WHITE else 'Черные'}")
            white_score_var.set(f"Очки белых: {self.game.white_points}")
            black_score_var.set(f"Очки черных: {self.game.black_points}")
            self.main_window.after(100, update_game_info)

        # Привязка событий
        main_canvas.bind("<Motion>", self.game.mouse_move)
        main_canvas.bind("<Button-1>", self.game.mouse_down)

        # Запуск обновления информации
        update_game_info()

        self.main_window.mainloop()

        # Обновление информации об игре
        def update_game_info():
            current_turn_var.set(f"Ход: {'Белые' if self.game.current_player == SideType.WHITE else 'Черные'}")
            white_score_var.set(f"Очки белых: {self.game.white_points}")
            black_score_var.set(f"Очки черных: {self.game.black_points}")
            self.main_window.after(100, update_game_info)

        # Привязка событий
        main_canvas.bind("<Motion>", self.game.mouse_move)
        main_canvas.bind("<Button-1>", self.game.mouse_down)

        # Запуск обновления информации
        update_game_info()

        self.main_window.mainloop()
    def draw_gui(self):
        """Отрисовка главного меню"""
        self.main_window.title("Канадские шашки")
        self.main_window.attributes("-fullscreen", True)
        self.main_window.configure(bg='#2c3e50')  # Темно-синий фон

        # Создаем основной контейнер с отступами
        main_container = tk.Frame(self.main_window, bg='#2c3e50')
        main_container.pack(expand=True)

        # Заголовок игры
        title_label = tk.Label(main_container, 
                            text="Канадские шашки", 
                            font=("Arial", 36, "bold"),
                            fg='#ecf0f1',  # Светлый текст
                            bg='#2c3e50')  # Темно-синий фон
        title_label.pack(pady=(50, 30))

        # Создаем рамку для кнопок
        button_frame = tk.Frame(main_container, bg='#2c3e50')
        button_frame.pack(pady=20)

        # Стиль для кнопок
        button_style = {
            'font': ("Arial", 16),
            'width': 20,
            'height': 2,
            'relief': tk.FLAT,
            'border': 0,
            'cursor': 'hand2'  # Курсор в виде руки при наведении
        }

        # Кнопка "Игра с человеком"
        play_button = tk.Button(button_frame,
                            text="Игра с человеком",
                            command=self.start_game_man,
                            bg='#27ae60',  # Зеленый
                            fg='white',
                            activebackground='#219a52',
                            activeforeground='white',
                            **button_style)
        play_button.pack(pady=10)

        # Кнопка "Правила"
        rules_button = tk.Button(button_frame,
                                text="Правила",
                                command=self.show_rules,
                                bg='#2980b9',  # Синий
                                fg='white',
                                activebackground='#2472a4',
                                activeforeground='white',
                                **button_style)
        rules_button.pack(pady=10)

        # Кнопка "Выход"
        exit_button = tk.Button(button_frame,
                            text="Выход",
                            command=self.exit_game,
                            bg='#c0392b',  # Красный
                            fg='white',
                            activebackground='#a93226',
                            activeforeground='white',
                            **button_style)
        exit_button.pack(pady=10)

# Запуск интерфейса авторизации
auth_gui()