from django import forms

class KeywordSearchForm(forms.Form):
    "Simple keyword search form"
    keywords = forms.CharField(required=False,
        help_text="one or more terms; will search anywhere in the finding aid")
    subject = forms.CharField(required=False,
        help_text="Controlled subject headings: subject, genre, geography, etc.")

class DocumentSearchForm(forms.Form):
    "Search item-level content within a single Finding Aid document."
    keywords = forms.CharField(required=True,
        help_text="one or more terms; will search anywhere in the finding aid")
    
