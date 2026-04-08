module = "trymtex"

sourcefiles  = {"trymtex.dtx", "trymtex.ins"}
installfiles = {"*.sty"}
typesetfiles = {"trymtex.dtx", "README.md"}
testfiledir  = "testfiles"
checkengines = {"pdftex", "xetex", "luatex"}
checkruns    = 1
