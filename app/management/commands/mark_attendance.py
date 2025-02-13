from io import BytesIO
import pandas as pd
import cv2
import numpy as np
import os
import csv
import pickle
import time
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from sklearn.neighbors import KNeighborsClassifier
from win32com.client import Dispatch
from django.core.files.base import ContentFile
from xlsxwriter import Workbook

from app.models import AttendanceFile, ClassSchedule, Students
from utils.email_utils import send_email_via_sendinblue

class Command(BaseCommand):
    help = 'Mark attendance by detecting faces using webcam'

    def speak(self, str1):
        speak = Dispatch(("SAPI.SpVoice"))
        speak.Speak(str1)

    def add_arguments(self, parser):
        parser.add_argument('schedule_id', type=int, help='ID of the class schedule')

    def save_attendance_file_to_db(self, excel_file, schedule):
    # Save the Excel file to the database
        attendance_instance = AttendanceFile(schedule=schedule)
        attendance_instance.file.save(f"{schedule.class_name}_{schedule.id}_attendance.xlsx", ContentFile(excel_file.read()))
        attendance_instance.save()
        print(f"Attendance file saved to the database for {schedule.class_name}.")

    def send_attendance_email(self, student_email, class_schedule):
        subject = f"Attendance Marked for {class_schedule.class_name} - {class_schedule.date}"
        content = f"Dear {student_email},<br>Your attendance has been marked for the class '{class_schedule.class_name}' on {class_schedule.date}.<br>Thank you!"
        send_email_via_sendinblue(subject, content, [student_email])

    def send_marksheet_to_lecturer(self, class_schedule, excel_file):
        subject = f"Marks for {class_schedule.class_name} - {class_schedule.date}"
        content = f"Dear {class_schedule.lecturer.l_email},<br>Please find the marksheet for the class '{class_schedule.class_name}' on {class_schedule.date}.<br>Best regards."
        send_email_via_sendinblue(subject, content, [class_schedule.lecturer.l_email], attachment=ContentFile(excel_file.read(), "attendance.xlsx"))

    def handle(self, *args, **options):
        schedule_id = options['schedule_id']
        schedule = ClassSchedule.objects.get(id=schedule_id)
        self.stdout.write(f"Marking attendance for {schedule.class_name}...")

        video = cv2.VideoCapture(0)
        facedetect = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

        with open('data/names.pkl', 'rb') as w:
            LABELS = pickle.load(w)

        with open('data/face_data.pkl', 'rb') as f:
            FACES = pickle.load(f)

        knn = KNeighborsClassifier(n_neighbors=5)
        knn.fit(FACES, LABELS)

        if not os.path.exists('Attendance'):
            os.makedirs('Attendance')

        email_sent = False
        date = datetime.now().strftime("%d-%m-%Y")

        while True:
            ret, frame = video.read()
            if not ret:
                print("Error: Failed to capture frame")
                break  

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = facedetect.detectMultiScale(gray, 1.3, 5)

            k = cv2.waitKey(1) & 0xFF

            for (x, y, w, h) in faces:
                crop_img = frame[y:y+h, x:x+w, :]
                resized_img = cv2.resize(crop_img, (50, 50)).flatten().reshape(1, -1)
                output = knn.predict(resized_img)
                timestamp = datetime.now().strftime("%H:%M:%S")
                attendance_file = f"Attendance/{schedule.class_name}_{schedule.id}_Attendance_{date}.csv"
                student_name = str(output[0])

                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 1)
                cv2.rectangle(frame, (x, y - 40), (x + w, y), (50, 50, 255), -1)
                cv2.putText(frame, student_name, (x, y - 15), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
                
                attendance_file = f"Attendance/{schedule.class_name}_{schedule.id}_Attendance_{date}.csv"
                # ✅ Check if student has already been marked
                if os.path.exists(attendance_file):
                    with open(attendance_file, "r") as csvfile:
                        reader = csv.reader(csvfile)
                        recorded_names = [row[0] for row in reader if row]

                    if student_name in recorded_names:
                        print(f"Attendance for {student_name} already marked. Skipping duplicate entry.")
                        continue  # Skip adding duplicate attendance

                # ✅ If not found, write new attendance entry
                with open(attendance_file, "+a") as csvfile:
                    writer = csv.writer(csvfile)
                    if os.stat(attendance_file).st_size == 0:
                        writer.writerow(['NAME', 'TIME'])  # Add header if file is new
                    writer.writerow([student_name, timestamp])

                    student = Students.objects.filter(s_first_name=student_name).first()
                    if student:
                        self.send_attendance_email(student.s_email, schedule)

            cv2.imshow("Frame", frame)

            # 📌 Check if class is about to end (send attendance sheet)
            class_end_time = timezone.make_aware(
                timezone.datetime.combine(schedule.date, schedule.end_time),
                timezone.get_current_timezone()
            )
            current_time = timezone.localtime(timezone.now())

            if class_end_time - timedelta(minutes=5) <= current_time and not email_sent:
                print("Generating Excel sheet and sending marksheet to lecturer...")

                attendance_data = []
                with open(attendance_file, "r") as file:
                    reader = csv.reader(file)
                    for row in reader:
                        attendance_data.append(row)

                df = pd.DataFrame(attendance_data[1:], columns=attendance_data[0])

                excel_file = BytesIO()
                with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name="Attendance")
                    writer.close()

                excel_file.seek(0)
                self.send_marksheet_to_lecturer(schedule, excel_file)
                self.save_attendance_file_to_db(excel_file, schedule)
                email_sent = True

            if k == ord('q'):
                print("Exiting attendance marking...")
                video.release()
                cv2.destroyAllWindows()
                os._exit(0)

        video.release()
        cv2.destroyAllWindows()
