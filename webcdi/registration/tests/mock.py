# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""
Mock request for unittest

This is a modification of django-registration_ ``admin.py``
The original code is written by James Bennett

.. _django-registration: https://bitbucket.org/ubernostrum/django-registration


Original License::

    Copyright (c) 2007-2011, James Bennett
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are
    met:

        * Redistributions of source code must retain the above copyright
        notice, this list of conditions and the following disclaimer.
        * Redistributions in binary form must reproduce the above
        copyright notice, this list of conditions and the following
        disclaimer in the documentation and/or other materials provided
        with the distribution.
        * Neither the name of the author nor the names of other
        contributors may be used to endorse or promote products derived
        from this software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
    A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
    OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
    SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
    LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
    DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
    THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
__author__ = 'Alisue <lambdalisue@hashnote.net>'
from django.contrib.sessions.middleware import SessionMiddleware
from django.test.client import RequestFactory
from registration.utils import get_site


def mock_request():
    """
    Construct and return a mock ``HttpRequest`` object; this is used
    in testing backend methods which expect an ``HttpRequest`` but
    which are not being called from views.
    
    """
    request = RequestFactory().get('/')

    # We have to manually add a session since we'll be bypassing
    # the middleware chain.
    session_middleware = SessionMiddleware()
    session_middleware.process_request(request)

    return request


def mock_site():
    """
    Construct and return a mock `Site`` object; this is used
    in testing methods which expect an ``Site``
    
    """
    return get_site(mock_request())

