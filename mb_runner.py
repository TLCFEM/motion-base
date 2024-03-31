#  Copyright (C) 2022-2024 Theodore Chang
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

from mb import run_app, Config

if __name__ == "__main__":
    config = Config()
    index = 1
    while index < len(sys.argv):
        if sys.argv[index].startswith("w"):
            config.workers = int(sys.argv[index + 1])
            index += 2
        elif sys.argv[index].startswith("h"):
            config.host = sys.argv[index + 1]
            index += 2
        elif sys.argv[index].startswith("p"):
            config.port = int(sys.argv[index + 1])
            index += 2
        elif sys.argv[index].startswith("o"):
            config.overwrite_env = True
            index += 1
        elif sys.argv[index].startswith("c"):
            config.celery = True
            index += 1
        elif sys.argv[index].startswith("d"):
            config.debug = True
            index += 1
        else:
            index += 1

    print(f"Run the app with the following arguments: {config.dict()}")
    run_app(config)
