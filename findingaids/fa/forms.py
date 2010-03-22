from django import forms

class KeywordSearchForm(forms.Form):
    "Simple keyword search form"
    keywords = forms.CharField(required=True,
        help_text="one or more terms; will search anywhere in the finding aid")


