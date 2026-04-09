PACKAGE := trymtex

.PHONY: check doc clean install uninstall examples test ctan

check:
	l3build check

doc:
	l3build doc

examples:
	TEXINPUTS=source: lualatex -output-directory=build examples/minimal.tex
	TEXINPUTS=source: lualatex -shell-escape -output-directory=build examples/showcase.tex

test:
	TEXINPUTS=source: lualatex -output-directory=build testfiles/smoke.tex

install:
	l3build install

uninstall:
	l3build uninstall

ctan:
	l3build ctan

clean:
	l3build clean
	rm -rf build
