#for dependency you want all tex files  but for acronyms you do not want to include the acronyms file itself.
tex=$(filter-out $(wildcard *acronyms.tex) , $(wildcard *.tex))  

DOC= DMTN-104
SRC= $(DOC).tex
TREES_DIR=trees
SUBTREES_DIR=subtrees
DOT_DIR=dot
DOT_FILES = $(shell cd $(DOT_DIR); ls *.dot)
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
TREES_PDF=$(TREE_FILES:.tex=.pdf)
TREES=$(TREE_FILES:.tex=)
SUBTREES_PDF=$(SUBTREE_FILES:.tex=.pdf)
SUBTREES=$(SUBTREE_FILES:.tex=)

#Default when you type make
all: generate_imgs crop_pdf_imgs $(OBJ)

# in travis I need to generate the images before generating the doc
generate_imgs: do_trees do_subtrees makedots

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
	rm -f *.pdf *.nav *.bbl *.xdv *.snm *.out *.toc *.blg *.fls
	rm -f trees/*.pdf trees/*.nav trees/*.bbl trees/*.xdv trees/*.snm
	rm -f subtrees/*.pdf subtrees/*.nav subtrees/*.bbl subtrees/*.xdv subtrees/*.snm

meta.tex: Makefile .FORCE
	rm -f $@
	touch $@
	echo '% GENERATED FILE -- edit this in the Makefile' >>$@
	/bin/echo '\newcommand{\lsstDocType}{$(DOCTYPE)}' >>$@
	/bin/echo '\newcommand{\lsstDocNum}{$(DOCNUMBER)}' >>$@
	/bin/echo '\newcommand{\vcsrevision}{$(GITVERSION)$(GITDIRTY)}' >>$@
	/bin/echo '\newcommand{\vcsdate}{$(GITDATE)}' >>$@

do_trees:
	for f in $(TREES); do \
	  cd $(TREES_DIR) ; \
	  xelatex -jobname="$$f" "$$f".tex ; \
	  cd .. ; \
	done

do_subtrees:
	for f in $(SUBTREES); do \
	  cd $(SUBTREES_DIR) ; \
	  xelatex -jobname="$$f" "$$f".tex ; \
	  cd .. ; \
	done

crop_pdf_imgs: 
	> cropPdf.log
	for f in $(TREES); do \
	  echo "Cropping" "$$f".pdf ; \
	  python ./bin/cropPdf.py -f $(TREES_DIR)/"$$f".pdf >> cropPdf.log; \
	done
	for f in $(SUBTREES); do \
	  echo "Cropping" "$$f".pdf ; \
	  python ./bin/cropPdf.py -f $(SUBTREES_DIR)/"$$f".pdf > /dev/null ; \
	done

makedots:
	for f in $(DOT_FILES); do \
	  cd $(DOT_DIR) ; \
	  dot -Tpdf -o"$$f".pdf "$$f" ; \
	  python ../bin/cropPdf.py -f "$$f".pdf > /dev/null ; \
	  pdf2ps "$$f".pdf "$$f".ps ; \
	  cd .. ; \
	done
