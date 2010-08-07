#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys

from mongrel2 import handler
import json

from wsgiref.handlers import SimpleHandler
try:
    import cStringIO as StringIO
except:
    import StringIO

DEBUG = True

sender_id = "BA73C5F4-5ADA-4946-8980-1D255EB9A765"

conn = handler.Connection(sender_id, "tcp://127.0.0.1:9997",
                          "tcp://127.0.0.1:9996")

def simple_app(environ, start_response):
    """Simplest possible WSGI application object"""
    status = '200 OK'
    response_headers = [('Content-type','text/plain')]
    start_response(status, response_headers)
    return ['Hello world!\n' for i in range(100)]

def encode_response(data, encoding='utf-8'):
    '''Data is a list of strings'''
    return [d.encode(encoding) for d in data]

def simple_app_utf8(environ, start_response):
    """Simplest possible WSGI application object"""
    status = '200 OK'
    response_headers = [('Content-type','text/plain; charset=utf-8')]
    start_response(status, response_headers)
    return encode_response([u'Héllo wörld!\n' for i in range(100)])

def wsgi_server(application):
    '''WSGI handler based on the Python wsgiref SimpleHandler.
    
    A WSGI application should return a iterable op StringTypes. 
    Any encoding must be handled by the WSGI application itself.
    '''
    
    while True:
        if DEBUG: print "WAITING FOR REQUEST"
        
        req = conn.recv()
        
        if DEBUG: print "REQUEST BODY: %r\n" % req.body
        
        if req.is_disconnect():
            if DEBUG: print "DISCONNECT"
            continue #effectively ignore the disconnect from the client
        
        environ = req.headers
        # Set a couple of environment attributes that are a must according to PEP 333
        environ['SERVER_PROTOCOL'] = u'HTTP/1.1' # SimpleHandler expects a server_protocol
        environ['REQUEST_METHOD'] = environ['METHOD']
        if ':' in environ['Host']:
            environ['SERVER_NAME'] = environ['Host'].split(':')[0]
            environ['SERVER_PORT'] = environ['Host'].split(':')[1]
        else:
            environ['SERVER_NAME'] = environ['Host']
            environ['SERVER_PORT'] = '80'
        environ['SCRIPT_NAME'] = '' # empty for now
        environ['PATH_INFO'] = environ['PATH']
        if '?' in environ['URI']:
            environ['QUERY_STRING'] = environ['URI'].split('?')[1]
        else:
            environ['QUERY_STRING'] = ''
        try:
            environ['CONTENT_LENGTH'] = environ['Content-Length'] # necessary for POST to work with Django
        except:
            pass
        environ['wsgi.input'] = req.body
        
        if DEBUG: print "ENVIRON: %r\n" % environ
        
        # SimpleHandler needs file-like stream objects
        reqIO = StringIO.StringIO(req.body)
        errIO = StringIO.StringIO()
        respIO = StringIO.StringIO()
        
        handler = SimpleHandler(reqIO, respIO, errIO, environ, multithread = False, multiprocess = False)
        handler.run(application)
        
        # Get response and filter out the response (=data) itself,
        # the response headers, 
        # the response status code and the response status description
        response = respIO.getvalue()
        response = response.split("\r\n")
        data = response[-1]
        headers = dict([r.split(": ") for r in response[1:-2]])
        code = response[0][9:12]
        status = response[0][13:]
        
        # strip BOM's from response data
        # Especially the WSGI handler from Django seems to generate them (2 actually, huh?)
        # a BOM isn't really necessary and cause HTML parsing errors in Chrome and Safari
        # See also: http://www.xs4all.nl/~mechiel/projects/bomstrip/
        # Although I still find this a ugly hack.
        data = data.replace('\xef\xbb\xbf', '')
        
        # Get the generated errors
        errors = errIO.getvalue()
        
        if DEBUG: print "RESPONSE: %r\n" % response
        if errors:
            if DEBUG: print "ERRORS: %r" % errors
            data = "%s\r\n\r\n%s" % (data, errors)            
        conn.reply_http(req, data, code = code, status = status, headers = headers)

if __name__ == "__main__":
    
    # Simple WSGI application
    simple_application = simple_app

    # Simple WSGI application with utf-8 response
    simple_utf8_application = simple_app_utf8
    
    # WSGI Test page
    import test_wsgi_app
    wsgi_test_application = test_wsgi_app.application
    
    # Django demo app
    sys.path.append('/home/berry/git/django/')
    sys.path.append('/home/berry/git/')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'djangodemo.settings'
    
    import django.core.handlers.wsgi
    django_application = django.core.handlers.wsgi.WSGIHandler()
    
    # Start WSGI application
    # wsgi_server(simple_application)
    # wsgi_server(simple_utf8_application)
    # wsgi_server(wsgi_test_application)
    wsgi_server(django_application)
