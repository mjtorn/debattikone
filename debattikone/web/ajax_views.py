# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from annoying.decorators import ajax_request
from annoying.functions import get_object_or_None

from debattikone.web import models

def handle_follow(request, debate_id, slug, func_name):
    debate = get_object_or_None(models.Debate, id=debate_id)

    if request.user.id is None:
        success = False
        msg = 'nologin'
    elif debate is None:
        success = False
        msg = 'notfound'
    else:
        func = getattr(debate.follower, func_name)
        func(request.user)

        success = True
        msg = 'ok'

    return {
        'success': success,
        'msg': msg,
    }
    
@ajax_request
def follow(request, debate_id, slug):
    return handle_follow(request, debate_id, slug, 'add')

@ajax_request
def unfollow(request, debate_id, slug):
    return handle_follow(request, debate_id, slug, 'delete')

@ajax_request
def participate(request, debate_id, slug):
    debate = get_object_or_None(models.Debate, id=debate_id)

    if debate is None:
        return {
            'success': False,
            'msg': 'Debattia ei löytynyt',
        }

    can_participate = debate.can_participate(request.user)
    if can_participate:
        debate.participate(request.user)
        return {
            'success': True,
            'msg': 'ok',
        }
    
    return {
        'success': False,
        'msg': 'Et voi liittyä tähän debattiin',
    }

# EOF

