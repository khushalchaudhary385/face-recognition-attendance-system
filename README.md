# Face Recognition Attendance System

A Python-based face recognition system for automated student attendance marking using facial recognition technology.

## Features

- **Face Recognition**: Uses OpenCV and LBPH Face Recognizer for accurate face matching
- **WiFi Verification**: Ensures attendance is marked only on authorized networks
- **Teacher Control**: Password-protected teacher interface to control attendance windows
- **Multi-platform**: Works on Windows, Linux, and macOS
- **Attendance Logging**: Stores attendance records in CSV format with timestamps
- **Snapshot Capture**: Saves snapshots of recognized faces for verification
- **System Backup**: Maintains backup attendance records

## Requirements

- Python 3.7+
- OpenCV (`opencv-contrib-python` for face recognition module)
- NumPy
- Pandas
- tkinter (usually comes with Python)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/khushalchaudhary385/face-recognition-attendance-system.git
cd face-recognition-attendance-system
```

2. Install dependencies:
```bash
pip install opencv-contrib-python numpy pandas
```

3. Ensure `haarcascade_frontalface_default.xml` is in the project directory

## Usage

### Step 1: Register Student Photos
1. Add student photos to the `pictures/` folder
2. Name files as: `ID_StudentName.jpg` (e.g., `101_Anuj.jpg`)
3. Click "Train from pictures" button to train the model

### Step 2: Start Attendance Window (Teacher)
1. Enter teacher password (`teacher123` by default)
2. Click "Start Attendance Window" button
3. Attendance window remains open for 120 seconds

### Step 3: Mark Attendance (Student)
1. Click "Mark Attendance (student)" button
2. Face camera and wait for recognition
3. Attendance is recorded when face is recognized

## Configuration

Edit the config section in the main script:
```python
TEACHER_PASSWORD = "teacher123"        # Change teacher password
ALLOWED_WIFI = "Chaudhary"             # Set allowed WiFi network
ATTENDANCE_WINDOW_SECONDS = 120         # Attendance window duration in seconds
```

## File Structure

```
├── temp3.py                              # Main application file
├── pictures/                             # Folder for student photos
├── attendance/                           # Folder for attendance records
│   └── snapshots/                       # Snapshots of recognized faces
├── system_attendance_backup/             # Backup attendance records
├── haarcascade_frontalface_default.xml   # Haar cascade classifier
├── trained_from_pictures.yml             # Trained LBPH model
└── pictures_labels.txt                   # Label mappings
```

## Output Files

- **CSV Attendance Records**: `attendance/attendance_YYYYMMDD.csv`
  - Contains: ID, Name, Timestamp
- **Backup Records**: `system_attendance_backup/backup_YYYYMMDD.csv`
- **Face Snapshots**: `attendance/snapshots/ID_Name_TIMESTAMP.jpg`

## Important Notes

1. Student photos must be clear and well-lit for better recognition
2. Photos should be named with student ID and name separated by underscore
3. WiFi network name verification adds security layer
4. Recognition confidence threshold is set to 80 (lower value = better match)
5. Attendance window prevents marking outside designated time periods

## Troubleshooting

### Camera not detected
- Ensure camera permissions are granted
- Check if camera is already in use by another application

### Face not recognized
- Ensure student photos are in the `pictures/` folder
- Run "Train from pictures" after adding photos
- Check lighting conditions during attendance marking
- Adjust confidence threshold if needed

### WiFi check failing
- Ensure connected to allowed WiFi network
- Or click "Continue anyway" to bypass WiFi check

## License

MIT License

## Author

Khushal Chaudhary
