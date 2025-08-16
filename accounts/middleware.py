from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from products.models import SuspendedUser

class SuspensionCheckMiddleware(MiddlewareMixin):
    """
    Middleware to check if logged-in users are suspended
    """
    
    def process_request(self, request):
        # Only check authenticated users
        if not request.user.is_authenticated:
            return None
        
        # Skip check for admin users
        if request.user.username == 'Hasnain Hassan':
            return None
        
        # Skip check for certain URLs (like logout, login pages)
        skip_urls = ['/accounts/login/', '/accounts/logout/', '/accounts/register/']
        if request.path in skip_urls:
            return None
        
        # Check if user is suspended
        try:
            suspension = SuspendedUser.objects.get(user=request.user, is_active=True)
            
            # Check if temporary suspension has expired
            if suspension.suspension_end and timezone.now() > suspension.suspension_end:
                # Suspension has expired, deactivate it
                suspension.is_active = False
                suspension.save()
                
                # Reactivate seller's products if they were a seller
                if request.user.role == 'seller':
                    request.user.products.update(is_active=True)
                
                return None  # Allow access, suspension expired
            
            # User is actively suspended - log them out and redirect
            logout(request)
            
            # Create appropriate message based on suspension type
            if suspension.suspension_end:
                messages.error(
                    request, 
                    f'Your account has been temporarily suspended until {suspension.suspension_end.strftime("%Y-%m-%d")}. '
                    f'Reason: {suspension.get_reason_display()}. '
                    f'Description: {suspension.description}'
                )
            else:
                messages.error(
                    request, 
                    f'Your account has been permanently suspended. '
                    f'Reason: {suspension.get_reason_display()}. '
                    f'Description: {suspension.description}'
                )
            
            return redirect('login')
            
        except SuspendedUser.DoesNotExist:
            # User is not suspended, continue normally
            return None
