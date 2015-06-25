

all:
	python layout.py > poster.tex
	pdflatex poster
