# file findingaids/fa/forms.py
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

from django import forms
from findingaids.fa.models import EadRepository
import re


def boolean_to_upper(data):
    """Convert boolean operators to uppercase"""
    ops = ['and', 'or', 'not']

    for op in ops:
        data = re.sub(r"\b%s\b" % (op), op.upper(), data)

    return data


class KeywordSearchForm(forms.Form):
    "Simple keyword search form"
    keywords = forms.CharField(
        required=False,
        help_text="one or more terms; will search anywhere in the finding aid")
    # checkbox to filter on presence of dao tags in a findingaid or file-level item
    dao = forms.BooleanField(
        label='Available Online',
        required=False,
        help_text='collections with digital resources only')

    def clean_keywords(self):
        """
        Performs any cleanup / validation specific to keywords field
        """
        # convert boolean operators to uppercase
        return boolean_to_upper(self.cleaned_data['keywords'])

    def clean(self):
        cleaned_data = super(KeywordSearchForm, self).clean()
        keywords = cleaned_data.get('keywords')
        dao = cleaned_data.get("dao")

        # dao filter can be specified with no keywords,
        # but at least one input is required
        if not keywords and not dao:
            raise forms.ValidationError('Please either enter a search term ' +
                                        'or restrict to resources available online')
        return cleaned_data


class AdvancedSearchForm(KeywordSearchForm):
    "Advanced search form for keyword, subject and repository"
    #redefining keywords because it is optional in the AdvancedSearchForm
    keywords = forms.CharField(required=False)
    subject = forms.CharField(
        required=False,
        help_text="Controlled subject headings: subject, genre, geography, etc.")
    # delay initializing choices until object init, since they are dynamic
    repository = forms.ChoiceField(
        required=False, initial='', help_text="Filter by repository")

    def __init__(self, *args, **kwargs):
        super(AdvancedSearchForm, self).__init__(*args, **kwargs)
        # generate a list of repository choices
        repo_choices = [('', 'All')]    # default option - no filter / all repos
        repo_choices = []
        # distinct list of repositories from eXist db: use exact phrase match for value/search
        repo_choices.extend([('"%s"' % r, r) for r in EadRepository.distinct()])
        self.fields['repository'].choices = repo_choices
        # configure select widget so all choices will be displayed
        self.fields['repository'].widget.attrs['size'] = len(repo_choices)

    def clean(self):
        """Custom form validation.  Keywords, dao filter, and subjects
        are all optional, but at least one of them should contain search terms
        or be set."""
        cleaned_data = self.cleaned_data

        keywords = cleaned_data.get('keywords')
        subject = cleaned_data.get('subject')
        dao = cleaned_data.get('dao')
        if not any([keywords, subject, dao, cleaned_data.get('repository')]):
            # for now, repository can only be used as a filter with keywords or subjects
            raise forms.ValidationError('Please enter search terms or choose a repository.')

        # TODO: if we can parse out subject:term or subject:"exact phrase"
        # from a keyword search, it would be nice to convert that to a subject search

        return cleaned_data
