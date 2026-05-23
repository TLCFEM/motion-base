from itertools import chain

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = list(chain(collect_submodules("taskiq"), collect_submodules("taskiq_aio_pika")))
