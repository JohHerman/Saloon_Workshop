# forms.py
from django import forms
from .models import Booking, Service, User

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['client_name', 'client_phone', 'client_email', 'service', 'preferred_attendant', 'notes', 'preferred_date']
        widgets = {
            'client_name': forms.TextInput(attrs={'placeholder': 'e.g., Marie Claire'}),
            'client_phone': forms.TextInput(attrs={'placeholder': '+255 123 456 789'}),
            'client_email': forms.EmailInput(attrs={'placeholder': 'marie@example.com'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': "e.g., I'd love to come on Tuesday after 3pm..."}),
            'preferred_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show workers as preferred attendants
        self.fields['preferred_attendant'].queryset = User.objects.filter(role='worker')
        self.fields['preferred_attendant'].required = False
        self.fields['preferred_attendant'].empty_label = "– any master –"
        
        # Only show active services
        self.fields['service'].queryset = Service.objects.all()
        self.fields['service'].empty_label = "– select service –"