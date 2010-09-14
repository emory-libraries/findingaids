from django import forms

class KeywordSearchForm(forms.Form):
    "Simple keyword search form"
    keywords = forms.CharField(required=False,
        help_text="one or more terms; will search anywhere in the finding aid")
    subject = forms.CharField(required=False,
        help_text="Controlled subject headings: subject, genre, geography, etc.")

    def clean(self):
        """Custom form validation.  Keywords and subjects are both optional,
        but at least one of them should contain search terms."""
        cleaned_data = self.cleaned_data
        
        keywords = cleaned_data.get('keywords')
        subject = cleaned_data.get('subject')
        if not keywords and not subject:
            raise forms.ValidationError("Please enter search terms for at least one of keywords and subject")

        # TODO: if we can parse out subject:term or subject:"exact phrase"
        # from a keyword search, it would be nice to convert that to a subject search
        
        return cleaned_data
        

class DocumentSearchForm(forms.Form):
    "Search item-level content within a single Finding Aid document."
    keywords = forms.CharField(required=True,
        help_text="one or more terms; will search anywhere in the finding aid")
    
