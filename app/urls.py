from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='user_logout'),

    path('add-student/', views.add_student, name='add_student'),
    path('students/', views.student_list, name='student_list'),
    path("update-student/", views.update_student, name="update_student"),
    path("delete-student/<path:s_reg_number>/", views.delete_student, name="delete_student"),

    path('add-lecture/', views.add_lecturer, name='add_lecturer'),
    path('lecturer/', views.lecture_list, name='lecture_list'),
    path("update-lecturer/", views.update_lecturer, name="update_lecturer"),
    path("delete-lecturer/<path:l_reg_number>/", views.delete_lecturer, name="delete_lecturer"),

    path('schedule-class/', views.schedule_class, name='schedule_class'),
    path('class-schedules/', views.class_schedule_list, name='class_schedule_list'),
    path('update-schedule/', views.update_schedule, name='update_schedule'),
    path('delete-schedule/<int:id>/', views.delete_schedule_class, name='delete_schedule'),

    path('create-lab/', views.create_lab, name='create_lab'),
    
    path('mark-attendance/<int:schedule_id>/', views.mark_attendance_view, name='mark_attendance'),
]