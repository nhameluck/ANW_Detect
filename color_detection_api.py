
import cv2
import numpy as np
from flask import Flask, request, jsonify
import os
import csv
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
FEEDBACK_FILE = 'feedback.csv'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Define color categories (RGB thresholds)
COLOR_THRESHOLDS = {
    "white": lambda avg: all(x > 220 for x in avg),
    "black": lambda avg: all(x < 50 for x in avg),
    "grey": lambda avg: 130 < avg[0] < 180 and 130 < avg[1] < 180 and 130 < avg[2] < 180,
    "yellow": lambda avg: avg[0] > 180 and avg[1] > 180 and avg[2] < 100,
    "orange": lambda avg: avg[0] > 200 and 100 < avg[1] < 160,
    "brown": lambda avg: avg[0] < 120 and avg[1] < 100 and avg[2] < 80
}

def classify_color(avg_color):
    for color, condition in COLOR_THRESHOLDS.items():
        if condition(avg_color):
            return color
    return "unknown"

@app.route("/detect-color", methods=["POST"])
def detect_color():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    file = request.files["image"]
    image_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(image_path)

    img = cv2.imread(image_path)
    h, w, _ = img.shape
    center = (w // 2, h // 2)
    inner_r = int(min(h, w) * 0.15)
    outer_r = int(min(h, w) * 0.25)

    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(mask, center, outer_r, 255, thickness=-1)
    cv2.circle(mask, center, inner_r, 0, thickness=-1)

    mean_color = cv2.mean(img, mask=mask)[:3]
    mean_color = tuple(map(int, mean_color[::-1]))  # Convert BGR to RGB
    detected = classify_color(mean_color)

    return jsonify({
        "dominant_color": detected,
        "average_rgb": mean_color
    })

@app.route("/feedback", methods=["POST"])
def save_feedback():
    data = request.get_json()
    true_color = data.get("true_color")
    avg_rgb = data.get("average_rgb")

    if not true_color or not avg_rgb:
        return jsonify({"error": "Missing data"}), 400

    with open(FEEDBACK_FILE, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([datetime.utcnow().isoformat(), avg_rgb, true_color])

    return jsonify({"status": "feedback saved"})

if __name__ == "__main__":
    app.run(debug=True)
