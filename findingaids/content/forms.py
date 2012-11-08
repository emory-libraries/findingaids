# file findingaids/content/forms.py
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
from django.conf import settings
from django.core.mail import send_mail

from eullocal.django.forms import captchafield
 
from findingaids.fa.utils import get_findingaid


class FeedbackForm(forms.Form):
    '''Simple Feedback form with reCAPTCHA.  Expects reCAPTCHA keys to be set
    in settings as RECAPTCHA_PUBLIC_KEY and RECAPTCHA_PRIVATE_KEY.  Form
    validation includes checking the CAPTCHA response.

    Captcha challenge html should be added to the form using
    :meth:`captcha_challenge`.

    When initializing this form to do validation, you must pass in the user's
    IP address, because it is required when submitting the captcha response
    for validation.  Example::

        form = FeedbackForm(data=request.POST, remote_ip=request.META['REMOTE_ADDR'])
    '''
    name = forms.CharField(required=False)
    email = forms.EmailField(required=False)
    message = forms.CharField(widget=forms.Textarea, required=True)

    # optional information; for use when submitting feedback about a single finding aid
    eadid = forms.CharField(widget=forms.HiddenInput, required=False)
    url = forms.CharField(widget=forms.HiddenInput, required=False)

    captcha = captchafield.ReCaptchaField()

    email_subject = 'Site Feedback'

    def __init__(self, data=None, remote_ip=None, **kwargs):
        self.remote_ip  = remote_ip
        super(FeedbackForm, self).__init__(data=data, **kwargs)
           
    def send_email(self):
        '''Send an email based on the posted form data.
        This method should not be called unless the form has validated.

        Sends a "Site Feedback" email to feedback email address configured
        in Django settings with the message submitted on the form.  If email
        and name are specified, they will be used as the From: address in the
        email that is generated; otherwise, the email will be sent from the
        SERVER_EMAIL setting configured in Django settings.

        Returns true when the email send.  Could raise an
        :class:`smtplib.SMTPException` if something goes wrong at the SMTP
        level.
        '''
        # construct a simple text message with the data from the form
        msg_parts = []
        # name & email are optional - repeat in email message if set
        if self.cleaned_data['email'] or self.cleaned_data['name']:
            msg_parts.append('Feedback from %(name)s %(email)s' % self.cleaned_data)
        # eadid & url are optional, hidden - will be set together for single-finding aid feedback
        if self.cleaned_data['eadid'] and self.cleaned_data['url']:
            eadid = self.cleaned_data['eadid']
            ead = get_findingaid(eadid=eadid, only=['title'])
            msg_parts.append("Feedback about %s (%s)\nFrom url: %s" % \
                (unicode(ead.title), eadid, self.cleaned_data['url']))
        # message is required, so should always be set
        msg_parts.append(self.cleaned_data['message'])
        # join together whatever parts of the message should be present
        message = '\n\n'.join(msg_parts)
      
        # send an email with settings comparable to mail_admins or mail_managers
        return send_mail(
            settings.EMAIL_SUBJECT_PREFIX + self.email_subject, # subject
            message,                                           # email text
            generate_from_email(self.cleaned_data),            # from address
            settings.FEEDBACK_EMAIL                           # list of recipient emails
        )

def generate_from_email(data):
    '''Generate a From: email address to use when sending an email.  Takes a
    dictionary (e.g., cleaned form data); if email or email & name are present,
    they will be used to generate the email address to be used; otherwise,
    returns a fall-back option of the configured SERVER_MAIL address.
    '''
    # email & name are optional; if they are set, use as From: address for the email
    if 'email' in data and data['email']:
        # if name is set, use both name and email
        if 'name' in data and data['name']:
            return '"%(name)s" <%(email)s>' % data
        # otherwise, use just email
        else:
            return data['email']
    # if no email was specified, use configured server email
    else:
        return settings.SERVER_EMAIL


class RequestMaterialsForm(forms.Form):
    'Email form where a researcher can request materials for their visit.'
    repo = forms.MultipleChoiceField(settings.REQUEST_MATERIALS_CONTACTS,
            label='Repository', required=True, widget=forms.CheckboxSelectMultiple)
    name = forms.CharField(required=True)
    date = forms.CharField(label='Date of Visit', required=True)
    email = forms.EmailField(label='Email address', required=True)
    phone = forms.CharField(label='Phone Number', required=False)
    request = forms.CharField(label='Materials Requested', widget=forms.Textarea)

    captcha = captchafield.ReCaptchaField()

    email_subject = 'Request for Materials'

    def send_email(self):
        # send an email (should not be used unless form is valid)
        # construct a simple text message with the data from the form
        message = '''
Name:                %(name)s
Date of Visit:       %(date)s
Email:               %(email)s
Phone Number:        %(phone)s
Materials Requested:

%(request)s
        ''' % self.cleaned_data
        # keys of repo field = email address(es) to receive message
        to_email = self.cleaned_data['repo']
        return send_mail(
            settings.EMAIL_SUBJECT_PREFIX + self.email_subject,  # subject
            message,                                              # email text
            generate_from_email(self.cleaned_data),               # from address
            to_email                                              # email recepient
        )
