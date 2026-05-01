PACKAGE := trymtex

.PHONY: check doc clean install uninstall examples test ctan

check:
	l3build check

doc:
	l3build doc

examples:
	latexmk -lualatex -outdir=build examples/minimal.tex
	TEXINPUTS=source: latexmk -lualatex -shell-escape -outdir=build examples/showcase.tex

test:
	l3build check

install:
	l3build install

uninstall:
	l3build uninstall

ctan:
	l3build ctan

clean:
	l3build clean
	rm -rf build
