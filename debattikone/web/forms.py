# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.contrib.auth import models as auth_models

from annoying.decorators import autostrip
from annoying.functions import get_object_or_None

from django import forms
from debattikone.web import models

REG_ERRS = {
    'required': 'Tämä tieto tarvitaan',
    'invalid': 'Virheellinen tieto',
    'invalid_choice': 'Tämä vaihtoehto ei ole yksi annetuista',
    'max_length': 'Korkeintaan %(limit_value)d merkkiä, kiitos (Nyt on %(show_value)d)',
}

@autostrip
class RegisterForm(forms.Form):
    username = forms.fields.CharField(label='Käyttäjätunnus', max_length=32, error_messages=REG_ERRS)
    email = forms.fields.EmailField(label='Sähköposti', error_messages=REG_ERRS)
    password = forms.fields.CharField(label='Salasana', widget=forms.widgets.HiddenInput(), error_messages=REG_ERRS)

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
class LoginForm(forms.Form):
    l_username = forms.fields.CharField(label='Käyttäjätunnus', max_length=32, error_messages=REG_ERRS)
    l_password = forms.fields.CharField(label='Salasana', widget=forms.widgets.PasswordInput())

    def clean(self):
        user = get_object_or_None(auth_models.User, username=self.cleaned_data['l_username'])

        if user is None:
            raise forms.ValidationError('Virheellinen käyttäjätunnus')

        self.cleaned_data['user'] = user
        return self.cleaned_data

@autostrip
class NewTopicForm(forms.Form):
    title = forms.fields.CharField(label='Otsikko', max_length=64, error_messages=REG_ERRS)
    summary = forms.fields.CharField(label='Yhteenveto', max_length=1024, widget=forms.widgets.Textarea(), error_messages=REG_ERRS)

    def save(self):
        topic = models.Topic()
        topic.title=self.cleaned_data['title']
        topic.summary=self.cleaned_data['summary']

        topic.save()

        return topic


@autostrip
class NewDebateForm(forms.Form):
    topic = forms.models.ModelChoiceField(models.Topic.objects.all().order_by('slug'), label='Aihe', empty_label=None, error_messages=REG_ERRS)
    invited = forms.models.ModelChoiceField(auth_models.User.objects.all().order_by('username'), label='Kutsu käyttäjä', required=False, error_messages=REG_ERRS)

    invite_random = forms.fields.BooleanField(label='Kutsu satunnainen käyttäjä', required=False)

    def clean(self):
        if not self.cleaned_data.has_key('topic'):
            raise forms.ValidationError('Jokin kenttä sisältää virheellisen arvon')

        invite_random = self.data.get('invite_random', False)
        if invite_random:
            from django.db.models import F
            user = self.data['user']
            invited = auth_models.User.objects.all().order_by('?')
            invited = invited.exclude(id=user.id)
            invited = invited.exclude(debate_invited_set__invited__username=F('username'))
            if invited:
                invited = invited[0]
                self.cleaned_data['invited'] = invited
            else:
                raise forms.ValidationError('Satunnaista vastapuolta ei löydetty')
        else:
            invited = self.cleaned_data.get('invited', None)

        debate = get_object_or_None(models.Debate, topic=self.cleaned_data['topic'], invited=invited)

        if debate is not None:
            if invite_random:
                raise forms.ValidationError('Satunnaista vastapuolta ei löydetty')
            elif not debate.is_closed():
                raise forms.ValidationError('Sinulla on jo tällainen debatti')

        return self.cleaned_data

    def save(self):
        debate = models.Debate()

        debate.topic = self.cleaned_data['topic']
        debate.invited = self.cleaned_data['invited']
        debate.user1 = self.cleaned_data['user']

        debate.save()

        return debate


@autostrip
class DebateMessageForm(forms.Form):
    message = forms.fields.CharField(label='Viesti', widget=forms.widgets.Textarea())

    def clean(self):
        ## Assume debate and user was smuggled in
        debate = self.data['debate']
        user = self.data['user']

        can_send = debate.can_send(user)

        if can_send is None:
            raise forms.ValidationError('Et voi lähettää debattiin')

        self.cleaned_data['argument_type'] = can_send

        return self.cleaned_data

    def save(self):
        debate = self.data['debate']
        user = self.data['user']

        argument_type = self.cleaned_data['argument_type']
        argument = self.cleaned_data['message']

        return debate.send(user, argument_type, argument)

# EOF

