from django import forms
from .models import Job
from site_core.models import Category  # adjust this to your project path

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            'title', 'description', 'category', 'job_type', 'location', 
            'company_name', 'company_logo', 'salary_min', 'salary_max', 'deadline', 
            'spots_total', 'level_requirement', 'price'
        ]
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'category': forms.Select(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show categories meant for Jobs
        self.fields['category'].queryset = Category.objects.filter(category_type='job')

    def clean(self):
        cleaned_data = super().clean()
        salary_min = cleaned_data.get('salary_min')
        salary_max = cleaned_data.get('salary_max')
        
        if salary_min and salary_max and salary_min > salary_max:
            raise forms.ValidationError("Minimum salary cannot be greater than maximum salary.")
        
        return cleaned_data
