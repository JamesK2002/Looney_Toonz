import threading
import random
import time
from dataclasses import dataclass, field
from typing import Tuple, Dict, List, Optional

# ------------ CONFIG -------------
SIZE = 10                # board size (SIZE x SIZE)
NUM_PLAYERS = 4
CARROTS_COUNT = 2
MOVE_DELAY = 0.12        # seconds between moves per thread (for demo)
TIME_MACHINE_CYCLE = 3   # teleport mountain after this many full cycles
# ---------------------------------

# directions: up, down, left, right
DIRS = [( -1, 0), ( 1, 0), ( 0, -1), ( 0, 1)]

random.seed()  # system seed

@dataclass
class Player:
    name: str              # 'B','D','T','M'
    x: int
    y: int
    alive: bool = True
    has_carrot: bool = False

class Race:
    def __init__(self, size=SIZE):
        self.size = size
        self.lock = threading.Lock()          # mutex for critical workspace
        self.players: Dict[str, Player] = {}  # keyed by symbol
        self.carrots: List[Tuple[int,int]] = []
        self.mountain: Tuple[int,int] = (0,0)
        self.cycle_moves = 0   # counts moves to determine full cycles
        self.full_cycles = 0
        self.game_over = False
        self.winner: Optional[str] = None

    def in_bounds(self, x, y):
        return 0 <= x < self.size and 0 <= y < self.size

    def occupied_by_player(self, x, y) -> Optional[str]:
        for sym, p in self.players.items():
            if p.alive and p.x == x and p.y == y:
                return sym
        return None

    def place_random_empty(self):
        # find random empty cell (not player, not carrot, not mountain)
        while True:
            x = random.randrange(self.size)
            y = random.randrange(self.size)
            if (x,y) == self.mountain: 
                continue
            if (x,y) in self.carrots:
                continue
            if self.occupied_by_player(x,y):
                continue
            return x,y

    def setup(self):
        # place players
        symbols = ['B','D','T','M']
        for sym in symbols:
            x,y = self.place_random_empty()
            self.players[sym] = Player(sym, x, y)

        # place carrots
        for _ in range(CARROTS_COUNT):
            x,y = self.place_random_empty()
            self.carrots.append((x,y))

        # place mountain
        mx,my = self.place_random_empty()
        self.mountain = (mx,my)

    def print_board(self):
        # create a string grid representation (support "X(C)" displays)
        grid = [['.' for _ in range(self.size)] for __ in range(self.size)]

        # carrots not picked
        for (cx,cy) in self.carrots:
            grid[cx][cy] = 'C'

        # mountain - show 'F' unless a player carrying carrot is on it (then winner)
        mx,my = self.mountain
        if grid[mx][my] == 'C':
            # carrot on same cell (rare) -> show 'C' ; mountain shouldn't be on carrot normally
            grid[mx][my] = 'F'
        else:
            grid[mx][my] = 'F'

        # place players (player takes precedence on display)
        for p in self.players.values():
            if not p.alive:
                continue
            disp = p.name
            if p.has_carrot:
                disp = f"{p.name}(C)"
            grid[p.x][p.y] = disp

        # print nicely aligned
        print("\n" + "="*(self.size*5))
        for i in range(self.size):
            row_elems = []
            for j in range(self.size):
                cell = grid[i][j]
                # pad to 4 chars for alignment
                row_elems.append(cell.center(4))
            print(' '.join(row_elems))
        print("="*(self.size*5) + "\n")

    def teleport_mountain(self):
        # move mountain to a random empty square (cannot be occupied by player or carrot)
        x,y = self.place_random_empty()
        self.mountain = (x,y)
        print(f"*** Time machine: Mountain moved to ({x},{y}) ***")

    # Movement attempt for a single player thread
    def attempt_move(self, symbol: str):
        p = self.players[symbol]
        if not p.alive or self.game_over:
            return

        # choose random direction, try until valid or limited retries
        attempts = 0
        while attempts < 8:
            dx,dy = random.choice(DIRS)
            nx, ny = p.x + dx, p.y + dy
            attempts += 1

            if not self.in_bounds(nx, ny):
                continue

            # if mountain cell and player not carrying carrot => cannot step
            if (nx,ny) == self.mountain and not p.has_carrot:
                continue

            # Check occupation
            occ = self.occupied_by_player(nx, ny)
            if occ:
                # If Marvin, he can enter and shoot
                if p.name == 'M':
                    # shoot and eliminate the other (if alive)
                    victim = self.players[occ]
                    if victim.alive:
                        print(f"Marvin shoots {victim.name} at ({nx},{ny}) and eliminates them!")
                        victim.alive = False
                        # if victim had carrot, steal it
                        if victim.has_carrot:
                            victim.has_carrot = False
                            p.has_carrot = True
                            print(f"Marvin steals the carrot from {victim.name}!")
                        # continue: Marvin will occupy tile
                    # else, dead already -> treat as empty
                else:
                    # non-Marvin cannot step onto occupied tile -> invalid move
                    continue

            # If non-Marvin and tile is player-free (or Marvin eliminated occupant), OK
            # If tile contains an unpicked carrot
            if (nx,ny) in self.carrots and not p.has_carrot:
                # pick it up
                p.has_carrot = True
                self.carrots.remove((nx,ny))
                print(f"{p.name} picked up a carrot at ({nx},{ny})!")

            # If tile is mountain and p.has_carrot => place carrot and win
            if (nx,ny) == self.mountain and p.has_carrot:
                # place carrot on mountain -> win
                print(f"*** {p.name} reaches mountain with carrot and places it. {p.name} WINS! ***")
                self.winner = p.name
                self.game_over = True
                # update position
                p.x, p.y = nx, ny
                return

            # Move player to new location (update coordinates)
            p.x, p.y = nx, ny
            return

        # if no valid move after attempts: stay in place
        return

    # thread target
    def player_thread(self, symbol: str):
        # threads run until game_over
        while not self.game_over and self.players[symbol].alive:
            with self.lock:
                # attempt one atomic move (workspace protected)
                self.attempt_move(symbol)

                # after each atomic move we update cycle/mountain rules
                self.cycle_moves += 1
                print(f"Cycle #: ", self.cycle_moves)
                print(self.players[symbol].name, f"'s turn.")

                # check if we've completed a full "round" (every player moved once)
                if self.cycle_moves % NUM_PLAYERS == 0:
                    self.full_cycles += 1
                    # activate time machine every TIME_MACHINE_CYCLE full cycles
                    if self.full_cycles % TIME_MACHINE_CYCLE == 0:
                        self.teleport_mountain()

                # print board after move
                self.print_board()

                # if a player was eliminated, ensure their position no longer blocks carrots/mountain (their coords remain but alive=False)
                # game_over check also inside attempt_move if someone placed carrot
                if self.game_over:
                    break

            # small sleep to allow other threads
            time.sleep(MOVE_DELAY * (0.5 + random.random()*1.0))

    def run(self):
        self.setup()
        self.print_board()

        threads = []
        # create and start threads in the sequence B, D, T, M as requested
        start_order = ['B','D','T','M']
        for sym in start_order:
            t = threading.Thread(target=self.player_thread, args=(sym,), name=f"Thread-{sym}")
            t.start()
            threads.append(t)

        # join
        for t in threads:
            t.join()

        if self.winner:
            print(f"Race finished. Winner: {self.winner}")
        else:
            print("Race ended with no winner.")

# ---------------------------
if __name__ == "__main__":
    race = Race(size=SIZE)
    race.run()
