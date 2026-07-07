import time
import threading
import speech_recognition as sr
import cv2
import mediapipe as mp
import pyttsx3

class OmniMedUltraSystem:
    def __init__(self):
        print("\n==================================================", flush=True)
        print("🚀 PROJECT OMNIMED FLOW: INITIALIZING ACTIVE CORE", flush=True)
        print("==================================================\n", flush=True)

        # --- 1. Audio Keyword & TTS Mapping ---
        print("[STARTUP 1/4] Setting up Audio Engine & Mic configuration...", flush=True)
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.rolling_memory = []
        
        self.EMERGENCY_DATABASE = {
            "help": "Emergency assistance requested immediately! Alerting the nearest medical response team.",
            "heart attack": "Warning! Acute myocardial infarction detected. Staging Heparin and Aspirin protocols.",
            "code blue": "Alert! Code Blue situation confirmed. Deploying critical resuscitation assets.",
            "heparin": "Staging Heparin medication block.",
            "epinephrine": "Deploying Epinephrine injection unit.",
            "anaphylaxis": "Critical Alert! Severe anaphylactic shock protocol initiated. Fetching Epinephrine.",
            "stroke": "Warning! Acute stroke pathway active. Staging tissue plasminogen activator.",
            "seizure": "Alert! Active patient seizure event detected. Preparing anti-convulsant doses.",
            "overdose": "Warning! Opioid or narcotic toxicity suspected. Staging Naloxone kits instantly.",
            "asthma": "Alert! Severe bronchospasm detected. Preparing emergency nebulizer units.",
            "bleeding": "Trauma Alert! Severe hemorrhage protocol. Staging clotting agents and pressure packs.",
            "unresponsive": "Alert! Patient is unresponsive. Prepare emergency response team."
        }
        self.last_spoken_alert = ""
        print("  -> Audio Engine Configured!", flush=True)

        # --- 2. Vision Core Setup (Hands + Pose Trackers) ---
        print("[STARTUP 2/4] Loading Hand Skeleton Tracking Models...", flush=True)
        self.mp_hands = mp.solutions.hands
        self.mp_pose = mp.solutions.pose
        self.mp_draw = mp.solutions.drawing_utils
        
        self.hands = self.mp_hands.Hands(
            static_image_mode=False, max_num_hands=1,
            min_detection_confidence=0.7, min_tracking_confidence=0.7
        )
        print("  -> Hand Tracking Assets Active!", flush=True)
        
        print("[STARTUP 3/4] Loading Humanoid Pose Engine (Torso & Chest Tracking)...", flush=True)
        self.pose = self.mp_pose.Pose(
            static_image_mode=False, model_complexity=0,
            min_detection_confidence=0.6, min_tracking_confidence=0.6
        )
        print("  -> Body Core Logic Active!", flush=True)
        
        # --- 3. System Control & Gestures Timers ---
        self.heart_gesture_start_time = None
        self.head_gesture_start_time = None
        self.active_vision_alert = "NONE"
        self.is_running = True
        print("[STARTUP 4/4] Core Calibration Complete! System ready to boot.", flush=True)

    # ==================== VOICE ANNOUNCEMENT ENGINE (TTS) ====================
    def trigger_voice_announcement(self, text_to_speak):
        def speech_worker():
            try:
                engine = pyttsx3.init()
                engine.setProperty('rate', 160)  
                engine.say(text_to_speak)
                engine.runAndWait()
            except Exception as e:
                print(f"[TTS ERROR] Voice engine drop: {e}", flush=True)

        threading.Thread(target=speech_worker, daemon=True).start()

    # ==================== AUDIO CORE LOGIC ====================
    def clean_expired_memory(self):
        current_time = time.time()
        self.rolling_memory = [chunk for chunk in self.rolling_memory if (current_time - chunk[1]) <= 20.0]

    def scan_for_keywords(self):
        combined_text = " ".join([chunk[0] for chunk in self.rolling_memory])
        if not combined_text.strip():
            return
            
        print(f"\n⏳ [20s ROLLING BUFFER] : \"{combined_text}\"", flush=True)
        
        for keyword, warning_speech in self.EMERGENCY_DATABASE.items():
            if keyword in combined_text:
                print(f"🎯 [AUDIO KEYWORD MATCH] Fired Trigger For: {keyword.upper()}", flush=True)
                
                if self.last_spoken_alert != keyword:
                    self.last_spoken_alert = keyword
                    self.trigger_voice_announcement(warning_speech)
                return 

    def start_microphone_stream(self):
        print("[INIT] Calibrating room mic environment... 2 seconds.", flush=True)
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        print("[ACTIVE] Microphone Matrix Live! Speak your commands.\n", flush=True)

        while self.is_running:
            try:
                with self.microphone as source:
                    audio_data = self.recognizer.listen(source, phrase_time_limit=4)
                raw_text = self.recognizer.recognize_google(audio_data).lower()
                if raw_text.strip():
                    self.rolling_memory.append((raw_text, time.time()))
                    print(f"🎙️ [MIC HEARD] '{raw_text}'", flush=True)
            except sr.UnknownValueError: continue
            except sr.RequestError: time.sleep(2)

    def continuous_brain_scanner(self):
        while self.is_running:
            time.sleep(2)
            self.clean_expired_memory()
            self.scan_for_keywords()

    # ==================== VISION CORE LOGIC ====================
    def start_camera_stream(self):
        cap = None
        print("\n[CAMERA SCAN] Probing available camera channels (0 to 3) via DirectShow...", flush=True)
        
        for index in [0, 1, 2, 3]:
            print(f"  -> Testing Port Index {index}...", flush=True)
            test_cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if test_cap.isOpened():
                ret, frame = test_cap.read()
                if ret:
                    cap = test_cap
                    print(f"✅ Active Feed successfully bound at Index: {index}!", flush=True)
                    break
            test_cap.release()

        if cap is None:
            print("\n❌ [CRITICAL ERROR] No active camera stream found!", flush=True)
            self.is_running = False
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # --- FORCE WINDOW TO FRONT LAYER ---
        cv2.namedWindow("OmniMed Ultra Dual Tracker", cv2.WINDOW_AUTOSIZE)
        cv2.setWindowProperty("OmniMed Ultra Dual Tracker", cv2.WND_PROP_TOPMOST, 1)
        
        print("\n[ACTIVE] Graphics Window Dispatched! Multi-Gesture Engine Armed.\n", flush=True)

        while cap.isOpened() and self.is_running:
            ret, frame = cap.read()
            if not ret: break

            frame = cv2.flip(frame, 1)
            h, w, c = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 1. Body Pose Tracking for Dynamic Boundaries
            pose_results = self.pose.process(rgb_frame)
            
            box_x_start, box_x_end = int(w * 0.35), int(w * 0.65)
            box_y_start, box_y_end = int(h * 0.45), int(h * 0.85)
            head_y_threshold = int(h * 0.30)
            shoulder_y_line = int(h * 0.40)
            chest_tracked = False
            
            if pose_results.pose_landmarks:
                self.mp_draw.draw_landmarks(frame, pose_results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
                landmarks = pose_results.pose_landmarks.landmark
                
                l_sh = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
                r_sh = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
                nose = landmarks[self.mp_pose.PoseLandmark.NOSE]
                
                l_x, l_y = int(l_sh.x * w), int(l_sh.y * h)
                r_x, r_y = int(r_sh.x * w), int(r_sh.y * h)
                nose_y = int(nose.y * h)
                
                mid_x = (l_x + r_x) // 2
                mid_y = (l_y + r_y) // 2
                sh_dist = abs(l_x - r_x)
                
                if sh_dist > 20:
                    box_x_start = mid_x - int(sh_dist * 0.45)
                    box_x_end = mid_x + int(sh_dist * 0.45)
                    box_y_start = mid_y + int(sh_dist * 0.15)
                    box_y_end = mid_y + int(sh_dist * 0.75)
                    
                    head_y_threshold = nose_y + int(sh_dist * 0.25)
                    shoulder_y_line = mid_y
                    chest_tracked = True

            # 2. Hand Matrix Analysis
            hand_results = self.hands.process(rgb_frame)
            
            hand_on_chest = False
            hand_on_head = False
            hand_raised_high = False

            if hand_results.multi_hand_landmarks:
                for hand_lms in hand_results.multi_hand_landmarks:
                    self.mp_draw.draw_landmarks(frame, hand_lms, self.mp_hands.HAND_CONNECTIONS)
                    
                    hx = int(hand_lms.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_MCP].x * w)
                    hy = int(hand_lms.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_MCP].y * h)
                    
                    if (box_x_start <= hx <= box_x_end) and (box_y_start <= hy <= box_y_end):
                        hand_on_chest = True
                    elif hy < head_y_threshold and (box_x_start - 30 <= hx <= box_x_end + 30):
                        hand_on_head = True
                    elif hy < shoulder_y_line - 40:
                        hand_raised_high = True

            # --- 3. MULTI-GESTURE TIMING LOGIC ---
            current_time = time.time()
            
            if hand_on_chest:
                if self.active_vision_alert == "NONE":
                    if self.heart_gesture_start_time is None: self.heart_gesture_start_time = current_time
                    elapsed = current_time - self.heart_gesture_start_time
                    if elapsed >= 5.0:
                        self.active_vision_alert = "HEART_ATTACK"
                        self.trigger_voice_announcement("Emergency! Patient chest gesture alert triggered.")
                    else:
                        cv2.rectangle(frame, (box_x_start, box_y_start), (box_x_end, box_y_end), (0, 165, 255), 3)
                        cv2.putText(frame, f"CHEST HOLD: {elapsed:.1f}s", (box_x_start, box_y_start - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)
            else: self.heart_gesture_start_time = None

            if hand_on_head and not hand_on_chest:
                if self.active_vision_alert == "NONE":
                    if self.head_gesture_start_time is None: self.head_gesture_start_time = current_time
                    elapsed = current_time - self.head_gesture_start_time
                    if elapsed >= 4.0:
                        self.active_vision_alert = "STROKE_HEAD_TRAUMA"
                        self.trigger_voice_announcement("Warning! Patient severe head distress gesture detected.")
                    else:
                        cv2.circle(frame, (w//2, head_y_threshold), 40, (255, 100, 0), 2)
                        cv2.putText(frame, f"HEAD DISTRESS: {elapsed:.1f}s", (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 100, 0), 2)
            else: self.head_gesture_start_time = None

            if hand_raised_high and self.active_vision_alert == "NONE":
                self.active_vision_alert = "NURSE_DISTRESS_CALL"
                self.trigger_voice_announcement("Alert! Patient calling for emergency assistance.")

            if not hand_on_chest and not hand_on_head and not hand_raised_high and not hand_results.multi_hand_landmarks:
                self.active_vision_alert = "NONE"

            # --- 4. UI RENDERING STATES ---
            if self.active_vision_alert == "HEART_ATTACK":
                cv2.rectangle(frame, (box_x_start, box_y_start), (box_x_end, box_y_end), (0, 0, 255), 4)
                cv2.putText(frame, "CRITICAL DETECTED: CHEST PAIN GESTURE", (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            elif self.active_vision_alert == "STROKE_HEAD_TRAUMA":
                cv2.putText(frame, "CRITICAL DETECTED: POTENTIAL STROKE SIGN", (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 128, 255), 2)
            elif self.active_vision_alert == "NURSE_DISTRESS_CALL":
                cv2.putText(frame, "ALERT ACTIVE: EMERGENCY DISTRESS CALL", (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
            else:
                color = (0, 255, 0) if chest_tracked else (0, 255, 255)
                label = "DYNAMIC CHEST TARGET" if chest_tracked else "STATIC FALLBACK TARGET"
                cv2.rectangle(frame, (box_x_start, box_y_start), (box_x_end, box_y_end), color, 2)
                cv2.putText(frame, label, (box_x_start, box_y_start - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            cv2.imshow("OmniMed Ultra Dual Tracker", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.is_running = False
                break

        cap.release()
        cv2.destroyAllWindows()

    def boot(self):
        threading.Thread(target=self.start_microphone_stream, daemon=True).start()
        threading.Thread(target=self.continuous_brain_scanner, daemon=True).start()
        self.start_camera_stream()

if __name__ == "__main__":
    system = OmniMedUltraSystem()
    system.boot()
