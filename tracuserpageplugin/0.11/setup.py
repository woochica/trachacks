#!/usr/bin/env python

from setuptools import setup

setup(
	name='TracUserPagePlugin',
	description='Personal and protected per-user pages for Trac',
	keywords='trac userpage',
	version='0.11.1.1',
	url='http://trac-hacks.org/wiki/TracUserPagePlugin',
	license='''
This software is in the Public Domain.

Representations, Warranties and Disclaimer.

ALL PUBLIC DOMAIN MATERIAL IS OFFERED AS-IS. NO REPRESENTATIONS OR
WARRANTIES OF ANY KIND ARE MADE CONCERNING THE MATERIALS, EXPRESS,
IMPLIED, STATUTORY OR OTHERWISE, INCLUDING, WITHOUT LIMITATION,
WARRANTIES OF TITLE, MERCHANTIBILITY, FITNESS FOR A PARTICULAR PURPOSE,
NONINFRINGEMENT, OR THE ABSENCE OF LATENT OR OTHER DEFECTS, ACCURACY, OR
THE PRESENCE OF ABSENCE OF ERRORS, WHETHER OR NOT DISCOVERABLE.

Limitation on Liability.

IN NO EVENT WILL THE AUTHOR(S), PUBLISHER(S), OR PRESENTER(S) OF ANY
PUBLIC DOMAIN MATERIAL BE LIABLE TO YOU ON ANY LEGAL THEORY FOR ANY
SPECIAL, INCIDENTAL, CONSEQUENTIAL, PUNITIVE OR EXEMPLARY DAMAGES
ARISING OUT OF THIS LICENSE OR THE USE OF THE WORK, EVEN IF THE
AUTHOR(S), PUBLISHER(S), OR PRESENTER(S) HAVE BEEN ADVISED OF THE
POSSIBILITY OF SUCH DAMAGES.
''',
	author='David Champion',
	author_email='dgc@uchicago.edu',
	zip_safe=True,
	packages=['UserPagePlugin'],
	entry_points={'trac.plugins': 'userpage = UserPagePlugin.UserPagePlugin'},
	)
