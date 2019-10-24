#for dependency you want all tex files  but for acronyms you do not want to include the acronyms file itself.
tex=$(filter-out $(wildcard *acronyms.tex) , $(wildcard *.tex))  

DOC= DMTN-104
SRC= $(DOC).tex
MKPDF=latexmk -pdf
TREES_DIR=trees
TEX_FILES = $(shell cd $(TREES_DIR); ls *.tex)

#export TEXMFHOME = lsst-texmf/texmf

# Version information extracted from git.
GITVERSION := $(shell git log -1 --date=short --pretty=%h)
GITDATE := $(shell git log -1 --date=short --pretty=%ad)
GITSTATUS := $(shell git status --porcelain)
ifneq "$(GITSTATUS)" ""
        GITDIRTY = -dirty
endif

OBJ=$(SRC:.tex=.pdf)

#Default when you type make
all: trees $(OBJ)

$(OBJ): $(tex) meta.tex acronyms.tex
	latexmk -bibtex -xelatex -f $(SRC)

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


trees: *.tex
	for f in $(TEX_FILES); do cd $(TREES_DIR); $(MKPDF) "$$f" ; done

