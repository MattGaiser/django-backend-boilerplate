from .signals import set_current_user


class CurrentUserMiddleware:
    """
    Middleware to capture the current user and store it in thread-local storage.
    
    This allows the signals to access the current user for automatic assignment
    of created_by and updated_by fields.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Set the current user in thread-local storage
        if hasattr(request, 'user'):
            set_current_user(request.user)
        else:
            set_current_user(None)
        
        response = self.get_response(request)
        
        # Clean up thread-local storage
        set_current_user(None)
        
        return response