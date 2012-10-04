
import datetime
import unittest

from trac.test import EnvironmentStub, Mock

from tracfullblog.db import FullBlogSetup
from tracfullblog.model import *

class GroupPostsByMonthTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()
        FullBlogSetup(self.env).upgrade_environment(self.env.get_db_cnx())

    def tearDown(self):
        self.env.destroy_db()
        del self.env

    def test_many_posts(self):
        # 2 posts in one period
        one = BlogPost(self.env, 'one')
        one.update_fields({'title': 'one', 'body': 'body', 'author': 'user'})
        self.assertEquals([], one.save('user'))
        two = BlogPost(self.env, 'two')
        two.update_fields({'title': 'two', 'body': 'body', 'author': 'user'})
        self.assertEquals([], two.save('user'))
        grouped = group_posts_by_month(get_blog_posts(self.env))
        self.assertEquals(1, len(grouped))
        # Add 1 post in another period
        three = BlogPost(self.env, 'three')
        three.update_fields({'title': 'three', 'body': 'body', 'author': 'user',
            'publish_time': three.publish_time - datetime.timedelta(days=-100)})
        self.assertEquals([], three.save('user'))
        grouped = group_posts_by_month(get_blog_posts(self.env))
        self.assertEquals(2, len(grouped))
        self.assertEquals(1, len(grouped[0][1]))
        self.assertEquals(2, len(grouped[1][1]))
        self.assertEquals(type(grouped[0][0]), datetime.datetime)
        self.assertEquals((one.name, one.version, one.publish_time, one.author, one.title, one.body, []), grouped[1][1][0])

    def test_no_posts(self):
        grouped = group_posts_by_month(get_blog_posts(self.env))
        self.assertEquals([], grouped)

class GetBlogPostsTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()
        FullBlogSetup(self.env).upgrade_environment(self.env.get_db_cnx())

    def tearDown(self):
        self.env.destroy_db()
        del self.env

    def test_get_by_category(self):
        bp = BlogPost(self.env, 'one')
        bp.update_fields({'title': 'one', 'body': 'body', 'author': 'user',
                          'categories': 'about stuff'})
        self.assertEquals([], bp.save('user'))
        posts = get_blog_posts(self.env)
        self.assertEquals(1, len(posts))
        self.assertEquals('one', posts[0][0])
        posts = get_blog_posts(self.env, category='non-existing')
        self.assertEquals(0, len(posts))
        posts = get_blog_posts(self.env, category='stuff')
        self.assertEquals(1, len(posts))
        self.assertEquals('one', posts[0][0])
        self.assertEquals(get_blog_posts(self.env, category='about'),
                          get_blog_posts(self.env, category='stuff'))
