import lxml.etree
import sys

etree = lxml.etree.parse(sys.argv[1])

text = lxml.etree.tostring(etree, encoding="unicode", pretty_print=True)
print(text)
