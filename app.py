import io
import os
import requests
from flask import Flask, send_file, jsonify
from PIL import Image

app = Flask(__name__)

BACKGROUND_FOLDER = "background"
DEFAULT_BACKGROUND = "background/Default.png"


def get_item_info(item_id):
    url = f"https://item-info-neon.vercel.app/info?item_id={item_id}"
    r = requests.get(url)

    if r.status_code != 200:
        return None

    return r.json()


def get_icon(item_id):
    url = f"https://item-info-neon.vercel.app/icon?item_id={item_id}"
    r = requests.get(url)

    if r.status_code != 200:
        return None

    return Image.open(io.BytesIO(r.content)).convert("RGBA")


@app.route("/ICON/<int:item_id>.png")
def generate_icon(item_id):

    info = get_item_info(item_id)

    if not info:
        return jsonify({"error": "Item not found"}), 404

    rare = info.get("Rare", "Default")

    bg_path = os.path.join(BACKGROUND_FOLDER, f"{rare}.png")

    if not os.path.exists(bg_path):
        bg_path = DEFAULT_BACKGROUND

    background = Image.open(bg_path).convert("RGBA")

    icon = get_icon(item_id)

    if icon is None:
        return jsonify({"error": "Icon not found"}), 404

    bg_w, bg_h = background.size

    target_w = int(bg_w * 0.8)
    target_h = int(bg_h * 0.8)

    icon_w, icon_h = icon.size
    icon_ratio = icon_w / icon_h
    target_ratio = target_w / target_h

    if icon_ratio > target_ratio:
        new_w = target_w
        new_h = int(target_w / icon_ratio)
    else:
        new_h = target_h
        new_w = int(target_h * icon_ratio)

    icon = icon.resize((new_w, new_h), Image.LANCZOS)

    paste_x = (bg_w - new_w) // 2
    paste_y = (bg_h - new_h) // 2

    layer = Image.new("RGBA", background.size, (0, 0, 0, 0))
    layer.paste(icon, (paste_x, paste_y), icon)

    final = Image.alpha_composite(background, layer)

    img_bytes = io.BytesIO()
    final.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    return send_file(img_bytes, mimetype="image/png")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)