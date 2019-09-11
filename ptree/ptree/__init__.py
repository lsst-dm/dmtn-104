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
from .util import mdTree, dms, dmcmp
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
@click.option('--username', prompt="MagicDraw Username", envvar="MD_USER", help="MagicDraw username")
@click.option('--password', prompt="MagicDraw Password", hide_input=True,
              envvar="MD_PASSWORD", help="MagicDraw Password")
@click.option('--subsystem', default='DM', help="LSST SubSystem (default DM)")
def generate(format, username, password, subsystem):
    """Generate product tree document
    """

    usr_pwd = username + ":" + password
    connection_id = b64encode(usr_pwd.encode("ascii")).decode("ascii")

    generate_document(subsystem, connection_id, format)


if __name__ == '__main__':
    cli()
