import cv2
import numpy as np
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ExifTags, ImageOps
import os
import hashlib
import webbrowser
import threading
import time
import urllib.parse
from datetime import datetime

# MediaPipe optional import with graceful fallback
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False

# Playwright optional import with graceful fallback
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Ultralytics YOLO optional import with graceful fallback
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False


# Theme & UI Configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Theme Palette (Cyberpunk / Enterprise Forensics Theme)
COLOR_BG_DARK = "#0A0E17"
COLOR_SIDEBAR = "#0F172A"
COLOR_CARD = "#1E293B"
COLOR_CARD_BORDER = "#334155"
COLOR_ACCENT_CYAN = "#00E5FF"
COLOR_ACCENT_HOVER = "#00B8D4"
COLOR_CRIMSON = "#FF3366"
COLOR_SUCCESS = "#10B981"
COLOR_WARNING = "#F59E0B"
COLOR_TEXT_MAIN = "#F8FAFC"
COLOR_TEXT_MUTED = "#94A3B8"


class CyberForensicsProV5(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Settings
        self.title("CYBER-FORENSICS PRO V5.0 || Enterprise Face Detection & Image Intelligence")
        self.geometry("1180x820")
        self.minsize(1050, 720)
        self.configure(fg_color=COLOR_BG_DARK)

        # Application State
        self.current_image_path = None
        self.cropped_face_path = None
        self.webcam_running = False
        self.webcam_thread = None
        self.cap = None

        # Output Directories
        self.output_dir = os.path.join(os.getcwd(), "Scanned_Faces")
        os.makedirs(self.output_dir, exist_ok=True)

        # Initialize AI Detection Engines
        self.init_detection_engines()

        # Build UI Architecture
        self.build_ui()

        # Initial Log Message
        self.log_message("SYSTEM", "CYBER-FORENSICS PRO V5.0 initialized successfully.", level="SUCCESS")
        if MEDIAPIPE_AVAILABLE:
            self.log_message("ENGINE", "MediaPipe Face Detection Engine loaded.", level="INFO")
        else:
            self.log_message("ENGINE", "MediaPipe not installed. OpenCV HaarCascade active as fallback.", level="WARNING")

        if YOLO_AVAILABLE:
            self.log_message("ENGINE", "YOLOv8 Real-time Vision Engine loaded.", level="INFO")
        else:
            self.log_message("ENGINE", "YOLOv8 not installed. Standard HaarCascade active for webcam.", level="WARNING")

    def init_detection_engines(self):
        """Initializes MediaPipe, HaarCascade, and YOLOv8 models safely."""
        # MediaPipe Face Detection
        if MEDIAPIPE_AVAILABLE:
            try:
                self.mp_face_detection = mp.solutions.face_detection
                self.mp_detector = self.mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5)
            except Exception:
                self.mp_detector = None
        else:
            self.mp_detector = None

        # OpenCV Haar Cascade Fallback
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
        except Exception:
            self.face_cascade = None

        # YOLOv8 Model
        if YOLO_AVAILABLE:
            try:
                self.yolo_model = YOLO('yolov8n.pt')
            except Exception:
                self.yolo_model = None
        else:
            self.yolo_model = None

    def build_ui(self):
        """Constructs the responsive CustomTkinter layout."""
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # =========================================================================
        # 1. LEFT SIDEBAR PANEL (Controls, Target Inputs, Social Dorking)
        # =========================================================================
        self.sidebar = ctk.CTkFrame(self, width=290, corner_radius=0, fg_color=COLOR_SIDEBAR)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(12, weight=1)

        # Title & Subtitle
        lbl_brand = ctk.CTkLabel(
            self.sidebar, text="🛡️ CYBER-FORENSICS PRO", 
            font=ctk.CTkFont(size=18, weight="bold"), text_color=COLOR_ACCENT_CYAN
        )
        lbl_brand.pack(padx=20, pady=(20, 2), anchor="w")

        lbl_sub = ctk.CTkLabel(
            self.sidebar, text="v5.0 Enterprise Recon & Image Intelligence", 
            font=ctk.CTkFont(size=10, slant="italic"), text_color=COLOR_TEXT_MUTED
        )
        lbl_sub.pack(padx=20, pady=(0, 15), anchor="w")

        # Action Buttons Section
        lbl_sec1 = ctk.CTkLabel(self.sidebar, text="PRIMARY OPERATIONS", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_TEXT_MUTED)
        lbl_sec1.pack(padx=15, pady=(10, 4), anchor="w")

        self.btn_select_img = ctk.CTkButton(
            self.sidebar, text="📁 Select Target Image", command=self.select_image_dialog,
            fg_color="#2563EB", hover_color="#1D4ED8", font=ctk.CTkFont(weight="bold"), height=36
        )
        self.btn_select_img.pack(padx=15, pady=4, fill="x")

        self.btn_run_recon = ctk.CTkButton(
            self.sidebar, text="⚡ Run Full Recon & Forensics", command=self.start_recon_pipeline_async,
            fg_color=COLOR_CRIMSON, hover_color="#D97706", font=ctk.CTkFont(weight="bold"), height=38
        )
        self.btn_run_recon.pack(padx=15, pady=4, fill="x")

        # Live Stream Control Buttons
        self.btn_webcam_start = ctk.CTkButton(
            self.sidebar, text="🎥 Start Live Webcam Detection", command=self.start_webcam_stream_async,
            fg_color="#059669", hover_color="#047857", font=ctk.CTkFont(weight="bold"), height=34
        )
        self.btn_webcam_start.pack(padx=15, pady=4, fill="x")

        self.btn_webcam_stop = ctk.CTkButton(
            self.sidebar, text="🛑 Stop Stream Hardware", command=self.stop_webcam_stream,
            fg_color="#7F1D1D", hover_color="#991B1B", font=ctk.CTkFont(weight="bold"), height=30, state="disabled"
        )
        self.btn_webcam_stop.pack(padx=15, pady=2, fill="x")

        # Social Media & OSINT Dorking Input Section
        lbl_sec2 = ctk.CTkLabel(self.sidebar, text="OSINT DORKING & RECON", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_WARNING)
        lbl_sec2.pack(padx=15, pady=(18, 4), anchor="w")

        self.entry_dork_query = ctk.CTkEntry(
            self.sidebar, placeholder_text="Enter Name / Username / Alias...",
            fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, text_color=COLOR_TEXT_MAIN, height=32
        )
        self.entry_dork_query.pack(padx=15, pady=4, fill="x")

        # Social Platform Search Buttons
        social_grid = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        social_grid.pack(padx=15, pady=4, fill="x")
        social_grid.grid_columnconfigure((0, 1), weight=1)

        btn_fb = ctk.CTkButton(
            social_grid, text="📘 Facebook", command=lambda: self.launch_social_dork("facebook"),
            fg_color="#1877F2", hover_color="#0D65D9", font=ctk.CTkFont(size=11), height=30
        )
        btn_fb.grid(row=0, column=0, padx=2, pady=2, sticky="ew")

        btn_ig = ctk.CTkButton(
            social_grid, text="📸 Instagram", command=lambda: self.launch_social_dork("instagram"),
            fg_color="#E1306C", hover_color="#C1275B", font=ctk.CTkFont(size=11), height=30
        )
        btn_ig.grid(row=0, column=1, padx=2, pady=2, sticky="ew")

        btn_tt = ctk.CTkButton(
            social_grid, text="🎵 TikTok", command=lambda: self.launch_social_dork("tiktok"),
            fg_color="#000000", hover_color="#1F2937", border_width=1, border_color=COLOR_CARD_BORDER, font=ctk.CTkFont(size=11), height=30
        )
        btn_tt.grid(row=1, column=0, padx=2, pady=2, sticky="ew")

        btn_li = ctk.CTkButton(
            social_grid, text="💼 LinkedIn", command=lambda: self.launch_social_dork("linkedin"),
            fg_color="#0A66C2", hover_color="#084E96", font=ctk.CTkFont(size=11), height=30
        )
        btn_li.grid(row=1, column=1, padx=2, pady=2, sticky="ew")

        # Progress Indicator & Status Bar (Sidebar Bottom)
        self.lbl_progress = ctk.CTkLabel(self.sidebar, text="Ready", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_MUTED)
        self.lbl_progress.pack(padx=15, pady=(15, 2), anchor="w")

        self.progressbar = ctk.CTkProgressBar(self.sidebar, fg_color=COLOR_CARD, progress_color=COLOR_ACCENT_CYAN, height=8)
        self.progressbar.pack(padx=15, pady=(0, 15), fill="x")
        self.progressbar.set(0.0)

        # =========================================================================
        # 2. MAIN DISPLAY CONTENT (Previews, Metadata Cards, Logs)
        # =========================================================================
        self.main_content = ctk.CTkFrame(self, fg_color=COLOR_BG_DARK, corner_radius=0)
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=12, pady=12)

        # Top Display Card: Image Containers
        self.card_previews = ctk.CTkFrame(self.main_content, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=12)
        self.card_previews.pack(fill="x", pady=(0, 10))

        # Split into Original Image Box & Extracted Face Box
        self.card_previews.grid_columnconfigure((0, 1), weight=1)

        # Box 1: Original Image
        self.box_src = ctk.CTkFrame(self.card_previews, fg_color=COLOR_BG_DARK, corner_radius=8, height=210)
        self.box_src.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")
        self.box_src.pack_propagate(False)

        lbl_src_header = ctk.CTkLabel(self.box_src, text="📷 ORIGINAL SOURCE IMAGE", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_TEXT_MUTED)
        lbl_src_header.pack(pady=(6, 2))

        self.display_src_img = ctk.CTkLabel(self.box_src, text="No Image Selected\nClick 'Select Target Image' to begin", text_color=COLOR_TEXT_MUTED)
        self.display_src_img.pack(expand=True, fill="both")

        # Box 2: Extracted Face ROI
        self.box_face = ctk.CTkFrame(self.card_previews, fg_color=COLOR_BG_DARK, corner_radius=8, height=210)
        self.box_face.grid(row=0, column=1, padx=12, pady=12, sticky="nsew")
        self.box_face.pack_propagate(False)

        lbl_face_header = ctk.CTkLabel(self.box_face, text="🎯 EXTRACTED FACE ROI (MEDIAPIPE/AI)", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_ACCENT_CYAN)
        lbl_face_header.pack(pady=(6, 2))

        self.display_face_img = ctk.CTkLabel(self.box_face, text="Awaiting Extraction Pipeline...", text_color=COLOR_TEXT_MUTED)
        self.display_face_img.pack(expand=True, fill="both")

        # Middle Display Card: Metadata & Cryptographic Hashes
        self.card_meta = ctk.CTkFrame(self.main_content, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=12)
        self.card_meta.pack(fill="x", pady=(0, 10))

        lbl_meta_title = ctk.CTkLabel(self.card_meta, text="📊 FORENSIC METADATA & CRYPTOGRAPHIC HASHES", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_SUCCESS)
        lbl_meta_title.pack(anchor="w", padx=15, pady=(8, 4))

        self.meta_grid = ctk.CTkFrame(self.card_meta, fg_color="transparent")
        self.meta_grid.pack(padx=15, pady=(0, 10), fill="x")
        self.meta_grid.grid_columnconfigure((0, 1), weight=1)

        self.lbl_meta_device = ctk.CTkLabel(self.meta_grid, text="📱 Camera / Model: --", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_MAIN, anchor="w")
        self.lbl_meta_device.grid(row=0, column=0, padx=5, pady=3, sticky="w")

        self.lbl_meta_datetime = ctk.CTkLabel(self.meta_grid, text="⏰ Timestamp: --", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_MAIN, anchor="w")
        self.lbl_meta_datetime.grid(row=0, column=1, padx=5, pady=3, sticky="w")

        self.lbl_meta_gps = ctk.CTkLabel(self.meta_grid, text="📍 GPS Geolocation: --", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_MAIN, anchor="w")
        self.lbl_meta_gps.grid(row=1, column=0, padx=5, pady=3, sticky="w")

        self.lbl_meta_res = ctk.CTkLabel(self.meta_grid, text="📐 Dimensions & Format: --", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_MAIN, anchor="w")
        self.lbl_meta_res.grid(row=1, column=1, padx=5, pady=3, sticky="w")

        self.lbl_meta_hashes = ctk.CTkLabel(self.meta_grid, text="🔑 Hashes (MD5 / SHA256): --", font=ctk.CTkFont(size=10, family="Consolas"), text_color=COLOR_ACCENT_CYAN, anchor="w")
        self.lbl_meta_hashes.grid(row=2, column=0, columnspan=2, padx=5, pady=3, sticky="w")

        # Bottom Display Card: Real-Time Console Log
        self.card_logs = ctk.CTkFrame(self.main_content, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=12)
        self.card_logs.pack(fill="both", expand=True)

        lbl_log_title = ctk.CTkLabel(self.card_logs, text="📡 AUDIT CONSOLE & RECON LOGS", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_WARNING)
        lbl_log_title.pack(anchor="w", padx=15, pady=(6, 2))

        self.log_box = ctk.CTkTextbox(
            self.card_logs, fg_color=COLOR_BG_DARK, text_color=COLOR_SUCCESS, 
            font=ctk.CTkFont(family="Consolas", size=10), corner_radius=8
        )
        self.log_box.pack(padx=12, pady=(0, 10), fill="both", expand=True)

    # =========================================================================
    # 3. HELPER & UTILITY FUNCTIONS
    # =========================================================================
    def log_message(self, category, message, level="INFO"):
        """Appends formatted messages to the console log with timestamps."""
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        level_tag = f"[{level}]"
        formatted_line = f"{timestamp} {level_tag} [{category}] {message}\n"

        def update_textbox():
            self.log_box.insert("end", formatted_line)
            self.log_box.see("end")

        self.after(0, update_textbox)

    def set_progress(self, value, text):
        """Updates progress bar and status text safely from threads."""
        def update_ui():
            self.progressbar.set(value)
            self.lbl_progress.configure(text=text)
        self.after(0, update_ui)

    def create_ctk_image(self, image_path, target_size=(320, 170)):
        """Utility to scale PIL images cleanly preserving aspect ratio."""
        try:
            pil_img = Image.open(image_path)
            # Preserve aspect ratio using Pillow ImageOps
            pil_img = ImageOps.contain(pil_img, target_size, Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
            return ctk_img
        except Exception as e:
            self.log_message("IMAGE_ERR", f"Failed to scale image: {str(e)}", level="ERROR")
            return None

    # =========================================================================
    # 4. EXIF & CRYPTOGRAPHIC HASH EXTRACTION
    # =========================================================================
    def extract_forensics_metadata(self, file_path):
        """Extracts EXIF metadata, GPS, and computes MD5 & SHA256 hashes."""
        # 1. Compute Hashes
        md5_hash = hashlib.md5()
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
                sha256_hash.update(chunk)

        md5_str = md5_hash.hexdigest()
        sha256_str = sha256_hash.hexdigest()

        device_info = "Unknown / EXIF Stripped"
        datetime_info = "Not Recorded"
        gps_info = "No GPS Metadata Found"
        res_info = "--"
        google_maps_url = None

        try:
            img = Image.open(file_path)
            res_info = f"{img.width} x {img.height} px ({img.format})"

            exif_raw = img._getexif()
            if exif_raw:
                exif_data = {ExifTags.TAGS.get(k, k): v for k, v in exif_raw.items()}

                make = str(exif_data.get('Make', '')).strip()
                model = str(exif_data.get('Model', '')).strip()
                if make or model:
                    device_info = f"{make} {model}".strip()

                dt = exif_data.get('DateTimeOriginal') or exif_data.get('DateTime')
                if dt:
                    datetime_info = str(dt)

                # Parse GPS Coordinates if present
                gps_tag_data = exif_data.get('GPSInfo')
                if gps_tag_data:
                    coords = self.parse_gps_coords(gps_tag_data)
                    if coords:
                        lat, lon = coords
                        gps_info = f"LAT: {lat:.6f}, LON: {lon:.6f}"
                        google_maps_url = f"https://www.google.com/maps?q={lat},{lon}"

        except Exception as ex:
            self.log_message("EXIF_ERR", f"Error parsing EXIF: {str(ex)}", level="WARNING")

        # Update UI Labels
        def update_labels():
            self.lbl_meta_device.configure(text=f"📱 Camera / Model: {device_info}")
            self.lbl_meta_datetime.configure(text=f"⏰ Timestamp: {datetime_info}")
            self.lbl_meta_res.configure(text=f"📐 Dimensions & Format: {res_info}")
            
            if google_maps_url:
                self.lbl_meta_gps.configure(text=f"📍 GPS Geolocation: {gps_info} (Maps Link Logged)", text_color=COLOR_ACCENT_CYAN)
            else:
                self.lbl_meta_gps.configure(text=f"📍 GPS Geolocation: {gps_info}", text_color=COLOR_TEXT_MAIN)

            self.lbl_meta_hashes.configure(text=f"🔑 MD5: {md5_str}\n🔒 SHA256: {sha256_str[:32]}...")

        self.after(0, update_labels)

        self.log_message("HASH", f"MD5: {md5_str}", level="INFO")
        self.log_message("HASH", f"SHA256: {sha256_str}", level="INFO")
        if google_maps_url:
            self.log_message("GPS", f"Google Maps Link: {google_maps_url}", level="SUCCESS")

    def parse_gps_coords(self, gps_info):
        """Converts raw EXIF GPS rational tuples into decimal degrees."""
        try:
            def convert_to_degrees(value):
                d = float(value[0])
                m = float(value[1])
                s = float(value[2])
                return d + (m / 60.0) + (s / 3600.0)

            lat_data = gps_info.get(2)
            lat_ref = gps_info.get(1)
            lon_data = gps_info.get(4)
            lon_ref = gps_info.get(3)

            if lat_data and lat_ref and lon_data and lon_ref:
                lat = convert_to_degrees(lat_data)
                if lat_ref.upper() == 'S':
                    lat = -lat

                lon = convert_to_degrees(lon_data)
                if lon_ref.upper() == 'W':
                    lon = -lon

                return lat, lon
        except Exception:
            return None
        return None

    # =========================================================================
    # 5. DIALOG & FILE SELECTION
    # =========================================================================
    def select_image_dialog(self):
        """Opens file dialog for target image selection."""
        file_path = filedialog.askopenfilename(
            title="Select Target Forensic Image",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp *.webp")]
        )
        if file_path:
            self.current_image_path = file_path
            self.log_message("LOAD", f"Target file selected: {os.path.basename(file_path)}", level="INFO")

            # Display Source Image
            ctk_img = self.create_ctk_image(file_path)
            if ctk_img:
                self.display_src_img.configure(image=ctk_img, text="")

            # Extract EXIF & Hashes asynchronously
            threading.Thread(target=self.extract_forensics_metadata, args=(file_path,), daemon=True).start()

            # Reset Face Box
            self.display_face_img.configure(image=None, text="Click 'Run Full Recon & Forensics'")
            self.set_progress(0.1, "Image Loaded. Ready for Recon.")

    # =========================================================================
    # 6. ASYNCHRONOUS RECON & FACE DETECTION PIPELINE
    # =========================================================================
    def start_recon_pipeline_async(self):
        """Launches the recon thread to keep GUI responsive."""
        if not self.current_image_path:
            messagebox.showwarning("Warning", "Fadlan marka hore soo dooro sawir (Select Target Image).")
            return

        self.btn_run_recon.configure(state="disabled")
        threading.Thread(target=self.execute_recon_pipeline, daemon=True).start()

    def execute_recon_pipeline(self):
        """Performs face isolation (MediaPipe/Cascade) and reverse OSINT dispatch."""
        try:
            self.set_progress(0.25, "[1/4] Loading Image Tensor...")
            self.log_message("RECON", "Starting Facial Detection Pipeline...", level="INFO")

            image_cv = cv2.imread(self.current_image_path)
            if image_cv is None:
                self.log_message("ERROR", "Failed to decode target image file.", level="ERROR")
                self.set_progress(0.0, "Error loading image.")
                return

            h, w, _ = image_cv.shape
            cropped_face = None
            detection_engine_used = "None"

            # -----------------------------------------------------------------
            # Engine 1: MediaPipe Face Detection
            # -----------------------------------------------------------------
            if self.mp_detector is not None:
                self.set_progress(0.4, "[2/4] Executing MediaPipe Face Detection...")
                rgb_img = cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB)
                results = self.mp_detector.process(rgb_img)

                if results.detections:
                    # Find detection with highest score
                    best_detection = max(results.detections, key=lambda d: d.score[0])
                    bboxC = best_detection.location_data.relative_bounding_box

                    # Dynamic 20% Padding
                    pad_w = bboxC.width * 0.20
                    pad_h = bboxC.height * 0.20

                    xmin = int(max(0, (bboxC.xmin - pad_w) * w))
                    ymin = int(max(0, (bboxC.ymin - pad_h) * h))
                    xmax = int(min(w, (bboxC.xmin + bboxC.width + pad_w) * w))
                    ymax = int(min(h, (bboxC.ymin + bboxC.height + pad_h) * h))

                    cropped_face = image_cv[ymin:ymax, xmin:xmax]
                    detection_engine_used = f"MediaPipe (Confidence: {best_detection.score[0]:.2f})"

            # -----------------------------------------------------------------
            # Engine 2: Fallback to OpenCV HaarCascade
            # -----------------------------------------------------------------
            if cropped_face is None and self.face_cascade is not None and not self.face_cascade.empty():
                self.set_progress(0.5, "[2/4] MediaPipe missed/unavailable. Running HaarCascade...")
                gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

                if len(faces) > 0:
                    # Select largest face area
                    (fx, fy, fw, fh) = max(faces, key=lambda f: f[2] * f[3])
                    pad_w = int(fw * 0.20)
                    pad_h = int(fh * 0.20)

                    xmin = max(0, fx - pad_w)
                    ymin = max(0, fy - pad_h)
                    xmax = min(w, fx + fw + pad_w)
                    ymax = min(h, fy + fh + pad_h)

                    cropped_face = image_cv[ymin:ymax, xmin:xmax]
                    detection_engine_used = "OpenCV HaarCascade Fallback"

            # -----------------------------------------------------------------
            # Graceful Fallback if No Face Detected
            # -----------------------------------------------------------------
            if cropped_face is None or cropped_face.size == 0:
                self.log_message("WARNING", "No distinct face detected in image. Using full frame for reverse search.", level="WARNING")
                cropped_face = image_cv
                detection_engine_used = "Full Image (No Face Isolated)"
            else:
                self.log_message("SUCCESS", f"Face isolated using {detection_engine_used} ({cropped_face.shape[1]}x{cropped_face.shape[0]} px).", level="SUCCESS")

            # Save Cropped Face ROI
            self.cropped_face_path = os.path.join(self.output_dir, "Extracted_Face.jpg")
            cv2.imwrite(self.cropped_face_path, cropped_face)

            # Display Cropped Face in UI
            self.set_progress(0.7, "[3/4] Updating UI ROI Display...")
            ctk_face = self.create_ctk_image(self.cropped_face_path)
            if ctk_face:
                def show_face():
                    self.display_face_img.configure(image=ctk_face, text="")
                self.after(0, show_face)

            # -----------------------------------------------------------------
            # Step 4: Dispatch Reverse Image OSINT Search
            # -----------------------------------------------------------------
            self.set_progress(0.85, "[4/4] Dispatching OSINT Reverse Engines...")
            self.dispatch_reverse_image_search()

            self.set_progress(1.0, "Recon Pipeline Completed Successfully.")
            self.log_message("COMPLETE", "Full reconnaissance sequence executed.", level="SUCCESS")

        except Exception as ex:
            self.log_message("CRITICAL", f"Pipeline Exception: {str(ex)}", level="ERROR")
            self.set_progress(0.0, "Pipeline Error occurred.")
        finally:
            def reenable():
                self.btn_run_recon.configure(state="normal")
            self.after(0, reenable)

    # =========================================================================
    # 7. RELIABLE REVERSE IMAGE OSINT DISPATCHER
    # =========================================================================
    def auto_upload_to_yandex_playwright(self, image_path):
        """Automates uploading the extracted facial ROI directly to Yandex Images using Playwright."""
        if not PLAYWRIGHT_AVAILABLE:
            self.log_message("PLAYWRIGHT", "Playwright not installed. Opening Yandex portal in default browser.", level="WARNING")
            webbrowser.open("https://yandex.com/images/")
            return

        try:
            self.log_message("PLAYWRIGHT", "Launching Playwright Auto-Upload to Yandex Images...", level="INFO")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                page = browser.new_page()
                page.goto("https://yandex.com/images/")
                page.wait_for_selector('.input__cbir-button', timeout=8000)
                page.click('.input__cbir-button')
                page.set_input_files('input[type="file"]', image_path)
                self.log_message("PLAYWRIGHT", "Face image payload uploaded successfully to Yandex Facial Recon!", level="SUCCESS")
        except Exception as ex:
            self.log_message("PLAYWRIGHT_ERR", f"Playwright auto-upload encountered issue: {str(ex)}. Opening default browser fallback.", level="WARNING")
            webbrowser.open("https://yandex.com/images/")

    def dispatch_reverse_image_search(self):
        """Launches reverse search providers using Playwright automation & browser fallbacks."""
        self.log_message("OSINT", "Launching multi-engine reverse search query...", level="INFO")

        # 1. Google Lens Portal
        webbrowser.open("https://lens.google.com/")
        self.log_message("DISPATCH", "Opened Google Lens Portal for visual matching.", level="INFO")

        # 2. Bing Visual Search Portal
        webbrowser.open("https://www.bing.com/visualsearch")
        self.log_message("DISPATCH", "Opened Bing Visual Search Portal.", level="INFO")

        # 3. Yandex Direct Auto-Upload via Playwright (or Fallback)
        if self.cropped_face_path and os.path.exists(self.cropped_face_path):
            self.auto_upload_to_yandex_playwright(self.cropped_face_path)
        else:
            webbrowser.open("https://yandex.com/images/")

        # 4. Open Local Folder containing Extracted Face for easy drag-and-drop
        try:
            os.startfile(self.output_dir)
            self.log_message("LOCAL", "Opened Scanned_Faces directory for direct drag-and-drop upload.", level="SUCCESS")
        except Exception:
            pass

    def launch_social_dork(self, platform):
        """Performs targeted social media OSINT dorking using provided query or metadata."""
        query = self.entry_dork_query.get().strip()

        if not query:
            query = "profile"

        encoded_query = urllib.parse.quote(query)
        self.log_message("DORK", f"Initiating targeted {platform.upper()} Dork Query: '{query}'...", level="INFO")

        if platform == "facebook":
            url = f"https://www.google.com/search?q=site:facebook.com+{encoded_query}"
        elif platform == "instagram":
            url = f"https://www.google.com/search?q=site:instagram.com+{encoded_query}"
        elif platform == "tiktok":
            url = f"https://www.google.com/search?q=site:tiktok.com+{encoded_query}"
        elif platform == "linkedin":
            url = f"https://www.google.com/search?q=site:linkedin.com/in/+{encoded_query}"
        else:
            url = f"https://www.google.com/search?q={encoded_query}"

        webbrowser.open(url)

    # =========================================================================
    # 8. REAL-TIME WEBCAM DETECTION (YOLOV8 / OPENCV)
    # =========================================================================
    def start_webcam_stream_async(self):
        """Starts real-time webcam processing loop in background thread."""
        if self.webcam_running:
            return

        self.webcam_running = True
        self.btn_webcam_start.configure(state="disabled")
        self.btn_webcam_stop.configure(state="normal")
        self.log_message("WEBCAM", "Initializing webcam hardware interface...", level="INFO")

        self.webcam_thread = threading.Thread(target=self.webcam_loop, daemon=True)
        self.webcam_thread.start()

    def stop_webcam_stream(self):
        """Signals the webcam thread to stop and releases hardware."""
        if self.webcam_running:
            self.webcam_running = False
            self.log_message("WEBCAM", "Stopping webcam stream requested...", level="INFO")

    def webcam_loop(self):
        """Executes non-blocking webcam frame capture and AI detection."""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.log_message("WEBCAM_ERR", "Could not access camera device (Index 0).", level="ERROR")
            self.webcam_running = False
            def reset_btn():
                self.btn_webcam_start.configure(state="normal")
                self.btn_webcam_stop.configure(state="disabled")
            self.after(0, reset_btn)
            return

        window_name = "CYBER-FORENSICS PRO V5 - Real-Time Vision (Press Q to exit)"
        frame_count = 0
        fps_start_time = time.time()
        fps_display = "FPS: --"

        self.log_message("WEBCAM", "Live video feed active.", level="SUCCESS")

        while self.webcam_running:
            ret, frame = self.cap.read()
            if not ret:
                break

            frame_count += 1
            if frame_count % 10 == 0:
                elapsed = time.time() - fps_start_time
                fps = 10 / elapsed if elapsed > 0 else 0
                fps_display = f"FPS: {fps:.1f}"
                fps_start_time = time.time()

            annotated_frame = frame.copy()

            # YOLO Object Detection Overlay if available
            if self.yolo_model is not None:
                try:
                    results = self.yolo_model(frame, verbose=False)
                    annotated_frame = results[0].plot()
                except Exception:
                    pass

            # OpenCV HaarCascade Face Detection Overlay
            if self.face_cascade is not None and not self.face_cascade.empty():
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
                for (x, y, w, h) in faces:
                    cv2.rectangle(annotated_frame, (x, y), (x + w, y + h), (255, 229, 0), 2)
                    cv2.putText(annotated_frame, 'Target Face', (x, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 229, 0), 2)

            # Draw HUD Overlays (FPS & Frame Counter)
            cv2.putText(annotated_frame, f"CYBER-FORENSICS V5 | {fps_display}", (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 229, 255), 2)

            cv2.imshow(window_name, annotated_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:  # Q or ESC key
                break

            # Check if user closed the OpenCV window manually
            try:
                if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                    break
            except Exception:
                break

        # Release Hardware Cleanly
        self.cap.release()
        cv2.destroyAllWindows()
        self.webcam_running = False

        def cleanup_ui():
            self.btn_webcam_start.configure(state="normal")
            self.btn_webcam_stop.configure(state="disabled")
        self.after(0, cleanup_ui)

        self.log_message("WEBCAM", "Webcam hardware released and stream terminated.", level="INFO")


# =========================================================================
# APPLICATION ENTRYPOINT
# =========================================================================
if __name__ == "__main__":
    app = CyberForensicsProV5()
    app.mainloop()
