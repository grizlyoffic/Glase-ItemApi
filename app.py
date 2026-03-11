import io
import os
import requests
from flask import Flask, send_file, jsonify
from PIL import Image

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BACKGROUND_FOLDER = os.path.join(BASE_DIR, "background")
DEFAULT_BACKGROUND = os.path.join(BACKGROUND_FOLDER, "white.jpg")


def get_item_info(item_id):
    url = f"https://item-info-neon.vercel.app/info?item_id={item_id}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
    except:
        return None
    return None


def get_icon(item_id):
    url = f"https://item-info-neon.vercel.app/icon?item_id={item_id}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return Image.open(io.BytesIO(r.content)).convert("RGBA")
    except:
        return None
    return None


@app.route("/ICON/<int:item_id>.png")
def generate_icon(item_id):

    info = get_item_info(item_id)

    if not info:
        return jsonify({"error": "Item info not found"}), 404

    rare = info.get("Rare", "Default")

    bg_path = os.path.join(BACKGROUND_FOLDER, f"{rare}.png")

    if not os.path.exists(bg_path):
        bg_path = DEFAULT_BACKGROUND

    try:
        background = Image.open(bg_path).convert("RGBA")
    except:
        return jsonify({"error": "Background not found"}), 500

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


# Vercel entry
app = app
