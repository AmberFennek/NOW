"""
Inlinefunc

Inline functions allow for direct conversion of text users mark in a
special way. Inlinefuncs are deactivated by default. To activate, add

    INLINEFUNC_ENABLED = True

to your settings file. The default inlinefuncs are found in
evennia.utils.inlinefunc.

In text, usage is straightforward:

{funcname([arg1,arg2,...]) text {/funcname

Example 1 (using the "pad" inlinefunc):
    "This is {pad(50,c,-) a center-padded text{/pad of width 50."
    ->
    "This is -------------- a center-padded text--------------- of width 50."

Example 2 (using "pad" and "time" inlinefuncs):
    "The time is {pad(30){time(){/time{/padright now."
    ->
    "The time is         Oct 25, 11:09         right now."

To add more inline functions, add them to this module, using
the following call signature:

    def funcname(text, *args, **kwargs)

where `text` is always the part between {funcname(args) and
{/funcname and the *args are taken from the appropriate part of the
call. If no {/funcname is given, `text` will be the empty string.

It is important that the inline function properly clean the
incoming `args`, checking their type and replacing them with sane
defaults if needed. If impossible to resolve, the unmodified text
should be returned. The inlinefunc should never cause a traceback.

While the inline function should accept **kwargs, the keyword is
never accepted as a valid call - this is only intended to be used
internally by Evennia, notably to send the `session` keyword to
the function; this is the session of the object viewing the string
and can be used to customize it to each session.

"""


def capitalize(text, *args, **kwargs):
    """Capitalizes the first character of the line."""
    # session = kwargs.get('session')
    return text.capitalize()

from random import *

def usage(text, *args, **kwargs):
    """Verbally describes how busy an area is"""
    # session = kwargs.get('session')

    text = 'quiet' 
    if random() > 0.5:
        text = 'busy'
    return text


def annotate(text, *args, **kwargs):
    """session sees original, unless session is a screen reader.
    ex. $annotate(original, annotation) or
        $annotate(original) for no annotation."""
    session = kwargs.get('session')
    nargs = len(args)
    annotate = ''
    original = ''

    if nargs > 0:
        annotate = args[0]
        original = text
    return annotate if session.protocol_flags['SCREENREADER'] else original


def unicode(text, *args, **kwargs):
    """session sees original, unless session uses unicode.
    ex. $unicode(original, unicode) or
        $unicode(original) for no annotation."""
    session = kwargs.get('session')
    nargs = len(args)
    u = ''
    o = ''

    if nargs > 0:
        u = unicode(args[0])
        o = text
    return u if session.protocol_flags['ENCODING'] == 'utf-8' else o


def verb(text, *args, **kwargs):
    """Proccess verb response messages"""
    session = kwargs.get('session')
    verb = text

    return verb