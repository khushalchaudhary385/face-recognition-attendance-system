# attendance_system_pictures.py
import cv2
import numpy as np
import os
import subprocess
import platform
from tkinter import *
from tkinter import messagebox
import pandas as pd
from datetime import datetime, timedelta

# ---------------- CONFIG ----------------
TEACHER_PASSWORD = "teacher123"
ALLOWED_WIFI = "Chaudhary"
ATTENDANCE_WINDOW_SECONDS = 120  # 2 minutes

# Folders
PICTURES_FOLDER = "pictures"           # <-- your chosen folder
ATTENDANCE_FOLDER = "attendance"
SNAPSHOT_FOLDER = os.path.join(ATTENDANCE_FOLDER, "snapshots")
TRAINED_MODEL = "trained_from_pictures.yml"
LABELS_FILE = "pictures_labels.txt"
FACE_CASCADE_PATH = "haarcascade_frontalface_default.xml"

# Create folders
os.makedirs(PICTURES_FOLDER, exist_ok=True)
os.makedirs(ATTENDANCE_FOLDER, exist_ok=True)
os.makedirs(SNAPSHOT_FOLDER, exist_ok=True)

# ----------------- Setup detector & recognizer -----------------
if not os.path.exists(FACE_CASCADE_PATH):
    raise FileNotFoundError(f"Missing Haar cascade: '{FACE_CASCADE_PATH}'. Place it in the script folder.")

face_cascade = cv2.CascadeClassifier(FACE_CASCADE_PATH)

try:
    recognizer = cv2.face.LBPHFaceRecognizer_create()
except Exception as e:
    raise RuntimeError("cv2.face not available. Install 'opencv-contrib-python'.") from e

# ----------------- Global state -----------------
attendance_window_active = False
window_end_time = None

# ----------------- Wi-Fi detection (improved multi-OS) -----------------
def get_connected_wifi():
    system = platform.system().lower()
    try:
        if system == "windows":
            # netsh method
            res = subprocess.check_output(["netsh", "wlan", "show", "interfaces"], stderr=subprocess.DEVNULL).decode(errors="ignore")
            for line in res.splitlines():
                if "SSID" in line and "BSSID" not in line:
                    return line.split(":", 1)[1].strip()
        elif system == "linux":
            # try iwgetid
            try:
                ssid = subprocess.check_output(["iwgetid", "-r"], stderr=subprocess.DEVNULL).decode().strip()
                if ssid:
                    return ssid
            except Exception:
                pass
            # try nmcli
            try:
                res = subprocess.check_output(["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"], stderr=subprocess.DEVNULL).decode(errors="ignore")
                for ln in res.splitlines():
                    if ln.startswith("yes:"):
                        return ln.split("yes:")[1].strip()
            except Exception:
                pass
        elif system == "darwin":
            try:
                res = subprocess.check_output(["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"], stderr=subprocess.DEVNULL).decode(errors="ignore")
                for line in res.splitlines():
                    if "SSID:" in line:
                        return line.split("SSID:")[1].strip()
            except Exception:
                pass
    except Exception:
        pass
    return None

# ----------------- GUI helper to keep WiFi label updated -----------------
def update_wifi_label():
    wifi = get_connected_wifi()
    if wifi:
        lbl_wifi.config(text=f"Connected WiFi: {wifi}")
        lbl_wifi.config(fg="green" if wifi == ALLOWED_WIFI else "red")
    else:
        lbl_wifi.config(text="Connected WiFi: Not detected", fg="red")
    root.after(2000, update_wifi_label)

# ----------------- Train model from pictures/ folder -----------------
def train_from_pictures():
    faces = []
    ids = []
    label_map = {}
    current_label = 0

    files = [f for f in os.listdir(PICTURES_FOLDER) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not files:
        messagebox.showerror("No files", f"No images found in '{PICTURES_FOLDER}'. Add files like '101_Anuj.jpg'.")
        return

    for file in files:
        path = os.path.join(PICTURES_FOLDER, file)
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue

        name_part = os.path.splitext(file)[0]
        if "_" not in name_part:
            messagebox.showwarning("Filename format", f"Skipping '{file}' — expected 'ID_Name.ext' format.")
            continue

        student_id, student_name = name_part.split("_", 1)
        # Optional: detect and crop face region from the stored picture for better training
        faces_detected = face_cascade.detectMultiScale(img, 1.3, 5)
        if len(faces_detected) > 0:
            (x, y, w, h) = faces_detected[0]  # take first face
            face_roi = img[y:y+h, x:x+w]
        else:
            # fallback to whole image (less ideal)
            face_roi = cv2.resize(img, (200, 200))

        faces.append(face_roi)
        ids.append(current_label)
        label_map[current_label] = f"{student_id}_{student_name}"
        current_label += 1

    if len(faces) == 0:
        messagebox.showerror("Training error", "No valid faces found in pictures.")
        return

    recognizer.train(faces, np.array(ids))
    recognizer.save(TRAINED_MODEL)

    with open(LABELS_FILE, "w") as f:
        for k, v in label_map.items():
            f.write(f"{k}:{v}\n")

    messagebox.showinfo("Trained", f"Trained on {len(faces)} registered photos.")

# ----------------- Start attendance window (teacher) -----------------
def start_attendance_window():
    global attendance_window_active, window_end_time

    pwd = txt_teacher_pass.get().strip()
    if pwd != TEACHER_PASSWORD:
        messagebox.showerror("Access denied", "Incorrect teacher password.")
        return

    # Optional: require being on allowed WiFi before starting
    wifi = get_connected_wifi()
    if wifi is None:
        if not messagebox.askyesno("WiFi unknown", "Could not detect WiFi. Continue anyway?"):
            return
    elif wifi != ALLOWED_WIFI:
        if not messagebox.askyesno("Wrong WiFi", f"Connected to '{wifi}' (required: '{ALLOWED_WIFI}'). Continue anyway?"):
            return

    attendance_window_active = True
    window_end_time = datetime.now() + timedelta(seconds=ATTENDANCE_WINDOW_SECONDS)
    lbl_status.config(text=f"Attendance window active until {window_end_time.strftime('%H:%M:%S')}", fg="blue")
    messagebox.showinfo("Attendance started", f"Attendance window active for {ATTENDANCE_WINDOW_SECONDS} seconds.")

# ----------------- Mark attendance (match live face to stored model) -----------------
def mark_attendance():
    global attendance_window_active, window_end_time

    # check window
    if not attendance_window_active:
        messagebox.showerror("Not allowed", "Teacher has NOT started the attendance window.")
        return
    if window_end_time and datetime.now() > window_end_time:
        attendance_window_active = False
        lbl_status.config(text="Attendance window expired", fg="red")
        messagebox.showerror("Expired", "Attendance window has closed.")
        return

    # check WiFi now
    wifi = get_connected_wifi()
    if wifi != ALLOWED_WIFI:
        messagebox.showerror("Wrong WiFi", f"Device connected to '{wifi or 'Unknown'}'. Required: '{ALLOWED_WIFI}'.")
        return

    # load trained model + labels
    try:
        recognizer.read(TRAINED_MODEL)
        label_map = {}
        with open(LABELS_FILE, "r") as f:
            for line in f:
                k, v = line.strip().split(":", 1)
                label_map[int(k)] = v
    except Exception:
        messagebox.showerror("Model missing", "Please train the system from the 'pictures' folder first.")
        return

    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        messagebox.showerror("Camera error", "Cannot open the camera.")
        return

    recognized = False
    start_time = datetime.now()

    while True:
        # safety: break if window expired while scanning
        if window_end_time and datetime.now() > window_end_time:
            break

        ret, frame = cam.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            face_roi = gray[y:y+h, x:x+w]
            try:
                label, conf = recognizer.predict(face_roi)
            except Exception:
                # if prediction fails (e.g. mismatched sizes), try resizing
                try:
                    face_small = cv2.resize(face_roi, (200, 200))
                    label, conf = recognizer.predict(face_small)
                except Exception:
                    label, conf = -1, 999

            # lower confidence -> better match. threshold may need tuning
            if conf < 80 and label in label_map:
                info = label_map[label]           # e.g. "101_Anuj"
                student_id, student_name = info.split("_", 1)

                # Save attendance record and snapshot
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                filename_csv = os.path.join(ATTENDANCE_FOLDER, f"attendance_{datetime.now().strftime('%Y%m%d')}.csv")

                # Append to CSV (create if not exists)
                row = {"ID": student_id, "Name": student_name, "Time": timestamp}
                if os.path.exists(filename_csv):
                    df = pd.read_csv(filename_csv)
                    # avoid duplicate consecutive entries for same student in same file
                    if not ((df['ID'] == student_id) & (df['Time'] == timestamp)).any():
                       # df = df.append(row, ignore_index=True)
                       df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
                else:
                    df = pd.DataFrame([row])
                df.to_csv(filename_csv, index=False)

                # Save snapshot of matched face
                snap_name = f"{student_id}_{student_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                snap_path = os.path.join(SNAPSHOT_FOLDER, snap_name)
                # Save just the face region (color)
                face_color = frame[y:y+h, x:x+w]
                try:
                    cv2.imwrite(snap_path, face_color)
                except Exception:
                    pass

                # GUI + popup feedback
                lbl_status.config(text=f"Attendance Marked: {student_name} (ID: {student_id})", fg="green")
                messagebox.showinfo("Attendance Marked", f"{student_name} (ID: {student_id})\nTime: {timestamp}")

                recognized = True
                break
            else:
                cv2.putText(frame, "Unknown", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)

        cv2.imshow("Mark Attendance (press ESC to cancel)", frame)

        # quick exit if recognized or user pressed ESC
        if recognized:
            cv2.waitKey(500)  # brief pause to show recognition
            break
        if cv2.waitKey(1) & 0xFF == 27:
            break

        # safety time-out: don't loop forever (optional)
        if (datetime.now() - start_time).total_seconds() > 25:
            # no recognition in reasonable time
            break

    cam.release()
    cv2.destroyAllWindows()

    if not recognized:
        lbl_status.config(text="No matching face found.", fg="red")
        messagebox.showinfo("No Match", "No registered face matched. Please try again or ask teacher to register the student photo.")

# ----------------- Build GUI -----------------
root = Tk()
root.title("Face Recognition Attendance (pictures)")
root.geometry("520x520")
root.configure(bg="#f6f6f6")

frm = Frame(root, bg="#f6f6f6")
frm.pack(padx=12, pady=12, fill=BOTH, expand=True)

Label(frm, text="Teacher Password:", bg="#f6f6f6").grid(row=0, column=0, sticky=W, pady=(0,6))
txt_teacher_pass = Entry(frm, width=28, show="*")
txt_teacher_pass.grid(row=0, column=1, pady=(0,6))

btn_start = Button(frm, text="Start Attendance Window", width=24, bg="#4a6cf7", fg="white", command=start_attendance_window)
btn_start.grid(row=0, column=2, padx=(8,0), pady=(0,6))

Label(frm, text="Pictures folder (for registered photos):", bg="#f6f6f6").grid(row=1, column=0, columnspan=2, sticky=W)
Label(frm, text=PICTURES_FOLDER, bg="#f6f6f6", fg="black").grid(row=1, column=2, sticky=W)

btn_train = Button(frm, text="Train from pictures", width=24, bg="#28a745", fg="white", command=train_from_pictures)
btn_train.grid(row=2, column=0, pady=(10,6))

btn_mark = Button(frm, text="Mark Attendance (student)", width=24, bg="#f0ad4e", fg="black", command=mark_attendance)
btn_mark.grid(row=2, column=1, pady=(10,6))

btn_exit = Button(frm, text="Exit", width=24, bg="#d9534f", fg="white", command=root.destroy)
btn_exit.grid(row=2, column=2, pady=(10,6))

lbl_wifi = Label(frm, text="Connected WiFi: Checking...", bg="#f6f6f6", fg="blue", font=("Arial", 11))
lbl_wifi.grid(row=3, column=0, columnspan=3, pady=(12,6))

lbl_status = Label(frm, text="Status: Idle", bg="#f6f6f6", fg="black", font=("Arial", 12))
lbl_status.grid(row=4, column=0, columnspan=3, pady=(8,6))

# nice note
note = (
    f"Notes:\n"
    f"- Put official student photos in '{PICTURES_FOLDER}' as ID_Name.jpg\n"
    f"- Press 'Train from pictures' once after adding/updating photos\n"
    f"- Teacher must start the attendance window first (password required)\n"
    f"- Students approach camera and press 'Mark Attendance' or teacher can allow students to press\n"
)
Label(frm, text=note, bg="#f6f6f6", justify=LEFT).grid(row=5, column=0, columnspan=3, pady=(6,0))

update_wifi_label()
root.mainloop()