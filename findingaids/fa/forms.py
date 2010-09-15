from django import forms
import re

def boolean_to_upper(data):
    """
    Converts boolean operators to uppercase
    """
    ops = ['and', 'or', 'not']

    for op in ops:
        upper_op = op.upper()
        data = re.sub(r"\b%s\b" % (op), upper_op, data)
        
    return data



from findingaids.fa.models import repositories

class KeywordSearchForm(forms.Form):
    "Simple keyword search form"
    keywords = forms.CharField(required=False,
        help_text="one or more terms; will search anywhere in the finding aid")
    subject = forms.CharField(required=False,
        help_text="Controlled subject headings: subject, genre, geography, etc.")
    # delay initializing choices until object init, since they are dynamic
    repository = forms.ChoiceField(required=False,
            initial='', help_text="Filter by repository")
            
    def __init__(self, *args, **kwargs):
        super(KeywordSearchForm, self).__init__(*args, **kwargs)
        # generate a list of repository choices
        repo_choices = [('', 'All')]    # default option - no filter / all repos
        # distinct list of repositories from eXist db: use exact phrase match for value/search
        repo_choices.extend([('"%s"' % r, r) for r in repositories()])
        self.fields['repository'].choices = repo_choices
        # configure select widget so all choices will be displayed
        self.fields['repository'].widget.attrs['size'] = len(repo_choices)

    def clean(self):
        """Custom form validation.  Keywords and subjects are both optional,
        but at least one of them should contain search terms."""
        cleaned_data = self.cleaned_data
        
        keywords = cleaned_data.get('keywords')
        subject = cleaned_data.get('subject')
        if not keywords and not subject:
            # for now, repository can only be used as a filter with keywords or subjects
            raise forms.ValidationError("Please enter search terms for at least one of keywords and subject")

        # TODO: if we can parse out subject:term or subject:"exact phrase"
        # from a keyword search, it would be nice to convert that to a subject search
        
        return cleaned_data
        

    def clean_keywords(self):
        data = self.cleaned_data['keywords']
        data = boolean_to_upper(data) #convert boolean operators to uppercase
        return data


class DocumentSearchForm(forms.Form):
    "Search item-level content within a single Finding Aid document."
    keywords = forms.CharField(required=True,
        help_text="one or more terms; will search anywhere in the finding aid")

    def clean_keywords(self):
        data = self.cleaned_data['keywords']
        data = boolean_to_upper(data) #convert boolean operators to uppercase
        return data
    
