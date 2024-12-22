#  Copyright (C) 2022-2025 Theodore Chang
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sys
from multiprocessing import freeze_support

from mb import run_app, Config


def config_and_run():
    config = Config()
    index = 1

    def next_arg():
        nonlocal index
        index += 1
        if index >= len(sys.argv):
            raise Exception("Missing argument.")
        return sys.argv[index]

    while index < len(sys.argv):
        if sys.argv[index].startswith("c"):
            config.celery = True
            config.celery_config = sys.argv[index + 1 :]
            break

        if sys.argv[index].startswith("w"):
            config.workers = int(next_arg())
        elif sys.argv[index].startswith("h"):
            config.host = next_arg()
        elif sys.argv[index].startswith("p"):
            config.port = int(next_arg())
        elif sys.argv[index].startswith("o"):
            config.overwrite_env = True
        elif sys.argv[index].startswith("d"):
            config.debug = True

        index += 1

    run_app(config)


if __name__ == "__main__":
    freeze_support()
    config_and_run()
