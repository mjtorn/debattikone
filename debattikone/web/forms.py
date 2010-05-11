# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.contrib.auth import models as auth_models

from annoying.decorators import autostrip
from annoying.functions import get_object_or_None

from django import forms
from debattikone.web import models

REG_ERRS = {
    'required': 'Tämä tieto tarvitaan',
    'invalid': 'Virheellinen tieto',
    'max_length': 'Korkeintaan %(limit_value)d merkkiä, kiitos (Nyt on %(show_value)d)',
}

@autostrip
class RegisterForm(forms.Form):
    username = forms.fields.CharField(max_length=32, error_messages=REG_ERRS)
    email = forms.fields.EmailField(error_messages=REG_ERRS)
    password = forms.fields.CharField(widget=forms.widgets.HiddenInput(), error_messages=REG_ERRS)

    def clean_username(self):
        u = get_object_or_None(auth_models.User, username=self.data['username'])
        if u is not None:
            raise forms.ValidationError('Käyttäjätunnus %s on jo otettu' % self.data['username'])
        return self.data['username']

    def save(self):
        username = self.cleaned_data['username']
        email = self.cleaned_data['email']
        password = self.cleaned_data['password']

        user = auth_models.User(username=username, email=email)
        user.set_password(password)

        return user.save()


@autostrip
class NewTopicForm(forms.Form):
    title = forms.fields.CharField(max_length=64, error_messages=REG_ERRS)
    summary = forms.fields.CharField(max_length=1024, widget=forms.widgets.Textarea(), error_messages=REG_ERRS)

    def save(self):
        topic = models.Topic()
        topic.title=self.cleaned_data['title']
        topic.summary=self.cleaned_data['summary']

        topic.save()

        return topic

# EOF

