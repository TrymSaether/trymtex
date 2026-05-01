module = "trymtex"

checkengines  = { "pdftex", "xetex", "luatex" }
checkformat   = "latex"
stdengine     = "pdftex"
sourcefiledir = "source"
testfiledir   = "testfiles"

installfiles  = { "trymtex.sty", "trymtex-*.tex" }
sourcefiles   = { "trymtex.sty", "trymtex-*.tex" }
typesetfiles  = { "doc/manual.tex" }
textfiles     = { "README.md", "CHANGELOG.md", "LICENSE" }
cleanfiles    = { "*.pdf", "*.zip", "build/*", "_minted*", "*.data.minted", "*.pyg" }

tdsroot       = "latex"
