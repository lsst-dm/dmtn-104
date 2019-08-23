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
Utility code for product tree generation
"""

import csv
import re
import requests
import datetime
from treelib import Tree
from time import sleep
from base64 import b64encode
from .config import Config

# MD Subsystem  Design Workspace @ID
sdw = '3130d49c-d90d-4df2-a110-5247a5d03296'
dms = '698d501b-660d-4d7e-8875-c6170ca0f513'
trunk = '698d501b-660d-4d7e-8875-c6170ca0f513'
dmpl = 'a0acbaa6-6625-4ea9-8aec-51931412a29e'  # DM Problem/Logic element server id
dmcmp = '60706435-6f8e-4b15-823b-06597f1cdada'  # DM Components element server ID
mdTree = Tree()
connectionId = b64encode(b"gcomoretto-read:dm-read").decode("ascii")
headers = {
    'accept': 'application/json',
    # 'authorization': 'Basic %s' % Config.CONNECTION_ID,
    'authorization': 'Basic %s' % connectionId,
    'Connection': 'close'
}


class Product(object):
    def __init__(self, p_id, name, parent, desc, wbs, manager, owner,
                 kind, pkgs, depends, el_id, links, teams):
        self.id = p_id
        self.name = name
        self.parent = parent
        self.desc = desc
        self.wbs = wbs
        self.manager = manager
        self.owner = owner
        self.kind = kind
        self.pkgs = pkgs
        self.depends = depends
        self.elId = el_id  # MagicDraw Element Server Id
        self.links = links
        self.teams = teams


# given a a session retun a json
# in case the max sessions opened is reached,
# waits 10 minutes before retry (probably not needed using only one session)
def rsget(session, url, verify):
    # print('>> url: ', url, '<<')

    wait = 600

    req = session.get(url, verify=verify)
    while req.status_code == 401:
        now = datetime.datetime.now()
        print(now.strftime("%H:%M:%S"), 'REST API connexions exceeded. Whaiting ...', wait, ' seconds on request:')
        print('  --  ', url) 
        sleep(wait)
        req = session.get(url, verify=verify)

    result = req.json()
    return result


# Generate an Id from the text
def fix_id_tex(text):
    text_id = re.sub(r"\s+", "", text)
    text_id = text_id.replace("(", "")
    text_id = text_id.replace(")", "")
    text_id = text_id.replace("\"", "")
    text_id = text_id.replace("_", "")
    text_id = text_id.replace(".", "")
    text_id = text_id.replace("&", "")
    return text_id


def fix_tex(text):
    fixed_text = text.replace("_", "\\_")
    fixed_text = fixed_text.replace("/", "/ ")
    fixed_text = fixed_text.replace("&", "\\& ")
    return fixed_text


# obsolete: to remove
def reqget(url, local_headers, verify):
    wait = 600
    req = requests.get(url, headers=local_headers, verify=verify)
    while req.status_code == 401:
        now = datetime.datetime.now()
        print(now.strftime("%H:%M:%S"), 'REST API connexions exceeded. Whaiting ...', wait, ' seconds on request:')
        print('  --  ', url) 
        sleep(wait)
        req = requests.get(url, headers=local_headers, verify=verify)
    result = req.json()
    req.close()
    return result


# given a file handler, it returns the tree
def construct_tree(fileinput):
    """Read the tree file and construct  a tree structure
    Input csv columns
    product key,short name,Parent,WBS,team,manager,product owner,packages,Name,Qualified Name,docgen,Element Server ID
    0           1          2      3   4    5       6             7        8    9              10     11"""
    count = 0
    ptree = Tree()

    with open(fileinput, 'r') as fin:
        reader = csv.reader(fin, dialect='excel')
        for line in reader:
            count = count + 1
            if count == 1:
                continue
            e_id = fix_id_tex(line[0])  # make an e_id from the name
            pid = fix_id_tex(line[2])  # use the same formaula on the parent name then we are good
            name = fix_tex(line[1])
            prod = Product(e_id, name, pid, "", line[3], line[5],
                           line[6], "", line[7], line[11])
#   def __init__(self, e_id, name, parent, desc, wbs, manager,
#                       owner, kind, pkgs, elId):

            # print("Product:" + prod.e_id + " name:" + prod.name + " parent:" + prod.parent)
            if count == 2:  # root node
                ptree.create_node(prod.id, prod.id, data=prod)
            else:
                # print("Creating node:" + prod.e_id + " name:"+ prod.name +
                #      " parent:" + prod.parent)
                if prod.parent != "":
                    ptree.create_node(prod.id, prod.id, data=prod,
                                      parent=prod.parent)
                else:
                    print(line[0] + " no parent")

    print("{} Product lines".format(count))
    return ptree


def tree_slice(ptree, outdepth):
    if ptree.depth() == outdepth:
        return ptree
    # copy the tree but stopping at given depth
    ntree = Tree()
    nodes = ptree.expand_tree()
    count = 0  # subtree in input
    for n in nodes:
        # print("Accesing {}".format(n))
        depth = ptree.depth(n)
        prod = ptree[n].data

        # print("outd={od} mydepth={d} Product: {p.id} name: {p.name} parent: {p.parent}".format(od=outdepth,
        #       d=depth, p=prod))
        if depth <= outdepth:
            # print(" YES ", end='')
            if count == 0:
                ntree.create_node(prod.id, prod.id, data=prod)
            else:
                ntree.create_node(prod.id, prod.id, data=prod,
                                  parent=prod.parent)
            count = count + 1
    return ntree


# get all information from MD for a single element
#   rcs: requests connection session
#   cid: MD subsystem id
#   eid: EM element id
def get_md_element(rcs, cid, eid):
    resp = rsget(rcs, Config.MD_COMP_URL.format(res=cid, comp=eid), True)
    print(resp)


# Returns the properties of an element
#
def get_pkg_properties(rcs, cid, eid):
    # print('uml:InstanceSpecification', eid)
    resp = rsget(rcs, Config.MD_COMP_URL.format(res=cid, comp=eid), True)

    properties = dict()
    properties['WBS'] = []
    properties['manager'] = []
    properties['product owner'] = []
    properties['packages'] = []
    properties['hyperlinkText'] = []
    properties['team'] = []

    for el in resp[0]['ldp:contains']:
        # print('  uml:Slot', el['@id'])
        slot = rsget(rcs, Config.MD_COMP_URL.format(res=cid, comp=el['@id']), True)
        if slot[1]['@type'] != 'uml:Slot':
            print('New type: ', slot[1]['@type'], ' on ', el['@id'], '(uml:Slot was expected)')
        else:
            # get property name
            # print('      definingFeature',slot[1]['kerml:esiData']['definingFeature']['@id'])
            pne = rsget(rcs, Config.MD_COMP_URL.format(res=cid,
                                                       comp=slot[1]['kerml:esiData']['definingFeature']['@id']), True)
            pname = pne[1]['kerml:name']
            # get property value
            pvalue = []
            # pvalue = " "
            for entry in slot[0]['ldp:contains']:
                pve = rsget(rcs, Config.MD_COMP_URL.format(res=cid, comp=entry['@id']), True)
                if pve[1]['@type'] in ('uml:LiteralString', 'uml:LiteralBoolean'):
                    pvalue.append(pve[1]['kerml:esiData']['value'])
                    # pvalue = pvalue + pve[1]['kerml:esiData']['value']
                elif pve[1]['@type'] == 'uml:InstanceValue':
                    instance = rsget(rcs, Config.MD_COMP_URL.format(res=cid,
                                                                    comp=pve[1]['kerml:esiData']['instance']['@id']), True)
                    pvalue.append(instance[1]['kerml:name'])
                else:
                    print('Unmapped property type ', pve[1]['@type'])
            properties[pname] = pvalue
            # print('         - ', pname, pvalue)
    if not properties['WBS']:
        properties['WBS'].append("")
    if not properties['manager']:
        properties['manager'].append("")
    if not properties['product owner']:
        properties['product owner'].append("")
    if not properties['packages']:
        properties['packages'].append("")
    if not properties['hyperlinkText']:
        properties['hyperlinkText'].append("")
    if not properties['team']:
        properties['team'].append("")

    return properties


def get_pkg_p2(rcs, cid, eid):
    # print('uml:InstanceSpecification', eid)
    resp = rsget(rcs, Config.MD_COMP_URL.format(res=cid, comp=eid), True)
    for el in resp[0]['ldp:contains']:
        resp2 = rsget(rcs, Config.MD_COMP_URL.format(res=cid, comp=el['@id']), True)
        if resp2[1]['@type'] == 'uml:InstanceSpecification':
            pkg_p = get_pkg_properties(rcs, cid, el['@id'])
        else:
            print("   > ", el['@id'], resp2[1]['@type'])
    return pkg_p


def explore_md_element(rcs, cid, eid, level):
    resp = rsget(rcs, Config.MD_COMP_URL.format(res=cid, comp=eid), True)

    for el in resp[0]['ldp:contains']:
        tmp = rsget(rcs, Config.MD_COMP_URL.format(res=cid, comp=el['@id']), True)
        if tmp[1]['@type'] not in ('uml:Package', 'uml:Class', 'uml:Association', 'uml:Abstraction', 'uml:Comment'):
            if 'name' in tmp[1]['kerml:esiData'].keys():
                name = tmp[1]['kerml:esiData']['name']
            else:
                name = ' -No Name- '
            if 'value' in tmp[1]['kerml:esiData'].keys():
                value = tmp[1]['kerml:esiData']['value']
            else:
                value = ' -No Value-'
            print(level, tmp[1]['@type'], name, value, el['@id'])
            explore_md_element(rcs, cid, el['@id'], level + ".")
            if tmp[1]['@type'] == 'uml:Slot':
                if 'definingFeature' in tmp[1]['kerml:esiData'].keys():
                    print(level, 'definingFeature', tmp[1]['kerml:esiData']['definingFeature'])
                    # resp1 = rsget(rcs, Config.MD_COMP_URL.format(res=cid,
                    #               comp=tmp[1]['kerml:esiData']['definingFeature']['@id']), True)
                    # explore_md_element(rcs, cid, tmp[1]['kerml:esiData']['definingFeature']['@id'], level+'_')
                    # print()
