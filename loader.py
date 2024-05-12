from PIL import Image
import numpy as np
from harmony import *
import time

# Record start time
start_time = time.time()


def to_rad(hue):
    return hue * 2 * np.pi / 255  # to float64


def to_int(hue):
    return (hue / (2 * np.pi / 255)).astype(np.uint8)


# Load the image
image_path = "./pic/sample2.png"
image = Image.open(image_path)
hsv = np.array(image.convert("HSV"))
arr_shape = hsv.shape
H, S, V = np.transpose(np.reshape(hsv, (-1, 3)))
H = to_rad(H)

# del hsv

# print(len(H), np.unique(H))

# Find the best harmonic template and orientation
# best_template, best_alpha = find_best_template(hues, saturations)
best_template, best_alpha = "I", 120.0 * np.pi / 180.0
print(f"Best harmonic template: {best_template}")
print(f"Best orientation: {best_alpha / np.pi * 180} degrees")

# Harmonize the colors
nH = to_int(harmonize_colors(H, S, best_template, best_alpha))

print(len(nH), np.unique(nH))


# Convert the harmonized hues back to RGB
new_hsv = np.reshape(
    np.transpose(np.stack([nH, S, V])),
    arr_shape,
)
# Save the harmonized image
harmonized_image = Image.fromarray(new_hsv, mode="HSV").convert("RGB")
# cannot write mode HSV as PNG

# Record end time
end_time = time.time()

# Calculate elapsed time
elapsed_time = end_time - start_time

print("Elapsed time:", elapsed_time, "seconds")


harmonized_image.save("harmonized_image.png")
