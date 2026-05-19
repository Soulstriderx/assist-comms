import cv2
import time
import threading
import numpy as np
import tensorflow as tf
import customtkinter as ctk
from mediapipe import Image, ImageFormat
from collections import deque, Counter
from PIL import Image as PILImage
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode

# =================================================================================
# Config
# =================================================================================
MODEL_PATH       = "./model/asl_landmark_model.keras"
CLASS_NAMES_PATH = "./model/class_names.txt"
LANDMARKER_PATH  = "./mediapipe/hand_landmarker.task"
CONF_THRESHOLD   = 0.70
BUFFER_SIZE      = 10

# Load class names saved during training to guarantee correct order
with open(CLASS_NAMES_PATH, 'r') as f:
    class_names = [line.strip() for line in f.readlines()]

model = tf.keras.models.load_model(MODEL_PATH)

base_options = python.BaseOptions(model_asset_path=LANDMARKER_PATH)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=VisionTaskRunningMode.VIDEO,
    num_hands=1,
    min_hand_detection_confidence=0.3,
    min_hand_presence_confidence=0.3,
    min_tracking_confidence=0.3
)
detector = vision.HandLandmarker.create_from_options(options)

# =================================================================================
# Landmark extraction — matches normalisation used in landmark_train.py
# =================================================================================
def extract_landmarks(frame):
    timestamp_ms = int(time.time() * 1000)
    rgb          = frame.astype(np.uint8)
    annotated    = rgb.copy()

    mp_image = Image(image_format=ImageFormat.SRGB, data=rgb)
    result   = detector.detect_for_video(mp_image, timestamp_ms)

    if not result.hand_landmarks:
        return None, annotated

    lms     = result.hand_landmarks[0]
    h, w, _ = frame.shape
    xs = [int(lm.x * w) for lm in lms]
    ys = [int(lm.y * h) for lm in lms]

    # Bounding box + dots for visualisation
    x_min = max(min(xs) - 20, 0);  y_min = max(min(ys) - 20, 0)
    x_max = min(max(xs) + 20, w);  y_max = min(max(ys) + 20, h)
    cv2.rectangle(annotated, (x_min, y_min), (x_max, y_max), (0, 255, 80), 2)
    for x, y in zip(xs, ys):
        cv2.circle(annotated, (x, y), 3, (255, 80, 0), -1)

    # Finger connections
    CONNECTIONS = [
        (0,1),(1,2),(2,3),(3,4),
        (0,5),(5,6),(6,7),(7,8),
        (0,9),(9,10),(10,11),(11,12),
        (0,13),(13,14),(14,15),(15,16),
        (0,17),(17,18),(18,19),(19,20),
        (5,9),(9,13),(13,17)
    ]
    for a, b in CONNECTIONS:
        cv2.line(annotated, (xs[a], ys[a]), (xs[b], ys[b]), (100, 220, 255), 1)

    # Normalise — wrist to origin, scale invariant (must match training)
    coords = np.array([[lm.x, lm.y, lm.z] for lm in lms], dtype=np.float32)
    coords -= coords[0]
    scale   = np.max(np.linalg.norm(coords, axis=1))
    if scale > 0:
        coords /= scale

    return coords.flatten(), annotated   # shape (63,)

# =================================================================================
# ASL Tab
# =================================================================================
class ASLTab:
    def __init__(self, parent, sentence_box: ctk.CTkTextbox):
        self.sentence_box    = sentence_box
        self.buffer          = deque(maxlen=BUFFER_SIZE)
        self.last_pred       = ""
        self.running         = False
        self.cap             = None
        self._last_commit    = 0.0
        self.COMMIT_COOLDOWN = 1.5
        self._build_ui(parent)

    def _build_ui(self, parent):
        parent.columnconfigure(0, weight=3, uniform="asl")
        parent.columnconfigure(1, weight=1, uniform="asl")
        parent.rowconfigure(0, weight=1)

        # Left: webcam
        left = ctk.CTkFrame(parent, corner_radius=12)
        left.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        self.video_label = ctk.CTkLabel(left, text="Press 'Start Camera' to begin")
        self.video_label.pack(expand=True, fill="both", padx=8, pady=8)

        # Right: controls
        right = ctk.CTkFrame(parent, corner_radius=12)
        right.grid(row=0, column=1, padx=(8, 0), sticky="nsew")

        ctk.CTkLabel(right, text="ASL Detector",
                    font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(20, 4))
        ctk.CTkLabel(right, text="MLP  ·  MediaPipe",
                    font=ctk.CTkFont(size=11), text_color="gray").pack(pady=(0, 16))

        ctk.CTkLabel(right, text="Current Prediction",
                    font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w", padx=20)
        self.pred_label = ctk.CTkLabel(right, text="—",
                                    font=ctk.CTkFont(size=36, weight="bold"),
                                    text_color="#4fc3f7")
        self.pred_label.pack(pady=(0, 4))
        self.conf_label = ctk.CTkLabel(right, text="",
                                    font=ctk.CTkFont(size=12), text_color="gray")
        self.conf_label.pack(pady=(0, 12))

        self.status = ctk.CTkLabel(right, text="● Stopped",
                                font=ctk.CTkFont(size=12), text_color="#ef5350")
        self.status.pack(pady=(0, 8))

        ctk.CTkButton(right, text="Start Camera", command=self._start,
                    height=38, font=ctk.CTkFont(size=13, weight="bold")).pack(
                    fill="x", padx=20, pady=2)
        ctk.CTkButton(right, text="Stop Camera", command=self.stop,
                    height=38, fg_color="#455a64", hover_color="#546e7a",
                    font=ctk.CTkFont(size=13)).pack(fill="x", padx=20, pady=2)
        ctk.CTkButton(right, text="⌫  Backspace", command=self._backspace,
                    height=34, fg_color="#37474f", hover_color="#455a64",
                    font=ctk.CTkFont(size=12)).pack(fill="x", padx=20, pady=2)
        ctk.CTkButton(right, text="Space", command=self._space,
                    height=34, fg_color="#37474f", hover_color="#455a64",
                    font=ctk.CTkFont(size=12)).pack(fill="x", padx=20, pady=2)

    # ---- Camera controls ----
    def _start(self):
        if self.running:
            return
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.status.configure(text="● Camera not found", text_color="#ef5350")
            return
        self.running = True
        self.status.configure(text="● Running", text_color="#66bb6a")
        threading.Thread(target=self._cam_loop, daemon=True).start()

    def stop(self, closing=False):
        self.running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        if not closing:
            try:
                self.status.configure(text="● Stopped", text_color="#ef5350")
                self.video_label.configure(image="", text="Press 'Start Camera' to begin")
                self.video_label.image = None
            except Exception:
                pass

    def clear_asl(self):
        """Clears ASL module's internal state, called by main"""
        self.buffer.clear()
        self.last_pred    = ""
        self._last_commit = 0.0

    def _backspace(self):
        try:
            self.sentence_box.delete("end-2c", "end-1c")
        except Exception:
            pass

    def _space(self):
        self._append_char(" ")

    def _append_char(self, char):
        self.sentence_box.insert("end", char)
        self.sentence_box.see("end")

    def _safe_func(self, fn):
        try:
            self.video_label.after(0, fn)
        except Exception:
            pass

    # ---- Camera loop ----
    def _cam_loop(self):
        while self.running:
            if not self.cap or not self.cap.isOpened():
                break
            ret, frame = self.cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            features, annotated = extract_landmarks(rgb)

            if features is not None:
                img   = np.expand_dims(features, axis=0)  # (1, 63)
                preds = model.predict(img, verbose=0)
                idx   = int(np.argmax(preds))
                conf  = float(np.max(preds))
                label = class_names[idx]

                if conf >= CONF_THRESHOLD:
                    self.buffer.append(label)
                    stable = Counter(self.buffer).most_common(1)[0][0]
                    if len(self.buffer) >= BUFFER_SIZE:
                        now        = time.time()
                        cooled     = (now - self._last_commit) >= self.COMMIT_COOLDOWN
                        new_letter = stable != self.last_pred
                        min_gap    = 1.0
                        if (now - self._last_commit) >= min_gap and (new_letter or cooled):
                            self.last_pred    = stable
                            self._last_commit = now
                            char = " " if stable == "Space" else stable
                            self.buffer.clear()
                            def _append_char(c=char):
                                try: self._append_char(c)
                                except Exception: pass
                            self._safe_func(_append_char)

                    def _update_pred(l=label, c=conf):
                        try:
                            self.pred_label.configure(text=l.upper())
                            self.conf_label.configure(
                                text=f"{c:.1%} confidence",
                                text_color="#66bb6a" if c > 0.85 else "#ffa726")
                        except Exception: pass
                    self._safe_func(_update_pred)
                else:
                    def _low_conf():
                        try: self.conf_label.configure(
                            text="Low confidence", text_color="#ef9a9a")
                        except Exception: pass
                    self._safe_func(_low_conf)
            else:
                def _no_hand():
                    try:
                        self.pred_label.configure(text="—")
                        self.conf_label.configure(
                            text="No hand detected", text_color="gray")
                    except Exception: pass
                self._safe_func(_no_hand)

            # Scale frame to label size
            lw = self.video_label.winfo_width()
            lh = self.video_label.winfo_height()
            if lw < 10 or lh < 10:
                lw, lh = 520, 560
            fh, fw  = annotated.shape[:2]
            scale   = min(lw / fw, lh / fh)
            dw      = int(fw * scale)
            dh      = int(fh * scale)
            disp    = cv2.resize(annotated, (dw, dh))
            pil     = PILImage.fromarray(disp)
            ctk_img = ctk.CTkImage(light_image=pil, dark_image=pil, size=(dw, dh))

            def _set_curr_frame(i=ctk_img):
                try: self.video_label.configure(image=i, text="")
                except Exception: pass
            self._safe_func(_set_curr_frame)