# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.db import models

from django.core import mail
from django.core.urlresolvers import reverse

from django.contrib.auth import models as auth_models

from django.template.defaultfilters import slugify

from django.template.loader import render_to_string

# Create your models here.

TYPE_NOTHING = None
TYPE_OPEN = 0
TYPE_QUESTION = 1
TYPE_REPLY = 2
TYPE_CLOSING = 3

class Topic(models.Model):
    title = models.CharField(max_length=64)
    summary = models.CharField(max_length=1024)
    slug = models.SlugField(unique=True)

    def __unicode__(self):
        return '%s (%s)' % (self.title, self.slug)

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
    argument_type = models.IntegerField(choices=((0, 'Opening argument'), (1, 'Question'), (2, 'Reply'), (3, 'Closing argument')))
    argument = models.TextField()

    def __unicode__(self):
        return self.argument


class Debate(models.Model):
    topic = models.ForeignKey(Topic)
    user1 = models.ForeignKey(auth_models.User, related_name='debate_user1_set')
    user2 = models.ForeignKey(auth_models.User, null=True, blank=True, default=None, related_name='debate_user2_set')

    invited = models.ForeignKey(auth_models.User, null=True, blank=True, default=None, related_name='debate_invited_set')

    follower = models.ManyToManyField(auth_models.User)

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
        if not user.id:
            return False

        if self.user1 == user or self.user2 == user:
            return False

        if self.user2 is None and self.invited is None:
            return True

        if self.user2 is None and self.invited == user:
            return True

        return False

    def can_send(self, user):
        """Return what type of message user can send
        None - nothing
        0 - opening
        1 - question
        2 - answer
        3 - closing
        """

        messages = self.debatemessage_set.all()

        # Assume numbers to not exceed line lengths ;P
        opening_messages = [m for m in messages if m.argument_type == 0]
        normal_messages = [m for m in messages if m.argument_type in (1, 2)]
        closing_messages = [m for m in messages if m.argument_type == 3]

        len_opening = len(opening_messages)
        len_normal = len(normal_messages)
        len_closing = len(closing_messages)

        # Users must be set, or user1 may open
        if self.user1 is None and self.user2 is None:
            return None
        elif self.user1 is not None and self.user2 is None:
            if self.user1 == user:
                if len(opening_messages) == 0:
                    return TYPE_OPEN

        # Users must be proper
        if self.user1 == user or self.user2 == user:
            if len_opening < 2:
                # User1 or User2 starts, no matter which
                if self.user1 == user:
                    if not self.user1 in [m.user for m in opening_messages]:
                        return TYPE_OPEN
                elif self.user2 == user:
                    if not self.user2 in [m.user for m in opening_messages]:
                        return TYPE_OPEN
                return None

            elif len_normal < self.msg_limit:
                # Can not present first question out of order
                if not len_normal and user != self.user1:
                    return None
                # user1 starts
                elif not len_normal and user == self.user1:
                    return TYPE_QUESTION
                elif len_normal >= 1:
                    # user1 asked and user2 replied, user2's turn
                    if normal_messages[-1].argument_type == TYPE_REPLY:
                        if normal_messages[-1].user == user:
                            return TYPE_QUESTION

                    # user2 replied, asked new question, user1's turn
                    if normal_messages[-1].argument_type == TYPE_QUESTION:
                        if normal_messages[-1].user != user:
                            return TYPE_REPLY

                return TYPE_NOTHING

            elif len_closing < 2:
                if self.user1 == user:
                    if not self.user1 in [m.user for m in closing_messages]:
                        return TYPE_CLOSING
                elif self.user2 == user:
                    if not self.user2 in [m.user for m in closing_messages]:
                        return TYPE_CLOSING

        return TYPE_NOTHING

    def is_closed(self):
        return self.debatemessage_set.count() == self.msg_limit + 2 + 2

    def is_pending(self):
        return self.user2 is None

    def invite(self, user):
        self.invited = user
        self.save()

        self.email_invite()

    def participate(self, user):
        self.user2 = user
        self.save()

        self.email_participate()

    def send(self, user, argument_type, argument):
        msg = DebateMessage()

        msg.user = user
        msg.debate = self
        msg.argument_type = argument_type
        msg.argument = argument

        msg.save()

        self.email_send(msg)

        return msg

    def get_table(self, as_text=False):
        debate_table = []

        messages = self.debatemessage_set.all().order_by('id')

        row = ['', '']
        for i in xrange(len(messages)):
            ## Set up message
            message = messages[i]
            try:
                next_message = messages[i + 1]
            except IndexError:
                next_message = None

            ## Set up row
            if message.user == self.user1:
                row_idx = 0
            else:
                row_idx = 1

            ## Where to go
            if as_text:
                row[row_idx] = message.argument
            else:
                row[row_idx] = message

            # Flush if last message
            if next_message is None:
                debate_table.append(row)
            else:
                if next_message.argument_type != message.argument_type:
                    if message.argument_type == TYPE_OPEN:
                        debate_table.append(row)
                        row = ['', '']
                        
                if message.argument_type in (TYPE_QUESTION, TYPE_REPLY):
                    debate_table.append(row)
                    row = ['', '']

        #for row in debate_table:
        #    print row
        return debate_table

    ## Email section
    def email_invite(self):
        ctx = {
            'topic': self.topic,
            'user1': self.user1,
            'uri': reverse('debate', args=(self.id, self.topic.slug)),
        }
        content = render_to_string('email/invited.txt', ctx)
        subject = '[debattikone] Kutsu: %s' % self.topic.title
        mail.send_mail(subject, content, 'debattikone@debattikone.fi', (self.invited.email,))

    def email_participate(self):
        ctx = {
            'topic': self.topic,
            'user2': self.user2,
            'uri': reverse('debate', args=(self.id, self.topic.slug)),
        }
        content = render_to_string('email/participated.txt', ctx)
        subject = '[debattikone] %s osallistui aiheeseen %s' % (self.user2.username, self.topic.title)
        mail.send_mail(subject, content, 'debattikone@debattikone.fi', (self.user1.email,))

    def email_send(self, msg):
        followers = self.follower.values('email')
        followers = [f['email'] for f in followers]

        ctx = {
            'topic': self.topic,
            'user': msg.user,
            'msg': msg,
            'uri': reverse('debate', args=(self.id, self.topic.slug)),
        }
        content = render_to_string('email/new_message.txt', ctx)
        subject = '[debattikone] %s kirjoitti aiheeseen %s' % (msg.user.username, self.topic.title)

        mail_message = mail.EmailMessage()
        mail_message.subject = subject
        mail_message.body = content

        mail_message.from_email = 'debattikone@debattikone.fi'

        # Do not mail self
        mail_message.bcc = followers
        if self.user2 is not None:
            mail_message.bcc.append(self.user2.email)

        mail_message.send()

# EOF

