"""
URL configuration for saloon project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from workshop import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('home', views.home, name='home'),
    path('About', views.about, name='About'),
    path('services', views.services, name='services'),
    path('bookings', views.bookings, name='bookings'),
    path('login', views.login, name='login'),
    path('register', views.register, name='register'),
    path('admin-dashboard', views.admin_dashboard, name='admin-dashboard'),
    path('worker-dashboard', views.worker_dashboard, name='worker-dashboard'),
    path('update-booking/<int:booking_id>/', views.update_booking_status, name='update-booking-status'),
    path('booking-success', views.booking_success, name='booking-success'),
    path('booking-details/<int:booking_id>/', views.booking_details, name='booking-details'),
]
