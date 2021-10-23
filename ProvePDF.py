# -*- coding: utf-8 -*-
"""
Created on Thu Dec  3 22:40:45 2020

@author: gogliom
"""

'''
gira su ambiente D:\altro\rpa\energy\iren\env
'''

'''
import pdftables_api

#a pagamento dopo 50 pagine (40 euro per 1000 pagine)
c = pdftables_api.Client('fe0marbgsmuq')   #API KEY
c.xlsx(r"D:\Altro\RPA\Energy\IREN\TEST CTE\CTE\esempi cte\Energit-Casa-Web.pdf", r"D:\Altro\RPA\Energy\IREN\TEST CTE\CTE\esempi cte\outputEnergit.xlsx")






import pdfquery

pdf = pdfquery.PDFQuery(r"D:\Altro\RPA\Energy\IREN\TEST CTE\CTE\esempi cte\Energit-Casa-Web.pdf")
pdf.load()

label = pdf.pq('LTTextLineHorizontal:contains("ULTERIORI INFORMAZIONI")')
left_corner = float(label.attr('x0'))
bottom_corner = float(label.attr('y0'))
name = pdf.pq('LTTextLineHorizontal:in_bbox("%s, %s, %s, %s")' % (left_corner, bottom_corner-200, left_corner+150, bottom_corner)).text()
name

xxx = 1

'''


import pdfminer
import io

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO

def convert_pdf_to_txt(path):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    #device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    device = TextConverter(rsrcmgr, retstr, laparams=laparams)
    fp = open(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos=set()

    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
        interpreter.process_page(page)

    text = retstr.getvalue()

    fp.close()
    device.close()
    retstr.close()
    return text






'''
xxx = convert_pdf_to_txt(r"D:\Altro\RPA\Energy\IREN\TEST CTE\CTE\esempi cte\CE_POWER_BASE_LSIC.pdf")



import camelot
tables = camelot.read_pdf(r"D:\Altro\RPA\Energy\IREN\TEST CTE\CTE\esempi cte\210120-dvdr6wg-6mesi-green-luce.pdf", pages = '1,2,3')


tables = camelot.read_pdf(r"D:\Altro\RPA\Energy\IREN\TEST CTE\CTE\foo.pdf")

tables.export('D:\Altro\RPA\Energy\IREN\TEST CTE\foo.csv', f='csv', compress=False)

tables

tables[0]

from pdfminer.high_level import extract_text

text = extract_text('samples/simple1.pdf')


from tabula import read_pdf 
from tabula import convert_into 

import pandas as pd

df = read_pdf(r"D:\Altro\RPA\Energy\IREN\TEST CTE\CTE\esempi cte\CE_POWER_BASE_LSIC.pdf", pages = "all"
              ,pandas_options={'header': None}
)

import pandas as pd

df_0 = df[0]
df_1 = df[1]
df_2 = df[2]
df_3 = df[3]
df_4 = df[4]
df_5 = df[5]
df_6 = df[6]


df_0.head()
print(df_0)

pd.df_8.to_csv("D:\Altro\RPA\Energy\aaa.csv")




import PyPDF2

# creating an object 
file = open(r"D:\Altro\RPA\Energy\IREN\TEST CTE\CTE\esempi cte\223_E3L12%2300005.pdf", 'rb')

# creating a pdf reader object
fileReader = PyPDF2.PdfFileReader(file)

# print the number of pages in pdf file
print(fileReader.numPages)

pageObj = fileReader.getPage(0)
xxx = pageObj.extractText()


import pdftotext

'''