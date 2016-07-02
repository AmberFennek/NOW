"""
Object

The Object is the "naked" base class for items in the game world.

Note that the default Character, Room and Exit does not inherit from
this Object, but from their respective default implementations in the
evennia library. If you want to use this class as a parent to change
the other types, you can do so by adding this as a multiple
inheritance.

"""

from evennia import DefaultObject
from evennia.utils.evmenu import get_input
from world.helpers import mass_unit
# from evennia import CmdSet
from commands.poll import PollCmdSet

from evennia.utils import lazy_property

from traits import TraitHandler
from effects import EffectHandler

class Object(DefaultObject):
    """
    This is the root typeclass object, implementing an in-game Evennia
    game object, such as having a location, being able to be
    manipulated or looked at, etc. If you create a new typeclass, it
    must always inherit from this object (or any of the other objects
    in this file, since they all actually inherit from BaseObject, as
    seen in src.object.objects).

    The BaseObject class implements several hooks tying into the game
    engine. By re-implementing these hooks you can control the
    system. You should never need to re-implement special Python
    methods, such as __init__ and especially never __getattribute__ and
    __setattr__ since these are used heavily by the typeclass system
    of Evennia and messing with them might well break things for you.


    * Base properties defined/available on all Objects

     key (string) - name of object
     name (string)- same as key
     aliases (list of strings) - aliases to the object. Will be saved to
                           database as AliasDB entries but returned as strings.
     dbref (int, read-only) - unique #id-number. Also "id" can be used.
                                  back to this class
     date_created (string) - time stamp of object creation
     permissions (list of strings) - list of permission strings

     player (Player) - controlling player (if any, only set together with
                       sessid below)
     sessid (int, read-only) - session id (if any, only set together with
                       player above). Use `sessions` handler to get the
                       Sessions directly.
     location (Object) - current location. Is None if this is a room
     home (Object) - safety start-location
     sessions (list of Sessions, read-only) - returns all sessions connected
                       to this object
     has_player (bool, read-only)- will only return *connected* players
     contents (list of Objects, read-only) - returns all objects inside this
                       object (including exits)
     exits (list of Objects, read-only) - returns all exits from this
                       object, if any
     destination (Object) - only set if this object is an exit.
     is_superuser (bool, read-only) - True/False if this user is a superuser

    * Handlers available

     locks - lock-handler: use locks.add() to add new lock strings
     db - attribute-handler: store/retrieve database attributes on this
                             self.db.myattr=val, val=self.db.myattr
     ndb - non-persistent attribute handler: same as db but does not create
                             a database entry when storing data
     scripts - script-handler. Add new scripts to object with scripts.add()
     cmdset - cmdset-handler. Use cmdset.add() to add new cmdsets to object
     nicks - nick-handler. New nicks with nicks.add().
     sessions - sessions-handler. Get Sessions connected to this
                object with sessions.get()

    * Helper methods (see src.objects.objects.py for full headers)

     search(ostring, global_search=False, attribute_name=None,
             use_nicks=False, location=None, ignore_errors=False, player=False)
     execute_cmd(raw_string)
     msg(text=None, **kwargs)
     msg_contents(message, exclude=None, from_obj=None, **kwargs)
     move_to(destination, quiet=False, emit_to_obj=None, use_destination=True)
     copy(new_key=None)
     delete()
     is_typeclass(typeclass, exact=False)
     swap_typeclass(new_typeclass, clean_attributes=False, no_default=True)
     access(accessing_obj, access_type='read', default=False)
     check_permstring(permstring)

    * Hooks (these are class methods, so args should start with self):

     basetype_setup()     - only called once, used for behind-the-scenes
                            setup. Normally not modified.
     basetype_posthook_setup() - customization in basetype, after the object
                            has been created; Normally not modified.

     at_object_creation() - only called once, when object is first created.
                            Object customizations go here.
     at_object_delete() - called just before deleting an object. If returning
                            False, deletion is aborted. Note that all objects
                            inside a deleted object are automatically moved
                            to their <home>, they don't need to be removed here.

     at_init()            - called whenever typeclass is cached from memory,
                            at least once every server restart/reload
     at_cmdset_get(**kwargs) - this is called just before the command handler
                            requests a cmdset from this object. The kwargs are
                            not normally used unless the cmdset is created
                            dynamically (see e.g. Exits).
     at_pre_puppet(player)- (player-controlled objects only) called just
                            before puppeting
     at_post_puppet()     - (player-controlled objects only) called just
                            after completing connection player<->object
     at_pre_unpuppet()    - (player-controlled objects only) called just
                            before un-puppeting
     at_post_unpuppet(player) - (player-controlled objects only) called just
                            after disconnecting player<->object link
     at_server_reload()   - called before server is reloaded
     at_server_shutdown() - called just before server is fully shut down

     at_access(result, accessing_obj, access_type) - called with the result
                            of a lock access check on this object. Return value
                            does not affect check result.

     at_before_move(destination)             - called just before moving object
                        to the destination. If returns False, move is cancelled.
     announce_move_from(destination)         - called in old location, just
                        before move, if obj.move_to() has quiet=False
     announce_move_to(source_location)       - called in new location, just
                        after move, if obj.move_to() has quiet=False
     at_after_move(source_location)          - always called after a move has
                        been successfully performed.
     at_object_leave(obj, target_location)   - called when an object leaves
                        this object in any fashion
     at_object_receive(obj, source_location) - called when this object receives
                        another object

     at_traverse(traversing_object, source_loc) - (exit-objects only)
                              handles all moving across the exit, including
                              calling the other exit hooks. Use super() to retain
                              the default functionality.
     at_after_traverse(traversing_object, source_location) - (exit-objects only)
                              called just after a traversal has happened.
     at_failed_traverse(traversing_object)      - (exit-objects only) called if
                       traversal fails and property err_traverse is not defined.

     at_msg_receive(self, msg, from_obj=None, **kwargs) - called when a message
                             (via self.msg()) is sent to this obj.
                             If returns false, aborts send.
     at_msg_send(self, msg, to_obj=None, **kwargs) - called when this objects
                             sends a message to someone via self.msg().

     return_appearance(viewer) - describes this object. Used by "look"
                                 command by default
     at_desc(viewer=None)      - called by 'look' whenever the
                                 appearance is requested.
     at_get(getter)            - called after object has been picked up.
                                 Does not stop pickup.
     at_drop(dropper)          - called when this object has been dropped.
     at_say(speaker, message)  - by default, called if an object inside this
                                 object speaks

     """

    STYLE = '|334'

    @lazy_property
    def traits(self):
        return TraitHandler(self)

    @lazy_property
    def skills(self):
        return TraitHandler(self, db_attribute='skills')

    @lazy_property
    def effects(self):
        return EffectHandler(self)

    # @lazy_property
    # def equipment(self):
    #     return EquipmentHandler(self)

    def reset(self):
        """Resets the object - quietly sends it home or nowhere."""
        self.location = self.home

    def junk(self):
        """Tags the object as junk to decay."""
        # TODO: Create a timer for final stage of decay.
        pass

    def read(self, pose, caller):
        """
        Implements the read command. This simply looks for an
        Attribute "readable_text" on the object and displays that.
        """
        readtext = self.db.readable_text
        obj_name = self.get_display_name(caller.sessions)
        if readtext:  # Attribute read_text is defined.
            string = "You read %s:\n  %s" % (obj_name, readtext)
            caller.location.msg_contents("%s |g%s|n reads %s." %
                                         (pose, caller.get_display_name(caller), obj_name))  # , exclude=caller)
        else:
            string = "There is nothing to read on %s." % obj_name
        caller.msg(string)

    def at_before_move(self, destination):
        """
        Called just before moving object - here we check to see if
        it is supporting another object that is currently in the room
        before allowing the move. If it is, we do prevent the move by
        returning False.
        """
        # When self is supporting something, do not move it.
        return False if self.attributes.has('locked') else True

    def at_get(self, caller):
        """Called after getting an object in the room."""
        caller.msg("%s is now in your posession." % self.mxp_name(caller, '@verb #%s' % self.id))

    def at_object_creation(self):
            """Called after object is created."""
            if self.tags.get('poll', category='flags'):
                self.cmdset.add('commands.poll.PollCmdSet', permanent=True)

    def drop(self, pose, caller):
        """Implements the attempt to drop this object."""
        if self.location != caller: # If caller is not holding object,
            caller.msg("You do not have %s." % self.get_display_name(caller))
            return False
        self.move_to(caller.location, quiet=True, use_destination=False)
        caller.location.msg_contents("%s |g%s|n drops %s." %
            (pose, caller.key, self.mxp_name(caller, '@verb #%s' % self.id)))
        self.at_drop(caller)  # Call at_drop() method.

    def get(self, pose, caller):
        """Implements the attempt to get this object."""
        if caller == self:
            caller.msg("You can't get yourself.")
        elif self.location == caller:
            caller.msg("You already have %s." % self.get_display_name(caller))
        elif self.move_to(caller, quiet=True):
            caller.location.msg_contents("%s |g%s|n takes %s." %
                (pose, caller.key, self.get_display_name(caller)))
            self.at_get(caller)  # calling hook method

    def surface_put(self, pose, caller, connection):
        """Implements the surface connection of object by caller."""
        if not self.attributes.has('surface'):
            self.db.surface = {}
        surface = self.db.surface
        if caller in surface:         
            return False
        surface[caller] = connection
        self.db.locked = True
        caller.db.locked = True
        caller.location.msg_contents("%s |g%s|n sits %s %s." %
                                     (pose, caller.key, connection, self.get_display_name(caller)))
        return True

    def surface_off(self, pose, caller):
        """Implements the surface disconnection of object by caller."""
        surface = self.db.surface
        if caller in surface:
            del(surface[caller])
            self.db.surface = surface
            if len(surface) < 1:
                self.attributes.remove('locked')
            caller.attributes.remove('locked')
            caller.location.msg_contents("%s |r%s|n leaves %s." %
                                         (pose, caller.key, self.mxp_name(caller, '@verb #%s' % self.id)))
            return True
        return False

    def get_display_name(self, looker, **kwargs):
        """Displays the name of the object in a viewer-aware manner."""
        if self.locks.check_lockstring(looker, "perm(Builders)"):
            return "%s%s|w(#%s)|n" % (self.STYLE, self.name, self.id)
        else:
            return "%s%s|n" % (self.STYLE, self.name)

    def mxp_name(self, viewer, command):
        """Returns the full styled and clickable-look name for the viewer's perspective as a string."""
        return "|lc%s|lt%s|le" % (command, self.get_display_name(viewer)) if viewer and \
            self.access(viewer, 'view') else ''

    def get_mass(self):
        mass = self.attributes.get('mass') or 1
        return reduce(lambda x, y: x+y.get_mass(), [mass] + self.contents)

    def return_appearance(self, viewer):
        """This formats a description. It is the hook a 'look' command
        should call.

        Args:
            viewer (Object): Object doing the looking.
        """
        if not viewer:
            return
        # get and identify all objects
        visible = (con for con in self.contents if con != viewer and con.access(viewer, "view"))
        exits, users, things = [], [], []
        for con in visible:
            if con.destination:
                exits.append(con)
            elif con.has_player:
                users.append(con)
            else:
                things.append(con)
        # get description, build string
        string = self.mxp_name(viewer, '@verb #%s' % self.id)
        string += " (%s)" % mass_unit(self.get_mass())
        if self.db.surface:
            string += " -- %s" % self.db.surface
        string += "\n"
        desc = self.db.desc
        desc_brief = self.db.desc_brief
        if desc:
            string += "%s" % desc
        elif desc_brief:
            string += "%s" % desc_brief
        else:
            string += 'A shimmering illusion shifts from form to form.'
        if exits:
            string += "\n|wExits: " + ", ".join("%s" % e.get_display_name(viewer) for e in exits)
        if users or things:
            user_list = ", ".join(u.get_display_name(viewer) for u in users)
            ut_joiner = ', ' if users and things else ''
            item_list = ", ".join(t.get_display_name(viewer) for t in things)
            string += "\n|wContains:|n " + user_list + ut_joiner + item_list
        return string

    def return_detail(self, detailkey):
        """
        This looks for an Attribute "obj_details" and possibly
        returns the value of it.

        Args:
            detailkey (str): The detail being looked at. This is
                case-insensitive.
        """
        details = self.db.details
        if details:
            return details.get(detailkey.lower(), None)

    def set_detail(self, detailkey, description):
        """
        This sets a new detail, using an Attribute "details".

        Args:
            detailkey (str): The detail identifier to add (for
                aliases you need to add multiple keys to the
                same description). Case-insensitive.
            description (str): The text to return when looking
                at the given detailkey.
        """
        if self.db.details:
            self.db.details[detailkey.lower()] = description
        else:
            self.db.details = {detailkey.lower(): description}


class Consumable(Object):  # TODO: State and analog decay. (State could be discrete analaog?)
    """
    This is the consumable typeclass object, implementing an in-game
    object, to be consumed and decay, break, be eaten, drank, cast,
    burned, or wear out slowly like clothing or furniture.
    """
    STYLE = '|321'

    def consume(self, caller):
        """
        Use health.
        """
        if self.attributes.has('health'):
            self.db.health -= 1
            if self.db.health < 1:
                self.db.health = 0
            return self.db.health

    def drink(self, caller):  # TODO: Make this use a more generic def consume
        """Response to drinking the object."""
        if not self.locks.check_lockstring(caller, 'holds()'):
            msg = "You are not holding %s." % self.get_display_name(caller.sessions)
            caller.msg(msg)
            return False
        finish = ''
        if self.attributes.has('health'):
            self.db.health -= 1
            if self.db.health < 1:
                finish = ', finishing it'
                # self.location = None # Leaves empty container.
        else:
            finish = ', finishing it'
            self.location = None
        msg = "%s takes a drink of %s%s." % (caller.get_display_name(caller.sessions),
                                             self.get_display_name(caller.sessions), finish)
        caller.location.msg_contents(msg)

        def drink_callback(caller, prompt, user_input):
            """"Response to input given after drink potion"""
            msg = "%s begins to have an effect on %s, transforming into species %s." %\
                  (self.get_display_name(caller.sessions), caller.get_display_name(caller.sessions), user_input)
            caller.location.msg_contents(msg)
            caller.db.species = user_input[0:20].strip()

        get_input(caller, "Species? (Type your species setting now, and then [enter]) ", drink_callback)

    def eat(self, caller):  # TODO: Make this use a more generic def consume
        """Response to eating the object."""
        if not self.locks.check_lockstring(caller,'holds()'):
            msg = "You are not holding %s." % self.get_display_name(caller.sessions)
            caller.msg(msg)
            return False
        finish = ''
        if self.attributes.has('health'):
            self.db.health -= 1
            if self.db.health < 1:
                finish = ', finishing it'
                self.location = None
        else:
            finish = ', finishing it'
            self.location = None
        msg = "%s takes a bite of %s%s." % (caller.get_display_name(caller.sessions),
            self.get_display_name(caller.sessions), finish)
        caller.location.msg_contents(msg)


class Tool(Consumable):
    """
    This is the Tool typeclass object, implementing an in-game
    object, to be used to craft, alter, or destroy other objects.
    """
    STYLE = '|511'

    # Currently there is nothing special about a tool compared to a Consumable.


class Dispenser(Consumable):
    """
    This is the Tool typeclass object, implementing an in-game
    object, to be used to craft, alter, or destroy other objects.
    """
    STYLE = '|350'

    def produce_weapon(self, caller):
        """
        This will produce a new weapon from the rack,
        assuming the caller hasn't already gotten one. When
        doing so, the caller will get Tagged with the id
        of this rack, to make sure they cannot keep
        pulling weapons from it indefinitely.
        """
        rack_id = self.db.rack_id
        # if caller.tags.get(rack_id, category="tutorial_world"):
        if True:
            caller.msg(self.db.no_more_weapons_msg)
        else:
            prototype = random.choice(self.db.available_weapons)
            # use the spawner to create a new Weapon from the
            # spawner dictionary, tag the caller
            wpn = spawn(WEAPON_PROTOTYPES[prototype], prototype_parents=WEAPON_PROTOTYPES)[0]
            caller.tags.add(rack_id, category='tutorial_world')
            wpn.location = caller
            caller.msg(self.db.get_weapon_msg % wpn.key)