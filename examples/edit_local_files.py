"""Image to image from local files: a product shot and a style board become one ad visual.

Local paths are sent as multipart image[] fields. Set aspect_ratio explicitly: an edit is 1:1
unless you ask otherwise, whatever shape the references have.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from nanobanana import NanoBanana, price, save  # noqa: E402

client = NanoBanana()
images = client.edit(
    "Place the sneaker from the first image on the concrete plinth from the second image. "
    "Keep the sneaker's colors, logo and laces exactly. Hard noon light, long shadow, 4:3 frame.",
    ["sneaker.png", "style-board.jpg"],
    model="nano-banana-pro",
    aspect_ratio="4:3",
    resolution="2k",
)
print(save(images, "sneaker-ad"))
print(f"cost: ${price('nano-banana-pro', '2k', len(images)):.2f}")  # $0.03 per image at any tier
