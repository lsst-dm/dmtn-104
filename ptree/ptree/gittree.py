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
from .util import GitPkg, _as_output_format, fix_tex, html_to_latex
from .config import Config
from jinja2 import Environment, PackageLoader, TemplateNotFound, ChoiceLoader, FileSystemLoader


def do_github_section(md_trees, token_path, output_format):
    """

    :param md_trees: list of MagicDraw tree dictionaries
    :return:
    """
    global template_path

    full_token_path = os.path.expanduser(token_path)
    with open(full_token_path, 'r') as fdo:
        token = fdo.readline().strip()
    g = github.Github(token)
    git_dm = dict()
    for tree in md_trees:
        for product in tree:
            # print(tree[product].name, tree[product].pkgs, len(tree[product].pkgs))
            if tree[product].pkgs:
                for pkg in tree[product].pkgs:
                    pkg_tmp = get_gitpkg_content(pkg, g)
                    if pkg_tmp:
                        pkg_tmp.component_id = tree[product].id
                        pkg_tmp.component_name = tree[product].name
                        git_dm[pkg] = pkg_tmp
        print("")

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
                           git_dm=git_dm)
    tex_file_name = "git_pkgs_section.tex"
    file = open(tex_file_name, "w")
    print(_as_output_format(text, output_format), file=file)
    file.close()


def get_gitpkg_content(pkg, g):
    """

    :return:
    """
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
        gg = g.get_organization(org)
    except:
        print(f"[[Error accessing organization {org}]]", end="", flush=True)
        return None
    try:
        repository = gg.get_repo(repo)
    except:
        print(f"[[Error accessing repository {repo} in organization {org}]]", end="", flush=True)
        return None
    rc = repository.get_contents("")
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
                ups_content = repository.get_file_contents(ups_path).decoded_content.decode('UTF-8').splitlines()
            except:
                print(f"[[Error in reading {repo} {ups_path} (ups table) file]]", end="", flush=True)
                return None
            for line in ups_content:
                if "setupRequired" in line and line[:1] != "#":
                    dependency = fix_tex(re.search(r'\((.*?)\)', line).group(1))
                    ups_table.append(dependency)

    # get description
    try:
        # print(repository)
        pkg_desc = html_to_latex(repository.description)
    except:
        print("[[Error getting Description]]", end="", flush=True)

    # get teams
    try:
        teams = repository.get_teams()
        for t in teams:
            pkg_teams.append(t.name)
    except:
        print("[[Error getting teams]]", end="", flush=True)

    gp = GitPkg(repo,
                org,
                readme,
                ups_table,
                pkg_teams,
                pkg_desc,
                "",
                "")
    return gp

