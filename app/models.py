from datetime import datetime
from django.db import models
from django.utils.timezone import now
from django.template.loader import render_to_string

from utils.email_utils import send_email_via_sendinblue

class Students(models.Model):
    DEPARTMENT_CHOICES = [
        ('CS', 'Computer Science'),
        ('IT', 'Information Technology'),
        ('ENG', 'Engineering'),
        ('BIZ', 'Business'),
        ('SCI', 'Science'),
    ]
    s_reg_number = models.CharField(max_length=20, unique=True)
    s_first_name = models.CharField(max_length=50)
    s_last_name = models.CharField(max_length=50)
    s_email = models.EmailField(unique=True)
    s_phone = models.CharField(max_length=15)
    s_Year = models.IntegerField(null=True)
    s_department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, default='CS')

    def full_name(self):
        return f"{self.s_first_name} {self.s_last_name}"

    def __str__(self):
        return self.full_name()

class Lecture(models.Model):
    DEPARTMENT_CHOICES = [
        ('CS', 'Computer Science'),
        ('IT', 'Information Technology'),
        ('ENG', 'Engineering'),
        ('BIZ', 'Business'),
        ('SCI', 'Science'),
    ]
    
    l_reg_number = models.CharField(max_length=20, unique=True, default='RJT/0000')
    l_first_name = models.CharField(max_length=50)
    l_last_name = models.CharField(max_length=50)
    l_email = models.EmailField(unique=True)
    l_phone = models.CharField(max_length=15)
    l_department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, default='CS')

    def full_name(self):
        return f"{self.l_first_name} {self.l_last_name}"

    def __str__(self):
        return self.full_name()
    
class Lab(models.Model):
    lab_number = models.CharField(max_length=10, unique=True)
    capacity = models.IntegerField()

    def __str__(self):
        return f"Lab {self.lab_number}"
    
class ClassSchedule(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Rescheduled', 'Rescheduled'),
        ('Finished', 'Finished'),
    ]

    class_name = models.CharField(max_length=100, unique=True)
    lecturer = models.ForeignKey(Lecture, on_delete=models.CASCADE)
    students = models.ManyToManyField('Students', blank=True)
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    s_department = models.CharField(max_length=100, blank=True, null=True)
    s_Year = models.CharField(max_length=10, blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    
    def save(self, *args, **kwargs):
        if self.pk:
            old_instance = ClassSchedule.objects.get(pk=self.pk)

            # If start time is changed, mark as Rescheduled and send an email
            if old_instance.start_time != self.start_time:
                self.status = 'Rescheduled'
                self.send_reschedule_email()

        if isinstance(self.end_time, str):
            try:
                self.end_time = datetime.strptime(self.end_time, "%H:%M").time()
            except ValueError:
                try:
                    self.end_time = datetime.strptime(self.end_time, "%H:%M:%S").time()
                except ValueError:
                    raise ValueError(f"Invalid time format: {self.end_time}")
                
        # ✅ Convert end_time if it's a string
        if isinstance(self.date, str):
            try:
                self.date = datetime.strptime(self.date, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f"Invalid date format: {self.date}")

        # ✅ Check if schedule is finished
        current_time = now()
        if self.date and self.end_time:
            if current_time.date() > self.date or (current_time.date() == self.date and current_time.time() > self.end_time):
                self.status = 'Finished'

        # if now().date() > self.date or (now().date() == self.date and now().time() > self.end_time):
        #     self.status = 'Finished'

        super().save(*args, **kwargs)

    def send_reschedule_email(self):
        """Send reschedule notification email to students and lecturer"""
        subject = f"Rescheduled Class: {self.class_name} on {self.date}"
        content = render_to_string('class_reschedule_email.html', {'class_schedule': self})

        # Get email lists for students and lecturer
        student_emails = list(self.students.values_list('s_email', flat=True))
        lecturer_email = [self.lecturer.l_email]

        recipients = student_emails + lecturer_email

        send_email_via_sendinblue(subject, content, recipients)
    def __str__(self):
        return f"{self.class_name} on {self.date} ({self.status})"
    









class Attendance(models.Model):
    class_schedule = models.ForeignKey(ClassSchedule, on_delete=models.CASCADE)
    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    time = models.DateTimeField(default=now)


class AttendanceFile(models.Model):
    schedule = models.ForeignKey(ClassSchedule, on_delete=models.CASCADE)
    file = models.FileField(upload_to='attendance_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Attendance file for {self.schedule.class_name} on {self.schedule.date}"