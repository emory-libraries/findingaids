from django import forms

from findingaids.fa.models import repositories

class KeywordSearchForm(forms.Form):
    "Simple keyword search form"
    keywords = forms.CharField(required=False,
        help_text="one or more terms; will search anywhere in the finding aid")
    subject = forms.CharField(required=False,
        help_text="Controlled subject headings: subject, genre, geography, etc.")
    repo_choices = [(r, r) for r in repositories()]
    repo_choices.insert(0, ('', 'All'))     # first option should be all
    repository = forms.ChoiceField(required=False, choices=repo_choices,
            initial='', help_text="Filter by repository",
            # configure select widget to be large enough to display all choices
            widget=forms.Select(attrs={'size': len(repo_choices)}))

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
    
