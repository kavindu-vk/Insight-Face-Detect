import json
import os
import pickle
import numpy as np
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404

from .form import ClassScheduleForm, LabForm, StudentForm, LectureForm
from .utils import capture_images
from datetime import date
from .models import ClassSchedule, Lab, Students, Lecture
from django.template.loader import render_to_string
from utils.email_utils import send_email_via_sendinblue
from django.core.management import call_command

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Path to pickle files
PICKLE_DIRECTORY = "data/"
NAMES_PICKLE_FILE = 'data/names.pkl'
FACE_DATA_PICKLE_FILE = 'data/face_data.pkl'

# Dashboard view
@login_required(login_url='/login/')
def home(request):
    today = date.today()

    total_students = Students.objects.count()
    total_lecturers = Lecture.objects.count()
    total_labs = Lab.objects.count()
    total_departments = Students.objects.values('s_department').distinct().count()
    class_schedules = ClassSchedule.objects.filter(date=today)
    return render(request, 'index.html', {'total_students': total_students, 'total_departments': total_departments, 'total_lecturers': total_lecturers, 'class_schedules': class_schedules, 'total_labs': total_labs})

# Login
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password')
            return render(request, 'login.html')
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    return redirect('login')

# Add a new student
@login_required(login_url='/login/')
def add_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save()
            # Capture the student's images
            capture_images(student.s_first_name)
            return JsonResponse({"success": True, "message": "Student added successfully!"})
        else:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)

# List all students
@login_required(login_url='/login/')
def student_list(request):
    students = Students.objects.all()
    form = StudentForm()
    return render(request, 'Students.html', {'students': students, 'form': form})

# Update a student
@login_required(login_url='/login/')
def update_student(request):
    if request.method == "POST":
        s_reg_number = request.POST.get("s_reg_number")
        student = get_object_or_404(Students, s_reg_number=s_reg_number)

        student.s_first_name = request.POST.get("s_first_name")
        student.s_last_name = request.POST.get("s_last_name")
        student.s_email = request.POST.get("s_email")
        student.s_phone = request.POST.get("s_phone")
        student.s_Year = request.POST.get("s_Year")
        student.s_department = request.POST.get("s_department")

        student.save()
        return JsonResponse({"success": True})

    return JsonResponse({"success": False}, status=400)

# Delete a student
def delete_student(request, s_reg_number):
    if request.method == "POST":
        student = get_object_or_404(Students, s_reg_number=s_reg_number)
        student_name = student.s_first_name
        student.delete()
        
        # Load existing pickle data
        names_data = []
        face_data = []

        # Remove student data from names.pkl
        if os.path.exists(NAMES_PICKLE_FILE):
            with open(NAMES_PICKLE_FILE,  'rb') as f:
                names_data = pickle.load(f)

        # print(f"Names before deletion: {names_data}")

        names_data = [name for name in names_data if name != student_name]

        with open(NAMES_PICKLE_FILE, 'wb') as f:
            pickle.dump(names_data, f)


        # Remove student data from face_data.pkl
        if os.path.exists(FACE_DATA_PICKLE_FILE):
            with open(FACE_DATA_PICKLE_FILE, 'rb') as f:
                face_data = pickle.load(f)

        # print(f"Face data before deletion: {face_data}")

        # if len(face_data) > 100:
        #     face_data = np.delete(face_data, range(100), axis=0)
        if len(face_data) == len(names_data):  # Ensure data alignment
            index_to_delete = names_data.index(student_name)
            face_data = np.delete(face_data, index_to_delete, axis=0)

        with open(FACE_DATA_PICKLE_FILE, 'wb') as f:
            pickle.dump(face_data, f)

        return JsonResponse({"success": True, "message": "Student deleted successfully."})
    return JsonResponse({"success": False, "message": "Invalid request."})


# Add a new lecturer
@login_required(login_url='/login/')
def add_lecturer(request):
    if request.method == "POST":
        form = LectureForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({"success": True, "message": "Lecturer added successfully!"})
        else:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)

# List all lecturers
@login_required(login_url='/login/')
def lecture_list(request):
    lectures = Lecture.objects.all()
    form = LectureForm()
    return render(request, 'Lecturer.html', {'lectures': lectures, 'form': form})

# Update a lecturer
def update_lecturer(request):
    if request.method == "POST":
        l_reg_number = request.POST.get("l_reg_number")
        lecturer = get_object_or_404(Lecture, l_reg_number=l_reg_number)

        lecturer.l_first_name = request.POST.get("l_first_name")
        lecturer.l_last_name = request.POST.get("l_last_name")
        lecturer.l_email = request.POST.get("l_email")
        lecturer.l_phone = request.POST.get("l_phone")
        lecturer.l_department = request.POST.get("l_department")

        lecturer.save()
        return JsonResponse({"success": True})

    return JsonResponse({"success": False}, status=400) 

# Delete a lecturer
def delete_lecturer(request, l_reg_number):
    if request.method == "POST":
        lecturer = get_object_or_404(Lecture, l_reg_number=l_reg_number)
        lecturer.delete()
        return JsonResponse({"success": True, "message": "Lecturer deleted successfully."})
    return JsonResponse({"success": False, "message": "Invalid request."})

# Views for Scheduling Classes
@login_required(login_url='/login/')
def schedule_class(request):
    if request.method == 'POST':
        form = ClassScheduleForm(request.POST)
        if form.is_valid():
            s_department = form.cleaned_data.get('s_department')
            s_Year = form.cleaned_data.get('s_Year')

            class_schedule = form.save(commit=False)
            class_schedule.s_department = s_department 
            class_schedule.s_Year = s_Year 
            class_schedule.save()

            # Assign students automatically
            if s_department and s_Year:
                students = Students.objects.filter(s_department=s_department, s_Year=s_Year)
                class_schedule.students.set(students)

            # Send email notifications
            subject = f"Class Schedule: {class_schedule.class_name} on {class_schedule.date}"
            content = render_to_string('class_schedule_email.html', {'class_schedule': class_schedule})
            
            # Get email lists for students and the lecturer
            student_emails = list(class_schedule.students.values_list('s_email', flat=True))
            lecturer_email = [class_schedule.lecturer.l_email]

            recipients = student_emails + lecturer_email

            send_email_via_sendinblue(subject, content, recipients)
            return redirect('class_schedule_list')
        
    else:
        form = ClassScheduleForm()
    return render(request, 'Schedule_classes.html', {'form': form})

# List all class schedules
def class_schedule_list(request):
    form = ClassScheduleForm()
    schedules = ClassSchedule.objects.all()
    labs = Lab.objects.all()
    lectures = Lecture.objects.all()
    return render(request, 'Schedule_classes.html', {'schedules': schedules, 'form': form, 'labs': labs, 'lectures': lectures})

# Update a class schedule
def update_schedule(request):
    if request.method == "POST":
        print(request.POST)
        class_name = request.POST.get("class_name")
        if not class_name:
            return JsonResponse({"error": "class_name is required"}, status=400)
        
        schedule = get_object_or_404(ClassSchedule, class_name=class_name)

        lab_id = request.POST.get("lab")
        lecturer_id = request.POST.get("lecturer")
        if not lab_id or not lecturer_id:
            return JsonResponse({"error": "lab and lecturer are required"}, status=400)

        # schedule.lab = get_object_or_404(Lab, id=request.POST.get("lab"))
        # schedule.lecturer = get_object_or_404(Lecture, id=request.POST.get("lecturer"))
        schedule.lab = get_object_or_404(Lab, id=lab_id)
        schedule.lecturer = get_object_or_404(Lecture, id=lecturer_id)
        # schedule.lecturer = request.POST.get("lecturer")
        schedule.s_department = request.POST.get("s_department")
        schedule.s_Year = request.POST.get("s_Year")
        schedule.date = request.POST.get("date")
        schedule.start_time = request.POST.get("start_time")
        schedule.end_time = request.POST.get("end_time")

        schedule.save()
        return JsonResponse({"success": True})

    return JsonResponse({"success": False}, status=400) 

# Delete a class schedule
def delete_schedule_class(request, id):
    if request.method == "POST":
        schedule = get_object_or_404(ClassSchedule, id=id)
        schedule.delete()
        return JsonResponse({"success": True, "message": "Class schedule deleted successfully."})
    return JsonResponse({"success": False, "message": "Invalid request."})

# Create new labs
def create_lab(request):
    if request.method == 'POST':
        form = LabForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lab_list')
    else:
        form = LabForm()
    return render(request, 'create_lab.html', {'form': form})

def mark_attendance_view(request, schedule_id):
    schedule = get_object_or_404(ClassSchedule, id=schedule_id)
    # You can also pass additional arguments to the command if needed
    call_command('mark_attendance', schedule_id)
    return JsonResponse({"status": f"Attendance marked for {schedule.class_name}"})