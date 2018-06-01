from setuptools import setup

setup(
    name='AKlever',
    version='0.94',
    packages=['venv.Lib.site-packages.pip', 'venv.Lib.site-packages.pip._vendor',
              'venv.Lib.site-packages.pip._vendor.idna', 'venv.Lib.site-packages.pip._vendor.pytoml',
              'venv.Lib.site-packages.pip._vendor.certifi', 'venv.Lib.site-packages.pip._vendor.chardet',
              'venv.Lib.site-packages.pip._vendor.chardet.cli', 'venv.Lib.site-packages.pip._vendor.distlib',
              'venv.Lib.site-packages.pip._vendor.distlib._backport', 'venv.Lib.site-packages.pip._vendor.msgpack',
              'venv.Lib.site-packages.pip._vendor.urllib3', 'venv.Lib.site-packages.pip._vendor.urllib3.util',
              'venv.Lib.site-packages.pip._vendor.urllib3.contrib',
              'venv.Lib.site-packages.pip._vendor.urllib3.contrib._securetransport',
              'venv.Lib.site-packages.pip._vendor.urllib3.packages',
              'venv.Lib.site-packages.pip._vendor.urllib3.packages.backports',
              'venv.Lib.site-packages.pip._vendor.urllib3.packages.ssl_match_hostname',
              'venv.Lib.site-packages.pip._vendor.colorama', 'venv.Lib.site-packages.pip._vendor.html5lib',
              'venv.Lib.site-packages.pip._vendor.html5lib._trie',
              'venv.Lib.site-packages.pip._vendor.html5lib.filters',
              'venv.Lib.site-packages.pip._vendor.html5lib.treewalkers',
              'venv.Lib.site-packages.pip._vendor.html5lib.treeadapters',
              'venv.Lib.site-packages.pip._vendor.html5lib.treebuilders', 'venv.Lib.site-packages.pip._vendor.lockfile',
              'venv.Lib.site-packages.pip._vendor.progress', 'venv.Lib.site-packages.pip._vendor.requests',
              'venv.Lib.site-packages.pip._vendor.packaging', 'venv.Lib.site-packages.pip._vendor.cachecontrol',
              'venv.Lib.site-packages.pip._vendor.cachecontrol.caches',
              'venv.Lib.site-packages.pip._vendor.webencodings', 'venv.Lib.site-packages.pip._vendor.pkg_resources',
              'venv.Lib.site-packages.pip._internal', 'venv.Lib.site-packages.pip._internal.req',
              'venv.Lib.site-packages.pip._internal.vcs', 'venv.Lib.site-packages.pip._internal.utils',
              'venv.Lib.site-packages.pip._internal.models', 'venv.Lib.site-packages.pip._internal.commands',
              'venv.Lib.site-packages.pip._internal.operations', 'venv.Lib.site-packages.idna',
              'venv.Lib.site-packages.PyQt5', 'venv.Lib.site-packages.PyQt5.uic',
              'venv.Lib.site-packages.PyQt5.uic.Loader', 'venv.Lib.site-packages.PyQt5.uic.port_v2',
              'venv.Lib.site-packages.PyQt5.uic.port_v3', 'venv.Lib.site-packages.PyQt5.uic.Compiler',
              'venv.Lib.site-packages.gevent', 'venv.Lib.site-packages.gevent.libev', 'venv.Lib.site-packages.lomond',
              'venv.Lib.site-packages.lomond.examples', 'venv.Lib.site-packages.certifi',
              'venv.Lib.site-packages.chardet', 'venv.Lib.site-packages.chardet.cli', 'venv.Lib.site-packages.urllib3',
              'venv.Lib.site-packages.urllib3.util', 'venv.Lib.site-packages.urllib3.contrib',
              'venv.Lib.site-packages.urllib3.contrib._securetransport', 'venv.Lib.site-packages.urllib3.packages',
              'venv.Lib.site-packages.urllib3.packages.backports',
              'venv.Lib.site-packages.urllib3.packages.ssl_match_hostname', 'venv.Lib.site-packages.requests',
              'venv.Lib.site-packages.cx_Freeze', 'venv.Lib.site-packages.websocket',
              'venv.Lib.site-packages.websocket.data', 'venv.Lib.site-packages.websocket.tests',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip', 'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip.req',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip.vcs',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip.utils',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip.compat',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip.models',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip._vendor',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip._vendor.distlib',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip._vendor.distlib._backport',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip._vendor.colorama',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip._vendor.html5lib',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip._vendor.html5lib._trie',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip._vendor.html5lib.filters',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip._vendor.html5lib.treewalkers',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip._vendor.html5lib.treeadapters',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip._vendor.html5lib.treebuilders',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip._vendor.lockfile',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip._vendor.progress',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip._vendor.requests',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip._vendor.requests.packages',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip._vendor.requests.packages.chardet',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip._vendor.requests.packages.urllib3',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip._vendor.requests.packages.urllib3.util',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip._vendor.requests.packages.urllib3.contrib',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip._vendor.requests.packages.urllib3.packages',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip._vendor.requests.packages.urllib3.packages.ssl_match_hostname',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip._vendor.packaging',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip._vendor.cachecontrol',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip._vendor.cachecontrol.caches',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip._vendor.webencodings',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip._vendor.pkg_resources',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip.commands',
              'venv.Lib.site-packages.pip-9.0.1-py3.6.egg.pip.operations'],
    url='',
    license='github.com/TaizoGem/AKlever',
    author='TaizoGem',
    author_email='',
    description='Bot for VK Clever and other trivias, written in python', install_requires=['lomond']
)
