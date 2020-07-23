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


from graphviz import Digraph
from .config import Config


def walk_deps(pkg):
    global dot
    global trace

    dot.node(pkg)

    for dep in Config.CACHED_GIT_REPOS[pkg].ups_table:
        if pkg not in trace.keys():
            trace[pkg] = [dep]
            dot.edge(pkg, dep)
            if dep in Config.CACHED_GIT_REPOS.keys():
                walk_deps(dep)
        elif dep not in trace[pkg]:
            trace[pkg].append(dep)
            dot.edge(pkg, dep)
            if dep in Config.CACHED_GIT_REPOS.keys():
                walk_deps(dep)


def make_graph(tree_data):
    global dot
    global trace

    trace = dict()
    root = tree_data['root']

    graph_format = 'pdf'

    dot = Digraph(comment='Graph for ' + root.name, format=graph_format)

    # print(root.name)
    # print("  -- ", tree_data['deps'])
    # print('  >> ', root.ups_table)

    dot.node(root.name)

    if len(root.ups_table) > 0:
        for dep in root.ups_table:
            trace[root.name] = [dep]
            dot.edge(root.name, dep)
            if dep in Config.CACHED_GIT_REPOS.keys():
                walk_deps(dep)
                # print(" ** -- ", Config.CACHED_GIT_REPOS[dep].ups_table)

        graph_file = "dot/" + root.name.lower() + ".dot"
        dot.render(graph_file)

        return graph_file + ".ps"
    else:
        return None
