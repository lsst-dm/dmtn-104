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
import os
from .util import Product
from treelib import Tree

txtheight = 36   # pt
leafHeight = 37  # pt space per leaf box .. height of page calc
leafWidth = 110  # pt space per leaf box .. width of page calc
smallGap = 6  # pt between leaf boxes in the same group
bigGap = 43  # pt between different levels, or leaf boxes
sep = 3  # pt inner sep
backgap = 14  # pt
backrate = (leafWidth - backgap) / leafWidth

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
    target = target.strip('\n')
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
          f"\\usepackage[paperwidth={pwidth}pt,paperheight={pheight}pt,\n"
          "left=-2mm,top=3mm,bottom=0mm,right=0mm,\n"
          "noheadfoot,marginparwidth=0pt,includemp=false,\n"
          "textwidth=30cm,textheight=50mm]{geometry}\n"
          "\\newcommand\showpage{%\n"
          "\\setlayoutscale{0.5}\setlabelfont{\\tiny}\printheadingsfalse\printparametersfalse\n"
          "\\currentpage\pagedesign}\n"
          "\\hypersetup{pdftitle={" + target + " products }, pdfsubject={Diagram illustrating the\n"
          "                products in LSST " + target +" }, pdfauthor={Extracted from MagicDraw}}\n"
          "\\tikzstyle{tbox}=[rectangle,text centered, text width=30mm]\n"
          "\\tikzstyle{wbbox}=[rectangle, rounded corners=3pt, draw=black, top color=blue!50!white,\n"
          "                    bottom color=white, very thick, minimum height=40pt, inner sep=2pt,\n"
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
        print(r" \draw[pline]   ({p.id}.north) -- ++(0.0,0.5) -| ({p.parent}.south) ; ".format(p=prod), file=fout)


def outputWBSPKG(fout, prod):
    print("] {", file=fout, end='')
    print(r"\textbf{" + prod.shortname + "} };", file=fout, end='')
    # print("};", file=fout)
    if WBS == 1 and prod.wbs != "":
        print(r"\node [below right] at ({p.id}.north west) {{\footnotesize \color{{blue}}{w}}} ;".
              format(p=prod, w=' '.join(prod.wbs)), file=fout)
    if PKG == 1 and prod.pkgs:
        print(r"\node ({p.id}pkg) [tbox,below=3mm of {p.id}.north] {{".format(g=smallGap, p=prod), file=fout, end='')
        print(r"{\footnotesize \color{black} \begin{verbatim} " + ' '.join(prod.pkgs) + r" \end{verbatim} }  };",
              file=fout)
    print("", file=fout)
    return


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
    prev = Product("n", "n", "n", "n", "n", "n", "n", "n", "n", "n", "n", "n", "n", "n", "n", "n", "n", "n")
    # Text height + the gap added to each one
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
                        print("right={d}pt of {p.id}".format(d=width, p=sib), file=fout, end='')
                    # print(r"] {\textbf{" + prod.shortname + "} };", file=fout)
                    outputWBSPKG(fout, prod)
            else:
                print(r"\node ({p.id}) [pbox,".format(p=prod), file=fout, end='')
                if prev.parent != prod.parent:  # first child to the right if portrait left if landscape
                    found = 0
                    scount = count - 1
                    while found == 0 and scount > 0:
                        scount = scount - 1
                        found = fnodes[scount].parent == prod.parent
                    if scount <= 0:  # first sib can go righ of parent
                        print("right={g}pt of {p.parent}".format(g=bigGap, p=prod),
                              file=fout, end='')
                    else:  # Figure how low to go  - find my prior sibling
                        psib = fnodes[scount]
                        leaves = ptree.leaves(psib.id)
                        depth = len(leaves) - 1
                        # the number of leaves below my sibling
                        dist = depth * (leafHeight + smallGap) + smallGap
                        print("below={}pt of {}".format(dist, psib.id),
                              file=fout, end='')
                else:
                    # benetih the sibling
                    dist = smallGap
                    print("below={}pt of {}".format(dist, prev.id), file=fout, end='')
                outputWBSPKG(fout, prod)
                print(r" \draw[pline] ({p.parent}.east) -| ++(0.4,0) |- ({p.id}.west); ".format(p=prod), file=fout)
            prev = prod
    return count


def tex_tree_portrait0(fout, ptree, width, sib, full):
    """
    Write the product tree in PORTRAIT COMPACT format
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
    prev = Product("n", "n", "n", "n", "n", "n", "n", "n", "n", "n", "n", "n", "n", "n", "n", "n", "n", "n")
    # Text height + the gap added to each one
    for n in nodes:
        prod = ptree[n].data
        fnodes.append(prod)
        depth = ptree.depth(n)
        count = count + 1
        if depth <= outdepth:
            if count == 1:  # root node
                if full:  # if the first node of a full tree, no parent
                    print(r"\node ({p.id}) [wbbox]{{\textbf{{{p.name}}}}};".format(p=prod), file=fout)
                else:  # some sub tree (portrait) in a landscape tree
                    print(r"\node ({p.id}) [pbox, ".format(p=prod), file=fout)
                    if sib:
                        print("right={d}pt of {p.id}".format(d=width, p=sib), file=fout, end='')
                    outputWBSPKG(fout, prod)
            else:
                print(r"\node ({p.id}) [pbox,".format(p=prod), file=fout, end='')
                if prev.parent != prod.parent:  # first child to the right if portrait left if landscape
                    found = 0
                    scount = count - 1
                    while found == 0 and scount > 0:
                        scount = scount - 1
                        found = fnodes[scount].parent == prod.parent
                    if scount <= 0:
                        print("below right={g}pt and -{b}pt of {p.parent}".format(p=prod, g=smallGap, b=backgap),
                              file=fout, end='')
                    else:  # Figure how low to go  - find my prior sibling
                        psib = fnodes[scount]
                        sib_sub_tree = ptree.subtree((psib.id))
                        nnodes = sib_sub_tree.size()
                        depth = nnodes - 1
                        # the number of leaves below my sibling
                        dist = depth * (txtheight + smallGap + 1) + smallGap
                        print("below={}pt of {}".format(dist, psib.id),
                              file=fout, end='')
                else:
                    # benetih the sibling
                    print("below={}pt of {}".format(smallGap, prev.id), file=fout, end='')
                outputWBSPKG(fout, prod)
                print(r" \draw[pline] ({p.parent}.south) -| ++(0,0) |- ({p.id}.west); ".format(p=prod), file=fout)
            prev = prod
    return count


def tex_tree_landmix1(fout, ptree, compact):
    """ Write the product tree diagram:
        first level in landscape
        second level subtrees in portrait
    :param fout: outputfile
    :param ptree: input product tree
    :param compact: if the landscape is compact or not
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
    root_position = int(count / 2) -1
    if root_position < 0:
        root_position = 0
    # print(f"Count: {count}, Root position: {root_position}")
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
        if compact:
            if d != 0:
                width = d * (leafWidth - backgap)
            else:
                width = bigGap
            count = count + tex_tree_portrait0(fout, stree, width, sib, False)
        else:
            width = d * (leafWidth + bigGap) + bigGap
            count = count + tex_tree_portrait(fout, stree, width, sib, False)
        sib = p
        prev = stree
    # place root node
    print(r"\node ({p.id}) "
          r"[wbbox, above={bg}pt of {c.id}]{{\textbf{{{p.name}}}}};".format(bg=bigGap, p=root, c=child), file=fout)
    drawLines(fout, row)
    print("{} Product lines in TeX ".format(count))


def tex_full_tree(fout, ptree, compact):
    """ Write the product tree diagram:
        first level in landscape
        second level subtrees in portrait
    :param fout: outputfile
    :param ptree: input product tree
    :param compact: if the landscape is compact or not
    :return: none
    """
    fl_stub = tree_slice(ptree, 1)
    fl_nodes = fl_stub.expand_tree(mode=Tree.WIDTH)  # default mode=DEPTH
    fl_row = []
    fl_count = 0
    root = None
    sl_d = 0
    sib = None
    p_count = 0
    for fl in fl_nodes:
        fl_count = fl_count + 1
        if fl_count == 1:  # root node
            root = ptree[fl].data
        else:
            fl_row.append(ptree[fl])  # superfluous, to remove
            s = ptree[fl].data
            sl_subtree = ptree.subtree(s.id)
            sl_stub = tree_slice(sl_subtree, 1)
            sl_nodes = sl_stub.expand_tree()
            sl_row = []
            sl_count = 0
            sl_root = None
            sl_size = 0
            for sl in sl_nodes:
                sl_count = sl_count + 1
                if sl_count == 1:
                    sl_root = ptree[sl].data
                else:
                    p = ptree[sl].data
                    sl_row.append(ptree[sl])
                    stree = ptree.subtree(p.id)
                    if compact:
                        if sl_d != 0 and sib is not None:
                            width = sl_d * (leafWidth - backgap)
                        else:
                            width = bigGap
                        sl_size = sl_size + width
                        p_count = p_count + tex_tree_portrait0(fout, stree, width, sib, False)
                    else:
                        width = sl_d * (leafWidth + bigGap) + bigGap
                        p_count = p_count + tex_tree_portrait(fout, stree, width, sib, False)
                    sib = p
                    sl_d = stree.depth()
            # position the subtree root
            sl_root_p = int(sl_count / 2) -1
            if sl_root_p < 0:
                sl_root_p = 0
            # print(sl_count, sl_root_p)
            sl_child = sl_row[sl_root_p].data
            print(r"\node ({p.id}) "
                  r"[wbbox, above={bg}pt of {c.id}]{{\textbf{{{p.name}}}}};".format(bg=bigGap,
                                                                                    p=sl_root, c=sl_child), file=fout)
            # print(" second level ", sl_row)
            drawLines(fout, sl_row)
    # place root node
    root_position = int(fl_count / 2) -1
    if root_position < 0:
        root_position = 0
    # print(f"Count: {count}, Root position: {root_position}")
    child = fl_row[root_position].data
    print(r"\node ({p.id}) "
          r"[wbbox, above={bg}pt of {c.id}]{{\textbf{{{p.name}}}}};".format(bg=bigGap, p=root, c=child), file=fout)
    # print("  first level ", fl_row)
    drawLines(fout, fl_row)
    print("{} Product lines in TeX ".format(p_count + fl_count))


def make_tree_portrait(ptree, filename, scope):
    """
    Fully portrait product tree diagram
    :param ptree:
    :param filename:
    :param scope:
    :return: none
    """
    print("Writing Portrait Product Tree in ", filename)

    paperwidth = (ptree.depth() + 1) * (leafWidth + bigGap)
    paperheight = len(ptree.leaves()) * (leafHeight + smallGap) + bigGap

    ofile = open(filename, "w")
    print_header(scope, paperwidth, paperheight, ofile)
    tex_tree_portrait(ofile, ptree, paperwidth, None, True)
    print_footer(ofile)
    ofile.close()


def make_tree_landmix1(ptree, filename, scope, compact):
    """
    First level landscape, and then portrait
    :param ptree:      tree to render in a graphic form
    :param filename:   filename to save the text source for the tree graph
    :param scope:
    :return: none
    """
    print("Writing Mixed (1 level) Landscape Product Tree in ", filename)

    # calculating diagram size
    first_level = tree_slice(ptree, 1)
    nodes = first_level.expand_tree()
    n_blocks_high = 0
    n_blocks_width = 0
    paperwidth = 0
    c = 0
    for n in nodes:
        c += 1
        if c != 1:  # skip the first, that is the tp level node.
            p = ptree[n].data
            sub_tree = ptree.subtree(p.id)
            if compact:
                nnodes = sub_tree.size()
                if nnodes > n_blocks_high:
                    n_blocks_high = nnodes
                sub_depth = sub_tree.depth()
                if sub_depth == 0:
                    n_blocks_width = n_blocks_width + 1
                    paperwidth = paperwidth + leafWidth + bigGap
                else:
                    # the compression factor has been calculated based on the backgap = 14 pt
                    n_blocks_width = n_blocks_width + 1 + sub_depth * 0.86
                    paperwidth = paperwidth + leafWidth * (1 + sub_depth * backrate)
                    # print(sub_depth, paperwidth)
            else:
                if len(sub_tree.leaves()) > n_blocks_high:
                    n_blocks_high = len(sub_tree.leaves())
                n_blocks_width = n_blocks_width + sub_tree.depth() + 1
                paperwidth = (n_blocks_width + 1) * (leafWidth + bigGap)
    paperheight = (n_blocks_high + 1) * (leafHeight + smallGap) + bigGap * 2

    # dump file
    ofile = open(filename, "w")
    # print(n_blocks_width, paperwidth, "backrate:", backrate)
    print_header(scope, paperwidth, paperheight, ofile)
    tex_tree_landmix1(ofile, ptree, compact)
    print_footer(ofile)
    ofile.close()


def make_full_tree(ptree, filename, scope, compact):
    """
    First level landscape, and then portrait
    :param ptree:
    :param filename:
    :param scope:
    :return: none
    """
    print("Writing Mixed (2 levels) Landscape Full Product Tree in ", filename)

    # calculating diagram size
    first_level = tree_slice(ptree, 1)
    fl_nodes = first_level.expand_tree()
    n_blocks_high = 0
    n_blocks_width = 0
    paperwidth = 0
    fl_c = 0
    for fl in fl_nodes:
        fl_c = fl_c + 1
        s = ptree[fl].data
        if fl_c != 1:
            sub_level = ptree.subtree(s.id)
            second_level = tree_slice(sub_level,1)
            sl_nodes = second_level.expand_tree()
            c = 0
            for n in sl_nodes:
                c = c + 1
                if c != 1:  # skip the first, that is the tp level node.
                    p = ptree[n].data
                    sub_tree = ptree.subtree(p.id)
                    nnodes = sub_tree.size()
                    if nnodes > n_blocks_high:
                        n_blocks_high = nnodes
                    sub_depth = sub_tree.depth()
                    if compact:
                        if sub_depth == 0:
                            n_blocks_width = n_blocks_width + 1
                            paperwidth = paperwidth + leafWidth + bigGap
                        else:
                            # the compression factor has been calculated based on the backgap = 14 pt
                            paperwidth = paperwidth + leafWidth * (sub_depth + 1) * backrate + smallGap
                        # print(p.id, sub_depth, paperwidth, nnodes)
                    else:
                        paperwidth = paperwidth + (sub_depth + 1) * (leafWidth + bigGap)
    paperheight = n_blocks_high * (leafHeight + smallGap) + (leafHeight + bigGap) * 2 + leafHeight
    paperwidth = paperwidth + leafWidth

    # dump file
    ofile = open(filename, "w")
    # print(n_blocks_width, paperwidth, "backrate:", backrate)
    print_header(scope, paperwidth, paperheight, ofile)
    tex_full_tree(ofile, ptree, compact)
    print_footer(ofile)
    ofile.close()


def make_subtrees(ptree, filename, scope, compact):
    """
    subtrees in landscape mixed mode
    :param ptree:
    :return: none
    """
    subfolder = "subtrees/"
    if not os.path.exists(subfolder):
        os.makedirs(subfolder)
    first_level = tree_slice(ptree, 1)
    nodes = first_level.expand_tree()
    c = 0
    for n in nodes:
        c = c + 1
        if c != 1:
            p = ptree[n].data
            sub_tree = ptree.subtree(p.id)
            sub_file_name = subfolder + filename + "_" + p.id + ".tex"
            make_tree_landmix1(sub_tree, sub_file_name, scope, compact)
