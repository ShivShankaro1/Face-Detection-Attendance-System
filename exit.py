import face_recognition
import os
import cv2
import numpy as np
import pyodbc
from datetime import datetime

class FaceExit:
    def __init__(self):
        self.face_locations = []
        self.face_encodings = []
        self.face_names = []
        self.known_face_encodings = []
        self.known_face_rollnos = []
        self.frame_count = 0

        # Database connection
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

        exit_logged = False

        while True:
            ret, frame = video_capture.read()
            self.frame_count += 1

            frame = cv2.flip(frame, 1)

            if self.frame_count % 3 == 0:
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = small_frame[:, :, ::-1]
                exit_logged = self.process_frame(rgb_small_frame)

            for (top, right, bottom, left), name in zip(self.face_locations, self.face_names):
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.putText(frame, name, (left + 6, bottom - 6),
                            cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 1)

            cv2.imshow('Face Exit Detection', frame)

            if exit_logged:
                print("Exit detected. Closing...")
                break  # Auto-close after successful exit

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        video_capture.release()
        cv2.destroyAllWindows()
        self.connection.close()

    def process_frame(self, rgb_small_frame):
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        current_time = datetime.now()
        tolerance = 0.5
        exit_logged = False

        for face_encoding in face_encodings:
            distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            best_match_index = np.argmin(distances)

            if len(distances) > 0 and distances[best_match_index] < tolerance:
                roll_no = self.known_face_rollnos[best_match_index]

                if self.update_exit_time(roll_no, current_time):
                    face_names.append(roll_no)
                    print(f"Exit logged for {roll_no}")
                    exit_logged = True
                else:
                    face_names.append("NoEntry")
                    print(f"No valid entry to exit for {roll_no}")
            else:
                face_names.append("Unknown")

        self.face_locations = face_locations
        self.face_names = face_names
        return exit_logged

    def update_exit_time(self, roll_no, timestamp):
        """Update the latest row with NULL ExitDetectionTime for this RollNo."""
        self.cursor.execute(
            """
            SELECT TOP 1 LogID FROM AttendanceTable
            WHERE RollNo = ? AND ExitDetectionTime IS NULL
            ORDER BY EntryDetectionTime DESC
            """, (roll_no,)
        )
        row = self.cursor.fetchone()
        if row:
            log_id = row[0]
            self.cursor.execute(
                """
                UPDATE AttendanceTable
                SET ExitDetectionTime = ?
                WHERE LogID = ?
                """, (timestamp, log_id)
            )
            self.connection.commit()
            return True
        return False

if __name__ == "__main__":
    fr = FaceExit()
    fr.encode_faces()
    fr.run_recognition()
