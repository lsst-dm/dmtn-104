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
import os
import csv
from .config import Config
from jinja2 import Environment, PackageLoader, TemplateNotFound, ChoiceLoader, FileSystemLoader
from .util import get_pkg_properties, rsget, fix_tex, fix_id_tex, Product, html_to_latex, get_yaml, _as_output_format
from .tree import make_tree_portrait, make_tree_landmix1, make_subtrees, make_full_tree
from treelib import Tree
from .gittree import do_github_section

requirements = {}


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


def get_requirements(rcs, mres, mdid):
    """
    returns the the requirement id and requirement name for a specific MD id
    """
    req = {}
    # get Association
    association = rsget(rcs, Config.MD_COMP_URL.format(res=mres, comp=mdid), True)
    supplier_id = association[1]["kerml:esiData"]["supplier"][0]['@id']
    if supplier_id in requirements.keys():
        req = requirements[supplier_id]
        # print("  already found:", req['id'])
    else:
        # get Supplier
        supplier = rsget(rcs, Config.MD_COMP_URL.format(res=mres, comp=supplier_id), True)
        req['name'] = fix_tex(supplier[1]["kerml:name"]).lstrip('0123456789.- ')
        ispec_id = supplier[1]["kerml:esiData"]["appliedStereotypeInstance"]['@id']
        ispec = rsget(rcs, Config.MD_COMP_URL.format(res=mres, comp=ispec_id), True)
        for el in ispec[0]["ldp:contains"]:
            tmp_resp = rsget(rcs, Config.MD_COMP_URL.format(res=mres, comp=el['@id']), True)
            # print(tmp_resp[1]["kerml:esiData"]["definingFeature"])
            if tmp_resp[1]["kerml:esiData"]["definingFeature"]['@id'] == "ff8cae42-782e-4158-aed0-56d589bfa42b":
                lpd = tmp_resp[0]["ldp:contains"]
                slot_resp = rsget(rcs, Config.MD_COMP_URL.format(res=mres, comp=lpd[0]['@id']), True)
                # print(slot_resp[0]["@type"])
                req['id'] = slot_resp[1]["kerml:esiData"]["value"]
                if req['id'] != "" and req['name'] != "":
                    requirements[supplier_id] = req
        # print(req)
    return req


def walk_tree(rcs, mres, mdid, pkey):
    """ Product Class Object
    id, name, parent, desc, wbs, manager, owner, kind, pkgs, elId"""

    global products_count
    global productTree
    products_count = products_count + 1

    resp = rsget(rcs, Config.MD_COMP_URL.format(res=mres, comp=mdid), True)
    if resp[1]['@type'] not in ('uml:Package', 'uml:Class'):
        print('Error: no package given containing the Product Tree')
        exit()
    pkg_name = fix_tex(resp[1]['kerml:name']).lstrip('0123456789.- ')
    try:
        pkg_index = int(resp[1]['kerml:name'].split()[0])
    except ValueError:
        pkg_index = ""
    print(f"{products_count}: {pkg_name}.{pkg_index}", end='')
    # print(Config.MD_COMP_URL.format(res=mres, comp=mdid))
    pkg_sub_pkgs = []
    pkg_classes = []
    pkg_comments = ""
    pkg_properties = dict()
    pkg_depends = []
    pkg_usedin = []
    reqs = []

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

    if resp[1]['@type'] == 'uml:Class':
        # get requirements
        if resp[1]['kerml:esiData']['_directedRelationshipOfSource']:
            for rid in resp[1]['kerml:esiData']['_directedRelationshipOfSource']:
                reqs.append(get_requirements(rcs, mres, rid['@id']))
        nreqs = len(reqs)
        if nreqs > 1:
            reqs = sorted(reqs, key= lambda req: req['id'])
        print(f"[{nreqs}] -- ", end='')
        # get dependencies
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
                   html_to_latex(pkg_comments),       # 4
                   pkg_properties["WBS"],             # 5
                   pkg_properties["manager"][0],      # 6
                   pkg_properties["product owner"],   # 7
                   "",                                # 8
                   pkg_properties["packages"],        # 9
                   pkg_depends,                       # 10
                   mdid,                              # 11
                   pkg_properties["hyperlinkText"],   # 12
                   pkg_properties["team"],            # 13
                   html_to_latex(pkg_properties["short name"][0]),   # 14 - shortname
                   pkg_usedin,                        # 15
                   reqs,                              # 16
                   pkg_properties["docs"],            # 17
                   pkg_index)                         # 18
    if pkey == "":  # first node in the tree
        prod.name = prod.shortname  # this is required, since the first node in MD usually is not meaningful.
        productTree.create_node(prod.id, prod.id, data=prod)
    else:
        if pkey != '':
            productTree.create_node(prod.id, prod.id, data=prod, parent=prod.parent)
        else:
            print('No parent for product:', pkg_name)
            exit()

    for pkg in pkg_sub_pkgs:
        walk_tree(rcs, mres, pkg, pkg_id)

    for cls in pkg_classes:
        walk_tree(rcs, mres, cls, pkg_id)


def get_md_revision(rs, mres, mdid):
    """
    Returns the last trunk MagicDraw revision that is extracted

    """
    resp = rsget(rs, Config.MD_COMP_URL.format(res=mres, comp=mdid), True)
    if resp[1]['kerml:revision']:
        rev_path = resp[1]['kerml:revision']
        rev_split = rev_path.split("/")
        return rev_split[-1]
    else:
        return "---"


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

    md_revision = get_md_revision(rs, mres, mdid)
    print("Magic Draw trunk revision:", md_revision)

    walk_tree(rs, mres, mdid, "")

    return md_revision


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
        snm = p.shortname.rstrip()
        pid = p.parent
        wbs = ' '.join(p.wbs)
        team = p.teams[0]
        mng = p.manager
        owner = p.owner[0]
        pkgs = ' '.join(p.pkgs)
        name = p.shortname.rstrip()
        csv = csv + f"{pkey}, {snm}, {pid}, {wbs}, {team}, {mng}, {owner}, {pkgs}, {name} \n"
    csv_filename = "csv/" + output_file + ".csv"
    file = open(csv_filename, "w")
    print(csv, file=file)
    file.close()


def do_trees_diagrams(tree, filename, scope, compact):
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
    make_tree_landmix1(tree, "trees/" + filename + "_mixedLand.tex", scope, compact)

    # build subtrees
    make_subtrees(tree, filename, scope, compact)


def do_md_section(sysid, levelid, connection_str, output_format, output_file, compact, doc_handler):
    """
    Given the MD ids, dump the content in the output file and produce the product tree diagrams
    :param sysid: MagicDraw subsystem id
    :param levelid: MagicDraw level id (package id containing the tree to extract)
    :param connection_str: MagicDraw encoded connection string
    :param output_format: OutputFormat
    :param output_file: File to dump
    :param compact: True if the portrait diagrams have to be in compact form
    :param doc_handler: the document id
    :param sub_name: name of the subsystem
    :return: none
    """
    global template_path
    global productTree
    global tree_dict
    productTree = Tree()
    products = []
    tree_dict = {}

    # get the information from MagicDraw
    mdr = build_md_tree(sysid, levelid, connection_str)
    print("\n  Product tree depth:", productTree.depth())

    nodes = productTree.expand_tree()
    for n in nodes:
        products.append(productTree[n].data)
        tree_dict[productTree[n].data.id] = productTree[n].data
    print(f"  Found {{np}} products (including container folders).".format(np=len(tree_dict)))

    envs = Environment(loader=ChoiceLoader([FileSystemLoader(Config.TEMPLATE_DIRECTORY),
                                           PackageLoader('ptree', 'templates')]),
                       lstrip_blocks=True, trim_blocks=True, autoescape=None)

    # dump a csv file
    do_csv(products, output_file)

    # create the diagrams tex files
    do_trees_diagrams(productTree, output_file, products[0].shortname, compact)

    # sort tree dictionary based
    mdp = productTree.to_dict(with_data=False)

    # get ordered dictionary
    new_mdpt = dict()
    for k0 in mdp:
        new_mdpt[k0] = order_tree_level(mdp[k0])

    # dump the tex section
    try:
        template_path = f"section.{Config.TEMPLATE_LANGUAGE}.jinja2"
        template = envs.get_template(template_path)
    except TemplateNotFound:
        click.echo(f"No Template Found: {template_path}", err=True)
        sys.exit(1)
    metadata = dict()
    metadata["template"] = template.filename
    text = template.render(metadata=metadata,
                           mdrev=mdr,
                           filename=output_file,
                           doc_handler=doc_handler,
                           mdt_dict=tree_dict,
                           mdp=new_mdpt,
                           mdps=products)
    tex_file_name = output_file + ".tex"
    file = open(tex_file_name, "w")
    print(_as_output_format(text, output_format), file=file)
    file.close()
    return tree_dict


def order_tree_level(udict):
    """
    Given an unordered tree returns a dictionary with ordered tree
    the tree data sall provide a unique index for each level
    :param udict: unsorted dictionary
    :return: sorted level dictionary
    """
    global tree_dict
    level = {}
    c = 0
    for child in udict['children']:
        if isinstance(child, dict):  # the child owns subchilds
            for k in child:
                c = c + 1
                if tree_dict[k].index != "":
                    i = int(tree_dict[k].index)
                else:
                    i = c
                nextl = order_tree_level(child[k])
                level.update({i: {'name': k, 'children': nextl}})
        else:
            c = c + 1
            if tree_dict[child].index != "":
                i = int(tree_dict[child].index)
            else:
                i = c
            level[i] = child
    olevel = dict(sorted(level.items()))
    return olevel


def do_full_tree(md_trees, subsystem_id, compact):
    """
    Merge each tree in md_trees and generate the full landscape product tree
    """

    full_tree = Tree()
    node0 = Product('full_' + subsystem_id,             # 1  (0 is self)
                    'Full ' + subsystem_id + ' Tree',   # 2
                    'full_' + subsystem_id,             # 3
                    [],                                 # 4
                    [],                                 # 5
                    [],                                 # 6
                    [],                                 # 7
                    "",                                 # 8
                    [],                                 # 9
                    [],                                 # 10
                    "",                                 # 11
                    [],                                 # 12
                    [],                                 # 13
                    'Full ' + subsystem_id + ' Tree',   # 14
                    [],                                 # 15
                    [],                                 # 16
                    [],                                 # 17
                    "")                                 # 18
    full_tree.create_node(node0.id, node0.id, data=node0)
    for subtree in md_trees:
        for node in subtree.values():
            if not node.parent:
                # this is the subtree parent node
                node.parent = node0.id
                full_tree.create_node(node.id, node.id, data=node, parent=node0.id)
            else:
                # if node.parent == sub_parent:
                #    node.parent = node0.id
                full_tree.create_node(node.id, node.id, data=node, parent=node.parent)
    # print(full_tree)

    # build full landscape tree
    make_full_tree(full_tree, "trees/" + subsystem_id + "_full.tex", node0.id, compact)


def get_csvfiles(filename):
    """
    Get csv files previously generated in csv/ folder
    """
    products = dict()
    csv_folder = 'csv'
    csvfile = filename + '.csv'
    fname_with_path = csv_folder + "/" + csvfile

    if os.path.exists(fname_with_path):
        print(fname_with_path, ": ", end="")
        with open(fname_with_path, 'r') as csvf:
            reader = csv.reader(csvf, dialect='excel')
            count = 0
            for line in reader:
                # print(len(line), line)
                if count == 0:
                    # first line
                    count = count + 1
                    continue
                else:
                    # Product key, Short name, Parent, WBS, Team, Manager, Product owner, Packages, Name
                    # 0            1           2       3    4     5        6              7         8
                    if len(line) != 0:
                        count = count + 1
                        p = Product(line[0],             # 1   key
                                    line[8],             # 2   name
                                    line[2],             # 3   parent
                                    "",                  # 4   description
                                    line[3].split(" "),  # 5   WBS
                                    line[5].split(" "),  # 6   manager
                                    line[6].split(" "),  # 7   owner
                                    "",                  # 8   kind
                                    line[7].split(' '),  # 9   pkgs
                                    [],                  # 10  depends
                                    "",                  # 11  MagicDraw Element Server Id
                                    [],                  # 12  links
                                    line[4].split(" "),  # 13  teams
                                    line[1],             # 14  shortname
                                    [],                  # 15  usedin
                                    [],                  # 16  requirements
                                    [],                  # 17  docs
                                    "")                  # 18  the position assigned in MD (number before the name)
                    products[p.id] = p
        print(f"got {len(products)} products.")
    else:
        print(f"No {fname_with_path} file found!")
    return products


def generate_document(connection_str, output_format, token_path, compact, csvonly):
    """Given system and level, generates the document content"""
    md_trees = []

    subsystem_info = get_yaml()

    subsystem_id = subsystem_info['subsystem']['id']
    doc_handler = subsystem_info['subsystem']['doc']
    subsystem_name = subsystem_info['subsystem']['name']
    subtrees = subsystem_info['subsystem']['subtrees']
    if not csvonly:
        print("-> Generating Main Product Tree  ==========================")
        level_id = subsystem_info['subsystem']['subtrees'][0]['id']
        filename = subsystem_info['subsystem']['subtrees'][0]['filename']
        md_trees.append(do_md_section(subsystem_id, level_id, connection_str, output_format, filename, compact,
                                      doc_handler))

        print("-> Generating Development Product Tree  ==========================")
        level_id = subsystem_info['subsystem']['subtrees'][1]['id']
        filename = subsystem_info['subsystem']['subtrees'][1]['filename']
        md_trees.append(do_md_section(subsystem_id, level_id, connection_str, output_format, filename, compact,
                                      doc_handler))

        print("-> Generating FULL Product Tree  ==========================")
        do_full_tree(md_trees, subsystem_name, True)
    else:
        print("-> Getting csv files  ==========================")
        for subtree in subtrees:
            prds = get_csvfiles(subtree['filename'])
            if len(prds) > 0:
                md_trees.append(prds)
        print(f"Loaded {{n}} csv files".format(n=len(md_trees)))

    print("-> Generating GitHub Product Tree  ==========================")
    do_github_section(md_trees, token_path, output_format)

    # print("-> [to do] Generating Auxiliary Product Tree  ==========================")
