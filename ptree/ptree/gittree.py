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

import github
import os
import click
import sys
import re
import time
from .util import GitPkg, _as_output_format, fix_tex, html_to_latex
from .config import Config
from jinja2 import Environment, PackageLoader, TemplateNotFound, ChoiceLoader, FileSystemLoader
from treelib import Tree


def do_github_section(md_trees, token_path, output_format):
    """

    :param md_trees: list of MagicDraw tree dictionaries
    :return:
    """
    global template_path
    global git_calls
    git_calls = 0
    git_trees = []
    git_trees_dict = dict()

    full_token_path = os.path.expanduser(token_path)
    with open(full_token_path, 'r') as fdo:
        token = fdo.readline().strip()
    g = github.Github(token)
    for tree in md_trees:
        for product in tree:
            # print(tree[product].name, tree[product].pkgs, len(tree[product].pkgs))
            if tree[product].pkgs:
                for pkg in tree[product].pkgs:
                    # pkg_tmp = get_gitpkg_content(pkg, g)
                    # if pkg_tmp:
                    #     pkg_tmp.component_id = tree[product].id
                    #    pkg_tmp.component_name = tree[product].name
                    #    git_dm[pkg] = pkg_tmp
                    tmp_tree = get_git_tree(pkg, g, tree[product])
                    if tmp_tree:
                        git_trees.append(tmp_tree)
                        root = tmp_tree.root
                        git_trees_dict[pkg] = tmp_tree[root].data
                        print(git_calls)

    envs = Environment(loader=ChoiceLoader([FileSystemLoader(Config.TEMPLATE_DIRECTORY),
                                           PackageLoader('ptree', 'templates')]),
                       lstrip_blocks=True, trim_blocks=True, autoescape=None)

    try:
        template_path = f"gitsection.{Config.TEMPLATE_LANGUAGE}.jinja2"
        template = envs.get_template(template_path)
    except TemplateNotFound:
        click.echo(f"No Template Found: {template_path}", err=True)
        sys.exit(1)
    metadata = dict()
    metadata["template"] = template.filename
    text = template.render(metadata=metadata,
                           git_dm=git_trees_dict)
    tex_file_name = "git_pkgs_section.tex"
    file = open(tex_file_name, "w")
    print(_as_output_format(text, output_format), file=file)
    file.close()


def get_gitpkg_content(pkg, g):
    """

    :return:
    """
    global git_calls

    sleep_time = 1  # delay seconds each time a call to git is done
                    # to avoid rate limit problem

    readme = dict()
    ups_table = []
    pkg_teams = []
    pkg_desc = ""

    if pkg == '':
        return None

    spkg = pkg.split("/")
    if len(spkg) == 2:
        org = spkg[0]
        repo = spkg[1]
    else:
        org = 'lsst'
        repo = pkg
    print(f"  > {pkg.strip()}", end="", flush=True)
    try:
        git_calls = git_calls + 1
        gg = g.get_organization(org)
        time.sleep(sleep_time)
        print(".", end="", flush=True)
    except Exception as ex:
        print(f"[[Error accessing organization {org} --> git calls {git_calls}]]")
        print(ex)
        exit()
    try:
        git_calls = git_calls + 1
        repository = gg.get_repo(repo)
        time.sleep(sleep_time)
        print(".", end="", flush=True)
    except Exception as ex:
        print(f"[[Error accessing repository {repo} in organization {org} --> {ex}]]", end="", flush=True)
        return None
    git_calls = git_calls + 1
    rc = repository.get_contents("")
    time.sleep(sleep_time)
    print(".", end="", flush=True)
    # finding the readme(s?) and dependencies
    for f in rc:
        if "README" in f.path:
            readme_file = f.path
            try:
                readme_full = repository.get_file_contents(readme_file).decoded_content
            except:
                print(f"[[Error in reading {repo} {readme_file} (readme) file]]", end="", flush=True)
                return None
            readme_split = readme_full.decode('UTF-8').splitlines()
            readme_20 = '\n'.join(readme_split[:20])
            readme[readme_file] = readme_20
        if "ups" in f.path:
            ups_path = 'ups/' + repo + '.table'
            try:
                git_calls = git_calls + 1
                ups_content = repository.get_file_contents(ups_path).decoded_content.decode('UTF-8').splitlines()
                time.sleep(sleep_time)
                print(".", end="", flush=True)
            except:
                print(f"[[Error in reading {repo} {ups_path} (ups table) file]]", end="", flush=True)
                return None
            for line in ups_content:
                if "setupRequired" in line and line[:1] != "#":
                    # dependency = fix_tex(re.search(r'\((.*?)\)', line).group(1))
                    dependency = re.search(r'\((.*?)\)', line).group(1)
                    ups_table.append(dependency)

    # get description
    raw_description = repository.description
    if raw_description:
        pkg_desc = html_to_latex(raw_description)

    # get teams
    try:
        git_calls = git_calls + 1
        teams = repository.get_teams()
        time.sleep(sleep_time)
        print(".", end="", flush=True)
        for t in teams:
            pkg_teams.append(t.name)
    except:
        print(f"[[Error getting teams for {repo}]]", end="", flush=True)

    gp = GitPkg("",
                "",
                repo,
                org,
                readme,
                ups_table,
                pkg_teams,
                pkg_desc,
                "",
                "")
    return gp


def get_git_tree(pkg, g, top_prd):
    """

    :return:
    """
    global pkg_tree
    global pkg_id
    global pkg_list
    pkg_tree = Tree()
    pkg_id = 0
    pkg_list = []

    if pkg == '':
        return None

    if pkg in Config.CACHED_GIT_REPOS:
        pkg_content = Config.CACHED_GIT_REPOS[pkg]
        print("^", end="", flush=True)
    else:
        pkg_content = get_gitpkg_content(pkg, g)

    if pkg_content:
        # first node in the tree
        pkg_content.key = str(pkg_id) + "." +pkg_content.name
        pkg_content.component_id = top_prd.id
        pkg_content.component_name = top_prd.name
        print(pkg_content.key, pkg_content.pkey, pkg_content.name, pkg_content.ups_table, ">>>>>>", end="", flush=True)
        pkg_tree.create_node(pkg_content.key, pkg_content.key, data=pkg_content)
        if pkg not in Config.CACHED_GIT_REPOS.keys():
            Config.CACHED_GIT_REPOS[pkg] = pkg_content
            print("+")
        for child in pkg_content.ups_table:
            walk_git_tree(child, g, pkg_content.key)
    else:
        return None

    print(pkg_tree)

    return pkg_tree


def walk_git_tree(pkg, g, pkey):
    """

    :param pkg:
    :param g:
    :return:
    """
    global pkg_tree
    global pkg_id
    global pkg_list

    if pkg in Config.CACHED_GIT_REPOS:
        pkg_content = Config.CACHED_GIT_REPOS[pkg]
        print("^")
    else:
        pkg_content = get_gitpkg_content(pkg, g)
        if pkg_content:
            Config.CACHED_GIT_REPOS[pkg] = pkg_content
            print("+", end="", flush=True)

    if pkg_content and pkg_content.name not in pkg_list:
        pkg_id = pkg_id + 1
        pkg_content.key = str(pkg_id) + "." + pkg_content.name
        print( pkg_content.key, pkg_content.pkey, pkg_content.name, pkg_content.ups_table, ">>")
        pkg_tree.create_node(pkg_content.key, pkg_content.key, data=pkg_content, parent=pkey)
        pkg_list.append(pkg_content.name)
        for child in pkg_content.ups_table:
            walk_git_tree(child, g, pkg_content.key)

