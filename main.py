from random import randint
from random import choice
from time import sleep


class BoardWrongShipException(Exception):
    pass


class BoardOutException(Exception):
    def __init__(self):
        super().__init__('Выход за пределы доски.')


class CoordinatesInvalidException(Exception):
    def __init__(self):
        super().__init__(f'Некорректный ввод. Необходимо ввести два числа от {1} до {Board.size}.')


class DotUsedException(Exception):
    def __init__(self):
        super().__init__('Клетка занята')


class Dot:
    empty = '-'
    miss = '•'
    ship = '■'
    hit = 'X'

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __str__(self):
        return f'{self.x + 1} {self.y + 1}'


class Ship:
    def __init__(self, size, bow, orientation):
        self.size = size
        self.bow = bow
        self.orientation = orientation
        self.hp = size

    @property
    def dots(self):
        dots = []
        for i in range(self.size):
            x, y = self.bow.x, self.bow.y
            if self.orientation == 'h':
                x += i
            if self.orientation == 'v':
                y += i
            dots.append(Dot(x, y))
        return dots


class Board:
    size = 6
    is_hidden = False

    def __init__(self):
        self.field = [[Dot.empty] * self.size for _ in range(self.size)]
        self.ships = []

    def __str__(self):
        field = '  | 1 | 2 | 3 | 4 | 5 | 6 |'
        for x in range(self.size):
            field += f'\n{x + 1} |'
            for y in range(self.size):
                field += f' {self.field[y][x]} |'

        if self.is_hidden:
            field = field.replace(Dot.ship, Dot.empty)

        return field

    def is_inside_of_board(self, dot):
        return 0 <= dot.x < self.size and 0 <= dot.y < self.size

    def is_empty(self, dot):
        return self.field[dot.x][dot.y] == Dot.empty

    def contour(self, ship):
        # Обведение кораблей точками (Dot.miss) используется в т.ч. для того,
        # чтобы между кораблями при расстановке оставалось пространство (add_ship).
        # При начальной расстановке кораблей все Dot.miss заменятся на Dot.empty (place_ships, class Game)
        near = [(-1, -1), (0, -1), (1, -1),
                (-1, 0), (0, 0), (1, 0),
                (-1, 1), (0, 1), (1, 1)]

        for dot in ship.dots:
            for dx, dy in near:
                current = Dot(dot.x + dx, dot.y + dy)
                if self.is_inside_of_board(current) and current not in ship.dots:
                    self.field[current.x][current.y] = Dot.miss

    def add_ship(self, ship):
        for dot in ship.dots:
            if not self.is_inside_of_board(dot) or not self.is_empty(dot):
                raise BoardWrongShipException()
            self.field[dot.x][dot.y] = Dot.ship

        self.ships.append(ship)
        # см. contour, class Board
        self.contour(ship)

    def shoot(self, dot):
        if not self.is_inside_of_board(dot):
            raise BoardOutException()

        if self.field[dot.x][dot.y] == Dot.miss or self.field[dot.x][dot.y] == Dot.hit:
            raise DotUsedException()

        for ship in self.ships:
            if dot in ship.dots:
                ship.hp -= 1
                self.field[dot.x][dot.y] = Dot.hit

                if ship.hp == 0:
                    self.ships.remove(ship)
                    self.contour(ship)
                    print(f'{dot} - Корабль уничтожен')
                    return True

                print(f'{dot} - Попадание в корабль')
                return True

        self.field[dot.x][dot.y] = Dot.miss
        print(f'{dot} - Промах')
        return False


class Player:
    def __init__(self, board, opponent_board):
        self.board = board
        self.opponent = opponent_board

    def ask(self):
        raise NotImplementedError()

    def move(self):
        # Вызывать ask() до тех пор, пока игрок не сделает корректный ход
        while True:
            try:
                return self.opponent.shoot(self.ask())
            except Exception as e:
                print(e)
                continue


class AI(Player):
    def ask(self):
        # AI будет стрелять только по Dot.empty или по Dot.ship
        coordinates = []
        for x in range(Board.size):
            for y in range(Board.size):
                if self.opponent.field[x][y] is Dot.empty or self.opponent.field[x][y] is Dot.ship:
                    coordinates.append((x, y))
        x_y = choice(coordinates)
        return Dot(x_y[0], x_y[1])


class User(Player):
    def ask(self):
        user_input = input('Введите координаты: ').replace(' ', '')
        x, y = user_input[0], user_input[1:]

        if not x.isdigit() or not y.isdigit():
            raise CoordinatesInvalidException()
        if not (0 < int(x) <= Board.size and 0 < int(y) <= Board.size):
            raise CoordinatesInvalidException()

        return Dot(int(x) - 1, int(y) - 1)


class Game:
    def __init__(self):
        user_board, ai_board = self.generate_board(), self.generate_board()
        ai_board.is_hidden = True
        self.user = User(user_board, ai_board)
        self.ai = AI(ai_board, user_board)

    @staticmethod
    def place_ships():
        ship_sizes = [3, 2, 2, 1, 1, 1, 1]
        attempt = 0
        board = Board()
        for size in ship_sizes:
            while True:
                attempt += 1
                if attempt >= 1000:
                    return None
                try:
                    board.add_ship(Ship(size, Dot(randint(0, Board.size), randint(0, Board.size)), choice(['h', 'v'])))
                    break
                except BoardWrongShipException:
                    continue

        # см. contour, class Board
        for x in range(0, Board.size):
            for y in range(0, Board.size):
                if board.field[x][y] == Dot.miss:
                    board.field[x][y] = Dot.empty
        return board

    def generate_board(self):
        board = None
        while board is None:
            board = self.place_ships()
        return board

    @staticmethod
    def greet():
        print('Старт игры')
        print('Формат ввода: два числа от 1 до 6 вида xy, где x - горизонталь, y - вертикаль')

    def start(self):
        self.greet()
        self.loop()

    def loop(self):
        # Делает ход только "активный" игрок. Если is_hit - False, то "активный" игрок меняется
        active, deactive = self.ai, self.user

        while True:
            print(f'---------Карта {self.user.__class__.__name__}---------\n{self.user.board}')
            print(f'----------Карта {self.ai.__class__.__name__}----------\n{self.ai.board}')

            if len(deactive.board.ships) == 0:
                print(f'Все корабли {deactive.__class__.__name__} уничтожены')
                print(f'Победа за {active.__class__.__name__}')
                break

            print(f'Ходит {active.__class__.__name__}:')
            is_hit = active.move()
            sleep(1)
            if is_hit:
                continue
            active, deactive = deactive, active


game = Game()
game.start()
