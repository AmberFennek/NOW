# -*- coding: UTF-8 -*-
"""
Commands

Commands describe the input the player can do to the game.

"""

from evennia import Command as BaseCommand
from evennia import default_cmds


class Command(BaseCommand):
    """
    Inherit from this if you want to create your own
    command styles. Note that Evennia's default commands
    use MuxCommand instead (next in this module).

    Note that the class's `__doc__` string (this text) is
    used by Evennia to create the automatic help entry for
    the command, so make sure to document consistently here.

    Each Command implements the following methods, called
    in this order:
        - at_pre_command(): If this returns True, execution is aborted.
        - parse(): Should perform any extra parsing needed on self.args
            and store the result on self.
        - func(): Performs the actual work.
        - at_post_command(): Extra actions, often things done after
            every command, like prompts.

    """
    # these need to be specified

    key = "MyCommand"
    aliases = []
    locks = "cmd:all()"
    help_category = "General"

    # optional
    # auto_help = False      # uncomment to deactive auto-help for this command.
    # arg_regex = r"\s.*?|$" # optional regex detailing how the part after
    # the cmdname must look to match this command.

    # (we don't implement hook method access() here, you don't need to
    #  modify that unless you want to change how the lock system works
    #  (in that case see evennia.commands.command.Command))

    def at_pre_cmd(self):
        """
        This hook is called before `self.parse()` on all commands.
        """
        pass

    def parse(self):
        """
        This method is called by the `cmdhandler` once the command name
        has been identified. It creates a new set of member variables
        that can be later accessed from `self.func()` (see below).

        The following variables are available to us:
           # class variables:

           self.key - the name of this command ('mycommand')
           self.aliases - the aliases of this cmd ('mycmd','myc')
           self.locks - lock string for this command ("cmd:all()")
           self.help_category - overall category of command ("General")

           # added at run-time by `cmdhandler`:

           self.caller - the object calling this command
           self.cmdstring - the actual command name used to call this
                            (this allows you to know which alias was used,
                             for example)
           self.args - the raw input; everything following `self.cmdstring`.
           self.cmdset - the `cmdset` from which this command was picked. Not
                         often used (useful for commands like `help` or to
                         list all available commands etc).
           self.obj - the object on which this command was defined. It is often
                         the same as `self.caller`.
        """
        pass

    def func(self):
        """
        This is the hook function that actually does all the work. It is called
        by the `cmdhandler` right after `self.parser()` finishes, and so has access
        to all the variables defined therein.
        """
        self.caller.msg("Command called!")

    def at_post_cmd(self):
        """
        This hook is called after `self.func()`.
        """
        pass


class MuxCommand(default_cmds.MuxCommand):
    """
    This sets up the basis for Evennia's 'MUX-like' command style.
    The idea is that most other Mux-related commands should
    just inherit from this and don't have to implement parsing of
    their own unless they do something particularly advanced.

    A MUXCommand command understands the following possible syntax:

        name[ with several words][/switch[/switch..]] arg1[,arg2,...] [[=|,] arg[,..]]

    The `name[ with several words]` part is already dealt with by the
    `cmdhandler` at this point, and stored in `self.cmdname`. The rest is stored
    in `self.args`.

    The MuxCommand parser breaks `self.args` into its constituents and stores them
    in the following variables:
        self.switches = optional list of /switches (without the /).
        self.raw = This is the raw argument input, including switches.
        self.args = This is re-defined to be everything *except* the switches.
        self.lhs = Everything to the left of `=` (lhs:'left-hand side'). If
                     no `=` is found, this is identical to `self.args`.
        self.rhs: Everything to the right of `=` (rhs:'right-hand side').
                    If no `=` is found, this is `None`.
        self.lhslist - `self.lhs` split into a list by comma.
        self.rhslist - list of `self.rhs` split into a list by comma.
        self.arglist = list of space-separated args (including `=` if it exists).

    All args and list members are stripped of excess whitespace around the
    strings, but case is preserved.
    """

    def func(self):
        """
        This is the hook function that actually does all the work. It is called
        by the `cmdhandler` right after `self.parser()` finishes, and so has access
        to all the variables defined therein.
        """
        # this can be removed in your child class, it's just
        # printing the ingoing variables as a demo.
        super(MuxCommand, self).func()


from past.builtins import cmp
from django.conf import settings
from evennia.comms.models import ChannelDB, Msg
#from evennia.comms import irc, imc2, rss
from evennia.players.models import PlayerDB
from evennia.players import bots
from evennia.comms.channelhandler import CHANNELHANDLER
from evennia.utils import create, utils, evtable
from evennia.utils.utils import make_iter
from evennia.commands.default.muxcommand import MuxCommand, MuxPlayerCommand

_DEFAULT_WIDTH = settings.CLIENT_DEFAULT_WIDTH

class CmdChannels(MuxPlayerCommand):
    """
    list all channels available to you
    Usage:
      @chan
      @channel
      @channels
    Lists all channels available to you, whether you listen to them or not.
    Use /list to only view your current channel subscriptions.
    Use /join or /part to join or depart channels.
    """
    key = "@channel"
    aliases = ["@chan", "@channels"]
    help_category = "Communication"
    locks = "cmd: not pperm(channel_banned)"

    def func(self):
        "Implement function"

        caller = self.caller

        # all channels we have available to listen to
        channels = [chan for chan in ChannelDB.objects.get_all_channels()
                    if chan.access(caller, 'listen')]
        if not channels:
            self.msg("No channels available.")
            # Suggest use of /join switch and brief-list join-able channels.
            return
        # all channel we are already subscribed to
        subs = ChannelDB.objects.get_subscriptions(caller)

        if 'list' in self.switches:
            # just display the subscribed channels with no extra info
            comtable = evtable.EvTable("|wchannel{n", "|wmy aliases{n",
                                       "|wdescription{n", align="l", maxwidth=_DEFAULT_WIDTH)
            #comtable = prettytable.PrettyTable(["|wchannel", "|wmy aliases", "|wdescription"])
            for chan in subs:
                clower = chan.key.lower()
                nicks = caller.nicks.get(category="channel", return_obj=True)
                comtable.add_row(*["%s%s" % (chan.key, chan.aliases.all() and
                                  "(%s)" % ",".join(chan.aliases.all()) or ""),
                                  "%s" % ",".join(nick.db_key for nick in make_iter(nicks)
                                  if nick and nick.strvalue.lower() == clower),
                                  chan.db.desc])
            caller.msg("\n|wChannel subscriptions{n (use |w@channels{n to list all, "
                       "|waddcom{n/|wdelcom{n to sub/unsub):{n\n%s" % comtable)
        elif 'join' in self.switches:
            caller.msg('Join a channel or list of channels.')
        elif 'part' in self.switches:
            caller.msg('Part a channel or list of channels.')
        else:
            # full listing (of channels caller is able to listen to)
            comtable = evtable.EvTable("|wsub{n", "|wchannel{n", "|wmy aliases{n",
                                       "|wlocks{n", "|wdescription{n", maxwidth=_DEFAULT_WIDTH)
            #comtable = prettytable.PrettyTable(["|wsub", "|wchannel", "|wmy aliases", "|wlocks", "|wdescription"])
            for chan in channels:
                clower = chan.key.lower()
                nicks = caller.nicks.get(category="channel", return_obj=True)
                nicks = nicks or []
                comtable.add_row(*[chan in subs and "{gYes{n" or "{rNo{n",
                                  "%s%s" % (chan.key, chan.aliases.all() and
                                  "(%s)" % ",".join(chan.aliases.all()) or ""),
                                  "%s" % ",".join(nick.db_key for nick in make_iter(nicks)
                                  if nick.strvalue.lower() == clower),
                                  str(chan.locks),
                                  chan.db.desc])
            caller.msg("\n|wAvailable channels{n" +
                       " (use |wcomlist{n,|waddcom{n and |wdelcom{n to manage subscriptions):\n%s" % comtable)


import time
from builtins import range
from django.conf import settings
from evennia.server.sessionhandler import SESSIONS
from evennia.commands.default.muxcommand import MuxPlayerCommand
from evennia.utils import ansi, utils, create, search, prettytable


class CmdLook(MuxCommand):
    """
    look at location or object
    Usage:
      look
      look <obj>
      look *<player>
    Observes your location or objects in your vicinity.
    """
    key = "look"
    aliases = ["l", "ls"]
    locks = "cmd:all()"
    arg_regex = r"\s|$"

    def func(self):
        """
        Handle looking at objects.
        """
        if not self.args:
            target = self.caller.location
            if not target:
                self.caller.msg("You have no location to look at!")
                return
        else:
            target = self.caller.search(self.args)
            if not target:
                return
        self.msg(self.caller.at_look(target))


class CmdQuit(MuxPlayerCommand):
    """
    quit the game
    Usage:
      @quit
    Switch:
      all - disconnect all connected sessions
    Gracefully disconnect your current session from the
    game. Use the /all switch to disconnect from all sessions.
    """
    key = "@quit"
    aliases = "quit"
    locks = "cmd:all()"

    def func(self):
        "hook function"
        player = self.player
        bye = '|RDisconnecting|n'
        exit_msg = 'Hope to see you again, soon.'

        if 'all' in self.switches:
            msg = bye + ' all sessions. ' + exit_msg
            player.msg(msg, session=self.session)
            for session in player.sessions.all():
                player.disconnect_session_from_player(session)
        else:
            nsess = len(player.sessions.all())
            if nsess == 2:
                msg = bye + '. One session is still connected.'
                player.msg(msg, session=self.session)
            elif nsess > 2:
                msg = bye + ". %i sessions are still connected."
                player.msg(msg % (nsess - 1), session=self.session)
            else:
                # we are quitting the last available session
                msg = bye + '. ' + exit_msg
                player.msg(msg, session=self.session)
            player.disconnect_session_from_player(self.session)


class CmdAccess(MuxCommand):
    "Removing"

    key = ''
    locks = "cmd:not all()"

class CmdAccessnew(MuxCommand):
    """
    show your current game access
    Usage:
      @access
    This command shows you the permission hierarchy and
    which permission groups you are a member of.
    """

    key = "@access"
    locks = "cmd:all()"
    arg_regex = r"$"

    def func(self):
        "Load the permission groups"

        caller = self.caller
        hierarchy_full = settings.PERMISSION_HIERARCHY
        string = "\n|wPermission Hierarchy{n (climbing):\n %s" % ", ".join(hierarchy_full)
        #hierarchy = [p.lower() for p in hierarchy_full]

        if self.caller.player.is_superuser:
            cperms = "<Superuser>"
            pperms = "<Superuser>"
        else:
            cperms = ", ".join(caller.permissions.all())
            pperms = ", ".join(caller.player.permissions.all())

        string += "\n|wYour access{n:"
        string += "\nCharacter {c%s{n: %s" % (caller.key, cperms)
        if hasattr(caller, 'player'):
            string += "\nPlayer {c%s{n: %s" % (caller.player.key, pperms)
        caller.msg(string)


class CmdOoc(MuxCommand):
    """
    Send an out-of-character message to your current location.
    Usage:
      ooc <message>
      ooc :<message>
      ooc "<message>
    """

    key = "ooc"
    aliases = ['_']
    locks = "cmd:all()"

    def func(self):
        "Run the ooc command"

        caller = self.caller
        args = self.args.strip()

        if not args:
            caller.execute_cmd("help ooc")
            return
        elif args[0] == '"' or args[0] == "'":
            caller.execute_cmd('say/o ' + caller.location.at_say(caller, args[1:]))
        elif args[0] == ':' or args[0] == ';':
            caller.execute_cmd('pose/o %s' % args[1:])
        else:
            caller.location.msg_contents('[OOC |c%s|n] %s' % (caller.name, args))


class CmdSpoof(MuxCommand):
    """
    Send a spoofed message to your current location.
    Usage:
      spoof <message>
    """

    key = "spoof"
    aliases = ['~', '`', 'sp']
    locks = "cmd:all()"

    def func(self):
        "Run the spoof command"

        caller = self.caller

        if not self.args:
            caller.execute_cmd("help spoof")
            return

        # calling the speech hook on the location
        spoof = caller.location.at_say(caller, self.args)

        # ansi.parse_ansi(self.args, strip_ansi=nomarkup)

        # Build the string to emit
        emit_string = '|m%s|n' % spoof
        caller.location.msg_contents(emit_string)


class CmdSay(MuxCommand):
    """
    Speak as your character.
    Usage:
      say <message>
    Switch:
      /o or /ooc - Out-of-character to the room.
    """

    key = "say"
    aliases = ['"', "'"]
    locks = "cmd:all()"

    def func(self):
        "Run the say command"

        caller = self.caller

        if not self.args:
            caller.execute_cmd("help say")
            return

        speech = caller.location.at_say(caller, self.args)

        if 'o' in self.switches or 'ooc' in self.switches:
            emit_string = '[OOC]|n |c%s|n says, "%s"' % (caller.name, speech)
        else:
            emit_string = '|c%s|n says, "%s|n"' % (caller.name, speech)
        caller.location.msg_contents(emit_string)


class CmdVerb(MuxPlayerCommand):
    """
    Set a verb lock.
    Usage:
      @verb <object>
    """

    key = "@verb"
    locks = "cmd:all()"

    def func(self):
        """
        Here's where the @verbing magic happens.
        """

        my_char = self.caller.get_puppet(self.session)
        args = self.args
        if my_char and my_char.location:
            obj_list = my_char.search(args, location=[my_char, my_char.location]) if args else my_char
            if obj_list:
                obj = obj_list
                verb_msg = "Verbs of %s: " % obj_list
            else:
                obj = my_char
                verb_msg = "Verbs on you: "
            verbs = obj.locks
            collector = ''
            for verb in ("%s" % verbs).split(';'):
                element = verb.split(':')[0]
                name = element[2:] if element[:2] == 'v-' else element
                # obj lock checked against character
                if obj.access(my_char, element):
                    collector += "|g%s " % name
                else:
                    collector += "|r%s " % name
            collector = collector + '|n'
            my_char.msg(verb_msg + "%s" % collector)


class CmdWho(MuxPlayerCommand):
    """
    list who is currently online
    Usage:
      who
    Shows who is currently online. Use the /f switch to see
    character locations, and more info for those with permissions.
    """
    key = "who"
    aliases = "ws"
    locks = "cmd:all()"

    def func(self):
        """
        Get all connected players by polling session.
        """

        player = self.player
        session_list = SESSIONS.get_sessions()

        session_list = sorted(session_list, key=lambda o: o.player.key)

        if 'f' in self.switches:
            show_session_data = player.check_permstring("Immortals") or player.check_permstring("Wizards")
        else:
            show_session_data = False

        nplayers = (SESSIONS.player_count())
        if 'f' in self.switches or 'full' in self.switches:
            if show_session_data:
                # privileged info - who/f by wizard or immortal
                table = prettytable.PrettyTable(["|wPlayer Name",
                                                 "|wOn for",
                                                 "|wIdle",
                                                 "|wCharacter",
                                                 "|wRoom",
                                                 "|wCmds",
                                                 "|wProtocol",
                                                 "|wHost"])
                for session in session_list:
                    if not session.logged_in: continue
                    delta_cmd = time.time() - session.cmd_last_visible
                    delta_conn = time.time() - session.conn_time
                    player = session.get_player()
                    puppet = session.get_puppet()
                    location = puppet.location.key if puppet else "None"
                    table.add_row([utils.crop(player.name, width=25),
                                   utils.time_format(delta_conn, 0),
                                   utils.time_format(delta_cmd, 1),
                                   utils.crop(puppet.key if puppet else "None", width=25),
                                   utils.crop(location, width=25),
                                   session.cmd_total,
                                   session.protocol_key,
                                   isinstance(session.address, tuple) and session.address[0] or session.address])
            else:
                # non privileged info - who/f by player
                table = prettytable.PrettyTable(["|wCharacter", "|wOn for", "|wIdle", "|wLocation"])
                for session in session_list:
                    if not session.logged_in:
                        continue
                    delta_cmd = time.time() - session.cmd_last_visible
                    delta_conn = time.time() - session.conn_time
                    character = session.get_puppet()
                    location = character.location.key if character and character.location else "None"
                    table.add_row([utils.crop(character.key if character else "- Unknown -", width=25),
                                   utils.time_format(delta_conn, 0),
                                   utils.time_format(delta_cmd, 1),
                                   utils.crop(location, width=25)])
        else:
            if 's' in self.switches or 'species' in self.switches or self.cmdstring == 'ws':
                table = prettytable.PrettyTable(["|wCharacter", "|wOn for", "|wIdle", "|wSpecies"])
                for session in session_list:
                    character = session.get_puppet()
                    my_character = self.caller.get_puppet(self.session)
                    if not session.logged_in or character.location != my_character.location:
                        continue
                    delta_cmd = time.time() - session.cmd_last_visible
                    delta_conn = time.time() - session.conn_time
                    character = session.get_puppet()
                    species = character.attributes.get('species', default='- None -')
                    table.add_row([utils.crop(character.key if character else "- Unknown -", width=25),
                                   utils.time_format(delta_conn, 0),
                                   utils.time_format(delta_cmd, 1),
                                   utils.crop(species, width=25)])
            else:
                # unprivileged info - who
                table = prettytable.PrettyTable(["|wCharacter", "|wOn for", "|wIdle"])
                for session in session_list:
                    if not session.logged_in:
                        continue
                    delta_cmd = time.time() - session.cmd_last_visible
                    delta_conn = time.time() - session.conn_time
                    character = session.get_puppet()
                    table.add_row([utils.crop(character.key if character else "- Unknown -", width=25),
                                   utils.time_format(delta_conn, 0),
                                   utils.time_format(delta_cmd, 1)])

        isone = nplayers == 1
        string = "%s\n%s unique account%s logged in." % (table, "One" if isone else nplayers, "" if isone else "s")
        self.msg(string)


class CmdPose(MuxCommand):
    """
    Describe and/or attempt to trigger an action on an object.
    The pose text will automatically begin with your name.

    Usage:
      pose <pose text>
      pose's <pose text>

      pose <verb> <noun>:<pose text>

      try <verb> <noun>
    Switch:
      /o or /ooc - Out-of-character to the room.

    Example:
      > pose is standing by the tree, smiling.
      Rulan is standing by the tree, smiling.

      > pose get anvil::puts his back into it.
      Rulan tries to get the anvil. He puts his back into it.
      (optional success message if anvil is liftable.)

      > try unlock door
      Rulan tries to unlock the door.
      (optional success message if door is unlocked.)
    """

    key = "pose"
    aliases = [':', ';', 'emote', 'try']
    locks = "cmd:all()"

    def parse(self):
        """
        Parse the cases where the emote starts with specific characters,
        such as 's, at which we don't want to separate the character's
        name and the emote with a space.
        
        Also parse for a verb and optional noun, which if blank is assumed
        to be the character, in a power pose of the form:
        verb noun::pose
        verb::pose
        
        verb noun::
        verb::

        or using the try command, just
        verb noun
        verb
        """

        super(CmdPose, self).parse()
        args = unicode(self.args)
        caller = self.caller
        self.verb = None
        self.obj = None
        non_space_chars = ["®", "©", "°", "·", "~", "@", "-", "'", "’", ",", ";", ":", ".", "?", "!", "…"]

        if 'magnet' in self.switches or 'm' in self.switches:
            caller.msg("Pose magnet glyphs are %s." % non_space_chars)

        if self.cmdstring == 'try':
            args += '::'
        if len(args.split('::')) > 1:
            verbnoun, pose = args.split('::', 1)
            if 0 < len(verbnoun.split()) <= 2:
                args = pose
                if len(verbnoun.split()) == 2:
                    self.verb, noun = verbnoun.split()
                else:
                    self.verb = verbnoun.strip();
                    noun = 'me'
                self.obj = caller.search(noun, location=[caller, caller.location])
        if args and not args[0] in non_space_chars:
            args = " %s" % args.strip()
        self.args = args

    def func(self):
        "Hook function"

        caller = self.caller
        if self.args:
            if 'o' in self.switches or 'ooc' in self.switches:
                msg = '[OOC]|n |c%s|n%s' % (caller.name, self.args)
            else:
                msg = "|c%s|n%s" % (caller.name, self.args)
            caller.location.msg_contents(msg)

#    def at_post_command(self):
#        "Verb response here."

#        super(CmdPose, self).at_post_command()
        if self.obj:
            obj = self.obj
            verb = self.verb
            caller = self.caller
            if obj.access(caller, verb):
                if verb == 'get' or verb == 'drop':
                    caller.execute_cmd(verb + ' ' + obj.name)
                else:
                    msg = "|g%s|n is able to %s %s." % \
                          (caller.name, verb, obj.name)
                    caller.location.msg_contents(msg)
            else:
                msg = "|r%s|n fails to %s %s." % \
                      (caller.name, verb, obj.name)
                caller.location.msg_contents(msg, exclude=caller)
                caller.msg("You failed to %s %s." % (verb, obj.name))
