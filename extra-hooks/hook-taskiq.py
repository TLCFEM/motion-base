from itertools import chain

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = list(
    chain(
        collect_submodules("taskiq"),
        collect_submodules("taskiq_aio_pika"),
        collect_submodules("taskiq_mongodb"),
        collect_submodules("aio_pika"),
        collect_submodules("aiormq"),
        collect_submodules("pamqp"),
        collect_submodules("pycron"),
    )
)
