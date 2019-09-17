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
Code for generation Product Tree diagrams
"""
from .util import Product
from treelib import Tree

txtheight = 35
leafHeight = 1.56  # cm space per leaf box .. height of page calc
leafWidth = 3.7  # cm space per leaf box .. width of page calc
smallGap = 0.2  # cm between leaf boxes in the same group
bigGap = 1.5  # cm between different levels, or leaf boxes
sep = 2  # inner sep
gap = 4
WBS = 1  # Put WBS on diagram
PKG = 1  # put packages on diagram
outdepth = 100  # set with --depth if you want a shallower tree


def tree_slice(ptree, outdepth):
    """
    Returns a subproduct with depth equal to outdepth
    :param ptree: input product tree
    :param outdepth: depth of the subproduct tree
    :return: sub product tree
    """
    if ptree.depth() == outdepth:
        return ptree
    # copy the tree but stopping at given depth
    ntree = Tree()
    nodes = ptree.expand_tree()
    count = 0
    for n in nodes:
        depth = ptree.depth(n)
        prod = ptree[n].data
        if depth <= outdepth:
            if count == 0:
                ntree.create_node(prod.id, prod.id, data=prod)
            else:
                ntree.create_node(prod.id, prod.id, data=prod,
                                  parent=prod.parent)
            count = count + 1
    return ntree


def print_header(target, pwidth, pheight, ofile):
    """
    Print Header of tex file
    :param target: the scope of the product tree
    :param pwidth: paper wodth
    :param pheight: paper hight
    :param ofile: output file resource to write
    :return: none
    """
    print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
          "%\n"
          f"% Document:     {target}  product tree\n"
          "%\n"
          "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
          "\\documentclass{article}\n"
          "\\usepackage{times,layouts}\n"
          "\\usepackage{tikz,hyperref,amsmath}\n"
          "\\usetikzlibrary{positioning,arrows,shapes,decorations.shapes,shapes.arrows}\n"
          "\\usetikzlibrary{backgrounds,calc}\n"
          f"\\usepackage[paperwidth={pwidth}cm,paperheight={pheight}cm,\n"
          "left=-2mm,top=3mm,bottom=0mm,right=0mm,\n"
          "noheadfoot,marginparwidth=0pt,includemp=false,\n"
          "textwidth=30cm,textheight=50mm]{geometry}\n"
          "\\newcommand\showpage{%\n"
          "\\setlayoutscale{0.5}\setlabelfont{\\tiny}\printheadingsfalse\printparametersfalse\n"
          "\\currentpage\pagedesign}\n"
          "\\hypersetup{pdftitle={DM products }, pdfsubject={Diagram illustrating the\n"
          "                products in LSST DM }, pdfauthor={Autogenerated from MD}}\n"
          "\\tikzstyle{tbox}=[rectangle,text centered, text width=30mm]\n"
          "\\tikzstyle{wbbox}=[rectangle, rounded corners=3pt, draw=black, top color=blue!50!white,\n"
          "                    bottom color=white, very thick, minimum height=12mm, inner sep=2pt,\n"
          "                    text centered, text width=30mm]\n"
          "\\tikzstyle{pbox}=[rectangle, rounded corners=3pt, draw=black, top\n"
          " color=yellow!50!white, bottom color=white, very thick,\n"
          f" minimum height={str(txtheight)}pt, inner sep={str(sep)}pt, text centered, text width=35mm]\n"
          "\\tikzstyle{pline}=[-, thick]\n"
          "\\begin{document}\n"
          "\\begin{tikzpicture}[node distance=0mm]\n"
          "\n", file=ofile)


def print_footer(ofile):
    """ Write end of tree tex file"""
    print("\n"
          "\\end{tikzpicture}\n"
          "\\end{document}", file=ofile)


def drawLines(fout, row):
    for p in row:
        prod = p.data
        print(r" \draw[pline]   ({p.id}.north) -- ++(0.0,0.5) -| ({p.parent}.south) ; ".format(p=prod), file=fout )


def tex_tree_portrait(fout, ptree, width, sib, full):
    """
    Write the product tree in PORTRAIT format
    :param ptree: product tree to dump
    :param width: the distance from the sibling, that depends from the depth of the previous subtree
    :param sib: the sibling that has to refer to (the left)
    :param full: true or false
    :param fout: output file resource
    :return:
    """
    fnodes = []
    nodes = ptree.expand_tree()  # default mode=DEPTH
    count = 0
    prev = Product("n", "n", "n", "n", "n", "n", "n", "n", "n", "n", "n", "n", "n", "n", "n")
    # Text height + the gap added to each one
    blocksize = txtheight + gap + sep
    for n in nodes:
        prod = ptree[n].data
        fnodes.append(prod)
        depth = ptree.depth(n)
        count = count + 1
        # print("{} Product: {p.id} name: {p.name} parent: {p.parent}".format(depth, p=prod))
        if depth <= outdepth:
            if count == 1:  # root node
                if full:  # if the first node of a full tree, no parent
                    print(r"\node ({p.id}) [wbbox]{{\textbf{{{p.name}}}}};".format(p=prod), file=fout)
                else:  # some sub tree (portrait) in a landscape tree
                    print(r"\node ({p.id}) [pbox, ".format(p=prod), file=fout)
                    if sib:
                        print("right={d}cm of {p.id}".format(d=width, p=sib), file=fout, end='')
                    print(r"] {\textbf{" + prod.name + "} };", file=fout)
            else:
                print(r"\node ({p.id}) [pbox,".format(p=prod), file=fout, end='')
                if prev.parent != prod.parent:  # first child to the right if portrait left if landscape
                    found = 0
                    scount = count - 1
                    while found == 0 and scount > 0:
                        scount = scount - 1
                        found = fnodes[scount].parent == prod.parent
                    if scount <= 0:  # first sib can go righ of parent
                        print("right=15mm of {p.parent}".format(p=prod),
                              file=fout, end='')
                    else:  # Figure how low to go  - find my prior sibling
                        psib = fnodes[scount]
                        leaves = ptree.leaves(psib.id)
                        depth = len(leaves) - 1
                        # the number of leaves below my sibling
                        dist = depth * blocksize + gap
                        print("below={}pt of {}".format(dist, psib.id),
                              file=fout, end='')
                else:
                    # benetih the sibling
                    dist = gap
                    print("below={}pt of {}".format(dist, prev.id), file=fout, end='')
                print(r"] {\textbf{" + prod.name + "} };", file=fout)
                print(r" \draw[pline] ({p.parent}.east) -| ++(0.4,0) |- ({p.id}.west); ".format(p=prod), file=fout)
            prev = prod
    return count


def tex_tree_landmix1(fout, ptree):
    """
    Write the product tree diagram:
        first level in landscape
        second level subtrees in portrait
    :param fout: outputfile
    :param ptree: input product tree
    :return: none
    """
    stub = tree_slice(ptree, 1)
    nodes = stub.expand_tree(mode=Tree.WIDTH)  # default mode=DEPTH
    row = []
    count = 0
    root = None
    for n in nodes:
        count = count + 1
        if count == 1:  # root node
            root = ptree[n].data
        else:
            row.append(ptree[n])
    root_position = (count - 1) // 2
    print(f"Count: {count}, Root position: {root_position}")
    child = row[root_position].data
    sib = None
    count = 1  # will output root after
    prev = None
    for n in row:  # for each top level element put it out in portrait
        p = n.data
        stree = ptree.subtree(p.id)
        d = 1
        if prev:
            d = prev.depth()
        width = d * (leafWidth + bigGap) + bigGap  # cm
        if sib:
            print(sib.name, d, p.name)
        print(r" {p.id} {p.parent} depth={d} width={w} ".format(p=p, d=d, w=width))
        count = count + tex_tree_portrait(fout, stree, width, sib, False)
        sib = p
        prev = stree
    # place root node
    print(r"\node ({p.id}) "
          r"[wbbox, above=15mm of {c.id}]{{\textbf{{{p.name}}}}};".format(p=root, c=child),
          file=fout)
    drawLines(fout, row)
    print("{} Product lines in TeX ".format(count))


def make_tree_portrait(ptree, filename, scope):
    """
    Fully portrait product tree diagram
    :param ptree:
    :param filename:
    :param scope:
    :return: none
    """
    print("Writing Portrait Product Tree in ", filename)

    paperwidth = (ptree.depth() + 1) * (leafWidth + bigGap)  # cm
    paperheight = len(ptree.leaves()) * leafHeight + 0.5  # cm

    ofile = open(filename, "w")
    print_header(scope, paperwidth, paperheight, ofile)
    tex_tree_portrait(ofile, ptree, paperwidth, None, True)
    print_footer(ofile)
    ofile.close()


def make_tree_landmix1(ptree, filename, scope):
    """
    First level landscape, and then portrait
    :param ptree:
    :param filename:
    :param scope:
    :return: none
    """
    print("Writing Mixed Landscape Product Tree in ", filename)

    # calculating diagram size
    first_level = tree_slice(ptree, 1)
    print(first_level)
    nodes = first_level.expand_tree()
    n_blocks_high = 0
    n_blocks_width = 0
    c = 0
    for n in nodes:
        print(n)
        c += 1
        if c != 1:  # skip the first, that is the tp level node.
            p = ptree[n].data
            print(p.name)
            sub_tree = ptree.subtree(p.id)
            if len(sub_tree.leaves()) > n_blocks_high:
                n_blocks_high = len(sub_tree.leaves())
                print("  - New number of leaves:", n_blocks_high)
            n_blocks_width = n_blocks_width + sub_tree.depth() + 1
            print("  - Width: ", n_blocks_width)
    paperwidth = (n_blocks_width + 1) * (leafWidth + bigGap)  # cm
    paperheight = (n_blocks_high + 1) * leafHeight + 0.5  # cm
    print(f"nW: {n_blocks_width}, nH: {n_blocks_high}, WxH: {paperwidth} cm {paperheight} cm")

    # dump file
    ofile = open(filename, "w")
    print_header(scope, paperwidth, paperheight, ofile)
    tex_tree_landmix1(ofile, ptree)
    print_footer(ofile)
    ofile.close()


def make_subtrees(ptree):
    """
    subtrees in landscape mixed mode
    :param ptree:
    :return: none
    """
