import time
import threading
import speech_recognition as sr
import cv2
import mediapipe as mp
import pyttsx3

class OmniMedUltraSystem:
    def __init__(self):
        # --- 1. Audio Keyword & TTS Mapping ---
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.rolling_memory = []
        
        # Extended Emergency Dictionary with Custom Voice Warnings (Added "help")
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

        # --- 2. Vision Core Setup (Hands + Pose Trackers) ---
        self.mp_hands = mp.solutions.hands
        self.mp_pose = mp.solutions.pose
        self.mp_draw = mp.solutions.drawing_utils
        
        self.hands = self.mp_hands.Hands(
            static_image_mode=False, max_num_hands=1,
            min_detection_confidence=0.7, min_tracking_confidence=0.7
        )
        self.pose = self.mp_pose.Pose(
            static_image_mode=False, model_complexity=0,
            min_detection_confidence=0.6, min_tracking_confidence=0.6
        )
        
        # --- 3. System Control & Gestures Timers ---
        self.heart_gesture_start_time = None
        self.head_gesture_start_time = None
        self.active_vision_alert = "NONE"
        self.is_running = True

    # ==================== VOICE ANNOUNCEMENT ENGINE (TTS) ====================
    def trigger_voice_announcement(self, text_to_speak):
        """Background thread worker that speaks alerts natively without freezing the camera frame."""
        def speech_worker():
            try:
                engine = pyttsx3.init()
                engine.setProperty('rate', 160)  # Safe professional speaking speed
                engine.say(text_to_speak)
                engine.runAndWait()
            except Exception as e:
                print(f"[TTS ERROR] Voice engine drop: {e}")

        # Spawn separate thread so camera feed loop doesn't stutter/lag
        threading.Thread(target=speech_worker, daemon=True).start()

    # ==================== AUDIO CORE LOGIC ====================
    def clean_expired_memory(self):
        current_time = time.time()
        self.rolling_memory = [chunk for chunk in self.rolling_memory if (current_time - chunk[1]) <= 20.0]

    def scan_for_keywords(self):
        combined_text = " ".join([chunk[0] for chunk in self.rolling_memory])
        if not combined_text.strip():
            return
            
        print(f"\n⏳ [20s ROLLING BUFFER] : \"{combined_text}\"")
        
        for keyword, warning_speech in self.EMERGENCY_DATABASE.items():
            if keyword in combined_text:
                print(f"🎯 [AUDIO KEYWORD MATCH] Fired Trigger For: {keyword.upper()}")
                
                if self.last_spoken_alert != keyword:
                    self.last_spoken_alert = keyword
                    self.trigger_voice_announcement(warning_speech)
                return 

    def start_microphone_stream(self):
        print("[INIT] Calibrating room mic environment... 2 seconds.")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        print("[ACTIVE] Microphone Matrix Live! Speak your commands.\n")

        while self.is_running:
            try:
                with self.microphone as source:
                    audio_data = self.recognizer.listen(source, phrase_time_limit=4)
                raw_text = self.recognizer.recognize_google(audio_data).lower()
                if raw_text.strip():
                    self.rolling_memory.append((raw_text, time.time()))
                    print(f"🎙️ [MIC HEARD] '{raw_text}'")
            except sr.UnknownValueError: continue
            except sr.RequestError: time.sleep(2)

    def continuous_brain_scanner(self):
        while self.is_running:
            time.sleep(2)
            self.clean_expired_memory()
            self.scan_for_keywords()

    # ==================== VISION CORE LOGIC ====================
    def start_camera_stream(self):
        cap = cv2.VideoCapture(1)  # Index 1 for Iriun. Change to 0 if screen is black.
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cv2.namedWindow("OmniMed Ultra Dual Tracker", cv2.WINDOW_AUTOSIZE)

        print("[ACTIVE] Camera Matrix Open! 3 Multi-Gestures Armed.\n")

        while cap.isOpened() and self.is_running:
            ret, frame = cap.read()
            if not ret: break

            frame = cv2.flip(frame, 1)
            h, w, c = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 1. Body Pose Tracking for Dynamic Boundaries
            pose_results = self.pose.process(rgb_frame)
            
            # Default static fallbacks for chest bounding box
            box_x_start, box_x_end = int(w * 0.35), int(w * 0.65)
            box_y_start, box_y_end = int(h * 0.45), int(h * 0.85)
            
            head_y_threshold = int(h * 0.30)  # Default head level line
            shoulder_y_line = int(h * 0.40)   # Default shoulder line
            
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
                    # Dynamic Chest Box calculations
                    box_x_start = mid_x - int(sh_dist * 0.45)
                    box_x_end = mid_x + int(sh_dist * 0.45)
                    box_y_start = mid_y + int(sh_dist * 0.15)
                    box_y_end = mid_y + int(sh_dist * 0.75)
                    
                    # Boundaries for new gestures
                    head_y_threshold = nose_y + int(sh_dist * 0.25)
                    shoulder_y_line = mid_y

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
                    
                    # GESTURE CHECK 1: Hand On Dynamic Chest Zone
                    if (box_x_start <= hx <= box_x_end) and (box_y_start <= hy <= box_y_end):
                        hand_on_chest = True
                        
                    # GESTURE CHECK 2: Hand on Head (Stroke/Trauma Sign)
                    elif hy < head_y_threshold and (box_x_start - 30 <= hx <= box_x_end + 30):
                        hand_on_head = True
                        
                    # GESTURE CHECK 3: Hand Raised High Past Shoulders (Distress Nurse Call)
                    elif hy < shoulder_y_line - 40:
                        hand_raised_high = True

            # --- 3. MULTI-GESTURE TIMING LOGIC ---
            current_time = time.time()
            
            # Gesture 1: Chest Pain (Needs 5 Seconds Hold)
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

            # Gesture 2: Severe Head Pain (Needs 4 Seconds Hold)
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

            # Gesture 3: Hand Raised (Instant Activation)
            if hand_raised_high and self.active_vision_alert == "NONE":
                self.active_vision_alert = "NURSE_DISTRESS_CALL"
                self.trigger_voice_announcement("Alert! Patient calling for emergency assistance.")

            if not hand_on_chest and not hand_on_head and not hand_raised_high and not hand_results.multi_hand_landmarks:
                self.active_vision_alert = "NONE"

            # --- 4. GRAPHICAL UI RENDERING STATUS ---
            if self.active_vision_alert == "HEART_ATTACK":
                cv2.rectangle(frame, (box_x_start, box_y_start), (box_x_end, box_y_end), (0, 0, 255), 4)
                cv2.putText(frame, "CRITICAL DETECTED: CHEST PAIN GESTURE", (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            elif self.active_vision_alert == "STROKE_HEAD_TRAUMA":
                cv2.putText(frame, "CRITICAL DETECTED: POTENTIAL STROKE SIGN", (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 128, 255), 2)
            elif self.active_vision_alert == "NURSE_DISTRESS_CALL":
                cv2.putText(frame, "ALERT ACTIVE: EMERGENCY DISTRESS CALL", (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
            else:
                cv2.rectangle(frame, (box_x_start, box_y_start), (box_x_end, box_y_end), (0, 255, 0), 2)
                cv2.putText(frame, "STATUS: ROOM MONITORING STABLE", (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

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
