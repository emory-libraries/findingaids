from django.forms import HiddenInput, Textarea, TextInput
from django.contrib.auth.forms import UserChangeForm
from findingaids.fa.models import Deleted
from django.forms import ModelForm

class FAUserChangeForm(UserChangeForm):
    """
    testing...
    """
    class Meta(UserChangeForm.Meta):
        fields = (
            'username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active',
            'is_superuser', 'last_login', 'date_joined', 'groups', 'user_permissions'
        )

class DeleteConfirmationForm(ModelForm):
    class Meta:
        model = Deleted
        exclude = ['date_time']
