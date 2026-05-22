"""
Face detection and recognition using OpenCV.
Uses Haar Cascade for face detection and LBPH for face recognition.
No dlib dependency — pure OpenCV.

Workflow:
1. Capture frame from webcam
2. Detect faces (Haar Cascade)
3. If known faces registered, try to recognize (LBPH)
4. Return detection results

To register a face:
  detector.register_face("Mickey", [image1, image2, ...])
"""

import cv2
import os
import json
import numpy as np
from config import DATA_DIR

FACES_DIR = os.path.join(DATA_DIR, "faces")
MODEL_FILE = os.path.join(FACES_DIR, "face_model.yml")
LABELS_FILE = os.path.join(FACES_DIR, "labels.json")

# Haar cascade for face detection (ships with OpenCV)
CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

_detector = None
_recognizer = None
_labels = {}


def _get_detector():
    global _detector
    if _detector is None:
        _detector = cv2.CascadeClassifier(CASCADE_PATH)
    return _detector


def _get_recognizer():
    global _recognizer, _labels
    if _recognizer is None:
        _recognizer = cv2.face.LBPHFaceRecognizer_create()
        if os.path.exists(MODEL_FILE) and os.path.exists(LABELS_FILE):
            _recognizer.read(MODEL_FILE)
            with open(LABELS_FILE, "r") as f:
                _labels = json.load(f)
    return _recognizer


def capture_frame() -> np.ndarray | None:
    """Capture a single frame from the default webcam."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return None
    ret, frame = cap.read()
    cap.release()
    return frame if ret else None


def detect_faces(frame: np.ndarray) -> list[dict]:
    """Detect faces in a frame. Returns list of {x, y, w, h}."""
    detector = _get_detector()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
    return [{"x": int(x), "y": int(y), "w": int(w), "h": int(h)} for (x, y, w, h) in faces]


def recognize_faces(frame: np.ndarray) -> list[dict]:
    """Detect and attempt to recognize faces."""
    faces = detect_faces(frame)
    if not faces or not os.path.exists(MODEL_FILE):
        return [{"bbox": f, "name": "unknown", "confidence": 0} for f in faces]

    recognizer = _get_recognizer()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    results = []

    for face in faces:
        x, y, w, h = face["x"], face["y"], face["w"], face["h"]
        roi = gray[y : y + h, x : x + w]
        roi = cv2.resize(roi, (200, 200))

        try:
            label_id, confidence = recognizer.predict(roi)
            # LBPH confidence: lower = better match. <50 = good, <80 = ok
            name = _labels.get(str(label_id), "unknown")
            if confidence > 80:
                name = "unknown"
            results.append({
                "bbox": face,
                "name": name,
                "confidence": round(100 - confidence, 1),  # Invert so higher = better
            })
        except Exception:
            results.append({"bbox": face, "name": "unknown", "confidence": 0})

    return results


def register_face(name: str, num_samples: int = 20) -> dict:
    """Capture face samples from webcam and train recognizer."""
    os.makedirs(FACES_DIR, exist_ok=True)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return {"status": "error", "reason": "Cannot open camera"}

    detector = _get_detector()
    samples = []
    captured = 0

    while captured < num_samples:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))
        for (x, y, w, h) in faces:
            roi = gray[y : y + h, x : x + w]
            roi = cv2.resize(roi, (200, 200))
            samples.append(roi)
            captured += 1
            if captured >= num_samples:
                break

    cap.release()

    if not samples:
        return {"status": "error", "reason": "No faces detected"}

    # Load existing labels or create new
    global _labels
    if os.path.exists(LABELS_FILE):
        with open(LABELS_FILE, "r") as f:
            _labels = json.load(f)

    # Assign label ID
    existing_ids = [int(k) for k in _labels.keys()] if _labels else []
    label_id = max(existing_ids) + 1 if existing_ids else 0
    _labels[str(label_id)] = name

    # Save labels
    with open(LABELS_FILE, "w") as f:
        json.dump(_labels, f)

    # Train or update recognizer
    recognizer = _get_recognizer()
    labels_array = np.array([label_id] * len(samples))

    if os.path.exists(MODEL_FILE):
        recognizer.update(samples, labels_array)
    else:
        recognizer.train(samples, labels_array)

    recognizer.save(MODEL_FILE)

    return {"status": "ok", "name": name, "samples": captured}


def get_registered_faces() -> list[str]:
    """List all registered face names."""
    if os.path.exists(LABELS_FILE):
        with open(LABELS_FILE, "r") as f:
            labels = json.load(f)
        return list(set(labels.values()))
    return []


def quick_check() -> dict:
    """Quick camera check: capture frame, detect faces, recognize if possible."""
    frame = capture_frame()
    if frame is None:
        return {"status": "no_camera", "faces": []}

    results = recognize_faces(frame)
    return {
        "status": "ok",
        "faces_detected": len(results),
        "faces": results,
    }
