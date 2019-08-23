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
from .config import Config
from .util import get_pkg_properties, mdTree, headers, rsget, fix_tex, fix_id_tex, Product, explore_md_element, \
    get_pkg_p2


def get_dep_key(rcs, mres, mdid):
    # print("Dep ID: ", mdid)
    resp = rsget(rcs, Config.MD_COMP_URL.format(res=mres, comp=mdid), True)
    dep_pkgs = dict()

    for element in resp[1]['kerml:esiData']['relatedElement']:
        tmpresp = rsget(rcs, Config.MD_COMP_URL.format(res=mres, comp=element['@id']), True)
        tmpname = fix_tex(tmpresp[1]['kerml:name']).lstrip('0123456789.- ')
        tmp_pkg_props = dict()
        for el in tmpresp[0]['ldp:contains']:
            tmp = rsget(rcs, Config.MD_COMP_URL.format(res=mres, comp=el['@id']), True)
            # if tmp[1]['@type'] == 'uml:Property':
            #    get_pkg_p2(rcs, mres, el['@id'])
            if tmp[1]['@type'] == 'uml:InstanceSpecification':
                tmp_pkg_props = get_pkg_properties(rcs, mres, el['@id'])
        tmp_pkg_id = fix_id_tex(tmp_pkg_props['product key'][0])
        dep_pkgs[tmp_pkg_id] = tmpname
        # print("Dependency found: ", tmpname, tmp_pkg_id)

    return dep_pkgs


def walk_tree(rcs, mres, mdid, pkey):
    """ Product Class Object
    id, name, parent, desc, wbs, manager, owner, kind, pkgs, elId"""

    resp = rsget(rcs, Config.MD_COMP_URL.format(res=mres, comp=mdid), True)
    if resp[1]['@type'] not in ('uml:Package', 'uml:Class'):
        print('Error: no package given containing the Product Tree')
        exit()
    pkg_name = fix_tex(resp[1]['kerml:name']).lstrip('0123456789.- ')
    print(f"->> Looking into {{pkg}} ({{pid}}, {{ptype}}), parent: '{{parent}}' ".format(pkg=pkg_name,
                                                                                         pid=mdid, parent=pkey,
                                                                                         ptype=resp[1]['@type']))
    pkg_sub_pkgs = []
    pkg_classes = []
    pkg_comments = ""
    pkg_properties = dict()
    pkg_depends = []

    for el in resp[0]['ldp:contains']:
        tmp = rsget(rcs, Config.MD_COMP_URL.format(res=mres, comp=el['@id']), True)
        if tmp[1]['@type'] == 'uml:Package':
            pkg_sub_pkgs.append(el['@id'])
            # print(f"      added sub package: {{name}} ({{pid}})".format(name=tmp[1]['kerml:name'], pid=el['@id']))
        elif tmp[1]['@type'] == 'uml:Class':
            pkg_classes.append(el['@id'])
            #
            # print(f"      added contained element: {{name}} ({{pid}})".format(name=tmp[1]['kerml:name'],
            # pid=el['@id']))
        elif tmp[1]['@type'] == 'uml:InstanceSpecification':
            pkg_properties = get_pkg_properties(rcs, mres, el['@id'])
            print(pkg_properties)
        elif tmp[1]['@type'] == 'uml:Property':
            continue
            # prop_tmp = get_pkg_p2(rcs, mres, el['@id'])
            # print("tmp-", prop_tmp)
        elif tmp[1]['@type'] == 'uml:Comment':
            pkg_comments = pkg_comments + tmp[1]['kerml:esiData']['body']
            # print('      added comment:', tmp[1]['kerml:esiData']['body'])
        elif tmp[1]['@type'] == 'uml:Dependency':
            # print(pkg_name, mdid)
            depkey = get_dep_key(rcs, mres, el['@id'])
            # print("   ----   dep key found: ", depkey)
            pkg_depends.append(depkey)
        elif tmp[1]['@type'] in ('uml:Abstraction', 'uml:Diagram', 'uml:Association'):
            continue
        else:
            print('Unmapped type: ', tmp[1]['@type'], el['@id'])

    pkg_id = fix_id_tex(pkg_properties['product key'][0])
    # print(pkg_id, mdTree.depth())
    # print(f" {{id}} - {{name}}".format(id=pkg_id, name=pkg_name))
    prod = Product(pkg_id,
                   pkg_name,
                   pkey,
                   pkg_comments,
                   pkg_properties["WBS"],
                   pkg_properties["manager"][0],
                   pkg_properties["product owner"],
                   "",
                   pkg_properties["packages"],
                   pkg_depends,
                   mdid,
                   pkg_properties["hyperlinkText"],
                   pkg_properties["team"])
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


#   Build The Tree from MD
#     mres: MD reference resource (such as DM subproject)
#     mdid: MD first component to read
def build_md_tree(mres, mdid):
    """ Build the tree reading from MD
    """

    rs = requests.Session()
    rs.headers = headers

    walk_tree(rs, mres, mdid, "")
