import os
import imageio.v2 as imageio
import numpy as np
from datetime import datetime
from PIL import Image
import sys
import time

start_time = datetime.now()

# SETTINGS
input_folder = 'OSU'
output_video = 'timelapses/OSU'
fps = 30
output_format = 'gif' # Options: 'mp4', 'gif'

gif_background_color = (56, 64, 82, 255) # RGBA
mp4_background_color = (0, 0, 0, 255)

crop = False # Specify a rectangle area to compile
x1, y1 = 7, 7 # top left pixel
x2, y2 = 1166, 876 # bottom right pixel

days_enabled = True # Day or days range to compile [[1]] or [[3,10]] or [[1, 4],[10, 51]]
days = [[6]]

hex_colors = [
"000000",
"3c3c3c",
"787878",
"aaaaaa",
"d2d2d2",
"ffffff",
"600018",
"a50e1e",
"ed1c24",
"fa8072",
"e45c1a",
"ff7f27",
"f6aa09",
"f9dd3b",
"fffabc",
"9c8431",
"c5ad31",
"e8d45f",
"4a6b3a",
"5a944a",
"84c573",
"0eb968",
"13e67b",
"87ff5e",
"0c816e",
"10aea6",
"13e1be",
"0f799f",
"60f7f2",
"bbfaf2",
"28509e",
"4093e4",
"7dc7ff",
"4d31b8",
"6b50f6",
"99b1fb",
"4a4284",
"7a71c4",
"b5aef1",
"780c99",
"aa38b9",
"e09ff9",
"cb007a",
"ec1f80",
"f38da9",
"9b5249",
"d18078",
"fab6a4",
"684634",
"95682a",
"dba463",
"7b6352",
"9c846b",
"d6b594",
"d18051",
"f8b277",
"ffc5a5",
"6d643f",
"948c6b",
"cdc59e",
"333941",
"6d758d",
"b3b9d1"
]

# Add background color to palette if not already present
bg_hex = f"{gif_background_color[0]:02x}{gif_background_color[1]:02x}{gif_background_color[2]:02x}"
if bg_hex not in hex_colors:
    hex_colors.append(bg_hex)

palette = []
for h in hex_colors:
    palette.extend([int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)])

pal_img = Image.new("P", (1, 1))
pal_img.putpalette(palette + [0, 0, 0] * (256 - len(hex_colors)))

# Collect PNG files in sorted order
image_files = sorted([f for f in os.listdir(input_folder) if f.endswith('.png')])

# First timestamp for relative days
first_file = image_files[0]
first_timestamp_str = first_file.split('.')[0]
first_timestamp = datetime.strptime(first_timestamp_str, '%Y-%m-%d_%H-%M-%S')

# Organize by day
day_images = {}
for file in image_files:
    img_path = os.path.join(input_folder, file)
    timestamp_str = file.split('.')[0]
    file_timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d_%H-%M-%S')
    time_diff = file_timestamp - first_timestamp
    relative_day = int(time_diff.total_seconds() // (24 * 3600)) + 1
    day_images.setdefault(relative_day, []).append((file_timestamp, file, img_path))

# Compute total selected days and frames
selected_days_list = days if days_enabled else [[day] for day in day_images]
all_selected_days = set()
total_frames = 0
for day_entry in selected_days_list:
    if len(day_entry) == 1:
        day = day_entry[0]
        if day in day_images:
            all_selected_days.add(day)
            total_frames += len(day_images[day])
    else:
        start_day, end_day = day_entry
        for day in range(start_day, end_day + 1):
            if day in day_images:
                all_selected_days.add(day)
                total_frames += len(day_images[day])
print(f"Selected {len(all_selected_days)} day(s) with total {total_frames} frames")

# Select images
selected_images = []
for day_entry in selected_days_list:
    if len(day_entry) == 1:
        day = day_entry[0]
        if day in day_images:
            day_images[day].sort(key=lambda x: x[0])
            first_image = day_images[day][0][1]
            last_image = day_images[day][-1][1]
            num_frames = len(day_images[day])
            print(f"Day {day}: {first_image} - {last_image} ({num_frames} frames)")
            selected_images.extend([img[2] for img in day_images[day]])
    else:
        start_day, end_day = day_entry
        for day in range(start_day, end_day + 1):
            if day in day_images:
                day_images[day].sort(key=lambda x: x[0])
                first_image = day_images[day][0][1]
                last_image = day_images[day][-1][1]
                num_frames = len(day_images[day])
                print(f"Day {day}: {first_image} - {last_image} ({num_frames} frames)")
                selected_images.extend([img[2] for img in day_images[day]])

# Saving
if selected_images:
    os.makedirs(os.path.dirname(output_video), exist_ok=True)
    total_frames = len(selected_images)
    total_seconds = total_frames / fps
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)
    milliseconds = int((total_seconds - int(total_seconds)) * 1000)
    duration_str = f"{minutes}m {seconds}s {milliseconds}ms"

    print(f"Processing and saving {output_format.upper()}")

    if output_format == 'gif':
        output_video = output_video + '.gif'
        duration_ms = int(1000 / fps)
        images_p = []  
        for img_path in selected_images:
            img = Image.open(img_path).convert("RGBA")
            if crop:
                img = img.crop((x1, y1, x2, y2))
            background = Image.new("RGBA", img.size, gif_background_color)
            composite_img = Image.alpha_composite(background, img)
            rgb_img = composite_img.convert("RGB")
            p_img = rgb_img.quantize(palette=pal_img, dither=Image.Dither.NONE)
            images_p.append(p_img)

        images_p[0].save(
            output_video,
            save_all=True,
            append_images=images_p[1:],
            duration=duration_ms,
            loop=0,
            disposal=2
        )

    elif output_format == 'mp4':
        output_video = output_video + '.mp4'
        writer = imageio.get_writer(
            output_video,
            format='FFMPEG',
            mode='I',
            fps=fps,
            codec='libx264',
            quality=None,
            ffmpeg_params=['-crf', '0', '-preset', 'ultrafast']
        )
        for img_path in selected_images:
            img = Image.open(img_path).convert("RGBA")
            if crop:
                img = img.crop((x1, y1, x2, y2))
            background = Image.new("RGBA", img.size, mp4_background_color)
            composite_img = Image.alpha_composite(background, img)
            rgb_img = composite_img.convert("RGB")
            rgb_arr = np.array(rgb_img)
            writer.append_data(rgb_arr)
        writer.close()

    else:
        print("Invalid Format Assigned")
        exit()

    end_time = datetime.now()
    processing_time = end_time - start_time
    proc_minutes = int(processing_time.total_seconds() // 60)
    proc_seconds = int(processing_time.total_seconds() % 60)
    proc_ms = int(processing_time.microseconds / 1000)
    runtime_fps = total_frames / processing_time.total_seconds() if processing_time.total_seconds() > 0 else 0

    print(f"""
Saved: {output_video}
Duration: {duration_str}
Runtime: {proc_minutes}m {proc_seconds}s {proc_ms}ms
Runtime FPS: {runtime_fps:.2f}
    """)
    
else:

    print("Missing Frames")
