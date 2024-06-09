from PIL import Image
import numpy as np
from harmony import *
import time

from numpy import pi, radians


def to_rad(hue):
    return hue * 2 * pi / 255  # to float64


def to_int(hue):
    return (hue / (2 * pi / 255)).astype(np.uint8)


# Load the image
image_path = "./pic/sample1.png"
image = Image.open(image_path)
hsv = np.array(image.convert("HSV"))
arr_shape = hsv.shape
H, S, V = np.transpose(np.reshape(hsv, (-1, 3))).astype(np.int32)

# print(H.dtype)
# exit()

# Record start time
start_time = time.time()

best_template = find_best_template(H, S)

end_time = time.time()
elapsed_time = end_time - start_time
print(f"Best harmonic template: {best_template.name}")
print(f"Best alpha: {best_template.alpha}")
print(f"centers {best_template.sectors[0].center}, {best_template.sectors[1].center}")
print("Elapsed time:", elapsed_time, "seconds")

partition = binary_partition(H, best_template)
# print(len(partition), np.unique(partition))
nH = shift_color(H, partition, best_template)

# Harmonize the colors
# nH = to_int(harmonize_colors(H, best_template))

print(len(nH), np.unique(nH))


# Convert the harmonized hues back to RGB
new_hsv = np.reshape(
    np.stack([nH, S, V]).T,
    arr_shape,
)

# Save the harmonized image
harmonized_image = Image.fromarray(new_hsv.astype(np.uint8), mode="HSV").convert("RGB")
# cannot write mode HSV as PNG

harmonized_image.save("harmonized_image.png")
