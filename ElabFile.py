# -*- coding: utf-8 -*-
"""
Created on Sun Dec 13 11:01:16 2020

@author: gogliom
"""

import os
import re
import numpy as np

from ProvePDF import convert_pdf_to_txt 
from Read_Pdf import read_pdf  #importazione basata sul pacchetto che tiene struttura
from LetturaPdf_2 import read_pdf_2 #importaizone basata sulla convert_pdf_to_txt e poi splittata in ele / gas in base ai paragrafi


from Funct import Durata
from Funct import PrezzoComponenteDispacciamento , PrezzoComponenteCommVendita
from Funct import Scadenza
from Funct import PrezzoComponenteEnergia
from Funct import PrezzoComponenteGAS

from Funct import Name
from Funct import SplitPDF
from Funct import energiaVerde
from Funct import PrezzoComponenteEnergiaF1, PrezzoComponenteEnergiaF2, PrezzoComponenteEnergiaF3
from Funct import CodiceOfferta
from Funct import ClassifyDoc
from Funct import replaceNumber


import pandas as pd



def ElabFile(Commodity, Energia, Energia2, Gas, Gas2, PdfSt):
    Prezzo = ""
    ResAll = []

    ResAll = pd.DataFrame(ResAll)
    
    #try:
    a = 1
    if a == 1:
        
        Res = []
        Res = pd.DataFrame(Res)
        
     
        #ci sono alcuni casi in cui nella lettura del pdf dopo un trattino si crea uno spazio. Elimino 
        Energia = Energia.replace("- ", "-")
        Gas = Gas.replace("- ", "-")  
        
        #alcuni operatori i costi fissi li scrivono in lettere..
        Energia = replaceNumber(Energia)
        Gas = replaceNumber(Gas)


        for Com in Commodity['Class']:
            Res = []
            Res = pd.DataFrame(Res)

            if Com == "Energia":
                Doc = Energia
                try:
                    Doc2 = Energia2
                except:
                    Doc2 = Energia
            if Com == "Gas":
                Doc = Gas
                try:
                    Doc2 = Gas2
                except: 
                    Doc2 = Gas

                    
            Res.at[0,'Commodity'] = Com   
                
            
            #try: 
            N = Name(PdfSt)
            Res.at[0,'Name'] = N.iloc[0]
            #except:
                #pass

            
            
            #il codice sembra funzionare meglio leggendolo nella versione con struttura 
            Res['CodiceOfferta'] = ""
            try:
                Cod = CodiceOfferta(Doc)
                Res.at[0, 'CodiceOfferta'] = Cod.iloc[0]
            except:
                pass
            #in alcuni casi il codice non viene letto, uso documento letto in altro modo 
            if len(Res['CodiceOfferta']) > 0:
                if Res['CodiceOfferta'][0] == "":
                    try:
                        Cod = CodiceOfferta(Doc)
                        Res.at[0, 'CodiceOfferta'] = Cod.iloc[0]
                    except: 
                        pass
                    
            elif len(Res['CodiceOfferta']) == 0: 
                print('aa') #nel caso in cui il dataframe non ha obs      
                try:
                    Cod = CodiceOfferta(Doc)
                    Res.at[0, 'CodiceOfferta'] = Cod.iloc[0]
                except:
                    pass             

        
            try:
                CV = PrezzoComponenteCommVendita(Doc)                
                Res.at[0, 'PrezzoCV'] = CV.iloc[0]
                #Res['PrezzoCV'] = CV.iloc[0]
            except:
                pass 
            
            
            try:
                DI = PrezzoComponenteDispacciamento(Doc)
                Res.at[0, 'PrezzoDISP'] = DI.iloc[0]
                #Res['PrezzoDISP'] = DI.iloc[0]
            except:
                pass
                          
            try:
                Scad = Scadenza(Doc)
                Res.at[0, 'Scadenza'] = Scad.iloc[0]
                #Res['Scadenza'] = Scad #Scad.iloc[0]
            except:
                pass 
                
                
            try:
                Dur = Durata(Doc)
                Res.at[0, 'Durata'] = Dur.iloc[0]
                #Res['Durata'] = Dur.iloc[0]
            except:
                pass 
                
                
            try:
                E = energiaVerde(Doc)
                E1 = E[0]
                E2 = E[1]
                Res.at[0,'FlagVerde'] = E1.iloc[0]
                Res.at[0,'PrezzoVerde'] = E2.iloc[0]
                
            except:
                pass
                    
            #Res['File'] = file
            
            
            ResAll = ResAll.append(Res)
                
             
    '''
    except:
        Res['File'] = file
        Res['Dir'] = directory
        #pass
    '''

    return ResAll

