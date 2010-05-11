# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.db import models

from django.contrib.auth import models as auth_models

from django.template.defaultfilters import slugify

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
    argument_type = models.IntegerField(choices=((0, 'Opening argument'), (1, 'Normal argument'), (2, 'Closing argument')))
    argument = models.TextField()


class Debate(models.Model):
    topic = models.ForeignKey(Topic)
    user1 = models.ForeignKey(auth_models.User, related_name='debate_user1_set')
    user2 = models.ForeignKey(auth_models.User, null=True, blank=True, default=None, related_name='debate_user2_set')

    invited = models.ForeignKey(auth_models.User, null=True, blank=True, default=None, related_name='debate_invited_set')

    created_at = models.DateTimeField(auto_now_add=True)

    # One round is 4 messages, this is 3 rounds
    _msg_limit = models.IntegerField(default=12, db_column='msg_limit')
    def get_msg_limit(self):
        return self._msg_limit
    def set_msg_limit(self, value):
        if not isinstance(value, int):
            raise TypeError('Need int for msg_limit')
        if value % 4 != 0:
            raise ValueError('Must be multiplier of 4')
    msg_limit = property(get_msg_limit, set_msg_limit)

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

    def can_send(self, user):
        """Return what type of message user can send
        None - nothing
        0 - opening
        1 - normal
        2 - closing
        """

        # Users must be set
        if self.user1 is None or self.user2 is None:
            return None

        # Users must be proper
        if self.user1 == user or self.user2 == user:
            messages = self.debatemessage_set.all()

            # Makes assumptions about numbers :(
            opening_messages = [m for m in messages if m.argument_type == 0]
            normal_messages = [m for m in messages if m.argument_type == 1]
            closing_messages = [m for m in messages if m.argument_type == 2]

            len_opening = len(opening_messages)
            len_normal = len(normal_messages)
            len_closing = len(closing_messages)

            if len_opening < 2:
                # User1 starts
                if len_opening == 0 and self.user1 == user:
                    return 0
                elif len_opening == 1 and self.user2 == user:
                    return 0
                return None

            if len_normal < self.msg_limit:
                # Can not present first question out of order
                if not len_normal and user != self.user1:
                    return None
                # user1 starts
                elif not len_normal and user == self.user1:
                    return 1
                # One message means user2 replies
                elif len_normal == 1:
                    if normal_messages[-1].user != user:
                        return 1
                elif len_normal >= 2:
                    # user1 asked and user2 replied, user2's turn
                    if normal_messages[-2].user != normal_messages[-1].user:
                        if normal_messages[-1].user == user:
                            return 1

                    # user2 replied, asked new question, user1's turn
                    if normal_messages[-2].user == normal_messages[-1].user:
                        if normal_messages[-1].user != user:
                            return 1

                return None

            if len_normal == self.msg_limit:
                if len_closing < 3:
                    return 2

        return None

    def is_closed(self):
        return self.debatemessage_set.count() == self.msg_limit

    def invite(self, user):
        self.invited = user
        self.save()

    def participate(self, user):
        self.user2 = user
        self.save()

    def send(self, user, argument_type, argument):
        msg = DebateMessage()

        msg.user = user
        msg.debate = self
        msg.argument_type = argument_type
        msg.argument = argument

        msg.save()

        return msg

# EOF

