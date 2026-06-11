# Copyright (C) 2026 Jakub T. Jankiewicz <https://jcu.bi/>
#
# This file is part of expression.py.
#
# expression.py is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# expression.py is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with expression.py. If not, see <https://www.gnu.org/licenses/>.

import os
import subprocess
import sys

from setuptools import setup
from setuptools.command.build_py import build_py


GRAMMAR_PATH = os.path.join("expression", "grammar.peg")
PARSER_PATH = os.path.join("expression", "parser.py")


def generate_parser():
    if not os.path.exists(GRAMMAR_PATH):
        return
    if os.path.exists(PARSER_PATH):
        if os.path.getmtime(PARSER_PATH) >= os.path.getmtime(GRAMMAR_PATH):
            return
    subprocess.check_call(
        [sys.executable, "-m", "pegen", GRAMMAR_PATH, "-o", PARSER_PATH]
    )


class BuildPy(build_py):
    def run(self):
        generate_parser()
        super().run()


setup(cmdclass={"build_py": BuildPy})
