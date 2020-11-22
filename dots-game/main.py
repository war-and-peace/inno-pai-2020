from tkinter import *
from copy import deepcopy
import random


class Move:
    def __init__(self, x, y, p):
        self.x = x
        self.y = y
        self.p = p


class Moves:
    def __init__(self):
        self.moves = []

    def add(self, move: Move):
        self.moves.append(move)

    def getMoves(self):
        return self.moves


class Game:
    def __init__(self, n, m):
        self.n = n
        self.m = m
        self.moves = Moves()
        self.matrix = []
        for i in range(n):
            self.matrix.append([-1 for _ in range(m)])
        self.next = [[1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0], [-1, -1], [0, -1], [1, -1]]

    def is_valid(self, x, y):
        return 0 <= x < self.n and 0 <= y < self.m

    def evaluate(self, matrix):
        agent, player = 0, 0
        for i in range(self.n):
            for j in range(self.m):
                if matrix[i][j] == 2:
                    agent += 1

                if matrix[i][j] == 3:
                    player += 1

        return agent, player

    def getAvailablePositions(self, matrix):
        res = []
        for i in range(self.n):
            for j in range(self.m):
                if matrix[i][j] == -1:
                    res.append((i, j))
        return res

    def dfs(self, matrix, x, y, xlast, ylast, p, path):
        found = False
        ind = 0
        for i in range(len(path)):
            if path[i][0] == x and path[i][1] == y:
                if len(path) - i <= 3:
                    return False, None
                found = True
                ind = i
                break
        if found:
            return True, path[ind:]

        path = deepcopy(path)
        path.append((x, y))

        for t in self.next:
            i, j = x + t[0], y + t[1]
            if self.is_valid(i, j) and matrix[i][j] == p and (not (i == xlast and j == ylast)):
                res, pp = self.dfs(matrix, i, j, x, y, p, path)
                if res:
                    return res, pp
        matrix[x][y] = 5
        return False, None

    def check_point(self, x, y, path):
        a, b, c, d = False, False, False, False
        for p in path:
            a = a or (p[1] == y and p[0] < x)
            b = b or (p[1] == y and p[0] > x)
            c = c or (p[0] == x and p[1] < y)
            d = d or (p[0] == x and p[1] > y)
        return a and b and c and d

    def cover_area(self, matrix, path, p):
        # print(f'cycle is: {path}')
        for i in range(self.n):
            for j in range(self.m):
                if self.check_point(i, j, path):
                    matrix[i][j] = p + 2
        for pp in path:
            matrix[pp[0]][pp[1]] = -(p + 2)

    def fix_matrix(self, matrix):
        m = deepcopy(matrix)
        pp = []
        for p in range(2):
            for i in range(self.n):
                for j in range(self.m):
                    if m[i][j] == p:
                        pp = []
                        res, path = self.dfs(m, i, j, -1, -1, p, pp)
                        if res:
                            self.cover_area(matrix, path, p)

    def addMove(self, x, y, p):
        print('new move added to game')
        self.moves.add(Move(x, y, p))
        self.matrix[x][y] = p
        self.fix_matrix(self.matrix)

    def getMoves(self):
        return self.moves


class Agent:
    def __init__(self, n, m, game):
        self.n = n
        self.m = m
        self.game = game

    def minimax(self, matrix, t, q, isMax):
        tt = self.game.getAvailablePositions(matrix)
        tempT = len(t)
        v = 1
        while (tempT > 0):
            if v * tempT > 200:
                break
            else:
                v *= tempT
            tempT -= 1

        if (len(tt) == 0) or q > max(1, 2 * (len(t) - tempT)):
            a, p = self.game.evaluate(matrix)
            return a - p

        best = -(self.n * self.m)
        if not isMax:
            best = -best

        for i in range(len(tt)):
            pos = tt[i]
            m = deepcopy(matrix)
            m[pos[0]][pos[1]] = 0 if isMax else 1
            self.game.fix_matrix(m)
            if isMax:
                best = max(best, self.minimax(m, t, q + 1, False))
            else:
                best = min(best, self.minimax(m, t, q + 1, True))
        return best

    def findBestMove(self, matrix):
        t = self.game.getAvailablePositions(matrix)
        print(f't = {t}')
        if len(t) == 0:
            return None
        p1, p2 = self.game.evaluate(matrix)
        best = - self.n * self.m
        bestMove = None
        for pos in t:
            m = deepcopy(matrix)
            m[pos[0]][pos[1]] = 0
            self.game.fix_matrix(m)
            res = self.minimax(m, t, 1, False)
            # print(f'res = {res}')
            if res > best:
                best = res
                bestMove = pos
            if res == best:
                if random.randint(1, 5) == 1:
                    bestMove = pos
        print(f'best move: {bestMove}')
        return bestMove

    def make_a_move(self, game_matrix):
        matrix = deepcopy(game_matrix)
        bestMove = self.findBestMove(matrix)
        return bestMove


from math import sqrt

OFFSET = 10
OVAL_SIZE = 5
n, m = None, None
canvas = None
graph = None
game = None
agent = None


def dist(x0, y0, x1, y1):
    return sqrt((x0 - x1) ** 2 + (y0 - y1) ** 2)


def get_color(player):
    return "#ff0000" if player == 1 else "#0000ff"


def get_canvas_info():
    w = canvas.winfo_width()
    h = canvas.winfo_height()
    offset = OFFSET
    int1, int2 = (w - 2 * offset) // n, (h - 2 * offset) // m

    return w, h, offset, int1, int2


def check_in_the_area(x, y):
    w, h, offset, int1, int2 = get_canvas_info()
    s = int(min(int1, int2) * 0.15)
    print(f'check in: {x}, {y}, size: {s}')

    for i in range(n + 1):
        x0 = offset + i * int1
        for j in range(m + 1):
            y0 = offset + j * int2
            if dist(x, y, x0, y0) < s:
                return True, i, j
    return False, None, None


def draw_calculating():
    w, h, offset, int1, int2 = get_canvas_info()
    canvas.create_text(int(w * 0.1), int(h * 0.1), fill="darkblue", font="Times 20 italic bold",
                       text="Calculating...", tag='calculating')


def draw_dot(event):
    w, h, offset, int1, int2 = get_canvas_info()
    print(f'({event.x}, {event.y})')
    res, x0, y0 = check_in_the_area(event.x, event.y)
    if not res:
        return

    print(f'added')
    s = OVAL_SIZE
    x, y = offset + x0 * int1, offset + y0 * int2
    canvas.create_oval(x - s, y - s, x + s, y + s, fill=get_color(1), tag='player_dots')

    draw_calculating()
    status['text'] = 'Calculating...'
    create_grid()
    root.update_idletasks()
    game.addMove(x0, y0, 1)

    m = agent.make_a_move(game.matrix)
    if m is not None:
        game.addMove(m[0], m[1], 0)
    else:
        print("Game is finished")
    score1, score2 = game.evaluate(game.matrix)
    print(f'Game score: {score1} - {score2}')
    score['text'] = f'Agent {score1} - {score2} Player'
    status['text'] = 'Your move'
    create_grid()


def create_grid(event=None):
    w, h, offset, int1, int2 = get_canvas_info()

    canvas.delete('grid_line')
    canvas.delete('player_dots')
    canvas.delete('calculating')

    for i in range(n + 1):
        x = offset + i * int1
        canvas.create_line([(x, 0), (x, h)], tag='grid_line')

    for i in range(m + 1):
        y = offset + i * int2
        canvas.create_line([(0, y), (w, y)], tag='grid_line')

    s = OVAL_SIZE
    moves = game.getMoves()
    print(f'moves size: {len(moves.getMoves())}')
    for move in moves.getMoves():
        x, y = offset + move.x * int1, offset + move.y * int2
        canvas.create_oval(x - s, y - s, x + s, y + s, fill=get_color(move.p), tag='player_dots')


def create_new_game():
    global game
    global agent
    global n
    global m
    nStr = nEntry.get()
    mStr = mEntry.get()
    print(f'n = {nStr}, m = {mStr}')
    try:
        newN = int(nStr)
        newM = int(mStr)
        if newN <= 1 or newM <= 1:
            return
        n = newN
        m = newM
        game = Game(n + 1, m + 1)
        agent = Agent(n + 1, m + 1)
    except:
        return
    status['text'] = "Resize window please"
    create_grid()
    root.geometry("=600x600")
    root.event_generate("<Configure>", when="now")
    root.update_idletasks()


if __name__ == '__main__':
    # n, m = map(int, input().split())
    n, m = 3, 3
    game = Game(n + 1, m + 1)
    agent = Agent(n + 1, m + 1, game)
    root = Tk()
    root.geometry("=600x600")
    info_panel = Frame(master=root, bg='white')
    info_panel.pack()
    status_label = Label(master=info_panel, text="Status: ")
    status_label.grid(row=1, column=0)
    status = Label(master=info_panel, text="              ", bg='white', fg='red')
    status.grid(row=1, column=1)
    score_label = Label(master=info_panel, text="Score: ")
    score_label.grid(row=1, column=2)
    score = Label(master=info_panel, text="Agent 0 - 0 You", bg='white')
    score.grid(row=1, column=3)

    nLabel = Label(master=info_panel, text="N = ")
    nLabel.grid(row=0, column=0)
    nEntry = Entry(master=info_panel)
    nEntry.grid(row=0, column=1)
    mLabel = Label(master=info_panel, text="M = ")
    mLabel.grid(row=0, column=2)
    mEntry = Entry(master=info_panel)
    mEntry.grid(row=0, column=3)
    button = Button(master=info_panel, text="New game", command=create_new_game)
    button.grid(row=0, column=4)
    canvas = Canvas(root, background='white')
    canvas.pack(fill=BOTH, expand=YES)
    canvas.bind('<Button-1>', draw_dot)
    canvas.bind('<Configure>', create_grid)
    print(root.winfo_width())
    status['text'] = 'Your move'
    root.mainloop()
