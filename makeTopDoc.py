#!/usr/bin/env python
# Take list file with parents and make a tex diagram of the product tree.
# Top of the tree will be left of the page ..
# this allows a LONG list of products.
from __future__ import print_function

from treelib import Tree
import argparse
import csv
import re


outputfile = "topLevel.tex"


class Product(object):
    def __init__(self, id, name, parent, desc, wbs, manager, owner,
                 kind, pkgs):
        self.id = id
        self.name = name
        self.parent = parent
        self.desc = desc
        self.wbs = wbs
        self.manager = manager
        self.owner = owner
        self.kind = kind
        self.pkgs = pkgs


def fixIdTex(text):
    id= re.sub(r"\s+","", text)
    id= id.replace("(","")
    id= id.replace(")","")
    id= id.replace("\"","")
    id= id.replace("_", "")
    id= id.replace(".","")
    id= id.replace("&","")
    return id


def fixTex(text):
    ret = text.replace("_", "\\_")
    ret = ret.replace("/", "/ ")
    ret = ret.replace("&", "\\& ")
    return ret


def readinputfile(inputfile):
    "Read the csv input file and construct  a tree structure"
    count = 0
    ptree = Tree()
    with open(inputfile, 'r') as fin:
        reader= csv.reader(fin,dialect='excel')
        for line in reader:
            count = count + 1
            if count == 1: # skip the header
                continue
            part = line
            id = fixIdTex(part[1]) #make an id from the name
            pid= fixIdTex(part[3]) #use the same formaula on the parent name then we are good
            name= fixTex(part[2])
            prod = Product(id, name, pid, "", part[4], part[6],
                           part[7], "", part[8])
            if (count == 2):  # root node
                ptree.create_node(prod.id, prod.id, data=prod)
            else:
                if prod.parent != "":
                    ptree.create_node(prod.id, prod.id, data=prod,
                                      parent=prod.parent)
                else:
                    print(part[0] + " no parent")

        print("{} Product lines".format(count))
    return ptree

def slice(ptree, outdepth):
    if (ptree.depth() == outdepth):
        return ptree
    # copy the tree but stopping at given depth
    ntree = Tree()
    nodes = ptree.expand_tree()
    count = 0  # subtree in input
    for n in nodes:
        #print("Accesing {}".format(n))
        depth = ptree.depth(n)
        prod = ptree[n].data

        #print("outd={od} mydepth={d} Product: {p.id} name: {p.name} parent: {p.parent}".format(od=outdepth, d=depth, p=prod))
        if (depth <= outdepth):
            # print(" YES ", end='')
            if (count == 0):
                ntree.create_node(prod.id, prod.id, data=prod)
            else:
                ntree.create_node(prod.id, prod.id, data=prod,
                                  parent=prod.parent)
            count = count + 1
         #print()
    return ntree

def productBody(product):
     tex = "\\begin{itemize}"
     tex = tex + "\\item Identification (short key): " + product.id + "\n"
     tex = tex + "\\item Parent in the worduct tree: " + product.parent + "\n"
     tex = tex + "\\item Description: " + product.desc + "\n"
     tex = tex + "\\item WBS: " + product.wbs + "\n"
     tex = tex + "\\item Manager: " + product.manager + "\n"
     tex = tex + "\\item Owner: " + product.owner + "\n"
     tex = tex + "\\item Kind:" + product.kind + "\n"
     pkgs = fixTex(product.pkgs)
     tex = tex + "\\item SW packages: " + pkgs + "\n"
     tex = tex + "\\end{itemize}"
     return(tex)

def subProducts(stree):
    snodes = stree.expand_tree(mode=Tree.WIDTH)
    count = 0
    tex = ""
    for n in snodes:
       if count == 0:
          count = count + 1
       else:
          count = count + 1
          node = stree[n]
          product = node.data
          tex = tex + "\\subsubsection{" + product.name + "}\n"
          tex = tex + productBody(product)

    return(tex)

# MAIN

parser = argparse.ArgumentParser()
parser.add_argument("--file", help="Input csv file ", default='DM Product Properties.csv')

args = parser.parse_args()

inputfile = args.file

ptree = readinputfile(inputfile)

stub = slice(ptree, 1) # I get the first row

nodes = stub.expand_tree(mode=Tree.WIDTH)

output = ""
for n in nodes:
   if n != 'DM':
     print(n)
     node = ptree[n]
     product = node.data
     stree = ptree.subtree(product.id)
     pname = fixTex(product.name)
     output = output + "\\subsection{" + pname + "}\n"
     output = output + productBody(product)
     #output = output + tmptex
     output = output + "Follows the list of sub-products."
     output = output + subProducts(stree)

with open(outputfile, 'w') as tout:
   print(output, file=tout)
