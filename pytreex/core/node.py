#!/usr/bin/env python
# coding=utf-8
#
# Classes related to Treex trees & nodes
#

from __future__ import unicode_literals
from pytreex.core.exception import RuntimeException
from pytreex.core.log import log_warn
from collections import deque
import types
import re
import sys
import inspect
import unidecode
from pytreex.core.util import as_list


__author__ = "Ondřej Dušek"
__date__ = "2012"


class Node(object):
    "Representing a node in a tree (recursively)"

    __lastId = 0
    # this holds attributes used for all nodes
    # (overridden in derived classes and used from get_attr_list)
    attrib = [('alignment', types.ListType), ('wild', types.DictType)]
    # this similarly holds a list of attributes that contain references
    # (to be overridden by derived classes)
    ref_attrib = []

    def __init__(self, data=None, parent=None, zone=None):
        "Constructor, can create a tree recursively"
        # create a dummy data dictionary if None is passed
        data = data or {}
        # upper level links
        self.__zone = zone or (parent and parent.zone) or None
        self.__document = self.zone and self.zone.document or None
        self.__parent = None
        self.parent = parent
        # set all attributes belonging to the current node class
        # (replace '.' with '_')
        for attr_type, safe_attr in zip(self.get_attr_list(include_types=True),
                                        self.get_attr_list(safe=True)):
            attr, att_type = attr_type
            # initialize lists and dicts, perform simple type coercion on other
            if att_type == types.DictType:
                setattr(self, safe_attr,
                        data.get(attr) is not None and dict(data[attr]) or {})
            elif att_type == types.ListType:
                setattr(self, safe_attr,
                        data.get(attr) is not None and list(data[attr]) or [])
            elif att_type == types.BooleanType:
                # booleans need to be prepared for values such as '1' and '0'
                setattr(self, safe_attr,
                        data.get(attr) is not None and bool(int(data[attr])) or False)
            else:
                # other types (int,str): be prepared for values that evaluate
                # to false -- cannot use the and-or trick
                if data.get(attr) is not None:
                    val = att_type(data[attr])
                else:
                    val = None
                setattr(self, safe_attr, val)
        # set or generate id (will be indexed automatically; must be called
        # after attributes have been set due to references)
        self.id = data.get('id') or self.__generate_id()
        # create children (will add themselves to the list automatically)
        self.__children = []
        if ('children' in data):
            # call the right constructor for each child from data
            [self.create_child(data=child_data)
             for child_data in data['children']]

    def __generate_id(self):
        "Generate successive IDs for all nodes"
        Node.__lastId += 1
        ret = re.sub(r'^.*\.', '', self.__class__.__name__.lower()) + '-node-'
        if self.zone:
            ret += self.zone.language_and_selector + '-'
            if self.zone.bundle:
                ret += 's' + str(self.zone.bundle.ord) + '-'
        ret += 'n' + str(Node.__lastId)
        return ret

    @staticmethod
    def __safe_name(attr):
        """Return a safe version of an attribute's name
        (mangle referencing attributes)."""
        if attr.endswith('.rf'):
            return '__' + re.sub(r'\.', '_', attr)
        return attr

    def __track_backref(self, name, value):
        """Track reverse references if the given attribute contains
        references (used by set_attr)"""
        # handle alignment as a special case
        if name == 'alignment':
            old_alignment = self.get_attr('alignment')
            if old_alignment:
                for reference in old_alignment:
                    self.document.remove_backref('alignment', self.id,
                                                 reference['counterpart.rf'])
            if value:
                for reference in value:
                    self.document.index_backref('alignment', self.id,
                                                reference['counterpart.rf'])
            return
        # test if the attribute contains references
        reference = self.get_ref_attr_list(split_nested=True).get(name)
        if not reference:
            return
        # normal case: value itself is a reference
        ref_keys = [name]
        ref_values = [value]
        # special case: value is a dict containing references
        if isinstance(reference, dict):
            ref_keys = [name + '/' + key for key in value if key in reference]
            ref_values = [value[key] for key in value if key in reference]
        # track all the references
        for ref_name, ref_value in zip(ref_keys, ref_values):
            old_value = self.get_attr(ref_name)
            self.document.remove_backref(ref_name, self.id, old_value)
            self.document.index_backref(ref_name, self.id, ref_value)

    def get_attr_list(self, include_types=False, safe=False):
        """Get attributes of the current class
        (gathering all attributes of base classes)"""
        # Caching for classes
        # (since the output is always the same for the same class)
        myclass = self.__class__
        if not hasattr(myclass, '__attr_list_cache'):
            myclass.__attr_list_cache = {}
        # Not in cache -- must compute
        if not (include_types, safe) in myclass.__attr_list_cache:
            mybases = inspect.getmro(myclass)
            attrs = [attr for cls in mybases if hasattr(cls, 'attrib') for attr in cls.attrib]
            if safe:
                attrs = [(Node.__safe_name(attr), atype)
                         for attr, atype in attrs]
            if not include_types:
                attrs = [attr for attr, atype in attrs]
            myclass.__attr_list_cache[(include_types, safe)] = attrs
        # Return the result from cache
        return myclass.__attr_list_cache[(include_types, safe)]

    def get_ref_attr_list(self, split_nested=False):
        """Return a list of the attributes of the current class that
        contain references (splitting nested ones, if needed)"""
        # Caching for classes
        # (since the output is always the same for the same class)
        myclass = self.__class__
        if not hasattr(myclass, '__ref_attr_cache'):
            myclass.__ref_attr_cache = {}
        # Not in cache -- must compute
        if split_nested not in self.__class__.__ref_attr_cache:
            mybases = inspect.getmro(myclass)
            attrs = [attr for cls in mybases if hasattr(cls, 'ref_attrib') for attr in cls.ref_attrib]
            if not split_nested:
                myclass.__ref_attr_cache[split_nested] = attrs
            else:
                # unwind the attributes to a dictionary
                attr_dict = {}
                for attr in attrs:
                    # always put True value for the whole path
                    attr_dict[attr] = True
                    # for nested values, put a nested dictionary in addition
                    if '/' in attr:
                        key, val = attr.split('/', 1)
                        if not isinstance(attr_dict.get(key), dict):
                            attr_dict[key] = {}
                        attr_dict[key][val] = True
                myclass.__ref_attr_cache[split_nested] = attr_dict
        # Return the result from cache
        return myclass.__ref_attr_cache[split_nested]

    def get_attr(self, name):
        """Return the value of the given attribute.
        Allows for dictionary nesting, e.g. 'morphcat/gender'"""
        if '/' in name:
            attr, path = name.split('/', 1)
            path = path.split('/')
            obj = getattr(self, Node.__safe_name(attr))
            for step in path:
                if type(obj) != dict:
                    return None
                obj = obj.get(step)
            return obj
        else:
            return getattr(self, Node.__safe_name(name))

    def set_attr(self, name, value):
        """Set the value of the given attribute.
        Allows for dictionary nesting, e.g. 'morphcat/gender'"""
        # handle referring attributes (keep track of backwards references)
        self.__track_backref(name, value)
        # any nested attributes
        if '/' in name:
            # prepare the attribute as a dict
            attr, path = name.split('/', 1)
            path = path.split('/')
            obj = getattr(self, Node.__safe_name(attr))
            if type(obj) != dict:
                obj = {}
                setattr(self, Node.__safe_name(attr), obj)
            # build dict path up to the last level
            for step in path[:-1]:
                if step not in obj:
                    obj[step] = {}
                obj = obj[step]
            # set the value
            obj[path[-1]] = value
        # plain attributes
        else:
            setattr(self, Node.__safe_name(name), value)

    def set_deref_attr(self, name, value):
        """This assumes the value is a node/list of nodes and
        sets its id/their ids as the value of the given attribute."""
        if type(value) == list:
            self.set_attr(name, [node.id for node in value])
        else:
            self.set_attr(name, value.id)

    def get_deref_attr(self, name):
        """This assumes the given attribute holds node id(s) and
        returns the corresponding node(s)"""
        value = self.get_attr(name)
        if type(value) == list:
            return [self.document.get_node_by_id(node_id) for node_id in value]
        elif value is not None:
            return self.document.get_node_by_id(value)
        return None

    def get_referenced_ids(self):
        """Return all ids referenced by this node, keyed under
        their reference types in a hash."""
        ret = {'alignment': []}
        for align in self.alignment:
            ret['alignment'].add(align['counterpart.rf'])
        for attr in self.get_ref_attr_list():
            value = self.get_attr(attr)
            if not value:
                continue
            ret[attr] = as_list(value)
        return ret

    def get_referencing_nodes(self, attr_name):
        return [self.document.get_node_by_id(node_id)
                for node_id in self.document.get_backref(attr_name, self.id)]

    def remove_reference(self, ref_type, refd_id):
        "Remove the reference of the given type to the given node."
        # handle alignment separately
        if ref_type == 'alignment':
            refs = self.get_attr('alignment')
            self.set_attr('alignment', [ref for ref in refs if
                                        ref['counterpart.rf'] != refd_id])
        # handle plain attributes and lists
        refs = self.get_attr(ref_type)
        if isinstance(refs, list):
            self.set_attr(ref_type, [ref for ref in refs if ref != refd_id])
        else:
            self.set_attr(ref_type, None)

    def get_aligned_nodes(self):
        "Return nodes aligned to the current node."
        ret = []
        for ali in self.alignment:
            ret.append(self.document.get_node_by_id(ali['counterpart.rf']))
        return ret

    def get_descendants(self, add_self=False, ordered=False,
                        preceding_only=False, following_only=False, except_subtree=None):
        "Return all topological descendants of this node."
        if except_subtree:
            if except_subtree==self:
                return []
            nodes = [desc for child in self.__children
                     for desc in
                     child.get_descendants(add_self=True, except_subtree=except_subtree)]
        else:
            nodes = [desc for child in self.__children
                     for desc in
                     child.__descs_and_self_unsorted()]
        return self._process_switches(nodes, add_self, ordered, preceding_only, following_only)

    def get_children(self, add_self=False, ordered=False,
                     preceding_only=False, following_only=False):
        "Return all children of the node"
        return self._process_switches(list(self.__children), add_self, ordered,
                                      preceding_only, following_only)

    def __descs_and_self_unsorted(self):
        "Recursive function to return all descendants + self, in any order."
        return [self] + [desc for child in self.__children
                         for desc in child.__descs_and_self_unsorted()]

    def _process_switches(self, nodes, add_self, ordered,
                          preceding_only, following_only):
        """Process all variants on a node list:
        add self, order, filter out only preceding or only following ones."""
        if preceding_only and following_only:
            raise RuntimeException('Cannot return preceding_only ' +
                                   'and following_only nodes')
        if preceding_only or following_only:
            ordered = True
        if add_self:
            nodes.append(self)
        # filtering
        if preceding_only:
            nodes = filter(lambda node: node < self, nodes)
        elif following_only:
            nodes = filter(lambda node: node > self, nodes)
        # sorting
        if ordered:
            nodes.sort()
        return nodes

    def create_child(self, id=None, data=None):
        "Create a child of the current node"
        if id:
            data = data and data or {}
            data['id'] = id
        return getattr(sys.modules[__name__],
                       self.__class__.__name__)(data=data, parent=self)

    def remove(self, fix_order=True):
        "Remove the node from the tree."
        root = self.root # backup, self.root will not be reliable (why?)
        for child in self.get_children():
            child.remove(fix_order=False)
        self.parent = None
        self.document.remove_node(self.id)

        # We need to normalize ordering, so there are no gaps
        if fix_order and isinstance(self, Ordered):
            for new_ord, node in enumerate(root.get_descendants(add_self=True, ordered=True)):
                node.ord = new_ord

    def is_descendant_of(self, another_node):
        "Is this node a descendant of another node?"
        ancestor = self.parent
        while ancestor is not None:
            if ancestor is another_node:
                return True;
            ancestor = ancestor.parent
        return False;

    @property
    def root(self):
        "The root of the tree this node is in."
        return self.__root

    @property
    def document(self):
        "The document this node is a member of."
        return self.__document

    @property
    def parent(self):
        "The parent of the current node. None for roots."
        return self.__parent

    @parent.setter
    def parent(self, value):
        "Change the parent of the current node."
        if value is not None:
            if self.__document != value.__document:
                raise RuntimeException('Cannot move nodes across documents.')
            if (value.is_descendant_of(self) or value is self):
                raise RuntimeException('Attempt to create cycle with nodeA.parent = descendant_of_nodeA.')
        # filter original parent's children
        if self.__parent:
            self.__parent.__children = [child for child
                                        in self.__parent.__children
                                        if child != self]
        # set new parent and update its children, set new root
        self.__parent = value
        if self.__parent:
            self.__parent.__children.append(self)
            self.__root = self.__parent.__root
        else:
            self.__root = self

    def get_depth(self):
        "Return the depth, i.e. the distance to the root."
        node = self
        depth = 0
        while not node.is_root:
            node = node.parent
            depth += 1
        return depth

    @property
    def id(self):
        "The unique id of the node within the document."
        return self.__id

    @id.setter
    def id(self, value):
        self.__id = value
        if self.__document:
            self.__document.index_node(self)

    @property
    def zone(self):
        "The zone this node belongs to."
        return self.__zone

    @property
    def is_root(self):
        """Return true if this node is a root"""
        return self.parent is None

    def __eq__(self, other):
        "Node comparison by id"
        return other is not None and self.id == other.id

    def __ne__(self, other):
        "Node comparison by id"
        return other is None or self.id != other.id

    def __lt__(self, other):
        "Node ordering is only implemented in Ordered"
        if not isinstance(self, Ordered) or not isinstance(other, Ordered):
            return NotImplemented
        return Ordered.__lt__(self, other)

    def __gt__(self, other):
        "Node ordering is only implemented in Ordered"
        if not isinstance(self, Ordered) or not isinstance(other, Ordered):
            return NotImplemented
        return Ordered.__gt__(self, other)

    def __le__(self, other):
        "Node ordering is only implemented in Ordered"
        if not isinstance(self, Ordered) or not isinstance(other, Ordered):
            return NotImplemented
        return Ordered.__le__(self, other)

    def __ge__(self, other):
        "Node ordering is only implemented in Ordered"
        if not isinstance(self, Ordered) or not isinstance(other, Ordered):
            return NotImplemented
        return Ordered.__ge__(self, other)


class Ordered(object):
    """\
    Representing an ordered node (has an attribute called ord),
    defines sorting.
    """

    attrib = [('ord', types.IntType)]
    ref_attrib = []

    def __lt__(self, other):
        return self.ord < other.ord

    def __gt__(self, other):
        return self.ord > other.ord

    def __le__(self, other):
        return self.ord <= other.ord

    def __ge__(self, other):
        return self.ord >= other.ord

    def shift_after_node(self, other, without_children=False):
        "Shift one node after another in the ordering."
        self.__shift_to_node(other, after=True, without_children=without_children)

    def shift_before_node(self, other, without_children=False):
        "Shift one node before another in the ordering."
        self.__shift_to_node(other, after=False, without_children=without_children)

    def shift_before_subtree(self, other, without_children=False):
        """\
        Shift one node before the whole subtree of another node
        in the ordering.
        """
        subtree = other.get_descendants(ordered=True, add_self=True, except_subtree=self)
        if len(subtree) <= 1 and self == other:
            return  # no point if self==other and there are no children
        self.__shift_to_node(subtree[0] == self and subtree[1] or subtree[0],
                             after=False, without_children=without_children)

    def shift_after_subtree(self, other, without_children=False):
        """\
        Shift one node after the whole subtree of another node in the ordering.
        """
        subtree = other.get_descendants(ordered=True, add_self=True, except_subtree=self)
        if len(subtree) <= 1 and self == other:
            return   # no point if self==other and there are no children
        self.__shift_to_node(subtree[-1] == self and subtree[-2] or subtree[-1],
                             after=True, without_children=without_children)

    def __shift_to_node(self, other, after, without_children=False):
        "Shift a node before or after another node in the ordering"
        if not without_children and other.is_descendant_of(self):
            raise RuntimeException('{} is a descendant of {}. Maybe you have forgotten without_children=True.'.format(other.id, self.id))
        all_nodes = self.root.get_descendants(ordered=True, add_self=True)
        # determine what's being moved
        to_move = [self] if without_children else self.get_descendants(ordered=True, add_self=True)
        moving = set(to_move)
        # do the moving
        cur_ord = 0
        for node in all_nodes:
            # skip nodes moved, handle them when we're at the reference node
            if node in moving:
                continue
            if after:
                node.ord = cur_ord
                cur_ord += 1
            # we're at the target node, move all needed
            if node == other:
                for moving_node in to_move:
                    moving_node.ord = cur_ord
                    cur_ord += 1
            if not after:
                node.ord = cur_ord
                cur_ord += 1

    def get_next_node(self):
        "Get the following node in the ordering."
        my_ord = self.ord
        next_ord, next_node = (None, None)
        for node in self.root.get_descendants():
            cur_ord = node.ord
            if cur_ord <= my_ord:
                continue
            if next_ord is not None and cur_ord > next_ord:
                continue
            next_ord, next_node = (cur_ord, node)
        return next_node

    def get_prev_node(self):
        "Get the preceding node in the ordering."
        my_ord = self.ord
        prev_ord, prev_node = (None, None)
        for node in self.root.get_descendants():
            cur_ord = node.ord
            if cur_ord >= my_ord:
                continue
            if prev_ord is not None and cur_ord < prev_ord:
                continue
            prev_ord, prev_node = (cur_ord, node)
        return prev_node

    def is_first_node(self):
        """\
        Return True if this node is the first node in the tree,
        i.e. has no previous nodes.
        """
        prev_node = self.get_prev_node()
        return prev_node is None

    def is_last_node(self):
        """\
        Return True if this node is the last node in the tree,
        i.e. has no following nodes.
        """
        next_node = self.get_next_node()
        return next_node is None

    @property
    def is_right_child(self):
        """Return True if this node has a greater ord than its parent. Returns None for a root."""
        if self.parent is None:
            return None
        return self.parent.ord < self.ord


class EffectiveRelations(object):
    "Representing a node with effective relations"

    attrib = [('is_member', types.BooleanType)]
    ref_attrib = []

    def is_coap_root(self):
        """\
        Testing whether the node is a coordination/apposition root.
        Must be implemented in descendants.
        """
        raise NotImplementedError

    # TODO: dive ~ subroutine / auxcp
    def get_echildren(self, or_topological=False,
                      add_self=False, ordered=False,
                      preceding_only=False, following_only=False):
        "Return the effective children of the current node."
        # test if we can get e-children
        if not self.__can_apply_eff(or_topological):
            return self.get_children(add_self, ordered,
                                     preceding_only, following_only)
        # my own effective children
        # (I am their only parent) & shared effective children
        echildren = self.__get_my_own_echildren() + self.__get_shared_echildren()
        # final filtering
        return self._process_switches(echildren, add_self, ordered,
                                      preceding_only, following_only)

    def __can_apply_eff(self, or_topological):
        """Return true if the given node is OK for effective relations
        to be applied, false otherwise."""
        if self.is_coap_root():
            caller_name = inspect.stack()[1][3]
            message = caller_name + ' called on coap_root (' + self.id + ').'
            if or_topological:
                return False
            else:
                # this should not happen, so warn about it
                log_warn(message + ' Fallback to topological.')
                return False
        return True

    def __get_my_own_echildren(self):
        "Return the e-children of which this node is the only parent."
        echildren = []
        for node in self.get_children():
            if node.is_coap_root():
                echildren.extend(node.get_coap_members())
            else:
                echildren.append(node)
        return echildren

    def __get_shared_echildren(self):
        "Return e-children this node shares with other node(s)"
        coap_root = self.__get_direct_coap_root()
        if not coap_root:
            return []
        echildren = []
        while coap_root:
            # add all shared children and go upwards
            echildren += [coap_member for node in coap_root.get_children()
                          if not node.is_member
                          for coap_member in node.get_coap_members()]
            coap_root = coap_root.__get_direct_coap_root()
        return echildren

    def __get_direct_coap_root(self):
        "Return the direct coap root."
        if self.is_member:
            return self.parent
        return None

    def get_coap_members(self):
        """Return the members of the coordination, if the node is a coap root.
        Otherwise return the node itself."""
        if not self.is_coap_root():
            return [self]
        queue = deque(filter(lambda node: node.is_member, self.get_children()))
        members = []
        while queue:
            node = queue.popleft()
            if node.is_coap_root():
                queue.extend(filter(lambda node: node.is_member,
                                    node.get_children()))
            else:
                members.append(node)
        return members

    def get_eparents(self, or_topological=False,
                     add_self=False, ordered=False,
                     preceding_only=False, following_only=False):
        "Return the effective parents of the current node."
        # test if we can get e-parents
        if not self.__can_apply_eff(or_topological):
            return [self.parent]
        return self._process_switches(self.__get_eparents(), add_self,
                                      ordered, preceding_only, following_only)

    def __get_eparents(self):
        if not self.parent:
            log_warn("Cannot find parents, using the root: " + self.id)
            return [self.root]
        # try getting coap root, if applicable
        node = self.__get_transitive_coap_root() or self
        # continue to parent
        node = node.parent
        if not node:
            return [self.__fallback_parent()]
        # if we are not in coap, return just the one node
        if not node.is_coap_root:
            return [node]
        # we are in a coap -> return members
        eff = node.get_coap_members()
        if eff:
            return eff
        return [self.__fallback_parent()]

    def __get_transitive_coap_root(self):
        "Climb up a nested coap structure and return its root."
        root = self.__get_direct_coap_root()
        if not root:
            return None
        while root.is_member:
            root = root.__get_direct_coap_root()
            if not root:
                return None
        return root

    def __fallback_parent(self):
        "Issue a warning and return the topological parent."
        log_warn("No effective parent, using topological: " + self.id)
        return self.parent


class InClause(object):
    "Represents nodes that are organized in clauses"

    attrib = [('clause_number', types.IntType),
              ('is_clause_head', types.BooleanType)]
    ref_attrib = []

    def get_clause_root(self):
        "Return the root of the clause the current node resides in."
        # default to self if clause number is not defined
        if self.clause_number is None:
            log_warn('Clause number undefined in: ' + self.id)
            return self
        highest = self
        parent = self.parent
        # move as high as possible within the clause
        while parent and parent.clause_number == self.clause_number:
            highest = parent
            parent = parent.parent
        # handle coordinations - shared attributes
        if parent and parent.is_coap_root() and not highest.is_member:
            try:
                eff_parent = next(child for child in parent.get_children()
                                  if child.is_member and
                                  child.clause_number == self.clause_number)
                return eff_parent
            except StopIteration:  # no eff_parent found
                pass
        return highest


class T(Node, Ordered, EffectiveRelations, InClause):
    "Representing a t-node"

    attrib = [('functor', types.UnicodeType), ('formeme', types.UnicodeType),
              ('t_lemma', types.UnicodeType), ('nodetype', types.UnicodeType),
              ('subfunctor', types.UnicodeType), ('tfa', types.UnicodeType),
              ('is_dsp_root', types.BooleanType), ('gram', types.DictType),
              ('a', types.DictType), ('compl.rf', types.ListType),
              ('coref_gram.rf', types.ListType),
              ('coref_text.rf', types.ListType),
              ('sentmod', types.UnicodeType),
              ('is_parenthesis', types.BooleanType),
              ('is_passive', types.BooleanType),
              ('is_generated', types.BooleanType),
              ('is_relclause_head', types.BooleanType),
              ('is_name_of_person', types.BooleanType),
              ('voice', types.UnicodeType), ('mlayer_pos', types.UnicodeType),
              ('t_lemma_origin', types.UnicodeType),
              ('formeme_origin', types.UnicodeType),
              ('is_infin', types.BooleanType),
              ('is_reflexive', types.BooleanType)]
    ref_attrib = ['a/lex.rf', 'a/aux.rf', 'compl.rf', 'coref_gram.rf',
                  'coref_text.rf']

    def __init__(self, data=None, parent=None, zone=None):
        "Constructor"
        Node.__init__(self, data, parent, zone)

    def is_coap_root(self):
        functor = self.functor or None
        return functor in ['CONJ', 'CONFR', 'DISJ', 'GRAD', 'ADVS', 'CSQ',
                           'REAS', 'CONTRA', 'APPS', 'OPER']

    @property
    def lex_anode(self):
        return self.get_deref_attr('a/lex.rf')

    @lex_anode.setter
    def lex_anode(self, value):
        self.set_deref_attr('a/lex.rf', value)

    @property
    # TODO think of a better way (make node.aux_anodes.append(node2) possible?)
    def aux_anodes(self):
        return self.get_deref_attr('a/aux.rf')

    @aux_anodes.setter
    def aux_anodes(self, value):
        self.set_deref_attr('a/aux.rf', value)

    @property
    def anodes(self):
        "Return all anodes of a t-node"
        return (self.lex_anode and [self.lex_anode] or []) + \
               (self.aux_anodes or [])

    def add_aux_anodes(self, new_anodes):
        "Add an auxiliary a-node/a-nodes to the list."
        # get the original anodes and set the union
        if self.aux_anodes:
            self.aux_anodes = self.aux_anodes + as_list(new_anodes)
        else:
            self.aux_anodes = as_list(new_anodes)

    def remove_aux_anodes(self, to_remove):
        "Remove an auxiliary a-node from the list"
        self.aux_anodes = [anode for anode in self.aux_anodes
                           if anode not in to_remove]
        if not self.aux_anodes:
            self.aux_anodes = None

    @property
    def coref_gram_nodes(self):
        return self.get_deref_attr('coref_gram.rf')

    @coref_gram_nodes.setter
    def coref_gram_nodes(self, new_coref):
        self.set_deref_attr('coref_gram.rf', new_coref)

    @property
    def coref_text_nodes(self):
        return self.get_deref_attr('coref_text.rf')

    @coref_text_nodes.setter
    def coref_text_nodes(self, new_coref):
        self.set_deref_attr('coref_text.rf', new_coref)

    @property
    def compl_nodes(self):
        return self.get_deref_attr('compl.rf')

    @compl_nodes.setter
    def compl_nodes(self, new_coref):
        self.set_deref_attr('compl.rf', new_coref)

    @property
    def gram_number(self):
        return self.get_attr('gram/number')

    @gram_number.setter
    def gram_number(self, value):
        self.set_attr('gram/number', value)

    @property
    def gram_gender(self):
        return self.get_attr('gram/gender')

    @gram_gender.setter
    def gram_gender(self, value):
        self.set_attr('gram/gender', value)

    @property
    def gram_tense(self):
        return self.get_attr('gram/tense')

    @gram_tense.setter
    def gram_tense(self, value):
        self.set_attr('gram/tense', value)

    @property
    def gram_negation(self):
        return self.get_attr('gram/negation')

    @gram_negation.setter
    def gram_negation(self, value):
        self.set_attr('gram/negation', value)

    @property
    def gram_aspect(self):
        return self.get_attr('gram/aspect')

    @gram_aspect.setter
    def gram_aspect(self, value):
        self.set_attr('gram/aspect', value)

    @property
    def gram_degcmp(self):
        return self.get_attr('gram/degcmp')

    @gram_degcmp.setter
    def gram_degcmp(self, value):
        self.set_attr('gram/degcmp', value)

    @property
    def gram_deontmod(self):
        return self.get_attr('gram/deontmod')

    @gram_deontmod.setter
    def gram_deontmod(self, value):
        self.set_attr('gram/deontmod', value)

    @property
    def gram_dispmod(self):
        return self.get_attr('gram/dispmod')

    @gram_dispmod.setter
    def gram_dispmod(self, value):
        self.set_attr('gram/dispmod', value)

    @property
    def gram_indeftype(self):
        return self.get_attr('gram/indeftype')

    @gram_indeftype.setter
    def gram_indeftype(self, value):
        self.set_attr('gram/indeftype', value)

    @property
    def gram_iterativeness(self):
        return self.get_attr('gram/iterativeness')

    @gram_iterativeness.setter
    def gram_iterativeness(self, value):
        self.set_attr('gram/iterativeness', value)

    @property
    def gram_numertype(self):
        return self.get_attr('gram/numertype')

    @gram_numertype.setter
    def gram_numertype(self, value):
        self.set_attr('gram/numertype', value)

    @property
    def gram_person(self):
        return self.get_attr('gram/person')

    @gram_person.setter
    def gram_person(self, value):
        self.set_attr('gram/person', value)

    @property
    def gram_politeness(self):
        return self.get_attr('gram/politeness')

    @gram_politeness.setter
    def gram_politeness(self, value):
        self.set_attr('gram/politeness', value)

    @property
    def gram_resultative(self):
        return self.get_attr('gram/resultative')

    @gram_resultative.setter
    def gram_resultative(self, value):
        self.set_attr('gram/resultative', value)

    @property
    def gram_verbmod(self):
        return self.get_attr('gram/verbmod')

    @gram_verbmod.setter
    def gram_verbmod(self, value):
        self.set_attr('gram/verbmod', value)

    @property
    def gram_sempos(self):
        return self.get_attr('gram/sempos')

    @gram_sempos.setter
    def gram_sempos(self, value):
        self.set_attr('gram/sempos', value)

    @property
    def gram_diathesis(self):
        return self.get_attr('gram/diathesis')

    @gram_diathesis.setter
    def gram_diathesis(self, value):
        self.set_attr('gram/diathesis', value)

    def __eq__(self, other):
        """Equality based on memory reference, IDs, and finally hashes.
        TODO evaluate thoroughly"""
        if self is other:  # same object (address)
            return True
        if self.id and other.id and self.id == other.id:  # same IDs
            return True
        return hash(self) == hash(other)  # same tree under different/no ID

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        """Return hash of the tree that is composed of t-lemmas, formemes,
        and parent orders of all nodes in the tree (ordered)."""
        return hash(unicode(self))

    def __unicode__(self):
        desc = self.get_descendants(add_self=1, ordered=1)
        return ' '.join(['%d|%d|%s|%s' % (n.ord if n.ord is not None else -1,
                                          n.parent.ord if n.parent else -1,
                                          n.t_lemma,
                                          n.formeme)
                         for n in desc])

    def __str__(self):
        return unicode(self).encode('UTF-8', 'replace')


class A(Node, Ordered, EffectiveRelations, InClause):
    "Representing an a-node"

    attrib = [('form', types.UnicodeType), ('lemma', types.UnicodeType),
              ('tag', types.UnicodeType), ('afun', types.UnicodeType),
              ('no_space_after', types.BooleanType),
              ('morphcat', types.DictType),
              ('is_parenthesis_root', types.BooleanType),
              ('edge_to_collapse', types.BooleanType),
              ('is_auxiliary', types.BooleanType),
              ('p_terminal.rf', types.UnicodeType),
              ('upos', types.UnicodeType), ('xpos', types.UnicodeType),
              ('feats', types.UnicodeType), ('deprel', types.UnicodeType),
              ('deps', types.UnicodeType), ('misc', types.UnicodeType),
              ]
    ref_attrib = ['p_terminal.rf']

    morphcat_members = ['pos', 'subpos', 'gender', 'number', 'case', 'person',
                        'tense', 'negation', 'voice', 'grade', 'mood',
                        'possnumber', 'possgender']

    def __init__(self, data=None, parent=None, zone=None):
        "Constructor"
        Node.__init__(self, data, parent, zone)

    def is_coap_root(self):
        afun = self.afun or None
        return afun in ['Coord', 'Apos']

    def reset_morphcat(self):
        "Reset the morphcat structure members to '.'"
        for category in A.morphcat_members:
            self.set_attr('morphcat/' + category, '.')

    @property
    def morphcat_pos(self):
        return self.get_attr('morphcat/pos')

    @morphcat_pos.setter
    def morphcat_pos(self, value):
        self.set_attr('morphcat/pos', value)

    @property
    def morphcat_subpos(self):
        return self.get_attr('morphcat/subpos')

    @morphcat_subpos.setter
    def morphcat_subpos(self, value):
        self.set_attr('morphcat/subpos', value)

    @property
    def morphcat_gender(self):
        return self.get_attr('morphcat/gender')

    @morphcat_gender.setter
    def morphcat_gender(self, value):
        self.set_attr('morphcat/gender', value)

    @property
    def morphcat_number(self):
        return self.get_attr('morphcat/number')

    @morphcat_number.setter
    def morphcat_number(self, value):
        self.set_attr('morphcat/number', value)

    @property
    def morphcat_case(self):
        return self.get_attr('morphcat/case')

    @morphcat_case.setter
    def morphcat_case(self, value):
        self.set_attr('morphcat/case', value)

    @property
    def morphcat_person(self):
        return self.get_attr('morphcat/person')

    @morphcat_person.setter
    def morphcat_person(self, value):
        self.set_attr('morphcat/person', value)

    @property
    def morphcat_tense(self):
        return self.get_attr('morphcat/tense')

    @morphcat_tense.setter
    def morphcat_tense(self, value):
        self.set_attr('morphcat/tense', value)

    @property
    def morphcat_negation(self):
        return self.get_attr('morphcat/negation')

    @morphcat_negation.setter
    def morphcat_negation(self, value):
        self.set_attr('morphcat/negation', value)

    @property
    def morphcat_voice(self):
        return self.get_attr('morphcat/voice')

    @morphcat_voice.setter
    def morphcat_voice(self, value):
        self.set_attr('morphcat/voice', value)

    @property
    def morphcat_grade(self):
        return self.get_attr('morphcat/grade')

    @morphcat_grade.setter
    def morphcat_grade(self, value):
        self.set_attr('morphcat/grade', value)

    @property
    def morphcat_mood(self):
        return self.get_attr('morphcat/mood')

    @morphcat_mood.setter
    def morphcat_mood(self, value):
        self.set_attr('morphcat/mood', value)

    @property
    def morphcat_possnumber(self):
        return self.get_attr('morphcat/possnumber')

    @morphcat_possnumber.setter
    def morphcat_possnumber(self, value):
        self.set_attr('morphcat/possnumber', value)

    @property
    def morphcat_possgender(self):
        return self.get_attr('morphcat/possgender')

    @morphcat_possgender.setter
    def morphcat_possgender(self, value):
        self.set_attr('morphcat/possgender', value)

    @property
    def iset_pos(self):
        val = self.get_attr('iset/pos')
        return val if val is not None else ''

    @iset_pos.setter
    def iset_pos(self, value):
        self.set_attr('iset/pos', value)

    @property
    def iset_nountype(self):
        val = self.get_attr('iset/nountype')
        return val if val is not None else ''

    @iset_nountype.setter
    def iset_nountype(self, value):
        self.set_attr('iset/nountype', value)

    @property
    def iset_nametype(self):
        val = self.get_attr('iset/nametype')
        return val if val is not None else ''

    @iset_nametype.setter
    def iset_nametype(self, value):
        self.set_attr('iset/nametype', value)

    @property
    def iset_adjtype(self):
        val = self.get_attr('iset/adjtype')
        return val if val is not None else ''

    @iset_adjtype.setter
    def iset_adjtype(self, value):
        self.set_attr('iset/adjtype', value)

    @property
    def iset_prontype(self):
        val = self.get_attr('iset/prontype')
        return val if val is not None else ''

    @iset_prontype.setter
    def iset_prontype(self, value):
        self.set_attr('iset/prontype', value)

    @property
    def iset_numtype(self):
        val = self.get_attr('iset/numtype')
        return val if val is not None else ''

    @iset_numtype.setter
    def iset_numtype(self, value):
        self.set_attr('iset/numtype', value)

    @property
    def iset_numform(self):
        val = self.get_attr('iset/numform')
        return val if val is not None else ''

    @iset_numform.setter
    def iset_numform(self, value):
        self.set_attr('iset/numform', value)

    @property
    def iset_numvalue(self):
        val = self.get_attr('iset/numvalue')
        return val if val is not None else ''

    @iset_numvalue.setter
    def iset_numvalue(self, value):
        self.set_attr('iset/numvalue', value)

    @property
    def iset_accommodability(self):
        val = self.get_attr('iset/accommodability')
        return val if val is not None else ''

    @iset_accommodability.setter
    def iset_accommodability(self, value):
        self.set_attr('iset/accommodability', value)

    @property
    def iset_verbtype(self):
        val = self.get_attr('iset/verbtype')
        return val if val is not None else ''

    @iset_verbtype.setter
    def iset_verbtype(self, value):
        self.set_attr('iset/verbtype', value)

    @property
    def iset_advtype(self):
        val = self.get_attr('iset/advtype')
        return val if val is not None else ''

    @iset_advtype.setter
    def iset_advtype(self, value):
        self.set_attr('iset/advtype', value)

    @property
    def iset_adpostype(self):
        val = self.get_attr('iset/adpostype')
        return val if val is not None else ''

    @iset_adpostype.setter
    def iset_adpostype(self, value):
        self.set_attr('iset/adpostype', value)

    @property
    def iset_conjtype(self):
        val = self.get_attr('iset/conjtype')
        return val if val is not None else ''

    @iset_conjtype.setter
    def iset_conjtype(self, value):
        self.set_attr('iset/conjtype', value)

    @property
    def iset_parttype(self):
        val = self.get_attr('iset/parttype')
        return val if val is not None else ''

    @iset_parttype.setter
    def iset_parttype(self, value):
        self.set_attr('iset/parttype', value)

    @property
    def iset_punctype(self):
        val = self.get_attr('iset/punctype')
        return val if val is not None else ''

    @iset_punctype.setter
    def iset_punctype(self, value):
        self.set_attr('iset/punctype', value)

    @property
    def iset_puncside(self):
        val = self.get_attr('iset/puncside')
        return val if val is not None else ''

    @iset_puncside.setter
    def iset_puncside(self, value):
        self.set_attr('iset/puncside', value)

    @property
    def iset_synpos(self):
        val = self.get_attr('iset/synpos')
        return val if val is not None else ''

    @iset_synpos.setter
    def iset_synpos(self, value):
        self.set_attr('iset/synpos', value)

    @property
    def iset_morphpos(self):
        val = self.get_attr('iset/morphpos')
        return val if val is not None else ''

    @iset_morphpos.setter
    def iset_morphpos(self, value):
        self.set_attr('iset/morphpos', value)

    @property
    def iset_poss(self):
        val = self.get_attr('iset/poss')
        return val if val is not None else ''

    @iset_poss.setter
    def iset_poss(self, value):
        self.set_attr('iset/poss', value)

    @property
    def iset_reflex(self):
        val = self.get_attr('iset/reflex')
        return val if val is not None else ''

    @iset_reflex.setter
    def iset_reflex(self, value):
        self.set_attr('iset/reflex', value)

    @property
    def iset_negativeness(self):
        val = self.get_attr('iset/negativeness')
        return val if val is not None else ''

    @iset_negativeness.setter
    def iset_negativeness(self, value):
        self.set_attr('iset/negativeness', value)

    @property
    def iset_definiteness(self):
        val = self.get_attr('iset/definiteness')
        return val if val is not None else ''

    @iset_definiteness.setter
    def iset_definiteness(self, value):
        self.set_attr('iset/definiteness', value)

    @property
    def iset_foreign(self):
        val = self.get_attr('iset/foreign')
        return val if val is not None else ''

    @iset_foreign.setter
    def iset_foreign(self, value):
        self.set_attr('iset/foreign', value)

    @property
    def iset_gender(self):
        val = self.get_attr('iset/gender')
        return val if val is not None else ''

    @iset_gender.setter
    def iset_gender(self, value):
        self.set_attr('iset/gender', value)

    @property
    def iset_possgender(self):
        val = self.get_attr('iset/possgender')
        return val if val is not None else ''

    @iset_possgender.setter
    def iset_possgender(self, value):
        self.set_attr('iset/possgender', value)

    @property
    def iset_animateness(self):
        val = self.get_attr('iset/animateness')
        return val if val is not None else ''

    @iset_animateness.setter
    def iset_animateness(self, value):
        self.set_attr('iset/animateness', value)

    @property
    def iset_number(self):
        val = self.get_attr('iset/number')
        return val if val is not None else ''

    @iset_number.setter
    def iset_number(self, value):
        self.set_attr('iset/number', value)

    @property
    def iset_possnumber(self):
        val = self.get_attr('iset/possnumber')
        return val if val is not None else ''

    @iset_possnumber.setter
    def iset_possnumber(self, value):
        self.set_attr('iset/possnumber', value)

    @property
    def iset_possednumber(self):
        val = self.get_attr('iset/possednumber')
        return val if val is not None else ''

    @iset_possednumber.setter
    def iset_possednumber(self, value):
        self.set_attr('iset/possednumber', value)

    @property
    def iset_case(self):
        val = self.get_attr('iset/case')
        return val if val is not None else ''

    @iset_case.setter
    def iset_case(self, value):
        self.set_attr('iset/case', value)

    @property
    def iset_prepcase(self):
        val = self.get_attr('iset/prepcase')
        return val if val is not None else ''

    @iset_prepcase.setter
    def iset_prepcase(self, value):
        self.set_attr('iset/prepcase', value)

    @property
    def iset_degree(self):
        val = self.get_attr('iset/degree')
        return val if val is not None else ''

    @iset_degree.setter
    def iset_degree(self, value):
        self.set_attr('iset/degree', value)

    @property
    def iset_person(self):
        val = self.get_attr('iset/person')
        return val if val is not None else ''

    @iset_person.setter
    def iset_person(self, value):
        self.set_attr('iset/person', value)

    @property
    def iset_possperson(self):
        val = self.get_attr('iset/possperson')
        return val if val is not None else ''

    @iset_possperson.setter
    def iset_possperson(self, value):
        self.set_attr('iset/possperson', value)

    @property
    def iset_politeness(self):
        val = self.get_attr('iset/politeness')
        return val if val is not None else ''

    @iset_politeness.setter
    def iset_politeness(self, value):
        self.set_attr('iset/politeness', value)

    @property
    def iset_position(self):
        val = self.get_attr('iset/position')
        return val if val is not None else ''

    @iset_position.setter
    def iset_position(self, value):
        self.set_attr('iset/position', value)

    @property
    def iset_subcat(self):
        val = self.get_attr('iset/subcat')
        return val if val is not None else ''

    @iset_subcat.setter
    def iset_subcat(self, value):
        self.set_attr('iset/subcat', value)

    @property
    def iset_verbform(self):
        val = self.get_attr('iset/verbform')
        return val if val is not None else ''

    @iset_verbform.setter
    def iset_verbform(self, value):
        self.set_attr('iset/verbform', value)

    @property
    def iset_mood(self):
        val = self.get_attr('iset/mood')
        return val if val is not None else ''

    @iset_mood.setter
    def iset_mood(self, value):
        self.set_attr('iset/mood', value)

    @property
    def iset_tense(self):
        val = self.get_attr('iset/tense')
        return val if val is not None else ''

    @iset_tense.setter
    def iset_tense(self, value):
        self.set_attr('iset/tense', value)

    @property
    def iset_aspect(self):
        val = self.get_attr('iset/aspect')
        return val if val is not None else ''

    @iset_aspect.setter
    def iset_aspect(self, value):
        self.set_attr('iset/aspect', value)

    @property
    def iset_voice(self):
        val = self.get_attr('iset/voice')
        return val if val is not None else ''

    @iset_voice.setter
    def iset_voice(self, value):
        self.set_attr('iset/voice', value)

    @property
    def iset_abbr(self):
        val = self.get_attr('iset/abbr')
        return val if val is not None else ''

    @iset_abbr.setter
    def iset_abbr(self, value):
        self.set_attr('iset/abbr', value)

    @property
    def iset_hyph(self):
        val = self.get_attr('iset/hyph')
        return val if val is not None else ''

    @iset_hyph.setter
    def iset_hyph(self, value):
        self.set_attr('iset/hyph', value)

    @property
    def iset_echo(self):
        val = self.get_attr('iset/echo')
        return val if val is not None else ''

    @iset_echo.setter
    def iset_echo(self, value):
        self.set_attr('iset/echo', value)

    @property
    def iset_style(self):
        val = self.get_attr('iset/style')
        return val if val is not None else ''

    @iset_style.setter
    def iset_style(self, value):
        self.set_attr('iset/style', value)

    @property
    def iset_typo(self):
        val = self.get_attr('iset/typo')
        return val if val is not None else ''

    @iset_typo.setter
    def iset_typo(self, value):
        self.set_attr('iset/typo', value)

    @property
    def iset_variant(self):
        val = self.get_attr('iset/variant')
        return val if val is not None else ''

    @iset_variant.setter
    def iset_variant(self, value):
        self.set_attr('iset/variant', value)

    @property
    def iset_tagset(self):
        val = self.get_attr('iset/tagset')
        return val if val is not None else ''

    @iset_tagset.setter
    def iset_tagset(self, value):
        self.set_attr('iset/tagset', value)

    @property
    def iset_other(self):
        val = self.get_attr('iset/other')
        return val if val is not None else ''

    @iset_other.setter
    def iset_other(self, value):
        self.set_attr('iset/other', value)


class N(Node):
    "Representing an n-node"

    attrib = [('ne_type', types.UnicodeType),
              ('normalized_name', types.UnicodeType),
              ('a.rf', types.ListType), ]
    ref_attrib = ['a.rf']

    def __init__(self, data=None, parent=None, zone=None):
        "Constructor"
        Node.__init__(self, data, parent, zone)


class P(Node):
    "Representing a p-node"

    attrib = [('is_head', types.BooleanType), ('index', types.UnicodeType),
              ('coindex', types.UnicodeType), ('edgelabel', types.UnicodeType),
              ('form', types.UnicodeType), ('lemma', types.UnicodeType),
              ('tag', types.UnicodeType), ('phrase', types.UnicodeType),
              ('functions', types.ListType), ]
    ref_attrib = []

    def __init__(self, data=None, parent=None, zone=None):
        "Constructor"
        Node.__init__(self, data, parent, zone)


class AMR(Node, Ordered):
    "Representing an AMR type"

    attrib = [('varname', types.UnicodeType), ('nodetype', types.UnicodeType),
              ('modifier', types.UnicodeType), ('concept', types.UnicodeType),
              ('src_tnode.rf', types.UnicodeType), ('coref.rf', types.ListType),
              ('is_ne_head', types.BooleanType), ('is_ne_subnode', types.BooleanType)]

    ref_attrib = ['src_tnode.rf', 'coref.rf']

    def __init__(self, data=None, parent=None, zone=None):
        "Constructor"
        if data:
            self._data_from_tamr(data)
        # first keep parent as none, then set it manually (wait till other attributes are
        # filled and update the variable name as well)
        Node.__init__(self, data, None, zone or parent.zone)
        self.parent = parent
        # for root, remember which variables are taken in descendants, update upon parent setting
        if self.is_root:
            self.vars = {}
            for node in self.get_descendants():
                self._allocate_var(node)

    @property
    def coref_nodes(self):
        return self.get_deref_attr('coref.rf')

    @coref_nodes.setter
    def coref_nodes(self, new_coref):
        self.set_deref_attr('coref.rf', new_coref)

    @property
    def src_tnode(self):
        return self.get_deref_attr('src_tnode.rf')

    @src_tnode.setter
    def src_tnode(self, value):
        self.set_deref_attr('src_tnode.rf', value)

    @Node.parent.setter
    def parent(self, value):
        # free old variable name when removing from a tree, keep track of old tree
        oldroot = None
        if self.parent is not None and value is not None and value.root != self.root:
            oldroot = self.root
            self.root._free_var(self)
        # super -- set the parent
        Node.parent.fset(self, value)
        # update variable name for the new tree (if moving/creating new node, not on data loading)
        if self.parent is not None and self.root != oldroot:
            if oldroot is not None or (self.varname == 'auto'
                                       or self.varname is None and self.nodetype == 'var'):
                self.set_auto_var()
            else:
                self.root._allocate_var(self)

    def remove(self):
        self.root._free_var(self)
        # super -- do the actual removal
        Node.remove(self)

    def set_auto_var(self):
        """Compute automatic variable name (using the first free number for the 1st letter
        of the given concept."""
        if self.coref_nodes:
            coref = self.coref_nodes
            self.varname = coref[0].varname
        elif self.varname or self.nodetype == 'var' or not self.concept.startswith('"'):
            # for concepts, just overwrite the variables
            letter = self.get_letter_for_concept()
            num = self.root._allocate_var_for_letter(letter)
            if num > 1:
                letter += str(num)
            self.varname = letter
            # update coreferencing nodes
            coref = self.get_referencing_nodes('coref.rf')
            if coref:
                for coref_node in coref:
                    coref_node.varname = letter

    def get_letter_for_concept(self):
        """Get letter for AMR concept (usually the first letter)."""
        c = self.concept
        c = unidecode.unidecode(c)
        c = re.sub(r'[^a-zA-Z]', '', c)
        c = c.lower()
        if not c:
            return "X"
        return c[0]

    def _split_varname(self):
        """Split an AMR variable name into the letter and the number (use 1 if no number)."""
        if self.varname is None:
            return None, None
        num = 1
        letter = self.varname[0]
        if len(self.varname) > 1:
            num = int(self.varname[1:])
        return letter, num

    def _free_var(self, removed_node):
        if removed_node.varname in [None, 'auto']:
            return
        letter, num = removed_node._split_varname()
        if self.vars[letter] == num:
            self.vars[letter] -= 1
            if self.vars[letter] == 0:
                del self.vars[letter]

    def _allocate_var_for_letter(self, letter):
        hinum = self.vars.get(letter, 0)
        hinum += 1
        self.vars[letter] = hinum
        return hinum

    def _allocate_var(self, added_node):
        if added_node.varname in [None, 'auto']:
            return
        letter, num = added_node._split_varname()
        hinum = self.vars.get(letter, -1)
        if num > hinum:
            self.vars[letter] = num

    def _data_from_tamr(self, data):
        """Convert into "true" AMR from TAMR-stored YAML data (used in constructor)."""
        if 'wild' in data and 'modifier' in data['wild']:
            data['modifier'] = data['wild']['modifier']
            del data['wild']['modifier']
        if 't_lemma' in data:
            m = re.match(r'^([a-zA-Z][0-9]*)/(.*)$', data['t_lemma'])
            if m:
                data['varname'] = m.group(1)
                data['concept'] = m.group(2)
                data['nodetype'] = 'var'
            else:
                m = re.match(r'^([a-zA-Z][0-9]*)$', data['t_lemma'])
                if m:
                    data['varname'] = m.group(1)
                    data['nodetype'] = 'coref'
                else:
                    data['concept'] = data['t_lemma']
                    data['nodetype'] = 'const'
            del data['t_lemma']
        if 'coref_text.rf' in data:
            data['coref.rf'] = data['coref_text.rf']
        if 'wild' in data:
            if 'is_ne_head' in data['wild']:
                data['is_ne_head'] = data['wild']['is_ne_head']
                del data['wild']['is_ne_head']
            if 'is_ne_subnode' in data['wild']:
                data['is_ne_subnode'] = data['wild']['is_ne_subnode']
                del data['wild']['is_ne_subnode']
        if data.get('nodetype') == 'coref' and 'coref.rf' not in data:
            log_warn('Coref-type node has no coreference: ' . str(data))

    def data_to_tamr(self, data):
        """Convert back from AMR into TAMR-stored YAML (used by YAML writer)."""
        if 'varname' in data and 'concept'in data:
            # concepts
            data['t_lemma'] = data['varname'] + '/' + data['concept']
            del data['varname']
            del data['concept']
        elif 'concept' in data:
            # constants
            data['t_lemma'] = data['concept']
            del data['concept']
        else:
            # coreference
            data['t_lemma'] = data['varname']
            data['coref_text.rf'] = data['coref.rf']
            del data['varname']
            del data['coref.rf']
        if 'wild' not in data and ('modifier' in data or
                                   'is_ne_head' in data or
                                   'is_ne_subnode' in data):
            data['wild'] = {}
        if 'modifier' in data:
            data['wild']['modifier'] = data['modifier']
            del data['modifier']
        if 'nodetype' in data and data['nodetype'] != 'root':
            del data['nodetype']
        if 'is_ne_head' in data:
            data['wild']['is_ne_head'] = data['is_ne_head']
        if 'is_ne_subnode' in data:
            data['wild']['is_ne_subnode'] = data['is_ne_subnode']
