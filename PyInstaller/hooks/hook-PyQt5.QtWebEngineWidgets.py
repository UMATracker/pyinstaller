#-----------------------------------------------------------------------------
# Copyright (c) 2014-2018, PyInstaller Development Team.
#
# Distributed under the terms of the GNU General Public License with exception
# for distributing bootloader.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import os
from PyInstaller.utils.hooks import add_qt5_dependencies, \
    remove_prefix, get_module_file_attribute, pyqt5_library_info, \
    collect_system_data_files
from PyInstaller.depend.bindepend import getImports
import PyInstaller.compat as compat

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)

# Include the web engine process, translations, and resources.
rel_data_path = ['PyQt5', 'Qt']
rel_framework_path = ['lib', 'QtWebEngineCore.framework']
data_path = pyqt5_library_info.location['DataPath']
framework_path = os.path.join(data_path, *rel_framework_path)
is_framework_build = os.path.exists(framework_path)
if compat.is_darwin and is_framework_build:
    # This is based on the layout of the Mac wheel from PyPi.
    resources = rel_framework_path + ['Resources']
    web_engine_process = rel_framework_path + ['Helpers']
    # When Python 3.4 goes EOL (see
    # `PEP 448 <https://www.python.org/dev/peps/pep-0448/>`_, this is
    # better written as ``os.path.join(*rel_data_path, *resources[:-1])``.
    datas += collect_system_data_files(
        os.path.join(data_path, *resources),
        os.path.join(*(rel_data_path + resources[:-1])), True)
    datas += collect_system_data_files(
        os.path.join(data_path, *web_engine_process),
        os.path.join(*(rel_data_path + web_engine_process[:-1])), True)
else:
    locales = 'qtwebengine_locales'
    resources = 'resources'
    datas += [
        # Gather translations needed by Chromium.
        (os.path.join(pyqt5_library_info.location['TranslationsPath'],
                      locales),
         os.path.join('PyQt5', 'Qt', 'translations', locales)),
        # Per the `docs <https://doc.qt.io/qt-5.10/qtwebengine-deploying.html#deploying-resources>`_,
        # ``DataPath`` is the base directory for ``resources``.
        #
        # When Python 3.4 goes EOL (see `PEP 448`_, this is better written as
        # ``os.path.join(*rel_data_path, resources)``.
        (os.path.join(data_path, resources),
         os.path.join(*(rel_data_path + [resources])))
    ]
    binaries += [
        # Include the webengine process.
        #
        # Again, rewrite when Python 3.4 is EOL to
        # ``os.path.join(*rel_data_path, remove_prefix(...``.
        (os.path.join(pyqt5_library_info.location['LibraryExecutablesPath'],
                      'QtWebEngineProcess*'),
         os.path.join(*(rel_data_path +
                      [remove_prefix(pyqt5_library_info.location['LibraryExecutablesPath'],
                                    pyqt5_library_info.location['PrefixPath'] + '/')])))
    ]

# Add Linux-specific libraries.
if compat.is_linux:
    # The automatic library detection fails for `NSS
    # <https://packages.ubuntu.com/search?keywords=libnss3>`_, which is used by
    # QtWebEngine. In some distributions, the ``libnss`` supporting libraries
    # are stored in a subdirectory ``nss``. Since ``libnss`` is not statically
    # linked to these, but dynamically loads them, we need to search for and add
    # them.
    #
    # First, get all libraries linked to ``PyQt5.QtWebEngineWidgets``.
    for imp in getImports(get_module_file_attribute('PyQt5.QtWebEngineWidgets')):
        # Look for ``libnss3.so``.
        if os.path.basename(imp).startswith('libnss3.so'):
            # Find the location of NSS: given a ``/path/to/libnss.so``,
            # add ``/path/to/nss/*.so`` to get the missing NSS libraries.
            binaries.append((os.path.join(os.path.dirname(imp), 'nss', '*.so'),
                             'nss'))
