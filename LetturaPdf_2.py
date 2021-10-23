# -*- coding: utf-8 -*-
"""
Created on Thu Dec 31 16:41:11 2020

@author: gogliom
"""



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

import pandas as pd
import re
from Funct import ClassifyDoc

def read_pdf_2(filename):

    App = convert_pdf_to_txt(filename)
    
    App = App.replace("\n"," ")
    App2 = App.split(". ")
    
    #App2 =  App.splitlines()
    
 
    App2 = [x for x in App2 if x]
    App2 = pd.DataFrame(App2, columns = ['text'])
    
        
    App2['text'] = App2.apply(lambda row: row.text.upper(), axis = 1)    
    App2['Class'] = App2.apply(lambda row: ClassifyDoc(row.text), axis = 1)
        
    App_Energy = App2[(App2['Class'] == 'Energia') | (App2['Class'] == 'Unknown')]    
    App_Gas = App2[(App2['Class'] == 'Gas') | (App2['Class'] == 'Unknown')]    
        
    Commodity = App2[['Class', 'text']].groupby(['Class']).count()
    #impongo debbano esserci almeno 2 blocchi per commidity 
    #Commodity = Commodity[Commodity['text'] > 3]
    #Commodity = Commodity.reset_index()
    #Commodity = Commodity[Commodity['Class']!= 'Unknown']
     
    
    #se una commodity è sotto il 25% dei paragrafi la elimino 
    Commodity = Commodity.reset_index()
    Tot = Commodity[Commodity['Class'] != 'Unknown']['text'].sum()
    Commodity['Pct'] = Commodity.apply(lambda row: row.text / Tot, axis = 1)
    Commodity = Commodity[Commodity['Pct'] > 0.25]
    Commodity = Commodity[Commodity['Class']!= 'Unknown']
    

    
        
    Ene = ' '.join(App_Energy.text)
    Gas = ' '.join(App_Gas.text)
        
    Ene = re.sub("<.*?>", "", Ene)
    Gas = re.sub("<.*?>", "", Gas)
    
    return (Commodity, Ene, Gas)
