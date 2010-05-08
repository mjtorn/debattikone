# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.db import models

from django.contrib.auth import models as auth_models

class DebattikoneModelException(Exception):
    pass


class DebattikoneInvalidUserException(DebattikoneModelException):
    pass

# Create your models here.

class Topic(models.Model):
    title = models.CharField(max_length=64)
    summary = models.CharField(max_length=1025)


class DebateMessage(models.Model):
    user = models.ForeignKey(auth_models.User)
    debate = models.ForeignKey("Debate")


class Debate(models.Model):
    topic = models.ForeignKey(Topic)
    user1 = models.ForeignKey(auth_models.User, related_name='debate_user1_set')
    user2 = models.ForeignKey(auth_models.User, null=True, blank=True, default=None, related_name='debate_user2_set')

    invited = models.ForeignKey(auth_models.User, null=True, blank=True, default=None, related_name='debate_invited_set')

    msg_limit = models.IntegerField(default=10)

    def can_participate(self, user):
        if self.user1 == user or self.user2 == user:
            return False

        if self.user2 is None:
            return True

    def is_closed(self):
        return self.debatemessage_set.count() == self.msg_limit

    def invite(self, inviter, invitee):
        if inviter != self.user1:
            raise DebattikoneInvalidUserException('You are not the creator')

        self.invited = invitee

        self.save()

# EOF

