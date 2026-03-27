from django.db import models

# Create your models here.

from django.db import models

class User(models.Model):
    ROLE_CHOICES = [
        ('worker', 'Worker'),
        ('admin', 'Admin'),
        ('manager', 'Manager'),
    ]

    full_name = models.CharField(max_length=150)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    nida = models.CharField(max_length=30, unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='worker')  # ← new
    created_at = models.DateTimeField(auto_now_add=True)
    specialization = models.CharField(max_length=100, blank=True, null=True)  # e.g., "Hair Stylist", "Makeup Artist"
    bio = models.TextField(blank=True, null=True)  # Short bio/description
    experience_years = models.IntegerField(default=0)  # Years of experience
    profile_image = models.ImageField(upload_to='workers/', blank=True, null=True)  # Profile photo
    is_available = models.BooleanField(default=True)  # Availability status

    def __str__(self):
        return self.username
    

# Add to your existing models.py

class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_minutes = models.IntegerField(help_text="Duration in minutes")
    
    def __str__(self):
        return self.name

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Client information
    client_name = models.CharField(max_length=150)
    client_phone = models.CharField(max_length=20)
    client_email = models.EmailField(blank=True, null=True)
    
    # Booking details
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, related_name='bookings')
    service_name = models.CharField(max_length=100, blank=True)  # Store service name if service is deleted
    preferred_attendant = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_bookings', limit_choices_to={'role': 'worker'})
    preferred_attendant_name = models.CharField(max_length=150, blank=True)  # Store attendant name
    
    # Additional info
    notes = models.TextField(blank=True)
    preferred_date = models.DateTimeField(null=True, blank=True)  # Preferred date/time
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # For admin/worker assignment
    assigned_worker = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='working_bookings', limit_choices_to={'role': 'worker'})
    
    def __str__(self):
        return f"Booking for {self.client_name} - {self.service_name or self.service}"
    
    def save(self, *args, **kwargs):
        # Store service name if service exists
        if self.service and not self.service_name:
            self.service_name = self.service.name
        # Store attendant name if attendant exists
        if self.preferred_attendant and not self.preferred_attendant_name:
            self.preferred_attendant_name = self.preferred_attendant.full_name
        super().save(*args, **kwargs)