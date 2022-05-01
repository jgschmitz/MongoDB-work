# %pip install tabula-py

from tabula import read_pdf
# Read pdf into list of DataFrame
df = read_pdf('test.pdf', pages='all')
