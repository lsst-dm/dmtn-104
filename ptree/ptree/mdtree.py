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
from .util import get_pkg_properties, mdTree, rsget, fix_tex, fix_id_tex, Product, html_to_latex


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


def get_pkg_key(rcs, mres, mdid):
    resp = rsget(rcs, Config.MD_COMP_URL.format(res=mres, comp=mdid), True)

    dependency = dict()

    dependency['name'] = fix_tex(resp[1]['kerml:name']).lstrip('0123456789.- ')

    pkg_properties = dict()

    for el in resp[0]['ldp:contains']:
        tmp = rsget(rcs, Config.MD_COMP_URL.format(res=mres, comp=el['@id']), True)
        if tmp[1]['@type'] == 'uml:InstanceSpecification':
            pkg_properties = get_pkg_properties(rcs, mres, el['@id'])
            #print(pkg_properties)
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

    return dependency


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
            # print(pkg_properties)
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
            print("   ----   dep key found: ", depkey)
            pkg_depends.append(depkey)
        elif tmp[1]['@type'] in ('uml:Abstraction', 'uml:Diagram', 'uml:Association'):
            continue
        else:
            print('Unmapped type: ', tmp[1]['@type'], el['@id'])

    if resp[1]['@type'] == 'uml:Class':
        for el in resp[1]['kerml:esiData']['ownedMember']:
            tmp = rsget(rcs, Config.MD_COMP_URL.format(res=mres, comp=el['@id']), True)
            if tmp[1]['kerml:esiData']['type']:
                # print(el['@id'], tmp[1]['@type'], tmp[1]['kerml:name'], tmp[1]['kerml:esiData']['type'])
                dep = get_pkg_key(rcs, mres, tmp[1]['kerml:esiData']['type']['@id'])
                if dep != "":
                    # print(" - dependency ", dep)
                    pkg_depends.append(dep)

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
                   [])                              # 15
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
def build_md_tree(mres, mdid, connectionId):
    """ Build the tree reading from MD
    """
    headers = {
        'accept': 'application/json',
        'authorization': 'Basic %s' % connectionId,
        'Connection': 'close'
    }

    rs = requests.Session()
    rs.headers = headers

    walk_tree(rs, mres, mdid, "")
