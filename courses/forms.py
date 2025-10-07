from django import forms
from .models import Course
from site_core.models import Category  # adjust import to your app

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'title', 'description', 'category', 'level', 'duration', 
            'mode', 'start_date', 'is_self_paced', 'price', 'spots_total',
            'preview_video', 'thumbnail'
        ]
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'category': forms.Select(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show categories meant for Courses
        self.fields['category'].queryset = Category.objects.filter(category_type='course')  

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        is_self_paced = cleaned_data.get('is_self_paced')
        
        if not is_self_paced and not start_date:
            raise forms.ValidationError("Start date is required for scheduled courses.")
        
        return cleaned_data
