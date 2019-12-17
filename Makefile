#for dependency you want all tex files  but for acronyms you do not want to include the acronyms file itself.
tex=$(filter-out $(wildcard *acronyms.tex) , $(wildcard *.tex))  

DOC= DMTN-104
SRC= $(DOC).tex
TREES_DIR=trees
SUBTREES_DIR=subtrees
TREE_FILES = $(shell cd $(TREES_DIR); ls *.tex)
SUBTREE_FILES = $(shell cd $(SUBTREES_DIR); ls *.tex)

#export TEXMFHOME = lsst-texmf/texmf

# Version information extracted from git.
GITVERSION := $(shell git log -1 --date=short --pretty=%h)
GITDATE := $(shell git log -1 --date=short --pretty=%ad)
GITSTATUS := $(shell git status --porcelain)
ifneq "$(GITSTATUS)" ""
        GITDIRTY = -dirty
endif

OBJ=$(SRC:.tex=.pdf)
TREE_PDF=$(TREE_FILES:.tex=.pdf)
TREES=$(TREE_FILES:.tex=)

#Default when you type make
all: subtrees $(TREE_PDF) $(OBJ) 

JOBNAME=$(DOC)

$(JOBNAME).pdf: $(tex) meta.tex acronyms.tex
	xelatex -jobname=$(JOBNAME) $(DOC)
	bibtex $(JOBNAME)
	xelatex -jobname=$(JOBNAME) $(DOC)
	xelatex -jobname=$(JOBNAME) $(DOC)
	xelatex -jobname=$(JOBNAME) $(DOC)

.FORCE:

#The generateAcronyms.py  script is in lsst-texmf/bin - put that in the path
acronyms.tex :$(tex) myacronyms.txt
	${TEXMFHOME}/../bin/generateAcronyms.py -t "DM"  $(tex)

clean :
	latexmk -c
	rm *.pdf *.nav *.bbl *.xdv *.snm

meta.tex: Makefile .FORCE
	rm -f $@
	touch $@
	echo '% GENERATED FILE -- edit this in the Makefile' >>$@
	/bin/echo '\newcommand{\lsstDocType}{$(DOCTYPE)}' >>$@
	/bin/echo '\newcommand{\lsstDocNum}{$(DOCNUMBER)}' >>$@
	/bin/echo '\newcommand{\vcsrevision}{$(GITVERSION)$(GITDIRTY)}' >>$@
	/bin/echo '\newcommand{\vcsdate}{$(GITDATE)}' >>$@

$(TREE_PDF): 
	for f in $(TREES); do \
	  cd $(TREES_DIR) ; \
	  xelatex -jobname="$$f" "$$f".tex ; \
	done

subtrees: $(SUBTREES_DIR)/*.tex
	for f in $(SUBTREE_FILES); do cd $(SUBTREES_DIR); xelatex "$$f" ; done

