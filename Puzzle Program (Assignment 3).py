import cv2
import numpy as np
import random
import tkinter as tk
from tkinter import filedialog

#Puzzle Settings
grid = 3
size = 450
tile_size = 150

image = None
tiles = []
moves = 0
hints = 0
selected = -1
hint_tile = -1
hint_home = -1
finished = False


def set_grid():
    global grid, size, tile_size

    value = grid_value.get()

    if value == "3 x 3":
        grid = 3
        size = 450
    elif value == "4 x 4":
        grid = 4
        size = 448
    else:
        grid = 5
        size = 450

    tile_size = size // grid


def prepare_image(original):
    height, width = original.shape[:2]

    scale = min(size / width, size / height)
    new_width = int(width * scale)
    new_height = int(height * scale)

    resized = cv2.resize(original, (new_width, new_height))

    result = np.full((size, size, 3), 230, dtype=np.uint8)

    x = (size - new_width) // 2
    y = (size - new_height) // 2

    result[y:y + new_height, x:x + new_width] = resized

    return result


def make_tiles():
    global tiles

    tiles = []

    for row in range(grid):
        for col in range(grid):
            x = col * tile_size
            y = row * tile_size

            piece = image[y:y + tile_size, x:x + tile_size].copy()

            tile = {
                "number": row * grid + col,
                "original": piece.copy(),
                "image": piece.copy()
            }

            tiles.append(tile)


def reset_tile(tile):
    tile["image"] = tile["original"].copy()


def rotate_tile(tile):
    tile["image"] = cv2.rotate(tile["image"], cv2.ROTATE_90_CLOCKWISE)


def flip_tile(tile):
    tile["image"] = cv2.flip(tile["image"], 1)


def tile_is_correct(place):
    tile = tiles[place]

    return (tile["number"] == place and
            np.array_equal(tile["image"], tile["original"]))


def puzzle_complete():
    for i in range(len(tiles)):
        if not tile_is_correct(i):
            return False

    return True


def wrong_count():
    count = 0

    for i in range(len(tiles)):
        if not tile_is_correct(i):
            count += 1

    return count


def clear_hint():
    global hint_tile, hint_home

    hint_tile = -1
    hint_home = -1


def scramble():
    amount = 6

    if grid == 4:
        amount = 12
    elif grid == 5:
        amount = 20

    for attempt in range(10):
        tiles.sort(key=lambda tile: tile["number"])

        for tile in tiles:
            reset_tile(tile)

        for i in range(amount):
            action = random.choice(["swap", "rotate", "flip"])
            place = random.randint(0, len(tiles) - 1)

            if action == "swap":
                other = random.randint(0, len(tiles) - 1)

                while other == place:
                    other = random.randint(0, len(tiles) - 1)

                tiles[place], tiles[other] = tiles[other], tiles[place]

            elif action == "rotate":
                rotate_tile(tiles[place])

            else:
                flip_tile(tiles[place])

        if not puzzle_complete():
            break


def load_puzzle(filename):
    global image, moves, hints, selected, finished

    loaded_image = cv2.imread(filename)

    if loaded_image is None:
        return False

    image = prepare_image(loaded_image)

    make_tiles()

    moves = 0
    hints = 0
    selected = -1
    clear_hint()
    finished = False

    scramble()

    return True


def tile_at(x, y):
    if 0 <= x < size and 0 <= y < size:
        row = y // tile_size
        col = x // tile_size
        return row * grid + col

    return -1


def swap_tiles(first, second):
    global moves

    if finished or first == second:
        return

    tiles[first], tiles[second] = tiles[second], tiles[first]

    moves += 1
    clear_hint()
    check_complete()


def rotate(place):
    global moves

    if finished:
        return

    rotate_tile(tiles[place])

    moves += 1
    clear_hint()
    check_complete()


def flip(place):
    global moves

    if finished:
        return

    flip_tile(tiles[place])

    moves += 1
    clear_hint()
    check_complete()


def check_complete():
    global finished, selected

    if puzzle_complete():
        finished = True
        selected = -1
        clear_hint()


def give_hint():
    global hint_tile, hint_home, hints

    if finished or hints >= 3:
        return

    wrong = []

    for i in range(len(tiles)):
        if not tile_is_correct(i):
            wrong.append(i)

    if len(wrong) == 0:
        return

    hint_tile = random.choice(wrong)
    hint_home = tiles[hint_tile]["number"]
    hints += 1


def solve_puzzle():
    global moves, selected, finished

    tiles.sort(key=lambda tile: tile["number"])

    for tile in tiles:
        reset_tile(tile)

    moves = 0
    selected = -1
    clear_hint()
    finished = True


def save_original():
    display = image.copy()

    if hint_home != -1:
        place = hint_home
        row = place // grid
        col = place % grid

        x = col * tile_size + tile_size // 2
        y = row * tile_size + tile_size // 2

        cv2.circle(display, (x, y), tile_size // 3, (255, 0, 0), 4)

    cv2.imwrite("original_display.png", display)


def make_puzzle_image():
    display = np.full((size, size, 3), 230, dtype=np.uint8)

    for place, tile in enumerate(tiles):
        row = place // grid
        col = place % grid

        x = col * tile_size
        y = row * tile_size

        display[y:y + tile_size, x:x + tile_size] = tile["image"]

    for i in range(1, grid):
        point = i * tile_size
        cv2.line(display, (point, 0), (point, size), (150, 150, 150), 1)
        cv2.line(display, (0, point), (size, point), (150, 150, 150), 1)

    if selected != -1:
        row = selected // grid
        col = selected % grid

        x = col * tile_size
        y = row * tile_size

        cv2.rectangle(
            display,
            (x + 2, y + 2),
            (x + tile_size - 2, y + tile_size - 2),
            (0, 0, 255),
            4
        )

    for place in range(len(tiles)):
        if tile_is_correct(place):
            row = place // grid
            col = place % grid

            x = col * tile_size + 25
            y = row * tile_size + 30

            cv2.circle(display, (x, y), 15, (0, 180, 0), -1)
            cv2.line(display, (x - 7, y), (x - 1, y + 7), (255, 255, 255), 2)
            cv2.line(display, (x - 1, y + 7), (x + 9, y - 8), (255, 255, 255), 2)

    if hint_tile != -1:
        row = hint_tile // grid
        col = hint_tile % grid

        x = col * tile_size + tile_size // 2
        y = row * tile_size + tile_size // 2

        cv2.circle(display, (x, y), tile_size // 3, (255, 0, 0), 4)

    return display


def save_puzzle():
    cv2.imwrite("puzzle_display.png", make_puzzle_image())


def show_images():
    save_original()
    save_puzzle()

    global original_photo, puzzle_photo

    original_photo = tk.PhotoImage(file="original_display.png")
    puzzle_photo = tk.PhotoImage(file="puzzle_display.png")

    original_picture.config(image=original_photo)
    puzzle_picture.config(image=puzzle_photo)


def update_text():
    moves_text.config(text="Moves: " + str(moves))
    wrong_text.config(text="Incorrect: " + str(wrong_count()))
    hints_text.config(text="Hints: " + str(hints) + "/3")


def load_image():
    filename = filedialog.askopenfilename(
        title="Choose image",
        filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp")]
    )

    if filename == "":
        return

    set_grid()

    if load_puzzle(filename):
        hint_button.config(state=tk.NORMAL)
        solve_button.config(state=tk.NORMAL)

        show_images()
        update_text()

        info.config(text="Left select/swap - Right rotate - Shift left flip")
    else:
        info.config(text="Image could not be loaded")


def left_click(event):
    global selected

    if image is None or finished:
        return

    place = tile_at(event.x, event.y)

    if place == -1:
        return

    if event.state & 1:
        flip(place)

    elif selected == -1:
        selected = place

    elif selected == place:
        selected = -1

    else:
        swap_tiles(selected, place)
        selected = -1

    show_images()
    update_text()


def right_click(event):
    global selected

    if image is None or finished:
        return

    place = tile_at(event.x, event.y)

    if place == -1:
        return

    selected = -1
    rotate(place)

    show_images()
    update_text()


def hint():
    if image is None or finished:
        return

    give_hint()

    global selected
    selected = -1

    show_images()
    update_text()

    if hints >= 3:
        hint_button.config(state=tk.DISABLED)


def solve():
    if image is None or finished:
        return

    solve_puzzle()

    show_images()
    update_text()

    hint_button.config(state=tk.DISABLED)
    solve_button.config(state=tk.DISABLED)


# GUI
root = tk.Tk()
root.title("Image Puzzle")

# buttons
top = tk.Frame(root)
top.pack()

grid_value = tk.StringVar(value="3 x 3")
grid_box = tk.OptionMenu(top, grid_value, "3 x 3", "4 x 4", "5 x 5")
grid_box.pack(side=tk.LEFT)

load_button = tk.Button(top, text="Load Image", command=load_image)
load_button.pack(side=tk.LEFT)

hint_button = tk.Button(top, text="Hint", command=hint, state=tk.DISABLED)
hint_button.pack(side=tk.LEFT)

solve_button = tk.Button(top, text="Solve", command=solve, state=tk.DISABLED)
solve_button.pack(side=tk.LEFT)

pictures = tk.Frame(root)
pictures.pack()

tk.Label(pictures, text="Original").grid(row=0, column=0)
tk.Label(pictures, text="Puzzle").grid(row=0, column=1)

original_picture = tk.Label(pictures)
original_picture.grid(row=1, column=0)

puzzle_picture = tk.Label(pictures)
puzzle_picture.grid(row=1, column=1)

puzzle_picture.bind("<Button-1>", left_click)
puzzle_picture.bind("<Button-3>", right_click)

bottom = tk.Frame(root)
bottom.pack()

moves_text = tk.Label(bottom, text="Moves: 0")
moves_text.pack(side=tk.LEFT)

wrong_text = tk.Label(bottom, text="Incorrect: 0")
wrong_text.pack(side=tk.LEFT)

hints_text = tk.Label(bottom, text="Hints: 0/3")
hints_text.pack(side=tk.LEFT)

info = tk.Label(root, text="Load an image")
info.pack()

root.mainloop()
