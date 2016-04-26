# file findingaids/fa_admin/forms.py
#
#   Copyright 2012 Emory University Library
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from django.forms import Textarea, TextInput
from findingaids.fa.models import Deleted
from django.forms import ModelForm


class DeleteForm(ModelForm):
    class Meta:
        model = Deleted
        # django 1.8 requires explicit field list or exclude list;
        # include all fields for now
        exclude = []
        # NOTE: not excluding date from edit form because on an update it MAY
        # need to be changed, but only a person can determine that
        widgets = {
            'note': Textarea(attrs={'cols': 80, 'rows': 10}),
            # display eadid and title, but don't allow them to be edited
            'eadid': TextInput(attrs={'readonly': 'readonly'}),
            'title': TextInput(attrs={'size': '80', 'readonly': 'readonly'})
        }
