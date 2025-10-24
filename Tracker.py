# CONFIGURATION SETTINGS

# Coordinates for 2 tiles: (min_x, min_y), (max_x, max_y)
# You can get tiles coordinates with wplace extensions like Blue Marble 
# (or manually check backend name for the tile)
# Only rectangle shapes of complete tiles are supported, e.g. 1x1, 1x2, 2x5, 10x10
# But nothing prevents setting custom resolution on Compiler.py for actual timelapses
bounds_input = [
    (824, 792),  # top-left
    (827, 795)   # bottom-right
]

# Output Folder Path (Where frames will be stored at)
output_folder = "OSU"

# Interval per capture (seconds)
sleep_seconds = 900

# ----------------------------------------------------------

import requests
from PIL import Image
import io
import time
import os

# Expand rectangle into full tile list
def expand_bounds(c1, c2):
    min_x, min_y = min(c1[0], c2[0]), min(c1[1], c2[1])
    max_x, max_y = max(c1[0], c2[0]), max(c1[1], c2[1])
    tiles = [(x, y) for y in range(min_y, max_y + 1) for x in range(min_x, max_x + 1)]
    return tiles, min_x, max_x, min_y, max_y

# Return tile URL
def tile_url(x, y):
    return f"https://backend.wplace.live/files/s0/tiles/{x}/{y}.png"

# Fetch tiles
def fetch_tiles(tile_coords, timeout=10.0):
    while True:
        try:
            tiles_map = {}
            determined_size = None

            for coord in tile_coords:
                x, y = coord
                resp = requests.get(tile_url(x, y), timeout=timeout)

                if resp.status_code == 404:
                    print(f"Tile {coord} replaced with transparent placeholder (404).")
                    img = Image.new("RGBA", (2000, 2000), (0, 0, 0, 0))
                    tiles_map[coord] = img
                    if determined_size is None:
                        determined_size = img.size
                    continue

                if resp.status_code != 200:
                    print(f"Tile {coord} returned status {resp.status_code}. Retrying whole batch in 5s...")
                    time.sleep(5)
                    raise Exception("bad tile status")

                img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
                tiles_map[coord] = img

                if determined_size is None:
                    determined_size = img.size

            if determined_size is None:
                print("Couldn't determine tile size. Retrying whole batch in 5s...")
                time.sleep(5)
                continue

            return tiles_map, determined_size

        except requests.exceptions.RequestException as e:
            print(f"Network error while fetching tiles: {e}. Retrying whole batch in 5s...")
            time.sleep(5)
            continue
        except Exception:
            time.sleep(5)
            continue

# Create combined RGBA image for rectangle
def create_combined_image(tiles_map, min_x, max_x, min_y, max_y, tile_size):
    tile_w, tile_h = tile_size
    grid_w = max_x - min_x + 1
    grid_h = max_y - min_y + 1
    combined = Image.new("RGBA", (grid_w * tile_w, grid_h * tile_h), (0, 0, 0, 0))

    for row_index, y in enumerate(range(min_y, max_y + 1)):
        for col_index, x in enumerate(range(min_x, max_x + 1)):
            coord = (x, y)
            dest_x = col_index * tile_w
            dest_y = row_index * tile_h
            img = tiles_map[coord]
            combined.paste(img, (dest_x, dest_y), mask=img.getchannel("A"))

    return combined

# Format runtime string
def format_runtime(start_time):
    total = int(time.time() - start_time)
    days = total // 86400
    hours = (total % 86400) // 3600
    minutes = (total % 3600) // 60
    seconds = total % 60
    return f"{days}d {hours}h {minutes}m {seconds}s"

# Save image and return path
def save_image(img, folder):
    timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')
    output_path = os.path.join(folder, f"{timestamp}.png")
    img.save(output_path)
    return output_path

# Top-level setup
os.makedirs(output_folder, exist_ok=True)
tiles, min_x, max_x, min_y, max_y = expand_bounds(bounds_input[0], bounds_input[1])
grid_w = max_x - min_x + 1
grid_h = max_y - min_y + 1
print(f"""\
SETTINGS
-------------------------------------------------
Cooldown: {sleep_seconds}s
Total Tiles: {len(tiles)}
Bounds: x[{min_x}-{max_x}] y[{min_y}-{max_y}]
Grid Dims: {grid_w}x{grid_h}
Output Folder: {output_folder}
-------------------------------------------------\
""")
frame_count = 0
script_start_time = time.time()

# Main loop
while True:
    tiles_map, tile_size = fetch_tiles(tiles)
    combined = create_combined_image(tiles_map, min_x, max_x, min_y, max_y, tile_size)
    output_path = save_image(combined, output_folder)

    frame_count += 1
    runtime_str = format_runtime(script_start_time)
    print(f"Frame {frame_count} - {output_path} | Runtime: {runtime_str}")

    time.sleep(sleep_seconds)
