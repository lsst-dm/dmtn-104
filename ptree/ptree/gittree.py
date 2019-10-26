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
Code for generation Product Tree document from GitHub
"""

import requests
import pandoc
import github
import os


def do_github_section(md_trees, token_path):
    """

    :param md_trees: list of MagicDraw tree dictionaries
    :return:
    """
    full_token_path = os.path.expanduser(token_path)
    with open(full_token_path, 'r') as fdo:
        token = fdo.readline().strip()
    g = github.Github(token)
    for tree in md_trees:
        for product in tree:
            # print(tree[product].name, tree[product].pkgs, len(tree[product].pkgs))
            if tree[product].pkgs:
                for pkg in tree[product].pkgs:
                    get_gitpkg_content(pkg, g)


def get_gitpkg_content(pkg, g):
    """

    :return:
    """
    if pkg == '':
        return
    spkg = pkg.split("/")
    # print(" - ", spkg)
    if len(spkg) == 2:
        org = spkg[0]
        repo = spkg[1]
        blnk = f"https://github.com/{pkg}"
    else:
        org = 'lsst'
        repo = pkg
        blnk = f"https://github.com/lsst/{pkg}"
    print("  --  ", blnk)
    try:
        gg = g.get_organization(org)
        try:
            re = gg.get_repo(repo)
            rc = re.get_contents("")
            for f in rc:
                print(f)
        except:
            print(f"Error accessing repository {repo} in organization {org}.")
    except:
        print(f"Error accessing organization {org}")
    # return
    #
    # response = requests.get(blnk, headers='')
    # r_code = response.status_code
    # print(r_code)
    # if r_code == 200:
    #    doc = pandoc.Document()
    #    doc.html = response.text.encode('utf-8')
    #    doctxt = doc.plain.decode('utf-8')
    #    print(doctxt)
