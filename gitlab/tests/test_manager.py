# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Gauvain Pocentek <gauvain@pocentek.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

try:
    import unittest
except ImportError:
    import unittest2 as unittest

from httmock import HTTMock  # noqa
from httmock import response  # noqa
from httmock import urlmatch  # noqa

from gitlab import *  # noqa
from gitlab.objects import BaseManager  # noqa


class FakeChildObject(GitlabObject):
    _url = "/fake"


class FakeChildManager(BaseManager):
    obj_cls = FakeChildObject


class FakeObject(GitlabObject):
    _url = "/fake"
    managers = [('children', FakeChildManager, [('child_id', 'id')])]


class FakeObjectManager(BaseManager):
    obj_cls = FakeObject


class TestGitlabManager(unittest.TestCase):
    def setUp(self):
        self.gitlab = Gitlab("http://localhost", private_token="private_token",
                             email="testuser@test.com",
                             password="testpassword", ssl_verify=True)

    def test_constructor(self):
        self.assertRaises(AttributeError, BaseManager, self.gitlab)

        @urlmatch(scheme="http", netloc="localhost", path="/api/v3/fake/1",
                  method="get")
        def resp_get(url, request):
            headers = {'content-type': 'application/json'}
            content = '{"id": 1, "name": "fake_name"}'.encode("utf-8")
            return response(200, content, headers, None, 5, request)

        with HTTMock(resp_get):
            mgr = FakeObjectManager(self.gitlab)
            fake_obj = mgr.get(1)
            self.assertEqual(fake_obj.id, 1)
            self.assertEqual(fake_obj.name, "fake_name")
            self.assertEqual(mgr.gitlab, self.gitlab)
            self.assertEqual(mgr.args, [])
            self.assertEqual(mgr.parent, None)

            self.assertIsInstance(fake_obj.children, FakeChildManager)
            self.assertEqual(fake_obj.children.gitlab, self.gitlab)
            self.assertEqual(fake_obj.children.parent, fake_obj)
            self.assertEqual(len(fake_obj.children.args), 1)

            fake_child = fake_obj.children.get(1)
            self.assertEqual(fake_child.id, 1)
            self.assertEqual(fake_child.name, "fake_name")

    def test_get(self):
        mgr = FakeObjectManager(self.gitlab)
        FakeObject.canGet = False
        self.assertRaises(NotImplementedError, mgr.get, 1)

        @urlmatch(scheme="http", netloc="localhost", path="/api/v3/fake/1",
                  method="get")
        def resp_get(url, request):
            headers = {'content-type': 'application/json'}
            content = '{"id": 1, "name": "fake_name"}'.encode("utf-8")
            return response(200, content, headers, None, 5, request)

        with HTTMock(resp_get):
            FakeObject.canGet = True
            mgr = FakeObjectManager(self.gitlab)
            fake_obj = mgr.get(1)
            self.assertIsInstance(fake_obj, FakeObject)
            self.assertEqual(fake_obj.id, 1)
            self.assertEqual(fake_obj.name, "fake_name")

    def test_list(self):
        mgr = FakeObjectManager(self.gitlab)
        FakeObject.canList = False
        self.assertRaises(NotImplementedError, mgr.list)

        @urlmatch(scheme="http", netloc="localhost", path="/api/v3/fake",
                  method="get")
        def resp_get(url, request):
            headers = {'content-type': 'application/json'}
            content = ('[{"id": 1, "name": "fake_name1"},'
                       '{"id": 2, "name": "fake_name2"}]')
            content = content.encode("utf-8")
            return response(200, content, headers, None, 5, request)

        with HTTMock(resp_get):
            FakeObject.canList = True
            mgr = FakeObjectManager(self.gitlab)
            fake_list = mgr.list()
            self.assertEqual(len(fake_list), 2)
            self.assertIsInstance(fake_list[0], FakeObject)
            self.assertEqual(fake_list[0].id, 1)
            self.assertEqual(fake_list[0].name, "fake_name1")
            self.assertIsInstance(fake_list[1], FakeObject)
            self.assertEqual(fake_list[1].id, 2)
            self.assertEqual(fake_list[1].name, "fake_name2")

    def test_create(self):
        mgr = FakeObjectManager(self.gitlab)
        FakeObject.canCreate = False
        self.assertRaises(NotImplementedError, mgr.create, {'foo': 'bar'})

        @urlmatch(scheme="http", netloc="localhost", path="/api/v3/fake",
                  method="post")
        def resp_post(url, request):
            headers = {'content-type': 'application/json'}
            data = '{"name": "fake_name"}'
            content = '{"id": 1, "name": "fake_name"}'.encode("utf-8")
            return response(201, content, headers, data, 5, request)

        with HTTMock(resp_post):
            FakeObject.canCreate = True
            mgr = FakeObjectManager(self.gitlab)
            fake_obj = mgr.create({'name': 'fake_name'})
            self.assertIsInstance(fake_obj, FakeObject)
            self.assertEqual(fake_obj.id, 1)
            self.assertEqual(fake_obj.name, "fake_name")
