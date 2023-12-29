j-vhf-uhf.pdf: README.md
	pandoc --dpi 130 --toc README.md -o j-vhf-uhf.pdf

%-simple.nec: %.nec
	sed "s/SY\\(.*\\)=\\(.*\\)/#define  \\1 \\2/g" $< | cpp | grep -v "^#" $@
