# -*- coding: utf-8 -*-
"""
Created on Fri Dec 25 14:28:03 2020

@author: gogliom
"""


# -*- coding: utf-8 -*-
"""
Created on Sun Dec 13 20:17:33 2020

@author: gogliom
"""

#identifico riga e tabella dove c'è 2.700
#prendo tutti i valori di quella riga e quella tabella e prendo riga del dataframe più vicina a quella dove c'era 2.700

import os
#os.chdir("D:\Altro\RPA\Energy\IREN\TEST CTE\DocumentAI")

#directory dove salvo i pickle da google cloud
#OutDir = "D:\Altro\RPA\Energy\IREN\TEST CTE\DocumentAI\Output"

import pandas as pd
from itertools import tee, islice, chain
import re 

#funzione per identificare elemento precedente e successivo in ciclo loop 
def previous_and_next(some_iterable):
    prevs, items, nexts , nexts_2 = tee(some_iterable, 4)
    prevs = chain([None], prevs)
    nexts = chain(islice(nexts, 1, None), [None])
    nexts_2 = chain(islice(nexts_2, 2, None), [None], [None])
    return zip(prevs, items, nexts, nexts_2) 


#funzione che carica pdf su google storage per eventuale elaborazione google api documentai
def upload_to_bucket(blob_name, path_to_file, bucket_name, cred_key):
    """ Upload data to a bucket"""

    # Explicitly use service account credentials by specifying the private key
    # file.
    storage_client = storage.Client.from_service_account_json(
        cred_key)

    #print(buckets = list(storage_client.list_buckets())

    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(path_to_file)

    #returns a public url
    return blob.public_url


def StimaSpesaFasce(NPICKLE, Value):



    ####################################################################
    #elaboro il pickle
    ####################################################################
    GGTab = pd.read_pickle(NPICKLE)
    GGTab['conta'] = GGTab.groupby(['Page','RowNum_Header','RowNum','Table']).cumcount()+1 
    
    
    
    regexNum1 = r'0,\d+'
    #regexNum2 = r'0\.\d+'
        
    regexNum = [regexNum1]  #, regexNum2]
    
    regexNum = re.compile('|'.join(regexNum))
    

    Value1 = Value
    Value2 = Value.replace('0','O')
    #Value3 = Value.replace('.','')
    
    GuessOverall = pd.DataFrame(columns=['Value'])
    App = pd.DataFrame(columns=['Value'])
    
    Guess = ""
    
    Rid = GGTab.drop(['Table', 'RowNum', 'Page', 'RowNum_Header', 'conta'], axis=1)
    ListaCol = Rid.columns
    
    for prevs, col, nexts, nexts_2 in previous_and_next(ListaCol):
   
        if col not in ['Table', 'RowNum', 'Page', 'RowNum_Header', 'conta']:
            try:

                #seleziono pagina e tabella dove trovo il valore di riferimento
                TableSel = GGTab[(GGTab[col].str.contains(Value1, na = False)) | (GGTab[col].str.contains(Value2, na = False))]
                #se trova un match estrae tutta la tabella 
                if len(TableSel) != 0:
                    print('ooo')
                    #se ci sono più righe per ora prendo la prima 
                    #TableSel = (TableSel.head(1))
                    
                    #estraggo la riga         
                    RowTableSel = GGTab.merge(TableSel[['conta']], left_on = ['conta'], right_on = ['conta'], how = 'inner')
                    #se trovo valore nella stessa colonna
                    RowTableSel['Guess'] = RowTableSel[col].str.findall(regexNum)
                    RowTableSel['Guess'] = RowTableSel['Guess'].str[0] #se ne ha trovati più di uno, prendo il primo
                    Guess = RowTableSel['Guess']
                      
                    
                    if Guess.isnull().all() or Guess.eq("").all() or len(Guess.iloc[0]) == 0:
                        print('zz')
                        #se trovo valore nella colonna appena successiva
                        RowTableSel['Guess'] = RowTableSel[nexts].str.findall(regexNum)
                        Guess = RowTableSel['Guess']
                    
                        #se non trovo valore nella colonna successiva vado alla riga successiva della stessa tabella:
                        if Guess.isnull().all() or Guess.eq("").all() or len(Guess.iloc[0]) == 0:
                            print('aaa')
                            
                            TableSel_2 = GGTab.merge(TableSel[['Page', 'Table', 'RowNum']], left_on = ['Page', 'Table', 'RowNum'], right_on = ['Page','Table','RowNum'], how = 'inner')
                            TableSel_2['ColShift'] = TableSel_2[col].shift(+1)
                            TableSel_2 = TableSel_2[(TableSel_2['ColShift'].str.contains(Value1, na = False)) | (TableSel_2['ColShift'].str.contains(Value2, na = False))]
                            #cerco prima nella stessa colonna della riga successiva
                            TableSel_2['Guess'] = TableSel_2[col].str.findall(regexNum)
                            TableSel_2['Guess'] = TableSel_2['Guess'].str[0] #se ne ha trovati più di uno, prendo il primo
                            Guess = TableSel_2['Guess']
                            TableSel_2 = TableSel_2.drop(['Guess'], axis = 1)
                            
            
                            if Guess.isnull().all() or Guess.eq("").all() or len(Guess.iloc[0]) == 0:
                                print('uu')
                                #cerco nella colonna successiva della riga successiva
                                TableSel_2['Guess'] = (TableSel_2[nexts].str.findall(regexNum))
                                TableSel_2['Guess'] = TableSel_2['Guess'].str[0] #se ne ha trovati più di uno, prendo il primo
                                Guess = TableSel_2['Guess'] 
                                
                                #se ancora nullo, vado 2 righe sotto nella colonna nexts (vedi engie)
                                if Guess.isnull().all() or Guess.eq("").all() or len(Guess.iloc[0]) == 0:
                                    TableSel_3 = GGTab.merge(TableSel[['Page', 'Table', 'RowNum']], left_on = ['Page', 'Table', 'RowNum'], right_on = ['Page','Table','RowNum'], how = 'inner')
                                    TableSel_3['ColShift'] = TableSel_3[col].shift(+2)
                                    TableSel_3 = TableSel_3[(TableSel_3['ColShift'].str.contains(Value1, na = False)) | (TableSel_3['ColShift'].str.contains(Value2, na = False))]
                                    #cerco prima nella stessa colonna di due righe successiva
                                    TableSel_3['Guess'] = TableSel_3[col].str.findall(regexNum)
                                    TableSel_3['Guess'] = TableSel_3['Guess'].str[0] #se ne ha trovati più di uno, prendo il primo
                                    Guess = TableSel_3['Guess']
                                    TableSel_3 = TableSel_3.drop(['Guess'], axis = 1)
                      
                                    if Guess.isnull().all() or Guess.eq("").all() or len(Guess.iloc[0]) == 0:
                                        #cerco nella colonna successiva di due righe successiva
                                        TableSel_3['Guess'] = (TableSel_3[nexts].str.findall(regexNum))
                                        TableSel_3['Guess'] = TableSel_3['Guess'].str[0] #se ne ha trovati più di uno, prendo il primo
                                        Guess = TableSel_3['Guess']                                
            
                                        #se ancora nullo, vado a 2 colonne successive (vedi ENI)
                                        if Guess.isnull().all() or Guess.eq("").all() or len(Guess.iloc[0]) == 0:
                                            RowTableSel['Guess'] = RowTableSel[nexts_2].str.findall(regexNum)
                                            Guess = RowTableSel['Guess']
                                            if Guess.isnull().all() or Guess.eq("").all() or len(Guess.iloc[0]) == 0:
                                                #cerco nella colonna successiva della riga successiva
                                                TableSel_2['Guess'] = TableSel_2[nexts_2].str.findall(regexNum)
                                                TableSel_2['Guess'] = TableSel_2['Guess'].str[0] #se ne ha trovati più di uno, prendo il primo
                                                Guess = TableSel_2['Guess'] 
                                            
                            
                    App['Value'] = pd.Series(Guess)        
                    GuessOverall = GuessOverall.append(App)
                    
            except:
                pass
    
    return GuessOverall['Value']
                            

