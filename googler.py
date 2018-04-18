#!/usr/bin/env python3
#
# googler
#
#

import argparse
import atexit
import base64
import collections
import codecs
import functools
import gzip
import html.entities
import html.parser
import http.client
from http.client import HTTPSConnection
import locale
import logging
import os
import signal
import socket
import ssl
import subprocess
import sys
import textwrap
import urllib.parse
import webbrowser

logging.basicConfig(format='[%(levelname)s] %(message)s')
logger = logging.getLogger()
_VERSION_ = '3.3'

# Disguise as Firefox on Ubuntu
USER_AGENT = ('Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:54.0) Gecko/20100101 Firefox/54.0')
ua = True  # User Agent is enabled by default

ENABLE_SELF_UPGRADE_MECHANISM = False

def printerr(msg):
    print(msg, file=sys.stderr)


def unwrap(text):
    lines = text.split('\n')
    result = ''
    for i in range(len(lines) - 1):
        result += lines[i]
        if not lines[i]:
            # Paragraph break
            result += '\n\n'
        elif lines[i + 1]:
            # Next line is not paragraph break, add space
            result += ' '
    # Handle last line
    result += lines[-1] if lines[-1] else '\n'
    return result

class TLS1_2Connection(HTTPSConnection):

    def __init__(self, host, **kwargs):
        HTTPSConnection.__init__(self, host, **kwargs)

    def connect(self, notweak=False):
        sock = socket.create_connection((self.host, self.port),
                                        self.timeout, self.source_address)

        # Optimizations not available on OS X
        if not notweak and sys.platform.startswith('linux'):
            try:
                sock.setsockopt(socket.SOL_TCP, socket.TCP_DEFER_ACCEPT, 1)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 524288)
            except OSError:
                # Doesn't work on Windows' Linux subsystem (#179)
                logger.debug('setsockopt failed')

        if getattr(self, '_tunnel_host', None):
            self.sock = sock
        elif not notweak:
            # Try to use TLS 1.2
            ssl_context = None
            if hasattr(ssl, 'PROTOCOL_TLS'):
                # Since Python 3.5.3
                ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
                ssl_context.options |= (ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 |
                                        ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1)
            elif hasattr(ssl, 'PROTOCOL_TLSv1_2'):
                # Since Python 3.4
                ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
            if ssl_context:
                self.sock = ssl_context.wrap_socket(sock)
                return

        # Fallback
        HTTPSConnection.connect(self)


class GoogleUrl(object):
    def __init__(self, opts=None, **kwargs):
        self.scheme = 'https'
        # self.netloc is a calculated property
        self.path = '/search'
        self.params = ''
        # self.query is a calculated property
        self.fragment = ''

        self._tld = None
        self._num = 10
        self._start = 0
        self._keywords = []
        self._sites = None
        self._query_dict = {
            'ie': 'UTF-8',
            'oe': 'UTF-8',
        }
        self.update(opts, **kwargs)

    def __str__(self):
        return self.url

    @property
    def url(self):
        return self.full()
    @property
    def hostname(self):
        return self.netloc
    @hostname.setter
    def hostname(self, hostname):
        self.netloc = hostname
    @property
    def keywords(self):
        return self._keywords
    @keywords.setter
    def keywords(self, keywords):
        self._keywords = keywords
    @property
    def news(self):
        return 'tbm' in self._query_dict and self._query_dict['tbm'] == 'nws'
    def full(self):
        url = (self.scheme + ':') if self.scheme else ''
        url += '//' + self.netloc + self.relative()
        return url

    def relative(self):
        rel = self.path
        if self.params:
            rel += ';' + self.params
        if self.query:
            rel += '?' + self.query
        if self.fragment:
            rel += '#' + self.fragment
        return rel

    def update(self, opts=None, **kwargs):

        if opts is None:
            opts = {}
        if hasattr(opts, '__dict__'):
            opts = opts.__dict__
        opts.update(kwargs)

        qd = self._query_dict
        if 'duration' in opts and opts['duration']:
            qd['tbs'] = 'qdr:%s' % opts['duration']
        if 'exact' in opts:
            if opts['exact']:
                qd['nfpr'] = 1
            else:
                qd.pop('nfpr', None)
        if 'keywords' in opts:
            self._keywords = opts['keywords']
        if 'lang' in opts and opts['lang']:
            qd['hl'] = opts['lang']
        if 'news' in opts:
            if opts['news']:
                qd['tbm'] = 'nws'
            else:
                qd.pop('tbm', None)
        if 'num' in opts:
            self._num = opts['num']
        if 'sites' in opts:
            self._sites = opts['sites']
        if 'start' in opts:
            self._start = opts['start']
        if 'tld' in opts:
            self._tld = opts['tld']
        if 'unfilter' in opts and opts['unfilter']:
            qd['filter'] = 0

    def set_queries(self, **kwargs):
        for k, v in kwargs.items():
            self._query_dict[k] = v

    def unset_queries(self, *args):
        for k in args:
            self._query_dict.pop(k, None)

    def next_page(self):

        self._start += self._num

    def prev_page(self):
        if self._start == 0:
            raise ValueError('Already at the first page.')
        self._start = (self._start - self._num) if self._start > self._num else 0

    def first_page(self):
        if self._start == 0:
            raise ValueError('Already at the first page.')
        self._start = 0
    @property
    def netloc(self):
        return 'www.google.com'

    @property
    def query(self):
        qd = {}
        qd.update(self._query_dict)
        if self._num != 10:
            qd['num'] = self._num
        if self._start:
            qd['start'] = self._start
        q = ''
        keywords = self._keywords
        sites = self._sites
        if keywords:
            if isinstance(keywords, list):
                q += '+'.join(urllib.parse.quote_plus(kw) for kw in keywords)
            else:
                q += urllib.parse.quote_plus(keywords)
        if sites:
            q += '+OR'.join('+site:' + urllib.parse.quote_plus(site) for site in sites)
        qd['q'] = q

        return '&'.join('%s=%s' % (k, qd[k]) for k in sorted(qd.keys()))
    @netloc.setter
    def netloc(self, value):
        self._netloc = value


class GoogleConnectionError(Exception):
    pass


class GoogleConnection(object):

    def __init__(self, host, port=None, timeout=45, proxy=None, notweak=False):
        self._host = None
        self._port = None
        self._proxy = proxy
        self._notweak = notweak
        self._conn = None
        self.new_connection(host, port=port, timeout=timeout)
        self.cookie = ''

    @property
    def host(self):
        return self._host

    def new_connection(self, host=None, port=None, timeout=45):
        if self._conn:
            self._conn.close()
        if not host:
            host = self._host
            port = self._port
        self._host = host
        self._port = port
        host_display = host + (':%d' % port if port else '')
        logger.debug('Connecting to new host %s', host_display)
        self._conn = TLS1_2Connection(host, port=port, timeout=timeout)
        try:
            self._conn.connect(self._notweak)
        except Exception as e:
            msg = 'Failed to connect to %s: %s.' % (host_display, e)
            raise GoogleConnectionError(msg)

    def renew_connection(self, timeout=45):
        self.new_connection(timeout=timeout)

    def fetch_page(self, url):
        try:
            self._raw_get(url)
        except (http.client.HTTPException, OSError) as e:
            logger.debug('Got exception: %s.', e)
            logger.debug('Attempting to reconnect...')
            self.renew_connection()
            try:
                self._raw_get(url)
            except http.client.HTTPException as e:
                logger.debug('Got exception: %s.', e)
                raise GoogleConnectionError("Failed to get '%s'." % url)

        resp = self._resp
        redirect_counter = 0
        while resp.status != 200 and redirect_counter < 3:
            if resp.status in {301, 302, 303, 307, 308}:
                redirection_url = resp.getheader('location', '')
                if 'sorry/IndexRedirect?' in redirection_url or 'sorry/index?' in redirection_url:
                    raise GoogleConnectionError('Connection blocked due to unusual activity.')
                self._redirect(redirection_url)
                resp = self._resp
                redirect_counter += 1
            else:
                break

        if resp.status != 200:
            raise GoogleConnectionError('Got HTTP %d: %s' % (resp.status, resp.reason))

        payload = resp.read()
        try:
            return gzip.decompress(payload).decode('utf-8')
        except OSError:
            # Not gzipped
            return payload.decode('utf-8')

    def _redirect(self, url):
        logger.debug('Redirecting to URL %s', url)
        segments = urllib.parse.urlparse(url)

        host = segments.netloc
        if host != self._host:
            self.new_connection(host)

        relurl = urllib.parse.urlunparse(('', '') + segments[2:])
        try:
            self._raw_get(relurl)
        except http.client.HTTPException as e:
            logger.debug('Got exception: %s.', e)
            raise GoogleConnectionError("Failed to get '%s'." % url)

    def _raw_get(self, url):
        logger.debug('Fetching URL %s', url)
        self._conn.request('GET', url, None, {
            'Accept-Encoding': 'gzip',
            'User-Agent': USER_AGENT if ua else '',
            'Cookie': self.cookie,
            'Connection': 'keep-alive',
            'DNT': '1',
        })
        self._resp = self._conn.getresponse()
        if self.cookie == '':
            complete_cookie = self._resp.getheader('Set-Cookie')
            # Cookie won't be available is already blocked
            if complete_cookie is not None:
                self.cookie = complete_cookie[:complete_cookie.find(';')]
                logger.debug('Cookie: %s' % self.cookie)

    def close(self):

        if self._conn:
            self._conn.close()


def annotate_tag(annotated_starttag_handler):

    def handler(self, tag, attrs):
        # Get context; assumes that the handler is called SCOPE_start
        context = annotated_starttag_handler.__name__[:-6]

        # If context is 'ignore', ignore all tests
        if context == 'ignore':
            self.insert_annotation(tag, None)
            return

        attrs = dict(attrs)

        # Compare against ignore list
        ignored = False
        for selector in self.IGNORE_LIST:
            for attr in selector:
                if attr == 'tag':
                    if tag != selector['tag']:
                        break
                elif attr == 'class':
                    tag_classes = set(self.classes(attrs))
                    selector_classes = set(self.classes(selector))
                    if not selector_classes.issubset(tag_classes):
                        break
                else:
                    if attrs[attr] != selector[attr]:
                        break
            else:
                # Passed all criteria of the selector
                ignored = True
                break

        # If tag matches ignore list, annotate and hand over to ignore_*
        if ignored:
            self.insert_annotation(tag, context + '_ignored')
            self.set_handlers_to('ignore')
            return

        # Standard
        annotation = annotated_starttag_handler(self, tag, attrs)
        self.insert_annotation(tag, annotation)

    return handler


def retrieve_tag_annotation(annotated_endtag_handler):
    def handler(self, tag):
        try:
            annotation = self.tag_annotations[tag].pop()
        except IndexError:
            # Malformed HTML -- more close tags than open tags
            annotation = None
        annotated_endtag_handler(self, tag, annotation)

    return handler


class Sitelink(object):

    def __init__(self, title, url, abstract):
        self.title = title
        self.url = url
        self.abstract = abstract
        self.index = ''
class GooglerCmdException(Exception):
    pass
class NoKeywordsException(GooglerCmdException):
    pass


def require_keywords(method):
    @functools.wraps(method)
    def enforced_method(self, *args, **kwargs):
        if not self.keywords:
            raise NoKeywordsException('No keywords.')
        method(self, *args, **kwargs)

    return enforced_method


def no_argument(method):
    @functools.wraps(method)
    def enforced_method(self, arg):
        if arg:
            method_name = arg.__name__
            command_name = method_name[3:] if method_name.startswith('do_') else method_name
            logger.warning("Argument to the '%s' command ignored.", command_name)
        method(self)

    return enforced_method