from itertools import chain

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = list(chain(collect_submodules("celery"), collect_submodules("kombu")))
