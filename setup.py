#  Copyright (C) 2022-2023 Theodore Chang
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


from setuptools import find_packages, setup


def install():
    major = 0
    minor = 0
    patch = 0

    with open('requirements.txt') as f:
        required = f.read().splitlines()

    setup(
        name='motion-base',
        version=f'{major}.{minor}.{patch}',
        package_dir={
            '': './'
        },
        packages=[f'mb.{pkg}' for pkg in find_packages('./mb')] + ['mb'],
        description='A strong motion database',
        author='Theodore Chang',
        author_email='tlcfem@gmail.com',
        install_requires=required,
        entry_points={
            'console_scripts': [
                'mb = mb:run'
            ]}
    )


if __name__ == '__main__':
    install()
