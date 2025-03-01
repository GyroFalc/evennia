"""
Unit tests for the prototypes and spawner

"""

import uuid
from random import randint, sample
from time import time

import mock
from anything import Something
from django.test.utils import override_settings

from evennia.prototypes import menus as olc_menus
from evennia.prototypes import protfuncs as protofuncs
from evennia.prototypes import prototypes as protlib
from evennia.prototypes import spawner
from evennia.prototypes.prototypes import _PROTOTYPE_TAG_META_CATEGORY
from evennia.utils.test_resources import BaseEvenniaTest
from evennia.utils.tests.test_evmenu import TestEvMenu

_PROTPARENTS = {
    "NOBODY": {},
    "GOBLIN": {
        "prototype_key": "GOBLIN",
        "typeclass": "evennia.objects.objects.DefaultObject",
        "key": "goblin grunt",
        "health": lambda: randint(1, 1),
        "resists": ["cold", "poison"],
        "attacks": ["fists"],
        "weaknesses": ["fire", "light"],
    },
    "GOBLIN_WIZARD": {
        "prototype_parent": "GOBLIN",
        "key": "goblin wizard",
        "spells": ["fire ball", "lighting bolt"],
    },
    "GOBLIN_ARCHER": {
        "prototype_parent": "GOBLIN",
        "key": "goblin archer",
        "attacks": ["short bow"],
    },
    "ARCHWIZARD": {"prototype_parent": "GOBLIN", "attacks": ["archwizard staff"]},
    "GOBLIN_ARCHWIZARD": {
        "key": "goblin archwizard",
        "prototype_parent": ("GOBLIN_WIZARD", "ARCHWIZARD"),
    },
    "ISSUE2908": {
        "typeclass": "evennia.objects.objects.DefaultObject",
        "key": "testobject_isse2909",
        "location": "$choice($objlist(",
    },
}


class TestSpawner(BaseEvenniaTest):
    def setUp(self):
        super().setUp()
        self.prot1 = {
            "prototype_key": "testprototype",
            "typeclass": "evennia.objects.objects.DefaultObject",
        }

    def test_spawn_from_prot(self):
        obj1 = spawner.spawn(self.prot1)
        # check spawned objects have the right tag
        self.assertEqual(list(protlib.search_objects_with_prototype("testprototype")), obj1)
        self.assertEqual(
            [
                o.key
                for o in spawner.spawn(
                    _PROTPARENTS["GOBLIN"],
                    _PROTPARENTS["GOBLIN_ARCHWIZARD"],
                    prototype_parents=_PROTPARENTS,
                )
            ],
            ["goblin grunt", "goblin archwizard"],
        )

    def test_spawn_from_str(self):
        protlib.save_prototype(self.prot1)
        obj1 = spawner.spawn(self.prot1["prototype_key"])
        self.assertEqual(list(protlib.search_objects_with_prototype("testprototype")), obj1)
        self.assertEqual(
            [
                o.key
                for o in spawner.spawn(
                    _PROTPARENTS["GOBLIN"],
                    _PROTPARENTS["GOBLIN_ARCHWIZARD"],
                    prototype_parents=_PROTPARENTS,
                )
            ],
            ["goblin grunt", "goblin archwizard"],
        )


class TestUtils(BaseEvenniaTest):
    def test_prototype_from_object(self):
        self.maxDiff = None
        self.obj1.attributes.add("test", "testval")
        self.obj1.tags.add("foo")
        new_prot = spawner.prototype_from_object(self.obj1)
        self.assertEqual(
            {
                "attrs": [("test", "testval", None, "")],
                "home": Something,
                "key": "Obj",
                "location": Something,
                "locks": ";".join(
                    [
                        "call:true()",
                        "control:perm(Developer)",
                        "delete:perm(Admin)",
                        "drop:holds()",
                        "edit:perm(Admin)",
                        "examine:perm(Builder)",
                        "get:all()",
                        "puppet:pperm(Developer)",
                        "tell:perm(Admin)",
                        "view:all()",
                    ]
                ),
                "prototype_desc": "Built from Obj",
                "prototype_key": Something,
                "prototype_locks": "spawn:all();edit:all()",
                "prototype_tags": [],
                "tags": [("foo", None, None)],
                "typeclass": "evennia.objects.objects.DefaultObject",
            },
            new_prot,
        )

    def test_update_objects_from_prototypes(self):

        self.maxDiff = None
        self.obj1.attributes.add("oldtest", "to_keep")

        old_prot = spawner.prototype_from_object(self.obj1)

        # modify object away from prototype
        self.obj1.attributes.add("test", "testval")
        self.obj1.attributes.add("desc", "changed desc")
        self.obj1.aliases.add("foo")
        self.obj1.tags.add("footag", "foocategory")

        # modify prototype
        old_prot["new"] = "new_val"
        old_prot["test"] = "testval_changed"
        old_prot["permissions"] = ["Builder"]
        # this will not update, since we don't update the prototype on-disk
        old_prot["prototype_desc"] = "New version of prototype"
        old_prot["attrs"] += (("fooattr", "fooattrval", None, ""),)

        # diff obj/prototype
        old_prot_copy = old_prot.copy()

        pdiff, obj_prototype = spawner.prototype_diff_from_object(old_prot, self.obj1)

        self.assertEqual(old_prot_copy, old_prot)

        self.assertEqual(
            obj_prototype,
            {
                "aliases": ["foo"],
                "attrs": [
                    ("desc", "changed desc", None, ""),
                    ("oldtest", "to_keep", None, ""),
                    ("test", "testval", None, ""),
                ],
                "key": "Obj",
                "home": Something,
                "location": Something,
                "locks": (
                    "call:true();control:perm(Developer);delete:perm(Admin);"
                    "drop:holds();"
                    "edit:perm(Admin);examine:perm(Builder);get:all();"
                    "puppet:pperm(Developer);tell:perm(Admin);view:all()"
                ),
                "prototype_desc": "Built from Obj",
                "prototype_key": Something,
                "prototype_locks": "spawn:all();edit:all()",
                "prototype_tags": [],
                "tags": [("footag", "foocategory", None)],
                "typeclass": "evennia.objects.objects.DefaultObject",
            },
        )

        self.assertEqual(
            old_prot,
            {
                "attrs": [("oldtest", "to_keep", None, ""), ("fooattr", "fooattrval", None, "")],
                "home": Something,
                "key": "Obj",
                "location": Something,
                "locks": (
                    "call:true();control:perm(Developer);delete:perm(Admin);"
                    "drop:holds();"
                    "edit:perm(Admin);examine:perm(Builder);get:all();"
                    "puppet:pperm(Developer);tell:perm(Admin);view:all()"
                ),
                "new": "new_val",
                "permissions": ["Builder"],
                "prototype_desc": "New version of prototype",
                "prototype_key": Something,
                "prototype_locks": "spawn:all();edit:all()",
                "prototype_tags": [],
                "test": "testval_changed",
                "typeclass": "evennia.objects.objects.DefaultObject",
            },
        )

        self.assertEqual(
            pdiff,
            {
                "home": (Something, Something, "KEEP"),
                "prototype_locks": ("spawn:all();edit:all()", "spawn:all();edit:all()", "KEEP"),
                "prototype_key": (Something, Something, "UPDATE"),
                "location": (Something, Something, "KEEP"),
                "locks": (
                    "call:true();control:perm(Developer);delete:perm(Admin);"
                    "drop:holds();edit:perm(Admin);examine:perm(Builder);"
                    "get:all();puppet:pperm(Developer);tell:perm(Admin);view:all()",
                    "call:true();control:perm(Developer);delete:perm(Admin);drop:holds();"
                    "edit:perm(Admin);examine:perm(Builder);get:all();"
                    "puppet:pperm(Developer);tell:perm(Admin);view:all()",
                    "KEEP",
                ),
                "prototype_tags": (None, None, "KEEP"),
                "attrs": {
                    "oldtest": (
                        ("oldtest", "to_keep", None, ""),
                        ("oldtest", "to_keep", None, ""),
                        "KEEP",
                    ),
                    "desc": (("desc", "changed desc", None, ""), None, "KEEP"),
                    "fooattr": (Something, ("fooattr", "fooattrval", None, ""), "ADD"),
                    "test": (
                        ("test", "testval", None, ""),
                        ("test", "testval_changed", None, ""),
                        "UPDATE",
                    ),
                    "new": (Something, ("new", "new_val", None, ""), "ADD"),
                },
                "key": ("Obj", "Obj", "KEEP"),
                "typeclass": (
                    "evennia.objects.objects.DefaultObject",
                    "evennia.objects.objects.DefaultObject",
                    "KEEP",
                ),
                "aliases": {"foo": ("foo", None, "REMOVE")},
                "tags": {"footag": (("footag", "foocategory", None), None, "REMOVE")},
                "prototype_desc": ("Built from Obj", "New version of prototype", "UPDATE"),
                "permissions": {"Builder": (None, "Builder", "ADD")},
            },
        )

        self.assertEqual(
            spawner.flatten_diff(pdiff),
            {
                "aliases": "REMOVE",
                "attrs": "UPDATE",
                "home": "KEEP",
                "key": "KEEP",
                "location": "KEEP",
                "locks": "KEEP",
                "permissions": "UPDATE",
                "prototype_desc": "UPDATE",
                "prototype_key": "UPDATE",
                "prototype_locks": "KEEP",
                "prototype_tags": "KEEP",
                "tags": "REMOVE",
                "typeclass": "KEEP",
            },
        )

        # apply diff
        count = spawner.batch_update_objects_with_prototype(
            old_prot, diff=pdiff, objects=[self.obj1]
        )
        self.assertEqual(count, 1)

        new_prot = spawner.prototype_from_object(self.obj1)
        self.assertEqual(
            {
                "aliases": ["foo"],
                "attrs": [
                    ("desc", "changed desc", None, ""),
                    ("fooattr", "fooattrval", None, ""),
                    ("new", "new_val", None, ""),
                    ("oldtest", "to_keep", None, ""),
                    ("test", "testval_changed", None, ""),
                ],
                "home": Something,
                "key": "Obj",
                "location": Something,
                "locks": ";".join(
                    [
                        "call:true()",
                        "control:perm(Developer)",
                        "delete:perm(Admin)",
                        "drop:holds()",
                        "edit:perm(Admin)",
                        "examine:perm(Builder)",
                        "get:all()",
                        "puppet:pperm(Developer)",
                        "tell:perm(Admin)",
                        "view:all()",
                    ]
                ),
                "tags": [("footag", "foocategory", None), (Something, "from_prototype", None)],
                "permissions": ["builder"],
                "prototype_desc": "Built from Obj",
                "prototype_key": Something,
                "prototype_locks": "spawn:all();edit:all()",
                "prototype_tags": [],
                "typeclass": "evennia.objects.objects.DefaultObject",
            },
            new_prot,
        )


class TestProtLib(BaseEvenniaTest):
    def setUp(self):
        super().setUp()
        self.obj1.attributes.add("testattr", "testval")
        self.prot = spawner.prototype_from_object(self.obj1)

    def test_prototype_to_str(self):
        prstr = protlib.prototype_to_str(self.prot)
        self.assertTrue(prstr.startswith("|cprototype-key:|n"))

    def test_check_permission(self):
        pass

    def test_save_prototype(self):
        result = protlib.save_prototype(self.prot)
        self.assertEqual(result, self.prot)
        # faulty
        self.prot["prototype_key"] = None
        self.assertRaises(protlib.ValidationError, protlib.save_prototype, self.prot)

    def test_search_prototype(self):
        protlib.save_prototype(self.prot)
        match = protlib.search_prototype("NotFound")
        self.assertFalse(match)
        match = protlib.search_prototype()
        self.assertTrue(match)
        match = protlib.search_prototype(self.prot["prototype_key"])
        self.assertEqual(match, [self.prot])
        match = protlib.search_prototype(self.prot["prototype_key"].upper())
        self.assertEqual(match, [self.prot])


class TestProtFuncs(BaseEvenniaTest):
    @override_settings(PROT_FUNC_MODULES=["evennia.prototypes.protfuncs"])
    def test_protkey_protfunc(self):
        test_prot = {"key1": "value1", "key2": 2}

        self.assertEqual(
            protlib.protfunc_parser("$protkey(key1)", testing=True, prototype=test_prot),
            "value1",
        )
        self.assertEqual(
            protlib.protfunc_parser("$protkey(key2)", testing=True, prototype=test_prot), 2
        )


class TestPrototypeStorage(BaseEvenniaTest):
    def setUp(self):
        super().setUp()
        self.maxDiff = None

        self.prot1 = spawner.prototype_from_object(self.obj1)
        self.prot1["prototype_key"] = "testprototype1"
        self.prot1["prototype_desc"] = "testdesc1"
        self.prot1["prototype_tags"] = [("foo1", _PROTOTYPE_TAG_META_CATEGORY)]

        self.prot2 = self.prot1.copy()
        self.prot2["prototype_key"] = "testprototype2"
        self.prot2["prototype_desc"] = "testdesc2"
        self.prot2["prototype_tags"] = [("foo1", _PROTOTYPE_TAG_META_CATEGORY)]

        self.prot3 = self.prot2.copy()
        self.prot3["prototype_key"] = "testprototype3"
        self.prot3["prototype_desc"] = "testdesc3"
        self.prot3["prototype_tags"] = [("foo1", _PROTOTYPE_TAG_META_CATEGORY)]

    def test_prototype_storage(self):

        # from evennia import set_trace;set_trace(term_size=(180, 50))
        prot1 = protlib.create_prototype(self.prot1)

        self.assertTrue(bool(prot1))
        self.assertEqual(prot1, self.prot1)

        self.assertEqual(prot1["prototype_desc"], "testdesc1")

        self.assertEqual(prot1["prototype_tags"], [("foo1", _PROTOTYPE_TAG_META_CATEGORY)])
        self.assertEqual(
            protlib.DbPrototype.objects.get_by_tag("foo1", _PROTOTYPE_TAG_META_CATEGORY)[
                0
            ].db.prototype,
            prot1,
        )

        prot2 = protlib.create_prototype(self.prot2)
        self.assertEqual(
            [
                pobj.db.prototype
                for pobj in protlib.DbPrototype.objects.get_by_tag(
                    "foo1", _PROTOTYPE_TAG_META_CATEGORY
                )
            ],
            [prot1, prot2],
        )

        # add to existing prototype
        prot1b = protlib.create_prototype(
            {"prototype_key": "testprototype1", "foo": "bar", "prototype_tags": ["foo2"]}
        )

        self.assertEqual(
            [
                pobj.db.prototype
                for pobj in protlib.DbPrototype.objects.get_by_tag(
                    "foo2", _PROTOTYPE_TAG_META_CATEGORY
                )
            ],
            [prot1b],
        )

        self.assertEqual(list(protlib.search_prototype("testprototype2")), [prot2])
        self.assertNotEqual(list(protlib.search_prototype("testprototype1")), [prot1])
        self.assertEqual(list(protlib.search_prototype("testprototype1")), [prot1b])

        prot3 = protlib.create_prototype(self.prot3)

        # partial match
        with mock.patch("evennia.prototypes.prototypes._MODULE_PROTOTYPES", {}):
            self.assertCountEqual(protlib.search_prototype("prot"), [prot1b, prot2, prot3])
            self.assertCountEqual(protlib.search_prototype(tags="foo1"), [prot1b, prot2, prot3])

        self.assertTrue(str(str(protlib.list_prototypes(self.char1))))


class _MockMenu(object):
    pass


class TestMenuModule(BaseEvenniaTest):

    maxDiff = None

    def setUp(self):
        super().setUp()

        # set up fake store
        self.caller = self.char1
        menutree = _MockMenu()
        self.caller.ndb._menutree = menutree

        self.test_prot = {
            "prototype_key": "test_prot",
            "typeclass": "evennia.objects.objects.DefaultObject",
            "prototype_locks": "edit:all();spawn:all()",
        }

    def test_helpers(self):

        caller = self.caller

        # general helpers

        self.assertEqual(olc_menus._get_menu_prototype(caller), {})
        self.assertEqual(olc_menus._is_new_prototype(caller), True)

        self.assertEqual(olc_menus._set_menu_prototype(caller, {}), {})

        self.assertEqual(
            olc_menus._set_prototype_value(caller, "key", "TestKey"), {"key": "TestKey"}
        )
        self.assertEqual(olc_menus._get_menu_prototype(caller), {"key": "TestKey"})

        self.assertEqual(
            olc_menus._format_option_value(
                "key", required=True, prototype=olc_menus._get_menu_prototype(caller)
            ),
            " (TestKey|n)",
        )
        self.assertEqual(
            olc_menus._format_option_value([1, 2, 3, "foo"], required=True), " (1, 2, 3, foo|n)"
        )

        self.assertEqual(
            olc_menus._set_property(
                caller, "ChangedKey", prop="key", processor=str, next_node="foo"
            ),
            "foo",
        )
        self.assertEqual(olc_menus._get_menu_prototype(caller), {"key": "ChangedKey"})

        self.assertEqual(
            olc_menus._wizard_options("ThisNode", "PrevNode", "NextNode"),
            [
                {"goto": "node_PrevNode", "key": ("|wB|Wack", "b"), "desc": "|W(PrevNode)|n"},
                {"goto": "node_NextNode", "key": ("|wF|Worward", "f"), "desc": "|W(NextNode)|n"},
                {"goto": "node_index", "key": ("|wI|Wndex", "i")},
                {
                    "goto": ("node_validate_prototype", {"back": "ThisNode"}),
                    "key": ("|wV|Walidate prototype", "validate", "v"),
                },
            ],
        )

        self.assertEqual(olc_menus._validate_prototype(self.test_prot), (False, Something))
        self.assertEqual(
            olc_menus._validate_prototype({"prototype_key": "testthing", "key": "mytest"}),
            (True, Something),
        )

        choices = ["test1", "test2", "test3", "test4"]
        actions = (("examine", "e", "l"), ("add", "a"), ("foo", "f"))
        self.assertEqual(olc_menus._default_parse("l4", choices, *actions), ("test4", "examine"))
        self.assertEqual(olc_menus._default_parse("add 2", choices, *actions), ("test2", "add"))
        self.assertEqual(olc_menus._default_parse("foo3", choices, *actions), ("test3", "foo"))
        self.assertEqual(olc_menus._default_parse("f3", choices, *actions), ("test3", "foo"))
        self.assertEqual(olc_menus._default_parse("f5", choices, *actions), (None, None))

    def test_node_helpers(self):

        caller = self.caller

        with mock.patch(
            "evennia.prototypes.menus.protlib.search_prototype",
            new=mock.MagicMock(return_value=[self.test_prot]),
        ):
            # prototype_key helpers
            self.assertEqual(olc_menus._check_prototype_key(caller, "test_prot"), None)
            caller.ndb._menutree.olc_new = True
            self.assertEqual(olc_menus._check_prototype_key(caller, "test_prot"), "node_index")

            # prototype_parent helpers
            self.assertEqual(olc_menus._all_prototype_parents(caller), ["test_prot"])
            # self.assertEqual(olc_menus._prototype_parent_parse(
            #     caller, 'test_prot'),
            #     "|cprototype key:|n test_prot, |ctags:|n None, |clocks:|n edit:all();spawn:all() "
            #     "\n|cdesc:|n None \n|cprototype:|n "
            #     "{\n  'typeclass': 'evennia.objects.objects.DefaultObject', \n}")

        with mock.patch(
            "evennia.prototypes.menus.protlib.search_prototype",
            new=mock.MagicMock(return_value=[_PROTPARENTS["GOBLIN"]]),
        ):
            self.assertEqual(
                olc_menus._prototype_parent_select(caller, "goblin"), "node_prototype_parent"
            )

        self.assertEqual(
            olc_menus._get_menu_prototype(caller),
            {
                "prototype_key": "test_prot",
                "prototype_locks": "edit:all();spawn:all()",
                "prototype_parent": "goblin",
                "typeclass": "evennia.objects.objects.DefaultObject",
            },
        )

        # typeclass helpers
        with mock.patch(
            "evennia.utils.utils.get_all_typeclasses",
            new=mock.MagicMock(return_value={"foo": None, "bar": None}),
        ):
            self.assertEqual(olc_menus._all_typeclasses(caller), ["bar", "foo"])

        self.assertEqual(
            olc_menus._typeclass_select(caller, "evennia.objects.objects.DefaultObject"), None
        )
        # prototype_parent should be popped off here
        self.assertEqual(
            olc_menus._get_menu_prototype(caller),
            {
                "prototype_key": "test_prot",
                "prototype_locks": "edit:all();spawn:all()",
                "prototype_parent": "goblin",
                "typeclass": "evennia.objects.objects.DefaultObject",
            },
        )

        # attr helpers
        self.assertEqual(olc_menus._caller_attrs(caller), [])
        self.assertEqual(olc_menus._add_attr(caller, "test1=foo1"), Something)
        self.assertEqual(olc_menus._add_attr(caller, "test2;cat1=foo2"), Something)
        self.assertEqual(olc_menus._add_attr(caller, "test3;cat2;edit:false()=foo3"), Something)
        self.assertEqual(
            olc_menus._add_attr(caller, "test4;cat3;set:true();edit:false()=foo4"), Something
        )
        self.assertEqual(
            olc_menus._add_attr(caller, "test5;cat4;set:true();edit:false()=123"), Something
        )
        self.assertEqual(olc_menus._add_attr(caller, "test1=foo1_changed"), Something)
        self.assertEqual(
            olc_menus._get_menu_prototype(caller)["attrs"],
            [
                ("test1", "foo1_changed", None, ""),
                ("test2", "foo2", "cat1", ""),
                ("test3", "foo3", "cat2", "edit:false()"),
                ("test4", "foo4", "cat3", "set:true();edit:false()"),
                ("test5", "123", "cat4", "set:true();edit:false()"),
            ],
        )

        # tag helpers
        self.assertEqual(olc_menus._caller_tags(caller), [])
        self.assertEqual(olc_menus._add_tag(caller, "foo1"), Something)
        self.assertEqual(olc_menus._add_tag(caller, "foo2;cat1"), Something)
        self.assertEqual(olc_menus._add_tag(caller, "foo3;cat2;dat1"), Something)
        self.assertEqual(olc_menus._caller_tags(caller), ["foo1", "foo2", "foo3"])
        self.assertEqual(
            olc_menus._get_menu_prototype(caller)["tags"],
            [("foo1", None, ""), ("foo2", "cat1", ""), ("foo3", "cat2", "dat1")],
        )
        self.assertEqual(olc_menus._add_tag(caller, "foo1", delete=True), "Removed Tag 'foo1'.")
        self.assertEqual(
            olc_menus._get_menu_prototype(caller)["tags"],
            [("foo2", "cat1", ""), ("foo3", "cat2", "dat1")],
        )

        self.assertEqual(
            olc_menus._display_tag(olc_menus._get_menu_prototype(caller)["tags"][0]), Something
        )
        self.assertEqual(olc_menus._caller_tags(caller), ["foo2", "foo3"])

        protlib.save_prototype(self.test_prot)

        # locks helpers
        self.assertEqual(olc_menus._lock_add(caller, "foo:false()"), "Added lock 'foo:false()'.")
        self.assertEqual(olc_menus._lock_add(caller, "foo2:false()"), "Added lock 'foo2:false()'.")
        self.assertEqual(
            olc_menus._lock_add(caller, "foo2:true()"), "Lock with locktype 'foo2' updated."
        )
        self.assertEqual(olc_menus._get_menu_prototype(caller)["locks"], "foo:false();foo2:true()")

        # perm helpers
        self.assertEqual(olc_menus._add_perm(caller, "foo"), "Added Permission 'foo'")
        self.assertEqual(olc_menus._add_perm(caller, "foo2"), "Added Permission 'foo2'")
        self.assertEqual(olc_menus._get_menu_prototype(caller)["permissions"], ["foo", "foo2"])

        # prototype_tags helpers
        self.assertEqual(olc_menus._add_prototype_tag(caller, "foo"), "Added Prototype-Tag 'foo'.")
        self.assertEqual(
            olc_menus._add_prototype_tag(caller, "foo2"), "Added Prototype-Tag 'foo2'."
        )
        self.assertEqual(olc_menus._get_menu_prototype(caller)["prototype_tags"], ["foo", "foo2"])

        # spawn helpers
        with mock.patch(
            "evennia.prototypes.menus.protlib.search_prototype",
            new=mock.MagicMock(return_value=[_PROTPARENTS["GOBLIN"]]),
        ):
            self.assertEqual(olc_menus._spawn(caller, prototype=self.test_prot), Something)
        obj = caller.contents[0]

        self.assertEqual(obj.typeclass_path, "evennia.objects.objects.DefaultObject")
        self.assertEqual(
            obj.tags.get(category=spawner.PROTOTYPE_TAG_CATEGORY), self.test_prot["prototype_key"]
        )

        # update helpers
        self.assertEqual(
            olc_menus._apply_diff(caller, prototype=self.test_prot, back_node="foo", objects=[obj]),
            "foo",
        )  # no changes to apply
        self.test_prot["key"] = "updated key"  # change prototype
        self.assertEqual(
            olc_menus._apply_diff(caller, prototype=self.test_prot, objects=[obj], back_node="foo"),
            "foo",
        )  # apply change to the one obj

        # load helpers
        self.assertEqual(
            olc_menus._prototype_load_select(caller, self.test_prot["prototype_key"]),
            ("node_examine_entity", {"text": "|gLoaded prototype test_prot.|n", "back": "index"}),
        )

        # diff helpers
        obj_diff = {
            "attrs": {
                "desc": (
                    ("desc", "This is User #1.", None, ""),
                    ("desc", "This is User #1.", None, ""),
                    "KEEP",
                ),
                "foo": (None, ("foo", "bar", None, ""), "ADD"),
                "prelogout_location": (
                    ("prelogout_location", "#2", None, ""),
                    ("prelogout_location", "#2", None, ""),
                    "KEEP",
                ),
            },
            "home": ("#2", "#2", "KEEP"),
            "key": ("TestChar", "TestChar", "KEEP"),
            "locks": (
                "boot:false();call:false();control:perm(Developer);delete:false();"
                "edit:false();examine:perm(Developer);get:false();msg:all();"
                "puppet:false();tell:perm(Admin);view:all()",
                "boot:false();call:false();control:perm(Developer);delete:false();"
                "edit:false();examine:perm(Developer);get:false();msg:all();"
                "puppet:false();tell:perm(Admin);view:all()",
                "KEEP",
            ),
            "permissions": {"developer": ("developer", "developer", "KEEP")},
            "prototype_desc": ("Testobject build", None, "REMOVE"),
            "prototype_key": ("TestDiffKey", "TestDiffKey", "KEEP"),
            "prototype_locks": ("spawn:all();edit:all()", "spawn:all();edit:all()", "KEEP"),
            "prototype_tags": {},
            "tags": {"foo": (None, ("foo", None, ""), "ADD")},
            "typeclass": (
                "typeclasses.characters.Character",
                "typeclasses.characters.Character",
                "KEEP",
            ),
        }

        texts, options = olc_menus._format_diff_text_and_options(obj_diff)
        self.assertEqual(
            "\n".join(txt.strip() for txt in texts),
            "- |wattrs:|n    |c[1] |yADD|n: foo |W=|n bar |W(category:|n None|W, locks:|n |W)|n"
            "\n- |whome:|n"
            "\n- |wkey:|n"
            "\n- |wlocks:|n"
            "\n- |wpermissions:|n"
            "\n- |wprototype_desc:|n    |c[2] |rREMOVE|n: Testobject build"
            "\n- |wprototype_key:|n"
            "\n- |wprototype_locks:|n"
            "\n- |wprototype_tags:|n"
            "\n- |wtags:|n    |c[3] |yADD|n: foo |W(category:|n None|W)|n"
            "\n- |wtypeclass:|n",
        )

        self.assertEqual(
            options,
            [
                {"goto": (Something, Something), "key": "1", "desc": "|gKEEP|n (attrs) None"},
                {
                    "goto": (Something, Something),
                    "key": "2",
                    "desc": "|gKEEP|n (prototype_desc) Testobject build",
                },
                {"goto": (Something, Something), "key": "3", "desc": "|gKEEP|n (tags) None"},
            ],
        )


@mock.patch(
    "evennia.prototypes.menus.protlib.search_prototype",
    new=mock.MagicMock(
        return_value=[
            {"prototype_key": "TestPrototype", "typeclass": "TypeClassTest", "key": "TestObj"}
        ]
    ),
)
@mock.patch(
    "evennia.utils.utils.get_all_typeclasses",
    new=mock.MagicMock(return_value={"TypeclassTest": None}),
)
class TestOLCMenu(TestEvMenu):

    maxDiff = None
    menutree = "evennia.prototypes.menus"
    startnode = "node_index"

    # debug_output = True
    expect_all_nodes = True

    expected_node_texts = {"node_index": "|c --- Prototype wizard --- |n"}

    expected_tree = [
        "node_index",
        [
            "node_prototype_key",
            [
                "node_index",
                "node_index",
                "node_index",
                "node_validate_prototype",
                ["node_index", "node_index", "node_index"],
                "node_index",
            ],
            "node_prototype_parent",
            [
                "node_prototype_parent",
                "node_prototype_key",
                "node_prototype_parent",
                "node_index",
                "node_validate_prototype",
                "node_index",
            ],
            "node_typeclass",
            [
                "node_typeclass",
                "node_prototype_parent",
                "node_typeclass",
                "node_index",
                "node_validate_prototype",
                "node_index",
            ],
            "node_key",
            ["node_typeclass", "node_key", "node_index", "node_validate_prototype", "node_index"],
            "node_aliases",
            ["node_key", "node_aliases", "node_index", "node_validate_prototype", "node_index"],
            "node_attrs",
            ["node_aliases", "node_attrs", "node_index", "node_validate_prototype", "node_index"],
            "node_tags",
            ["node_attrs", "node_tags", "node_index", "node_validate_prototype", "node_index"],
            "node_locks",
            ["node_tags", "node_locks", "node_index", "node_validate_prototype", "node_index"],
            "node_permissions",
            [
                "node_locks",
                "node_permissions",
                "node_index",
                "node_validate_prototype",
                "node_index",
            ],
            "node_location",
            [
                "node_permissions",
                "node_location",
                "node_index",
                "node_validate_prototype",
                "node_index",
                "node_index",
            ],
            "node_home",
            [
                "node_location",
                "node_home",
                "node_index",
                "node_validate_prototype",
                "node_index",
                "node_index",
            ],
            "node_destination",
            [
                "node_home",
                "node_destination",
                "node_index",
                "node_validate_prototype",
                "node_index",
                "node_index",
            ],
            "node_prototype_desc",
            [
                "node_prototype_key",
                "node_prototype_parent",
                "node_index",
                "node_validate_prototype",
                "node_index",
            ],
            "node_prototype_tags",
            [
                "node_prototype_desc",
                "node_prototype_tags",
                "node_index",
                "node_validate_prototype",
                "node_index",
            ],
            "node_prototype_locks",
            [
                "node_prototype_tags",
                "node_prototype_locks",
                "node_index",
                "node_validate_prototype",
                "node_index",
            ],
            "node_validate_prototype",
            "node_index",
            "node_prototype_spawn",
            ["node_index", "node_index", "node_validate_prototype"],
            "node_index",
            "node_search_object",
            ["node_index", "node_index", "node_index"],
        ],
    ]


class PrototypeCrashTest(BaseEvenniaTest):

    # increase this to 1000 for optimization testing
    num_prototypes = 10

    def create(self, num=None):
        if not num:
            num = self.num_prototypes
        # print(f"Creating {num} additional prototypes...")
        for x in range(num):
            prot = {
                "prototype_key": str(uuid.uuid4()),
                "some_attributes": [str(uuid.uuid4()) for x in range(10)],
                "prototype_tags": list(sample(["demo", "test", "stuff"], 2)),
            }
            protlib.save_prototype(prot)

    def test_prototype_dos(self, *args, **kwargs):
        num_prototypes = self.num_prototypes
        for x in range(2):
            self.create(num_prototypes)
            # print("Attempting to list prototypes...")
            # start_time = time()
            self.char1.execute_cmd("spawn/list")
            # print(f"Prototypes listed in {time()-start_time} seconds.")


class Test2474(BaseEvenniaTest):
    """
    Test bug #2474 (https://github.com/evennia/evennia/issues/2474),
    where the prototype's attribute fails to take precedence over
    that of its prototype_parent.

    """

    prototypes = {
        "WEAPON": {
            "typeclass": "evennia.objects.objects.DefaultObject",
            "key": "Weapon",
            "desc": "A generic blade.",
            "magic": False,
        },
        "STING": {
            "prototype_parent": "WEAPON",
            "key": "Sting",
            "desc": "A dagger that shines with a cold light if Orcs are near.",
            "magic": True,
        },
    }

    def test_magic_spawn(self):
        """
        Test magic is inherited.

        """
        sting = spawner.spawn(self.prototypes["STING"], prototype_parents=self.prototypes)[0]
        self.assertEqual(sting.db.magic, True)

    def test_non_magic_spawn(self):
        """
        Test inverse - no magic.

        """
        sting = spawner.spawn(self.prototypes["WEAPON"], prototype_parents=self.prototypes)[0]
        self.assertEqual(sting.db.magic, False)


class TestPartialTagAttributes(BaseEvenniaTest):
    """
    Make sure tags and attributes are homogenized if given as incomplete tuples.

    See https://github.com/evennia/evennia/issues/2524.

    """

    def setUp(self):
        super().setUp()
        self.prot = {
            "prototype_key": "rock",
            "typeclass": "evennia.objects.objects.DefaultObject",
            "key": "a rock",
            "tags": [("quantity", "groupable")],  # missing data field
            "attrs": [("quantity", 1)],  # missing category and lock fields
            "desc": "A good way to get stoned.",
        }

    def test_partial_spawn(self):
        obj = spawner.spawn(self.prot)
        self.assertEqual(obj[0].key, self.prot["key"])


class TestIssue2908(BaseEvenniaTest):
    """
    Test spawning a prototype with a nested protfunc, as per issue #2908.

    """

    def test_spawn_with_protfunc(self):

        self.room1.tags.add("beach", category="zone")

        prot = {
            "prototype_key": "rock",
            "typeclass": "evennia.objects.objects.DefaultObject",
            "key": "a rock",
            "location": "$choice($objlist(beach,category=zone,type=tag))",
        }

        obj = spawner.spawn(prot, caller=self.char1)
        self.assertEqual(obj[0].location, self.room1)
