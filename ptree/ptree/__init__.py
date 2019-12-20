# LSST Data Management System
# Copyright 2018 AURA/LSST.
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <http://www.lsstcorp.org/LegalNotices/>.

import click
import pandoc
from base64 import b64encode

from .config import Config
from .mdtree import generate_document


@click.group()
@click.option('--namespace', default='dm', help='Project namespace (dm, ts, example, etc..). '
                                                'Defaults to "dm".')
def cli(namespace):
    """Docsteady generates documents from Jira with the Adaptavist
    Test Management plugin.
    """
    Config.MODE_PREFIX = f"{namespace.lower()}-" if namespace else ""
    Config.DOC = pandoc.Document()


@cli.command("generate")
@click.option('--format', default='latex', help='Pandoc output format (see pandoc for options)')
@click.option('--compact/--no-compact', default=True, help='Ladscape Product Tree compact (default True)')
@click.option('--username', prompt="MagicDraw Username", envvar="MD_USER", help="MagicDraw username")
@click.option('--password', prompt="MagicDraw Password", hide_input=True,
              envvar="MD_PASSWORD", help="MagicDraw Password")
@click.option('--tokenpath', default='~/.sq_github_token', help="Path to the Github generated token")
def generate(format, username, password, tokenpath, compact):
    """Generate product tree document
    """

    if compact:
        cmp = True
    else:
        cmp = False

    usr_pwd = username + ":" + password
    connection_str = b64encode(usr_pwd.encode("ascii")).decode("ascii")

    generate_document(connection_str, format, tokenpath, cmp)


if __name__ == '__main__':
    cli()
