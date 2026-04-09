PACKAGE := trymtex

.PHONY: check doc clean install uninstall examples test ctan

check:
	l3build check

doc:
	l3build doc

examples:
	TEXINPUTS=source: latexmk -lualatex -outdir=build examples/minimal.tex
	TEXINPUTS=source: latexmk -lualatex -shell-escape -outdir=build examples/showcase.tex

test:
	TEXINPUTS=source: latexmk -lualatex -outdir=build testfiles/smoke.tex

install:
	l3build install

uninstall:
	l3build uninstall

ctan:
	l3build ctan

clean:
	l3build clean
	rm -rf build
