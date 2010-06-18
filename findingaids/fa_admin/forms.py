#from django import forms
from django.contrib.auth.forms import UserChangeForm

class FAUserChangeForm(UserChangeForm):
    """
    testing...
    """
    class Meta(UserChangeForm.Meta):
        fields = (
            'username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active',
            'is_superuser', 'last_login', 'date_joined', 'groups', 'user_permissions'
        )




