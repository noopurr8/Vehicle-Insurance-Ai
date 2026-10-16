from ultralytics import YOLO

MODEL_PATH = r"C:\Users\noopu\Desktop\vehicle-insurance-ai\runs\detect\train-2\weights\best.pt"

model = YOLO(MODEL_PATH)


def detect_damage(image_path):
    results = model(image_path, conf=0.25, verbose=False)

    detections = []

    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            detections.append({
                "damage_type": result.names[class_id],
                "confidence": round(confidence, 3)
            })

    return {
        "damage_count": len(detections),
        "damages": detections
    }


if __name__ == "__main__":
    print("YOLO damage detection service ready.")