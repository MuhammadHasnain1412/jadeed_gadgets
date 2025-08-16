from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.utils import timezone
from products.models import SuspendedUser

User = get_user_model()

class SuspensionAwareBackend(ModelBackend):
    """
    Custom authentication backend that checks for user suspensions
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        # First, try the default authentication
        user = super().authenticate(request, username, password, **kwargs)
        
        if user is None:
            return None
        
        # Check if user is suspended
        if self.is_user_suspended(user):
            return None  # Prevent login for suspended users
        
        return user
    
    def is_user_suspended(self, user):
        """Check if user has an active suspension"""
        try:
            suspension = SuspendedUser.objects.get(user=user, is_active=True)
            
            # Check if temporary suspension has expired
            if suspension.suspension_end:
                if timezone.now() > suspension.suspension_end:
                    # Suspension has expired, deactivate it
                    suspension.is_active = False
                    suspension.save()
                    
                    # Reactivate seller's products if they were a seller
                    if user.role == 'seller':
                        user.products.update(is_active=True)
                    
                    return False
            
            return True  # User is actively suspended
            
        except SuspendedUser.DoesNotExist:
            return False  # User is not suspended
