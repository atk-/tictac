import os
import random
import re

BLACK, EMPTY, WHITE = (-1, 0, 1)

CMAP = {
    EMPTY: '.',
    BLACK: 'X',
    WHITE: 'O',
}


def transpose(arr):
    return [[a[i] for a in arr] for i in range(len(arr[0]))]


def seq_contains(seq, subseq):
    for i in range(len(seq) - len(subseq) + 1):
        if seq[i:i+len(subseq)] == subseq:
            return True


class InvalidCoordError(Exception):
    pass


class Board:
    def __init__(self, x, y, rlen):
        self.x = x
        self.y = y
        self.rlen = rlen
        self.gutter = 3

        self.data = [[EMPTY for i in range(self.x)] for j in range(self.y)]
        self.history = []

    def out(self):
        os.system('clear')
        print(' ' * self.gutter + ' '.join(str(i+1) for i in range(self.x)))
        for r, row in enumerate(self.data):
            print(chr(r + 65).ljust(self.gutter) + ' '.join([CMAP.get(n) for n in row]))

    def set(self, y, x, value):
        self.data[y][x] = value
        if value != EMPTY:
            self.history.append((y, x, value))

    def to_coords(self, square):
        square = square.upper()
        m = re.match('([A-Z])([0-9]+)', square)
        if not m:
            raise InvalidCoordError()

        row, col = m.groups()
        row = ord(row) - 65
        col = int(col) - 1
        if not 0 <= row < self.y:
            raise InvalidCoordError(f'invalid row: {row}')
        if not 0 <= col < self.x:
            raise InvalidCoordError(f'invalid col: {col}')

        return row, col

    @property
    def empty_squares(self):
        """Get coordinates of empty squares in a list."""
        ret = []
        for y in range(self.y):
            for x in range(self.x):
                if self.data[y][x] == EMPTY:
                    ret.append((y, x))
        return ret

    def lines(self):
        # get vertical and horizontal lines
        lines = self.data + transpose(self.data)

        # add diagonals
        for y in range(-self.y + 1, self.y * 2):
            diag = [self.data[y-x][x] for x in range(self.x)
                    if 0 <= x < self.x and 0 <= y - x < self.y]
            if len(diag) >= self.rlen:
                lines.append(diag)

            diag = [self.data[y+x][x] for x in range(self.x)
                    if 0 <= x < self.x and 0 <= y + x < self.y]
            if len(diag) >= self.rlen:
                lines.append(diag)

        return lines

    def undo(self):
        """Undo previous move."""
        if not self.history:
            return

        y, x, val = self.history[-1]
        self.set(y, x, EMPTY)
        self.history = self.history[:-1]

    def check_state(self):
        lines = self.lines()

        for row in lines:
            for v in (BLACK, WHITE):
                if seq_contains(row, [v] * self.rlen):
                    return v

        return None

    def ai_random_move(self):
        while True:
            x = random.randint(0, self.x - 1)
            y = random.randint(0, self.y - 1)
            if self.data[y][x] == EMPTY:
                break

        self.set(y, x, WHITE)
        return self

    def ai_simple_move(self, color, cutoff=None):
        """Find the move that maximizes valfunc for color."""
        vdic = {}

        for y, x in self.empty_squares:
            self.set(y, x, color)
            value = self.valfunc(color)
            vdic[(y, x)] = value
            self.undo()
            if cutoff and value > cutoff:
                break

        vmax = max(vdic.values())
        for k, v in vdic.items():
            if v == vmax:
                break

        return vmax, k

    def ai_minimax(self):
        """Find a minimax move looking ahead one movement pair."""
        vdic = {}
        vmin = None

        for y, x in self.empty_squares:
            self.set(y, x, WHITE)
            vmax, coords = self.ai_simple_move(BLACK, cutoff=vmin)
            vdic[(y, x)] = vmax
            if vmin is None or vmax < vmin:
                vmin = vmax
            self.undo()

        vmin = min(vdic.values())
        for k, v in vdic.items():
            if v == vmin:
                break

        return vmin, k

    def valfunc(self, color=WHITE):
        # ad hoc value for current board state, maximizing for given color
        value = 0

        for line in self.lines():
            for i in range(0, len(line) - self.rlen + 1):
                chunk = line[i:i+self.rlen]
                if WHITE in chunk and BLACK in chunk:
                    # let's not give a value for "contested" bits
                    continue
                else:
                    f = 1 if color in chunk else -1
                    n = len([c for c in chunk if c != EMPTY])
                    if n > 0:
                        if n == self.rlen:
                            value += f * 999
                        else:
                            value += f * 2 ** n

        return value


if __name__ == '__main__':
    board = Board(9, 9, 4)

    while True:
        board.out()
        print()
        print(board.valfunc())
        print()
        winner = board.check_state()
        if winner:
            print(winner)
            break

        while True:
            repeat = False
            try:
                square = input('> ')
                row, col = board.to_coords(square)
                if board.data[row][col] == EMPTY:
                    board.set(row, col, BLACK)
                else:
                    print('square occupied')
                    repeat = True
            except InvalidCoordError as err:
                print(err)
                repeat = True

            if not repeat:
                break

        vmax, coords = board.ai_minimax()
        ay, ax = coords
        board.set(ay, ax, WHITE)

