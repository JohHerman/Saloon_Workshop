from urllib import request
from django.shortcuts import redirect, render
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from .models import User
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from .models import User, Booking, Service
from .forms import BookingForm
from django.utils import timezone
from datetime import datetime, timedelta


def home(request):
    # Get all workers (users with role='worker')
    workers = User.objects.filter(role='worker')
    
    return render(request, 'workshop/home.html', {
        'workers': workers
    })

def about(request):
    return render(request, 'workshop/About.html')

def services(request):
    # Get all services from database
    services_list = Service.objects.all().order_by('name')
    
    return render(request, 'workshop/services.html', {
        'services': services_list
    })

def bookings(request):
    """Handle booking form display and submission"""
    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save()
            
            # Send notification to admin (you can add email notifications here)
            messages.success(request, "Your booking request has been sent! We'll contact you within 24 hours to confirm.")
            
            # Optionally, you can redirect to a success page
            return redirect('booking-success')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = BookingForm()
    
    return render(request, 'workshop/bookings.html', {'form': form})

def booking_success(request):
    """Success page after booking submission"""
    return render(request, 'workshop/booking_success.html')

@login_required
def admin_dashboard(request):
    """Admin dashboard showing all bookings and users"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    if request.session.get('user_role') != 'admin':
        return redirect('worker-dashboard')
    
    user = User.objects.get(id=user_id)
    users = User.objects.all().order_by('-created_at')
    
    # Get all bookings with related info
    all_bookings = Booking.objects.all().order_by('-created_at')
    
    # Statistics
    pending_bookings = Booking.objects.filter(status='pending').count()
    confirmed_bookings = Booking.objects.filter(status='confirmed').count()
    completed_bookings = Booking.objects.filter(status='completed').count()
    cancelled_bookings = Booking.objects.filter(status='cancelled').count()
    
    return render(request, 'workshop/admin-dashboard.html', {
        'user': user,
        'users': users,
        'bookings': all_bookings,
        'pending_count': pending_bookings,
        'confirmed_count': confirmed_bookings,
        'completed_count': completed_bookings,
        'cancelled_count': cancelled_bookings,
    })

@login_required
def worker_dashboard(request):
    """Worker dashboard showing assigned bookings"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    user = User.objects.get(id=user_id)
    
    # Get bookings assigned to this worker
    assigned_bookings = Booking.objects.filter(assigned_worker=user).order_by('-created_at')
    
    # Also show bookings where this worker was preferred (if not assigned elsewhere)
    preferred_bookings = Booking.objects.filter(
        preferred_attendant=user,
        assigned_worker__isnull=True
    ).order_by('-created_at')
    
    # All bookings that need attention (pending with no worker assigned)
    pending_bookings = Booking.objects.filter(
        status='pending',
        assigned_worker__isnull=True
    ).order_by('-created_at')
    
    return render(request, 'workshop/worker_dashboard.html', {
        'user': user,
        'assigned_bookings': assigned_bookings,
        'preferred_bookings': preferred_bookings,
        'pending_bookings': pending_bookings,
    })

@login_required

def update_booking_status(request, booking_id):
    """Update booking status (for admin and workers)"""
    # Check if user is logged in
    if not request.session.get('user_id'):
        messages.error(request, "Please login to continue")
        return redirect('login')
    
    if request.method == "POST":
        booking = get_object_or_404(Booking, id=booking_id)
        new_status = request.POST.get('status')
        worker_id = request.POST.get('assign_worker')
        user_role = request.session.get('user_role')
        current_user_id = request.session.get('user_id')
        
        # Update status if provided
        if new_status:
            booking.status = new_status
        
        # Handle worker assignment
        if worker_id:
            # Case 1: Admin is assigning a worker
            if user_role == 'admin':
                try:
                    booking.assigned_worker = User.objects.get(id=worker_id)
                    messages.success(request, f"Worker assigned successfully to booking #{booking_id}")
                except User.DoesNotExist:
                    messages.error(request, "Worker not found")
            
            # Case 2: Worker is claiming a booking (worker sends their own ID)
            elif user_role == 'worker' and int(worker_id) == current_user_id:
                booking.assigned_worker = User.objects.get(id=current_user_id)
                messages.success(request, f"You have successfully claimed booking #{booking_id}")
            
            # Case 3: Someone trying to assign a different worker (unauthorized)
            elif user_role == 'worker' and int(worker_id) != current_user_id:
                messages.error(request, "You can only claim bookings for yourself")
        
        # If no worker_id but status is in_progress (for workers)
        elif user_role == 'worker' and new_status == 'in_progress' and not booking.assigned_worker:
            # Auto-assign the booking to this worker
            booking.assigned_worker = User.objects.get(id=current_user_id)
            messages.success(request, f"You have claimed booking #{booking_id}")
        
        # Save the booking
        booking.save()
        
        # Additional success message for status update only
        if new_status and not worker_id:
            messages.success(request, f"Booking #{booking_id} status updated to {new_status}")
        
        # Redirect back to appropriate dashboard
        if user_role == 'admin':
            return redirect('admin-dashboard')
        else:
            return redirect('worker-dashboard')
    
    # If not POST, redirect to dashboard
    if request.session.get('user_role') == 'admin':
        return redirect('admin-dashboard')
    else:
        return redirect('worker-dashboard')


def login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)

            if check_password(password, user.password):
                request.session['user_id'] = user.id
                request.session['user_role'] = user.role  # ← save role in session

                # Redirect based on role
                if user.role == 'admin':
                    return redirect('admin-dashboard')
                else:
                    return redirect('worker-dashboard')

            else:
                messages.error(request, "Invalid password")

        except User.DoesNotExist:
            messages.error(request, "User does not exist")

    return render(request, 'workshop/login.html')


def register(request):
     if request.method == "POST":
        full_name = request.POST.get('full_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        nida = request.POST.get('nida')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # ✅ Check passwords match
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect('register')

        # ✅ Check if username/email already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect('register')

        # ✅ Save user
        user = User(
            full_name=full_name,
            username=username,
            email=email,
            phone=phone,
            nida=nida,
            password=make_password(password)  # 🔒 hash password
        )
        user.save()

        messages.success(request, "Account created successfully!")
        return redirect('login')

     return render(request, 'workshop/register.html')



def worker_dashboard(request):
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    user = User.objects.get(id=user_id)
    
    # Get all bookings assigned to this worker
    assigned_bookings = Booking.objects.filter(
        assigned_worker=user
    ).order_by('-created_at')
    
    # Get bookings where this worker was preferred but not assigned yet
    preferred_bookings = Booking.objects.filter(
        preferred_attendant=user,
        assigned_worker__isnull=True,
        status='pending'
    ).order_by('-created_at')
    
    # Get pending bookings available to claim (not assigned to anyone)
    pending_bookings = Booking.objects.filter(
        status='pending',
        assigned_worker__isnull=True
    ).order_by('-created_at')
    
    # Get completed bookings for history
    completed_history = Booking.objects.filter(
        assigned_worker=user,
        status='completed'
    ).order_by('-updated_at')[:20]
    
    # Calculate stats
    today = timezone.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    today_count = assigned_bookings.filter(
        preferred_date__range=[today_start, today_end]
    ).count()
    
    in_progress_count = assigned_bookings.filter(status='in_progress').count()
    completed_today_count = assigned_bookings.filter(
        status='completed',
        updated_at__range=[today_start, today_end]
    ).count()
    
    pending_available = pending_bookings.count()
    
    return render(request, 'workshop/worker_dashboard.html', {
        'user': user,
        'assigned_bookings': assigned_bookings,
        'preferred_bookings': preferred_bookings,
        'pending_bookings': pending_bookings,
        'completed_history': completed_history,
        'today_count': today_count,
        'in_progress_count': in_progress_count,
        'completed_today_count': completed_today_count,
        'pending_available': pending_available,
    })



def admin_dashboard(request):
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    if request.session.get('user_role') != 'admin':
        return redirect('worker-dashboard')
    
    user = User.objects.get(id=user_id)
    users = User.objects.all().order_by('-created_at')
    
    # Get all workers (users with role='worker')
    workers = User.objects.filter(role='worker')
    
    # Get all bookings
    all_bookings = Booking.objects.all().order_by('-created_at')
    
    # Get completed bookings for history tab
    completed_bookings = Booking.objects.filter(status='completed').order_by('-updated_at')[:20]
    
    # Statistics
    pending_count = Booking.objects.filter(status='pending').count()
    confirmed_count = Booking.objects.filter(status='confirmed').count()
    completed_count = Booking.objects.filter(status='completed').count()
    cancelled_count = Booking.objects.filter(status='cancelled').count()
    
    return render(request, 'workshop/admin-dashboard.html', {
        'user': user,
        'users': users,
        'workers': workers,  # Pass workers to template
        'bookings': all_bookings,
        'completed_bookings': completed_bookings,  # For history tab
        'pending_count': pending_count,
        'confirmed_count': confirmed_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
    })

def booking_details(request, booking_id):
    """View booking details (for workers and admins)"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check if user has permission to view
    user = User.objects.get(id=user_id)
    if user.role != 'admin' and booking.assigned_worker != user:
        messages.error(request, "You don't have permission to view this booking.")
        return redirect('worker-dashboard')
    
    return render(request, 'workshop/booking_details.html', {
        'booking': booking,
        'user': user,
    })



# Create your views here.
