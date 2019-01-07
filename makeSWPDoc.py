#!/usr/bin/env python
# Take list file with parents and make a tex diagram of the product tree.
# Top of the tree will be left of the page ..
# this allows a LONG list of products.
from __future__ import print_function

from treelib import Tree
import argparse
import csv
import re
import requests
import pandoc


outputfile = "swProducts.tex"


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

def getContent(pkg):
    subText = ''
    readMe = ''
    #print('  . ', pkg, ' -----------------------------------------------------')
    # get the list of files in the pkg home folder and subtitle
    link = 'https://github.com/lsst/' + pkg + '.git'
    response = requests.get(link, headers='')
    if response.status_code != 200:
       # try lsst-dm org
       link = 'https://github.com/lsst-dm/' + pkg + '.git'
       response = requests.get(link, headers='')
       if response.status_code != 200:
           # try testpackaging org
           link = 'https://github.com/testpackaging/' + pkg + '.git'
           response = requests.get(link, headers='')
           if response.status_code != 200:
               ROK = False
               org = ''
           else:
               ROK = True
               org = "testpackaging"
       else:
           ROK = True
           org = 'lsst-dm'
    else:
       ROK = True
       org = 'lsst'
    if ROK:
       #print('      (', org, ')')
       doc = pandoc.Document()
       doc.html = response.text.encode('utf-8')
       doctxt = doc.plain.decode('utf-8')
       subText0 = doctxt.split('Sign up')
       subText1 = subText0[1].split('-')
       subText = subText1[0].strip()
       #print('      ..substitle.. ', subText)
       files0 = doctxt.split('Failed to load latest commit information.')
       files1 = files0[1].split('[]')
       f = []
       for fn in files1:
           ftmp0 = fn.split(' ')
           ftmp1 = ftmp0[0].split('-')
           fname = ftmp1[0].strip()
           if fname == '':
               continue
           fnameSL = fname.splitlines()
           fname = fnameSL[0]
           #print('    .... ', fname)
           f.append(fname)
       # get README if present
       link = ""
       readmetype = 'none'
       if 'README.txt' in f:
           link = "https://raw.github.com/lsst/" + pkg +"/master/README.txt"     
           readmetype = 'txt'
       if 'README.md' in f:
           link = "https://raw.github.com/lsst/" + pkg +"/master/README.md"     
           readmetype = 'md'
       if link != "":
           r2 = requests.get(link)
           if r2.status_code == 200:
               if readmetype == 'md':
                   if '## Installation' in r2.text:
                       sr = r2.text.split('## Installation')
                       readMe = sr[0]
                   elif '## Usage' in r2.text:
                       sr = r2.text.split('## Usage')
                       readMe = sr[0]
                   else:
                       rmSL = r2.text.splitlines()
                       readMe = '\n'.join(rmSL[:15])
               if readmetype == 'txt':
                   rmSL = r2.text.splitlines()
                   readMe = '\n'.join(rmSL[:15])
               #print('*****************************')
               #print(readMe)
               #print('*****************************')
           #else:
           #    print("error reading README:\n", link) 
    # convert plain readMe to latex
    tex = '\\paragraph{' + fixTex(pkg) + '}\n'
    tex = tex + '\\textit{' + fixTex(subText) + '}\n\n'
    tex = tex + 'Github package organization: \\textit{' + org + '}\n\n'
    tex = tex + 'Readme header:\n\n'
    if readMe != '':
        tex = tex + '\\begin{verbatim}\n' + readMe + '\\end{verbatim}\n\n'
    else:
        tex = tex + '\\textit{No README provided.}\n\n'
    return(tex)

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

def gitPkgs(product):
    print(' - ', product.name)
    if product.pkgs:
        tex = ''
        pkgsList = product.pkgs.split(',')
        for pkg in pkgsList:
            tex = getContent(pkg)
        return(tex)
    else:
        return("No git packages defined.")

def swProducts(stree):
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
          tex = tex + "\\subsubsection{" + product.name + " git packages}\n"
          tex = tex + gitPkgs(product)

    return(tex)

# MAIN

parser = argparse.ArgumentParser()
parser.add_argument("--file", help="Input csv file ", default='DM Product Properties.csv')

args = parser.parse_args()

inputfile = args.file

ptree = readinputfile(inputfile)

swtree = ptree.subtree('DMSW')

#print(swtree)

stub = slice(swtree, 1) # I get the first row
nodes = stub.expand_tree(mode=Tree.WIDTH)

output = ""
for n in nodes:
   if n != 'DMSW':
     print(n)
     node = swtree[n]
     product = node.data
     stree = swtree.subtree(product.id)
     pname = fixTex(product.name)
     output = output + "\\subsection{" + pname + " Software Products}\n"
#     output = output + productBody(product)
#     output = output + "Follows the list of sub-products."
     output = output + swProducts(stree)

with open(outputfile, 'w') as tout:
   print(output, file=tout)
