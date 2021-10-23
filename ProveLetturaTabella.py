# -*- coding: utf-8 -*-
"""
Created on Sun Dec 13 20:17:33 2020

@author: gogliom
"""

#identifico riga e tabella dove c'è 2.700
#prendo tutti i valori di quella riga e quella tabella e prendo riga del dataframe più vicina a quella dove c'era 2.700

import os

import pandas as pd
from itertools import tee, islice, chain

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


def StimaSpesaAnnua(NPICKLE, Value, Tabella):
    
    ####################################################################
    #elaboro il pickle
    ####################################################################
    GGTab = pd.read_pickle(NPICKLE)
    GGTab['conta'] = GGTab.groupby(['Page','RowNum_Header','RowNum','Table']).cumcount()+1 
    
    Value1 = Value
    Value2 = Value.replace(',','')
    Value3 = Value.replace('.','')
    
    GuessOverall = pd.DataFrame(columns=['Value'])
    App = pd.DataFrame(columns=['Value'])
    
    Guess = ""
    
    Rid = GGTab.drop(['Table', 'RowNum', 'Page', 'RowNum_Header', 'conta'], axis=1)
    ListaCol = Rid.columns
    for prevs, col, nexts, nexts_2 in previous_and_next(ListaCol):
    

 
        if col not in ['Table', 'RowNum', 'Page', 'RowNum_Header']:
            #seleziono pagina e tabella dove trovo il valore di riferimento

            TableSel = GGTab[(GGTab[col].str.replace(" ","") == Value1) | 
                             (GGTab[col].str.replace(" ","") == Value2) | 
                             (GGTab[col].str.replace(" ","") == Value3)]
            #se trova un match estrae tutta la tabella 
            if len(TableSel) != 0:
                print('ooo')
                #predno la tabella in base al check che viene fatto nel programma Loop, se viene prima NordOrientale o NordOccidentale
                #(per il Gas) --- Per energia prendo sempre la prima
                    
                TableSel = TableSel.iloc[[Tabella]]

                #ContaNum = TableSel['conta']
                #ContaNum = int(ContaNum[0])
                #estraggo la riga         
                RowTableSel = GGTab.merge(TableSel[['conta']], left_on = ['conta'], right_on = ['conta'], how = 'inner')
                #se trovo valore nella colonna appena successiva
                Guess = RowTableSel[nexts]
                #se non trovo valore nella colonna successiva vado alla riga successiva della stessa tabella:
                if Guess.isnull().all() or Guess.eq("").all():
                    print('aaa')
                    
                    TableSel_2 = GGTab.merge(TableSel[['Page', 'Table', 'RowNum']], left_on = ['Page', 'Table', 'RowNum'], right_on = ['Page','Table','RowNum'], how = 'inner')
                    TableSel_2['ColShift'] = TableSel_2[col].shift(+1)
                    TableSel_2 = TableSel_2[(TableSel_2['ColShift'].str.replace(" ","") == Value1) | 
                                            (TableSel_2['ColShift'].str.replace(" ","") == Value2) |
                                            (TableSel_2['ColShift'].str.replace(" ","") == Value3)]
                    #cerco prima nella stessa colonna della riga successiva
                    Guess = TableSel_2[col]
    
                    if Guess.isnull().all() or Guess.eq("").all():
                        #cerco nella colonna successiva della riga successiva
                        Guess = TableSel_2[nexts] 
    
                        #se ancora nullo, vado a 2 colonne successive (vedi ENI)
                        if Guess.isnull().all() or Guess.eq("").all():
                            Guess = RowTableSel[nexts_2]
                            if Guess.isnull().all() or Guess.eq("").all():
                                #cerco nella colonna successiva della riga successiva
                                Guess = TableSel_2[nexts_2] 
                            else:
                                break
                        else:
                            break
                    else:
                        break
                else:
                    break
                    
    App['Value'] = pd.Series(Guess)        
    App['Value'] = App.apply(lambda row: row.Value.replace(".",""), axis = 1) 
    App['Value'] = App.apply(lambda row: row.Value.replace(",","."), axis = 1) 
    App['Value'] = App.apply(lambda row: row.Value.replace("€",""), axis = 1) 

    GuessOverall = GuessOverall.append(App)
    
    return GuessOverall['Value']
            
                



