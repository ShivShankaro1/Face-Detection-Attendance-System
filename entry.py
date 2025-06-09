import face_recognition
import os
import cv2
import numpy as np
import pyodbc
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import subprocess

class FaceEntry:
    def __init__(self):
        self.face_locations = []
        self.face_encodings = []
        self.face_names = []
        self.known_face_encodings = []
        self.known_face_rollnos = []
        self.frame_count = 0
        self.detected = False

        # DB connection
        self.connection = pyodbc.connect(
            'Driver={ODBC Driver 17 for SQL Server};'
            'Server=localhost\\SQLEXPRESS02;'
            'Database=master;'
            'Trusted_Connection=yes;'
        )
        self.cursor = self.connection.cursor()

    def encode_faces(self):
        for image in os.listdir('faces'):
            face_image = face_recognition.load_image_file(f'faces/{image}')
            encoding = face_recognition.face_encodings(face_image)
            if encoding:
                self.known_face_encodings.append(encoding[0])
                roll_no = os.path.splitext(image)[0]
                self.known_face_rollnos.append(roll_no)

    def run_recognition(self):
        video_capture = cv2.VideoCapture(0)
        if not video_capture.isOpened():
            print('Camera not found.')
            return

        while True:
            ret, frame = video_capture.read()
            self.frame_count += 1
            frame = cv2.flip(frame, 1)

            if self.frame_count % 3 == 0:
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = small_frame[:, :, ::-1]
                self.process_frame(rgb_small_frame)

            for (top, right, bottom, left), name in zip(self.face_locations, self.face_names):
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, name, (left + 6, bottom - 6),
                            cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 1)

            cv2.imshow('Face Entry Detection', frame)

            if self.detected:
                break

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        video_capture.release()
        cv2.destroyAllWindows()
        self.connection.close()

        if self.detected:
            # Pass the name to prompt_next_action
            self.prompt_next_action(self.face_names[0])

    def process_frame(self, rgb_small_frame):
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        names = []
        current_time = datetime.now()
        tolerance = 0.5

        for face_encoding in face_encodings:
            distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            best_match_index = np.argmin(distances)

            if len(distances) > 0 and distances[best_match_index] < tolerance:
                roll_no = self.known_face_rollnos[best_match_index]
                if not self.has_existing_entry(roll_no):
                    self.save_entry(roll_no, current_time)
                    names.append(roll_no)
                    self.detected = True
                else:
                    names.append("Duplicate")
            else:
                names.append("Unknown")

        self.face_locations = face_locations
        self.face_names = names

    def has_existing_entry(self, roll_no):
        self.cursor.execute(
            """
            SELECT TOP 1 EntryDetectionTime, ExitDetectionTime 
            FROM AttendanceTable
            WHERE RollNo = ? 
            ORDER BY LogID DESC
            """, (roll_no,)
        )
        row = self.cursor.fetchone()
        return row is not None and row.EntryDetectionTime is not None and row.ExitDetectionTime is None

    def save_entry(self, roll_no, timestamp):
        self.cursor.execute(
            """
            INSERT INTO AttendanceTable (RollNo, EntryDetectionTime)
            VALUES (?, ?)
            """,
            (roll_no, timestamp)
        )
        self.connection.commit()

    def prompt_next_action(self, detected_name):
        root = tk.Tk()
        root.withdraw()
        # Include the detected name in the prompt message
        choice = messagebox.askquestion("Next Action", f"Detected: {detected_name}. Retake Entry?", icon='question', default='yes')
        if choice == 'yes':
            # Retake entry
            fr = FaceEntry()
            fr.encode_faces()
            fr.run_recognition()
        else:
            exit_choice = messagebox.askyesno("Exit Confirmation", "Would you like to punch-out now?")
            if exit_choice:
                subprocess.Popen(["python", "exit.py"])
            else:
                pass  # Skip, just close


if __name__ == "__main__":
    fr = FaceEntry()
    fr.encode_faces()
    fr.run_recognition()
