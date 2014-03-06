# file findingaids/fa/templatetags/ark_pid.py
#
#   Copyright 2014 Emory University Library
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

"""
Custom template filters for displaying the pid portion of an ARK URL.
"""

from django import template
from django.template.defaultfilters import stringfilter

from pidservices.clients import is_ark, parse_ark

register = template.Library()

@register.filter
@stringfilter
def ark_pid(value):
    '''Template filter to display just the pid portion of an ARK URI.
    Returns None if the value passed in is not recognized as an ARK.'''
    if is_ark(value):
        ark_parts = parse_ark(value)
        return ark_parts['noid']

