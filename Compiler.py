# CONFIGURATION SETTINGS

# Folder containing your source images (frames)
# Example: 'OSU' means images are stored in ./OSU/
input_folder = 'OSU'

# Path and filename (without extension) for the generated timelapse
# Example: 'Timelapses/OSU' > output will be 'Timelapses/OSU.mp4' or '.webm'
output_file = 'Timelapses/OSU'

# Frames per second (FPS) for the final timelapse
# Higher = smoother playback, but larger file size and shorter duration
fps = 30

# Output format of the final timelapse
# Options:
# 'mp4'  - smaller file size, no transparency
# 'webm' - video with any kind of transparency
# 'gif'  - larger file size, supports only complete transparency
output_format = 'gif'

# Color to fill transparent areas 
# Example: (23, 33, 48, 255) > a dark bluish background 
# Set to None if you want to keep transparency (Not supported in mp4)
transparency_replacement = (23, 33, 48, 255) # RGBA tuple or None

# Crop the images before compiling
# True  > apply crop to each frame
# False > use full images
crop = True
# Define the crop rectangle area (pixels)
# Coordinates: (x1, y1) = top-left corner, (x2, y2) = bottom-right corner
# Example below keeps the region on input images from (0, 0) to (1166, 1450)
x1, y1 = 0, 0
x2, y2 = 1166, 1450

# Process only specific "days" (frame ranges)
# Set to True to enable filtering, or False to process everything
days_enabled = True
# Specify days to include, using one or more ranges:
# [[1]]        > only day 1
# [[3, 10]]    > days 3 through 10
# [[1, 4], [10, 51]] > multiple ranges
days = [[1],[10]]

# ----------------------------------------------------------

import os
import imageio.v2 as imageio
import numpy as np
from datetime import datetime
from PIL import Image
import sys
import time

start_time = datetime.now()

# Color palette initialization
hex_colors = [
    "000000", "3c3c3c", "787878", "aaaaaa", "d2d2d2", "ffffff",
    "600018", "a50e1e", "ed1c24", "fa8072", "e45c1a", "ff7f27",
    "f6aa09", "f9dd3b", "fffabc", "9c8431", "c5ad31", "e8d45f",
    "4a6b3a", "5a944a", "84c573", "0eb968", "13e67b", "87ff5e",
    "0c816e", "10aea6", "13e1be", "0f799f", "60f7f2", "bbfaf2",
    "28509e", "4093e4", "7dc7ff", "4d31b8", "6b50f6", "99b1fb",
    "4a4284", "7a71c4", "b5aef1", "780c99", "aa38b9", "e09ff9",
    "cb007a", "ec1f80", "f38da9", "9b5249", "d18078", "fab6a4",
    "684634", "95682a", "dba463", "7b6352", "9c846b", "d6b594",
    "d18051", "f8b277", "ffc5a5", "6d643f", "948c6b", "cdc59e",
    "333941", "6d758d", "b3b9d1"
]

# Add background color to palette if replacement color is set
if transparency_replacement is not None:
    bg_hex = f"{transparency_replacement[0]:02x}{transparency_replacement[1]:02x}{transparency_replacement[2]:02x}"
    if bg_hex not in hex_colors:
        hex_colors.append(bg_hex)

palette = []
for h in hex_colors:
    palette.extend([int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)])

pal_img = Image.new("P", (1, 1))
pal_img.putpalette(palette + [0, 0, 0] * (256 - len(hex_colors)))

# Gather and organize image files
image_files = sorted([f for f in os.listdir(input_folder) if f.endswith('.png')])
if not image_files:
    print("No PNG files found in input folder.")
    sys.exit(1)

first_file = image_files[0]
first_timestamp = datetime.strptime(first_file.split('.')[0], '%Y-%m-%d_%H-%M-%S')

day_images = {}
for file in image_files:
    timestamp = datetime.strptime(file.split('.')[0], '%Y-%m-%d_%H-%M-%S')
    rel_day = int((timestamp - first_timestamp).total_seconds() // (24 * 3600)) + 1
    day_images.setdefault(rel_day, []).append((timestamp, file, os.path.join(input_folder, file)))

# Filter and list selected days
selected_days_list = days if days_enabled else [[day] for day in day_images]
all_selected_days = set()
total_frames = 0

for entry in selected_days_list:
    if len(entry) == 1:
        d = entry[0]
        if d in day_images:
            all_selected_days.add(d)
            total_frames += len(day_images[d])
    else:
        for d in range(entry[0], entry[1] + 1):
            if d in day_images:
                all_selected_days.add(d)
                total_frames += len(day_images[d])

print(f"Selected {len(all_selected_days)} day(s) with total of {total_frames} frames")

selected_images = []
for entry in selected_days_list:
    if len(entry) == 1:
        d = entry[0]
        if d in day_images:
            day_images[d].sort(key=lambda x: x[0])
            print(f"Day {d}: {day_images[d][0][1]} - {day_images[d][-1][1]} ({len(day_images[d])} frames)")
            selected_images.extend([i[2] for i in day_images[d]])
    else:
        for d in range(entry[0], entry[1] + 1):
            if d in day_images:
                day_images[d].sort(key=lambda x: x[0])
                print(f"Day {d}: {day_images[d][0][1]} - {day_images[d][-1][1]} ({len(day_images[d])} frames)")
                selected_images.extend([i[2] for i in day_images[d]])

# Output generation
if not selected_images:
    print("Missing Frames")
    sys.exit(1)

os.makedirs(os.path.dirname(output_file), exist_ok=True)
total_frames = len(selected_images)
total_seconds = total_frames / fps
duration_str = f"{int(total_seconds // 60)}m {int(total_seconds % 60)}s {int((total_seconds % 1) * 1000)}ms"

print(f"Transparency Replacement: {transparency_replacement}")
print(f"Processing and saving {output_format.upper()} at {fps} fps...")

if output_format == 'gif':
    output_file += '.gif'
    duration_ms = int(1000 / fps)
    images_p = []

    for path in selected_images:
        img = Image.open(path).convert("RGBA")
        if crop:
            img = img.crop((x1, y1, x2, y2))

        if transparency_replacement is not None:
            bg = Image.new("RGBA", img.size, transparency_replacement)
            img = Image.alpha_composite(bg, img)
            img = img.convert("RGB")
            p_img = img.quantize(palette=pal_img, dither=Image.Dither.NONE)
        else:
            p_img = img.convert("RGBA")

        images_p.append(p_img)

    save_kwargs = {
        "save_all": True,
        "append_images": images_p[1:],
        "duration": duration_ms,
        "loop": 0,
        "disposal": 2
    }

    if transparency_replacement is None:
        save_kwargs["transparency"] = 0
        save_kwargs["dispose"] = 2

    images_p[0].save(output_file, **save_kwargs)


elif output_format in ('mp4', 'webm'):
    if output_format == 'mp4':
        output_file += '.mp4'
        codec = 'libx264'
        output_params = ['-crf', '18', '-preset', 'ultrafast']
    else:  # webm with alpha
        output_file += '.webm'
        codec = 'libvpx-vp9'
        output_params = ['-pix_fmt', 'yuva420p', '-crf', '18', '-b:v', '0', '-loglevel', 'error']


    writer = imageio.get_writer(
        output_file,
        format='FFMPEG',
        mode='I',
        fps=fps,
        codec=codec,
        quality=None,
        macro_block_size=None,  # prevents resizing warning
        output_params=output_params
    )

    for path in selected_images:
        img = Image.open(path).convert("RGBA")
        if crop:
            img = img.crop((x1, y1, x2, y2))

        if transparency_replacement is not None:
            bg = Image.new("RGBA", img.size, transparency_replacement)
            img = Image.alpha_composite(bg, img)

        arr = np.array(img)
        writer.append_data(arr)

    writer.close()


else:
    print("Invalid Format Assigned")
    sys.exit(1)

# Summary output
end_time = datetime.now()
elapsed = end_time - start_time
runtime_fps = total_frames / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
size_bytes = os.path.getsize(output_file)
size_mb = size_bytes // (1024 * 1024)
size_kb = (size_bytes % (1024 * 1024)) // 1024

print(f"""
Saved: {output_file}
Duration: {duration_str}
Runtime: {elapsed.seconds // 60}m {elapsed.seconds % 60}s {elapsed.microseconds // 1000}ms
Runtime FPS: {runtime_fps:.2f}
File Size: {size_mb}MB {size_kb}KB
""")
