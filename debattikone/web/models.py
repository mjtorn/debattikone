# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.db import models

from django.contrib.auth import models as auth_models

# Create your models here.

class Topic(models.Model):
    title = models.CharField(max_length=64)
    summary = models.CharField(max_length=1025)


class DebateMessage(models.Model):
    user = models.ForeignKey(auth_models.User)
    debate = models.ForeignKey("Debate")


class Debate(models.Model):
    topic = models.ForeignKey(Topic)
    user1 = models.ForeignKey(auth_models.User, related_name='user1')
    user2 = models.ForeignKey(auth_models.User, null=True, blank=True, default=None, related_name='user2')
    msg_limit = models.IntegerField(default=10)

    def can_participate(self, user):
        if self.user2 is None:
            return True

    def is_closed(self):
        return self.debatemessage_set.count() == self.msg_limit

# EOF

