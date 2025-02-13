from django import forms
from .models import ClassSchedule, Lab, Students, Lecture

class StudentForm(forms.ModelForm):
    class Meta:
        model = Students
        fields = '__all__'

class LectureForm(forms.ModelForm):
    class Meta:
        model = Lecture
        fields = '__all__'

class ClassScheduleForm(forms.ModelForm):
    s_department = forms.ChoiceField(
        choices = [('', 'Select Department')] + [(dept, dept) for dept in Students.objects.values_list('s_department', flat=True).distinct()],
        required=False,
        label="Department",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'department'})
    )

    s_Year = forms.ChoiceField(
        choices = [('', 'Select Year')] + [(year, year) for year in Students.objects.values_list('s_Year', flat=True).distinct()],
        required=False,
        label="Year",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'year'})
    )

    class Meta:
        model = ClassSchedule
        fields = ['class_name', 'lecturer', 'lab', 'date', 'start_time', 'end_time']
        widgets = {
            'class_name': forms.TextInput(attrs={'class': 'form-control', 'id': 'className'}),
            'lecturer': forms.Select(attrs={'class': 'form-select', 'id': 'lecturer'}),
            'lab': forms.Select(attrs={'class': 'form-select', 'id': 'labNumber',}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'id': 'startTime'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'id': 'endTime'}),
        }
    
    def clean_status(self):
        return self.instance.status

    def __init__(self, *args, **kwargs):
        super(ClassScheduleForm, self).__init__(*args, **kwargs)
        departments = Students.objects.values_list('s_department', flat=True).distinct()
        self.fields['s_department'].choices = [('', 'Select Department')] + [(dept, dept) for dept in departments]

        years = Students.objects.values_list('s_Year', flat=True).distinct()
        self.fields['s_Year'].choices = [('', 'Select Year')] + [(year, year) for year in years]

         

    
class LabForm(forms.ModelForm):
    class Meta:
        model = Lab
        fields = ['lab_number', 'capacity']