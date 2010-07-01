from django.forms import Textarea, TextInput
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

class DeleteForm(ModelForm):
    class Meta:
        model = Deleted
        # NOTE: not excluding date from edit form because on an update it MAY
        # need to be changed, but only a person can determine that
        widgets = {'note': Textarea(attrs={'cols': 80, 'rows': 10}),
                    # display eadid and title, but don't allow them to be edited
                   'eadid': TextInput(attrs={'readonly':'readonly'}),
                   'title': TextInput(attrs={'size':'80', 'readonly': 'readonly'})
                   }


