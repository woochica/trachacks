#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Gefasoft AG
# Copyright (C) 2011 Franz Mayer <franz.mayer@gefasoft.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import find_packages, setup

setup(
    name='AttachmentPolicyPlugin',
    version='0.1.0',
    author='Gefasoft AG, Franz Mayer',
    author_email='franz.mayer@gefasoft.de',
    description="""Adds permission TICKET_ATTACHMENT_DELETE, so deleting
        attachments can be done without granting the TICKET_ADMIN
        permission""",
    url='https://trac-hacks.org/wiki/AttachmentPolicyPlugin',
    license='BSD 3-Clause',
    packages=find_packages(exclude=['*.tests*']),
    entry_points="""
        [trac.plugins]
        attachmentpolicy = attachmentpolicy
    """,
)
