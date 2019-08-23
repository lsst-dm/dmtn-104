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
import sys

import click
import pandoc
from jinja2 import Environment, PackageLoader, TemplateNotFound, ChoiceLoader, FileSystemLoader
from base64 import b64encode

from .config import Config
from .util import mdTree, dms, dmcmp
from .mdtree import build_md_tree


@click.group()
@click.option('--namespace', default='dm', help='Project namespace (dm, ts, example, etc..). '
                                                'Defaults to "dm".')
def cli(namespace):
    """Docsteady generates documents from Jira with the Adaptavist
    Test Management plugin.
    """
    Config.MODE_PREFIX = f"{namespace.lower()}-" if namespace else ""
    Config.DOC = pandoc.Document()


def _as_output_format(text):
    if Config.TEMPLATE_LANGUAGE != OUTPUT_FORMAT:
        setattr(Config.DOC, Config.TEMPLATE_LANGUAGE, text.encode("utf-8"))
        text = getattr(Config.DOC, OUTPUT_FORMAT).decode("utf-8")
    return text


@cli.command("generate")
@click.option('--format', default='latex', help='Pandoc output format (see pandoc for options)')
@click.option('--username', prompt="MagicDraw Username", envvar="MD_USER", help="MagicDraw username")
@click.option('--password', prompt="MagicDraw Password", hide_input=True,
              envvar="MD_PASSWORD", help="MagicDraw Password")
@click.option('--inputf', default="DMProductsProperties.csv")
@click.argument('element_id', required=False)
def generate(format, username, password, element_id, inputf):
    """Generate product tree document
    """

    global OUTPUT_FORMAT
    OUTPUT_FORMAT = format

    usr_pwd = username + ":" + password
    Config.CONNECTION_ID = b64encode(usr_pwd.encode()).decode("ascii")

    # rs = requests.Session()
    # rs.headers = headers
    # ptree = build_mdtree(rs, dms, dmcmp)
    # print('Products found:', len(ptree))
    # for c in ptree:
    #    print(c['name'])

    # init()

    print(mdTree.depth())
    build_md_tree(dms, dmcmp)
    # print(mdTree)
    print(mdTree.depth())
    md_products = []
    nodes = mdTree.expand_tree()
    mdtree_dict = {}

    for n in nodes:
        # print(mdTree[n].data.name)
        md_products.append(mdTree[n].data)
        # print(mdTree[n].data.name)
        mdtree_dict[mdTree[n].data.id] = mdTree[n].data

    mdp = mdTree.to_dict(with_data=False)

    # for k0 in mdp:
    #    # print(k0, mdtree_dict[k0].name, mdtree_dict[k0].manager, mdtree_dict[k0].owner)
    #    for child in mdp[k0]['children']:
    #        for k1 in child:
    #            # print(" - ", k1, mdtree_dict[k1].name, mdtree_dict[k1].manager, mdtree_dict[k1].owner)
    #            for subchild in child[k1]['children']:
    #                if isinstance(subchild, dict):
    #                    for k2 in subchild:
    #                        # print("  -- ", k2, mdtree_dict[k2].name, mdtree_dict[k2].manager, mdtree_dict[k2].owner)
    #                        for sch1 in subchild[k2]['children']:
    #                            print("    + ", sch1, mdtree_dict[sch1].owner, mdtree_dict[sch1].pkgs)
    #                else:
    #                    print("   + ", subchild, mdtree_dict[subchild].owner)

    file = open("toplevel1.tex", "w")

    env = Environment(loader=ChoiceLoader([
        FileSystemLoader(Config.TEMPLATE_DIRECTORY),
        PackageLoader('ptree', 'templates')
        ]),
        lstrip_blocks=True, trim_blocks=True,
        autoescape=None
    )

    try:
        template_path = f"ptree.{Config.TEMPLATE_LANGUAGE}.jinja2"
        template = env.get_template(template_path)
    except TemplateNotFound as e:
        click.echo(f"No Template Found: {template_path}", err=True)
        sys.exit(1)

    metadata = dict()
    metadata["template"] = template.filename
    text = template.render(metadata=metadata,
                           mdt_dict=mdtree_dict,
                           mdp=mdp,
                           mdps=md_products)

    print(_as_output_format(text), file=file)


if __name__ == '__main__':
    cli()
