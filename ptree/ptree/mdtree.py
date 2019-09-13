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

"""
Code for generation Product Tree document from MagicDraw
"""
import requests
import click
import sys
from .config import Config
from jinja2 import Environment, PackageLoader, TemplateNotFound, ChoiceLoader, FileSystemLoader
from .util import get_pkg_properties, mdTree, rsget, fix_tex, fix_id_tex, Product, html_to_latex
from .tree import make_tree_portrait, make_tree_landmix


def _as_output_format(text, output_format):
    if Config.TEMPLATE_LANGUAGE != output_format:
        setattr(Config.DOC, Config.TEMPLATE_LANGUAGE, text.encode("utf-8"))
        text = getattr(Config.DOC, output_format).decode("utf-8")
    return text


def get_dep_key(rcs, mres, mdid):
    resp = rsget(rcs, Config.MD_COMP_URL.format(res=mres, comp=mdid), True)
    dep_pkgs = dict()

    for element in resp[1]['kerml:esiData']['relatedElement']:
        tmpresp = rsget(rcs, Config.MD_COMP_URL.format(res=mres, comp=element['@id']), True)
        tmpname = fix_tex(tmpresp[1]['kerml:name']).lstrip('0123456789.- ')
        tmp_pkg_props = dict()
        for el in tmpresp[0]['ldp:contains']:
            tmp = rsget(rcs, Config.MD_COMP_URL.format(res=mres, comp=el['@id']), True)
            if tmp[1]['@type'] == 'uml:InstanceSpecification':
                tmp_pkg_props = get_pkg_properties(rcs, mres, el['@id'])
        tmp_pkg_id = fix_id_tex(tmp_pkg_props['product key'][0])
        dep_pkgs[tmp_pkg_id] = tmpname

    return dep_pkgs


def get_pkg_key(rcs, mres, mdid):
    resp = rsget(rcs, Config.MD_COMP_URL.format(res=mres, comp=mdid), True)

    diagram_ids = []

    if resp[1]['kerml:esiData']['ownedDiagram']:
        for dia in resp[1]['kerml:esiData']['ownedDiagram']:
            diagram_ids.append(dia['@id'])

    dependency = dict()

    dependency['name'] = fix_tex(resp[1]['kerml:name']).lstrip('0123456789.- ')

    pkg_properties = dict()

    for el in resp[0]['ldp:contains']:
        tmp = rsget(rcs, Config.MD_COMP_URL.format(res=mres, comp=el['@id']), True)
        if tmp[1]['@type'] == 'uml:InstanceSpecification':
            pkg_properties = get_pkg_properties(rcs, mres, el['@id'])
        else:
            continue

    if "product key" in pkg_properties.keys():
        dependency["key"] = pkg_properties['product key'][0]
    else:
        dependency["key"] = ""
    if "short name" in pkg_properties.keys():
        dependency["shortname"] = pkg_properties['short name'][0]
    else:
        dependency["shortname"] = ""

    dependency['diagrams'] = diagram_ids

    return dependency


def walk_tree(rcs, mres, mdid, pkey):
    """ Product Class Object
    id, name, parent, desc, wbs, manager, owner, kind, pkgs, elId"""

    global products_count
    products_count = products_count + 1

    resp = rsget(rcs, Config.MD_COMP_URL.format(res=mres, comp=mdid), True)
    if resp[1]['@type'] not in ('uml:Package', 'uml:Class'):
        print('Error: no package given containing the Product Tree')
        exit()
    pkg_name = fix_tex(resp[1]['kerml:name']).lstrip('0123456789.- ')
    print(f"{{pc}}: {{pn}}".format(pc=products_count,pn=pkg_name), end='')
    pkg_sub_pkgs = []
    pkg_classes = []
    pkg_comments = ""
    pkg_properties = dict()
    pkg_depends = []
    pkg_usedin = []

    for el in resp[0]['ldp:contains']:
        tmp = rsget(rcs, Config.MD_COMP_URL.format(res=mres, comp=el['@id']), True)
        if tmp[1]['@type'] == 'uml:Package':
            pkg_sub_pkgs.append(el['@id'])
        elif tmp[1]['@type'] == 'uml:Class':
            pkg_classes.append(el['@id'])
        elif tmp[1]['@type'] == 'uml:InstanceSpecification':
            pkg_properties = get_pkg_properties(rcs, mres, el['@id'])
            if 'product key' in pkg_properties.keys():
                print(f" ({{k}}), ".format(k=pkg_properties['product key'][0]), end='')
                sys.stdout.flush()
            else:
                print(" () ", end="")
        elif tmp[1]['@type'] == 'uml:Property':
            continue
        elif tmp[1]['@type'] == 'uml:Comment':
            pkg_comments = pkg_comments + tmp[1]['kerml:esiData']['body']
        elif tmp[1]['@type'] in ('uml:Abstraction', 'uml:Diagram', 'uml:Association', 'uml:Dependency'):
            continue
        else:
            print('Unmapped type: ', tmp[1]['@type'], el['@id'])

    # get dependencies
    if resp[1]['@type'] == 'uml:Class':
        if resp[1]['kerml:esiData']['_typedElementOfType']:
            for typed in resp[1]['kerml:esiData']['_typedElementOfType']:
                typed_id = typed['@id']
                tmp = rsget(rcs, Config.MD_COMP_URL.format(res=mres, comp=typed_id), True)
                owned_member_id = ""
                typed_namespace_ofmember0 = tmp[1]['kerml:esiData']['_namespaceOfMember'][0]['@id']
                if len(tmp[1]['kerml:esiData']['_namespaceOfMember']) > 1:
                    typed_namespace_ofmember1 = tmp[1]['kerml:esiData']['_namespaceOfMember'][1]['@id']
                else:
                    typed_namespace_ofmember1 = ""
                aggregation = ""
                # get association
                if tmp[1]['kerml:esiData']['association']:
                    asid = tmp[1]['kerml:esiData']['association']['@id']
                    typed_aggregation = tmp[1]['kerml:esiData']['aggregation']
                    if asid == typed_namespace_ofmember1:
                        relation_id = typed_namespace_ofmember0
                        relation = get_pkg_key(rcs, mres, relation_id)
                        if len(relation['diagrams']) == 0:
                            if typed_aggregation == "composite":
                                if relation not in pkg_usedin:
                                    pkg_usedin.append(relation)
                            else:
                                if relation not in pkg_depends:
                                    pkg_depends.append(relation)
                    elif typed_aggregation == "composite" and typed_namespace_ofmember1 != "":
                        relation_id = typed_namespace_ofmember1
                        relation = get_pkg_key(rcs, mres, relation_id)
                        if len(relation['diagrams']) == 0:
                            if relation not in pkg_usedin:
                                pkg_usedin.append(relation)
                    else:
                        association = rsget(rcs, Config.MD_COMP_URL.format(res=mres, comp=asid), True)
                        asmember0 = association[1]['kerml:esiData']['member'][0]['@id']
                        asmember1 = association[1]['kerml:esiData']['member'][1]['@id']
                        asmemberend0 = association[1]['kerml:esiData']['memberEnd'][0]['@id']
                        asmemberend1 = association[1]['kerml:esiData']['memberEnd'][1]['@id']
                        kerml_owner_id = tmp[1]['kerml:owner']['@id']
                        if asid == kerml_owner_id:
                            # get relation from ownedMember - type
                            if asmemberend0 != typed_id:
                                owned_member_id = asmemberend0
                            else:
                                owned_member_id = asmemberend1
                            # print("        - ownedMember: ", owned_member_id)
                            owned_member_json = rsget(rcs, Config.MD_COMP_URL.format(res=mres, comp=owned_member_id),
                                                      True)
                            relation_id = owned_member_json[1]['kerml:esiData']['type']['@id']
                            aggregation = owned_member_json[1]['kerml:esiData']['aggregation']
                        else:
                            relation_id = tmp[1]['kerml:owner']['@id']
                        relation = get_pkg_key(rcs, mres, relation_id)
                        # I consider the association only if the target id not a diagram (ibd)
                        if len(relation['diagrams']) == 0:
                            if (owned_member_id != "") and (aggregation == "composite"):
                                if relation not in pkg_depends:
                                    pkg_depends.append(relation)
                            else:
                                if (asmemberend1 == typed_id) and ((asmember0 == typed_id) or (asmember1 == typed_id)):
                                    if relation not in pkg_usedin:
                                        pkg_depends.append(relation)
                                else:
                                    if relation not in pkg_usedin:
                                        pkg_usedin.append(relation)

    pkg_id = fix_id_tex(pkg_properties['product key'][0])
    prod = Product(pkg_id,                            # 1  (0 is self)
                   pkg_name,                          # 2
                   pkey,                              # 3
                   html_to_latex(pkg_comments),     # 4
                   pkg_properties["WBS"],             # 5
                   pkg_properties["manager"][0],      # 6
                   pkg_properties["product owner"],   # 7
                   "",                                # 8
                   pkg_properties["packages"],        # 9
                   pkg_depends,                       # 10
                   mdid,                              # 11
                   pkg_properties["hyperlinkText"],   # 12
                   pkg_properties["team"],            # 13
                   pkg_properties["short name"][0],   # 14
                   pkg_usedin)                              # 15
    if pkey == "":  # first node in the tree
        mdTree.create_node(prod.id, prod.id, data=prod)
    else:
        # print(mdTree)
        if pkey != '':
            mdTree.create_node(prod.id, prod.id, data=prod, parent=prod.parent)
        else:
            print('No parent for product:', pkg_name)
            exit()

    for pkg in pkg_sub_pkgs:
        walk_tree(rcs, mres, pkg, pkg_id)

    for cls in pkg_classes:
        walk_tree(rcs, mres, cls, pkg_id)


def build_md_tree(mres, mdid, connection_id):
    """ Build the tree reading from MD
    """
    global products_count
    products_count = 0

    headers = {
        'accept': 'application/json',
        'authorization': 'Basic %s' % connection_id,
        'Connection': 'close'
    }

    rs = requests.Session()
    rs.headers = headers

    walk_tree(rs, mres, mdid, "")


def do_csv(products, output_file):
    """
    Create csv file
    :param products:
    :param output_file:
    :return:
    """
    csv = "Product key, Short name, Parent, WBS, Team, Manager, Product owner, Packages, Name\n"
    for p in products:
        pkey = p.id
        snm = p.shortname
        pid = p.parent
        wbs = ' '.join(p.wbs)
        team = p.teams[0]
        mng = p.manager
        owner = p.owner[0]
        pkgs = ' '.join(p.pkgs)
        name = p.name
        csv = csv + f"{pkey}, {snm}, {pid}, {wbs}, {team}, {mng}, {owner}, {pkgs}, {name} \n"
    csv_filename = "csv/" + output_file + ".csv"
    file = open(csv_filename, "w")
    print(csv, file=file)
    file.close()


def do_trees_diagrams(tree, filename, scope):
    """
    Print out the different build trees
    :param tree: dictionary that contains the tree information
    :param filename: output file to write
    :param scope:
    :return: none
    """
    # build the portrait tree
    make_tree_portrait(tree, "trees/" + filename + "_portrait.tex", scope)

    # build landscape tree
    make_tree_landmix(tree, "trees/" + filename + "_mixedLand.tex", scope)

    # build subtrees


def do_md_section(sysid, levelid, connection_str, output_format, output_file):
    """
    Given the MD ids, dump the content in the output file and produce the product tree diagrams
    :param sysid: MagicDraw subsystem id
    :param levelid: MagicDraw level id (package id containing the tree to extract)
    :param connection_str: MagicDraw encoded connection string
    :param output_format: OutputFormat
    :param output_file: File to dump
    :return: none
    """
    global template_path
    products = []
    tree_dict = {}

    # get the information from MagicDraw
    build_md_tree(sysid, levelid, connection_str)
    print("\n  Product tree depth:", mdTree.depth())

    nodes = mdTree.expand_tree()
    for n in nodes:
        products.append(mdTree[n].data)
        tree_dict[mdTree[n].data.id] = mdTree[n].data
    print(f"  Found {{np}} products (including container folders).".format(np=len(tree_dict)))

    envs = Environment(loader=ChoiceLoader([FileSystemLoader(Config.TEMPLATE_DIRECTORY),
                                           PackageLoader('ptree', 'templates')]),
                       lstrip_blocks=True, trim_blocks=True, autoescape=None)

    # dump a csv file
    do_csv(products, output_file)

    # create the diagrams tex files
    do_trees_diagrams(mdTree, output_file, products[0].shortname)

    # dump the tex section
    mdp = mdTree.to_dict(with_data=False)
    try:
        template_path = f"section.{Config.TEMPLATE_LANGUAGE}.jinja2"
        template = envs.get_template(template_path)
    except TemplateNotFound:
        click.echo(f"No Template Found: {template_path}", err=True)
        sys.exit(1)
    metadata = dict()
    metadata["template"] = template.filename
    text = template.render(metadata=metadata,
                           mdt_dict=tree_dict,
                           mdp=mdp,
                           mdps=products)
    tex_file_name = output_file + ".tex"
    file = open(tex_file_name, "w")
    print(_as_output_format(text, output_format), file=file)
    file.close()


def generate_document(subsystem, connection_str, output_format):
    """Given system and level, generates the document content"""

    print("-> Generating Main Product Tree  ==========================")
    subsystem_id = Config.SUBSYSTEMS[subsystem]['ID']  # former dms
    level_id = Config.SUBSYSTEMS[subsystem]['Top']  # former dmcmp
    do_md_section(subsystem_id, level_id, connection_str, output_format, 'Main')

    print("-> [to do] Generating Development Product Tree  ==========================")

    print("-> [to do] Generating GitHub Product Tree  ==========================")

    print("-> [to do] Generating Auxiliary Product Tree  ==========================")
