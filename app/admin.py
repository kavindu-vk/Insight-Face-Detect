from django.contrib import admin
from .models import Attendance, AttendanceFile, Lecture, Students, Lab, ClassSchedule

@admin.register(Lecture)
class LecturerAdmin(admin.ModelAdmin):
    list_display = ['l_reg_number', 'full_name', 'l_email', 'l_phone', 'l_department',]

    def full_name(self, obj):
        return f"{obj.l_first_name} {obj.l_last_name}"
    full_name.short_description = 'Lecturer Name'

@admin.register(Students)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['s_reg_number', 'full_name', 's_email', 's_phone', 's_Year', 's_department',]

    def full_name(self, obj):
        return f"{obj.s_first_name} {obj.s_last_name}"
    full_name.short_description = 'Student Name'

@admin.register(Lab)
class LabAdmin(admin.ModelAdmin):
    list_display = ['lab_number', 'capacity']

@admin.register(ClassSchedule)
class ClassScheduleAdmin(admin.ModelAdmin):
    list_display = ['class_name', 'lecturer', 's_department', 's_Year', 'lab', 'date', 'start_time', 'end_time', 'status']
    list_filter = ['s_department', 's_Year', 'lecturer', 'lab', 'date']
    search_fields = ['class_name', 'lecturer__l_name', 's_department', 's_Year']
    filter_horizontal = ['students']
    readonly_fields = ['status'] 
    
admin.site.register(Attendance)
admin.site.register(AttendanceFile)

