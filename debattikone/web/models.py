# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.db import models

from django.contrib.auth import models as auth_models

from django.template.defaultfilters import slugify

class DebattikoneModelException(Exception):
    pass


class DebattikoneInvalidUserException(DebattikoneModelException):
    pass

# Create your models here.

class Topic(models.Model):
    title = models.CharField(max_length=64)
    summary = models.CharField(max_length=1025)
    slug = models.SlugField(unique=True)

    def save(self):
        slug = slugify(self.title)
        if not Topic.objects.filter(slug=slug).exclude(id=self.id).count():
            self.slug = slug
            return super(Topic, self).save()

        i = 1
        while True:
            slug = slugify('%s %d' % (self.title, i))
            if not Topic.objects.filter(slug=slug).exclude(id=self.id).count():
                self.slug = slug
                return super(Topic, self).save()
            i += 1


class DebateMessage(models.Model):
    user = models.ForeignKey(auth_models.User)
    debate = models.ForeignKey("Debate")


class Debate(models.Model):
    topic = models.ForeignKey(Topic)
    user1 = models.ForeignKey(auth_models.User, related_name='debate_user1_set')
    user2 = models.ForeignKey(auth_models.User, null=True, blank=True, default=None, related_name='debate_user2_set')

    invited = models.ForeignKey(auth_models.User, null=True, blank=True, default=None, related_name='debate_invited_set')

    msg_limit = models.IntegerField(default=10)

    def can_invite(self, inviter, invitee):
        if inviter != self.user1:
            return False

        if invitee == self.user1:
            return False

        return True

    def can_participate(self, user):
        if self.user1 == user or self.user2 == user:
            return False

        if self.user2 is None and self.invited is None:
            return True

        if self.user2 is None and self.invited == user:
            return True

    def is_closed(self):
        return self.debatemessage_set.count() == self.msg_limit

    def invite(self, inviter, invitee):
        if inviter != self.user1:
            raise DebattikoneInvalidUserException('You are not the creator')

        if invitee == self.user1:
            raise DebattikoneInvalidUserException('Can not invite self')

        self.invited = invitee

    def invite(self, user):
        self.invited = user
        self.save()

    def participate(self, user):
        self.user2 = user
        self.save()

# EOF

