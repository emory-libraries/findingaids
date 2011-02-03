from django import forms
from django.conf import settings
from django.core.mail import send_mail

class FeedbackForm(forms.Form):
    name = forms.CharField(required=False)
    email = forms.EmailField(required=False)
    message = forms.CharField(widget=forms.Textarea, required=True)

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
        message = '''
Name:                %(name)s
Email:               %(email)s

%(message)s
''' % self.cleaned_data

        # email & name are optional; if they are set, use as From: address for the email
        if self.cleaned_data['email']:
            # if name is set, use both name and email 
            if self.cleaned_data['name']:
                from_email = '"%(name)s" <%(email)s>' % self.cleaned_data
            # otherwise, use just email
            else:
                from_email = self.cleaned_data['email']
        # if no email was specified, use configured server email
        else:
            from_email = settings.SERVER_EMAIL

        # send an email with settings comparable to mail_admins or mail_managers
        return send_mail(
            settings.EMAIL_SUBJECT_PREFIX + 'Site Feedback',   # subject
            message,                                           # email text
            from_email,                                        # from address
            settings.FEEDBACK_EMAIL,                           # list of recipient emails
        )