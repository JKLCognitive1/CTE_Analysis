
import pandas as pd
import re
import numpy as np
from operator import itemgetter
import fitz
import json
import os
from shutil import copyfile


def Durata(Doc):
    PossiblePrice = []
    Base = []

    # le inserisco come regular expression perchè mettendo . come any character (spezi,"E", a capo..)
    r1 = 'DURATA'
    r2 = 'VALIDIT'
    r3 = 'RINNOV'
    r4 = 'PER.{,5}MESI'
    r5 = 'PER.{,5}ANN'

    regex = [r1, r2, r3, r4, r5]

    regex = re.compile('|'.join(regex))

    Base = [m.start() for m in regex.finditer(Doc)]
    Base = pd.DataFrame(Base, columns=['PositionBase'])

    # prendo numeri interi (mesi o anni)
    d1 = r'\s\d{1,2}\s'

    d = [d1]  # le regex potrebbero essere sovrapposte,metto prima
    # le più lunghe così se prende quelle si ferma a quella  --> SI DOVREBBE GESTIRE MEGLIO
    regexNum = re.compile('|'.join(d))
    NumberPos = [m.start() for m in regexNum.finditer(Doc)]
    NumberValue = regexNum.findall(Doc)
    NumberTuples = list(zip(NumberValue, NumberPos))

    PossiblePrice = pd.DataFrame(NumberTuples, columns=['Price', 'Position'])
    PossiblePrice['Price'] = PossiblePrice['Price'].str.extract('(\d+)').astype(int)
    PossiblePrice = PossiblePrice[PossiblePrice['Price'].isin(['1', '2', '3', '4', '6', '12', '18', '24', '36'])]

    Base['key'] = 0
    PossiblePrice['key'] = 0

    Durata = Base.merge(PossiblePrice, how='outer')
    Durata['dist'] = Durata.apply(lambda row: row.Position - row.PositionBase, axis=1)
    # FILTRO PER LE DISTANZE POSITIVE (IL NUMERO VIENE DOPO LA PAROLA, OPPURE NEGATIVE MOLTO PICCOLE DOVE QUINDI LA BASE VIENE IMMEDIATAMENTE DOPO )
    Durata = Durata[(Durata['dist'] > - 30) & (Durata['dist'] < 300)]

    # verifico se nei 40 caratteri prima o dopo c'è riferimento a mese o anno
    dur1_m = r'\bMESE\b'
    dur2_m = r'\bMESI\b'
    dur_m = [dur1_m, dur2_m]
    regexDur_m = re.compile('|'.join(dur_m))

    dur1_a = r'\bANNO\b'
    dur2_a = r'\bANNI\b'
    dur_a = [dur1_a, dur2_a]
    regexDur_a = re.compile('|'.join(dur_a))

    Durata['Intorno'] = Durata.apply(lambda row: Doc[row.Position - 40:row.Position + 40], axis=1)
    Durata['Mese'] = np.where(Durata['Intorno'].str.contains(regexDur_m), 1, 0)
    Durata['Anno'] = np.where(Durata['Intorno'].str.contains(regexDur_a), 1, 0)

    # filtro per le durata possibili (6, 12, 18, 24 mesi -- 1, 2 anni)
    Dm = Durata[(Durata['Mese'] == 1) & (Durata['Price'].isin(['6', '12', '18', '24']))]
    Da = Durata[(Durata['Anno'] == 1) & (Durata['Price'].isin(['1', '2']))]
    Durata = Dm.append(Da)

    Durata = Durata.nsmallest(1, 'dist')

    if Durata['Anno'].all() == 1:
        Durata['Price'] = Durata['Price'].apply(str) + ' anno'
    elif Durata['Mese'].all() == 1:
        Durata['Price'] = Durata['Price'].apply(str) + ' mesi'
    else:
        Durata['Price'] = Durata['Price'].apply(str) + ' anno'

    # print(Prezzo)
    return Durata['Price']



import regex as re  # ATTENZIONE! DEVO IMPORTARE 3RD PARTY REGEX MODULO PERCHè QUESTO SUPPORTA I "NEGATIVE LOOKAHEAD
                    # DI LUNGHEZZA VARIABILE --> DEVO PRENDERE "VERDE" CHE NON SIA PRECEDUTO DA NUMERO O DA N° E QUESTO
                    # E' UN NEGATIVE LOOKAHEAD DI LUNGHEZZA VARIABILE CHE VA IN ERRORE SU MODULO STANDARD DI RE
                    #  CFR (https://www.reddit.com/r/learnpython/comments/d5g4ow/regex_match_pattern_not_preceded_by_either_of_two/)

def PrezzoComponenteCommVendita(Doc):
    PossiblePrice_CV = []
    Base_CV = []

    # le inserisco come regular expression perchè mettendo . come any character (spezi,"E", a capo..)
    r1 = 'PREZZO.{0,10}COMMERCIALIZZAZIONE.{0,10}VENDITA'
    r2 = 'COSTI.{0,10}COMMERCIALIZZAZIONE'
    r3 = 'PCV'
    r5 = 'COMMERCIALIZZAZIONE.{0,10}VENDITA'
    r6 = 'CORRISPETTIVO.{0,10}COMMERCIALIZZAZIONE'
    r7 = 'COMPONENTE.{0,10}COMMERCIALIZZAZIONE'

    # introdotte per il gas
    r4 = '(?<!MATERIA PRIMA.{1,80})QVD'

    regex_CV = [r1, r2, r3, r4, r5, r6, r7]

    regex_CV = re.compile('|'.join(regex_CV))

    Base_CV = [m.start() for m in regex_CV.finditer(Doc)]
    Base_CV = pd.DataFrame(Base_CV, columns=['PositionBase'])

    # r1 = '-?\d*,?\d+\s'
    # r2 = '-?\d*\.?\d+\s'

    r1 = '(?<!ARTICOLO.{0,10})-?\s+\d*,?\d+\s(?!.{0,5}MESI)'
    # r2 = '-?\s\d*\.?\d+\s'
    r3 = '(?<!ARTICOLO.{0,10})-?\s+\d*,?\d+€(?!.{0,5}MESI)'
    # r4 = '-?\s\d*\.?\d+€'

    regex_Num = [r1, r3]

    regexNum_CV = re.compile('|'.join(regex_Num))

    # prendo i numeri eventualmente decimali
    NumberPos_CV = [m.start() for m in regexNum_CV.finditer(Doc)]
    NumberValue_CV = regexNum_CV.findall(Doc)
    NumberTuples_CV = list(zip(NumberValue_CV, NumberPos_CV))

    PossiblePrice_CV = pd.DataFrame(NumberTuples_CV, columns=['Price', 'Position'])
    # converto in numero
    PossiblePrice_CV['Price_NUM'] = PossiblePrice_CV.apply(lambda row: row.Price.replace(",", "."), axis=1)
    PossiblePrice_CV['Price_NUM'] = PossiblePrice_CV.apply(lambda row: row.Price_NUM.replace(" ", ""), axis=1)
    PossiblePrice_CV['Price_NUM'] = PossiblePrice_CV.apply(lambda row: row.Price_NUM.replace("€", ""), axis=1)
    PossiblePrice_CV['Price_NUM'] = PossiblePrice_CV.apply(lambda row: float(row.Price_NUM), axis=1)

    # filtro numeri > 10 e positivi
    PossiblePrice_CV = PossiblePrice_CV[(PossiblePrice_CV['Price_NUM'] > 5) & (PossiblePrice_CV['Price_NUM'] < 200)]

    # verifico se nei 40 caratteri prima o dopo c'è riferimento a mese o anno
    PossiblePrice_CV['Intorno'] = PossiblePrice_CV.apply(lambda row: Doc[row.Position - 40:row.Position + 40], axis=1)
    PossiblePrice_CV['Mese'] = np.where(PossiblePrice_CV['Intorno'].str.contains('MESE'), 1,
                                        np.where(PossiblePrice_CV['Intorno'].str.contains('MENSIL'), 1,
                                                 0))
    PossiblePrice_CV['Anno'] = np.where(PossiblePrice_CV['Intorno'].str.contains('ANNO'), 1,
                                        np.where(PossiblePrice_CV['Intorno'].str.contains('ANNUAL'), 1,
                                                 0))
    Base_CV['key'] = 0
    PossiblePrice_CV['key'] = 0

    Prezzo_CV = Base_CV.merge(PossiblePrice_CV, how='outer')
    Prezzo_CV['dist'] = Prezzo_CV.apply(lambda row: row.Position - row.PositionBase, axis=1)
    # FILTRO PER LE DISTANZE POSITIVE (IL NUMERO VIENE DOPO LA PAROLA, OPPURE NEGATIVE MOLTO PICCOLE DOVE QUINDI LA BASE VIENE IMMEDIATAMENTE DOPO )
    Prezzo_CV = Prezzo_CV[(Prezzo_CV['dist'] > - 35) & (Prezzo_CV['dist'] < 200)]

    Prezzo_CV = Prezzo_CV.nsmallest(1, 'dist')
    # trovo sia mese che anno, filtro in base a valore
    if Prezzo_CV['Mese'].iloc[0] == 1 and Prezzo_CV['Anno'].iloc[0] == 1:
        if Prezzo_CV['Price_NUM'].iloc[0] > 15:
            Prezzo_CV['Price'] = Prezzo_CV['Price'] + " anno"
        else:
            Prezzo_CV['Price'] = Prezzo_CV['Price'] + " mese"
            # trovo solo mese
    elif Prezzo_CV['Mese'].iloc[0] == 1:
        Prezzo_CV['Price'] = Prezzo_CV['Price'] + " mese"

        # trovo solo anno
    elif Prezzo_CV['Anno'].iloc[0] == 1:
        Prezzo_CV['Price'] = Prezzo_CV['Price'] + " anno"

    # non trovo niente
    else:
        if Prezzo_CV['Price_NUM'].iloc[0] > 15:
            Prezzo_CV['Price'] = Prezzo_CV['Price'] + " anno"
        else:
            Prezzo_CV['Price'] = Prezzo_CV['Price'] + " mese"

    return Prezzo_CV['Price']


def PrezzoComponenteDispacciamento(Doc):
    PossiblePrice = []
    Base = []

    # le inserisco come regular expression perchè mettendo . come any character (spezi,"E", a capo..)
    r1 = 'PREZZO.+DISPACCIA'
    r2 = 'COSTI.+DISPACCIA'
    r3 = 'COMPONEN.+DISPACCIA'

    regex = [r1, r2, r3]

    regex = re.compile('|'.join(regex))

    Base = [m.start() for m in regex.finditer(Doc)]
    Base = pd.DataFrame(Base, columns=['PositionBase'])

    r1 = '-?\s\d*,?\d+\s'
    r2 = '-?\s\d*\.?\d+\s'
    r3 = '-?\s\d*,?\d+€'
    r4 = '-?\s\d*\.?\d+€'

    # r1 = '-?\d*,?\d+'
    # r2 = '-?\d*.?\d+'

    regex_Num = [r1, r2, r3, r4]

    regexNum_DIS = re.compile('|'.join(regex_Num))

    NumberPos = [m.start() for m in regexNum_DIS.finditer(Doc)]
    NumberValue = regexNum_DIS.findall(Doc)
    NumberTuples = list(zip(NumberValue, NumberPos))

    PossiblePrice = pd.DataFrame(NumberTuples, columns=['Price', 'Position'])
    # converto in numero

    PossiblePrice['Price_NUM'] = PossiblePrice.apply(lambda row: row.Price.replace(",", "."), axis=1)
    PossiblePrice['Price_NUM'] = PossiblePrice.apply(lambda row: row.Price_NUM.replace(" ", ""), axis=1)
    PossiblePrice['Price_NUM'] = PossiblePrice.apply(lambda row: row.Price_NUM.replace("€", ""), axis=1)
    PossiblePrice['Price_NUM'] = PossiblePrice.apply(lambda row: float(row.Price_NUM), axis=1)

    # filtro numeri > - 30 (possono essere negativi..)
    PossiblePrice = PossiblePrice[(PossiblePrice['Price_NUM'] > -30) & (PossiblePrice['Price_NUM'] < 100)]

    Base['key'] = 0
    PossiblePrice['key'] = 0

    Prezzo = Base.merge(PossiblePrice, how='outer')
    Prezzo['dist'] = Prezzo.apply(lambda row: row.Position - row.PositionBase, axis=1)
    # FILTRO PER LE DISTANZE POSITIVE (IL NUMERO VIENE DOPO LA PAROLA, OPPURE NEGATIVE MOLTO PICCOLE DOVE QUINDI LA BASE VIENE IMMEDIATAMENTE DOPO )
    Prezzo = Prezzo[Prezzo['dist'] > - 10]

    Prezzo = Prezzo.nsmallest(1, 'dist')

    print(Prezzo)
    return Prezzo['Price']


import re

def Scadenza(Doc):
    PossiblePrice = []
    Base = []

    # le inserisco come regular expression perchè mettendo . come any character (spezi,"E", a capo..)
    r1 = 'CONDIZIONI.{,40}VALID'
    r2 = 'ADESION.{,10}ENTRO'
    r3 = 'ADESION.{,10}FINO'
    r4 = 'VALID.{,25}FINO'
    r5 = 'SOTTOSCRIVIBIL.{,30}'
    r6 = 'VALID.{,30}DA.{,15}A'
    r7 = 'ENTRO IL'
    # r8 = 'DAL\s.{,15}AL\s'
    r8 = 'SCADENZA'
    r9 = 'VALID.{,25}ENTRO'
    r10 = 'VALIDIT.{,10}OFFERTA'

    regex = [r1, r2, r3, r4, r5, r6, r7, r8, r9, r10]

    regex = re.compile('|'.join(regex))

    Base = [m.start() for m in regex.finditer(Doc)]
    Base = pd.DataFrame(Base, columns=['PositionBase'])

    # prendo possibili date
    d1 = '\d\d\\\d\d\\\d{2,4}'  # 10\10\20 oppure 10\10\2020
    d2 = '\d\d/\d\d/\d{2,4}'  # 10/10/20 oppure 10/10/2020
    d3 = '\d\d\\\d\d\\\d{2,4}.{0,5}AL.{0,5}\d\d\\\d\d\\\d{2,4}'  # 10\10\20 AL 20\20\20 (con anni anche a 4)
    d4 = '\d\d/\d\d/\d{2,4}.{0,5}AL.{0,5}\d\d/\d\d/\d{2,4}'  # 10/10/20 AL 20/20/20 (con anni anche a 4)

    d = [d4, d3, d1, d2]  # le regex potrebbero essere sovrapposte,metto prima
    # le più lunghe così se prende quelle si ferma a quella  --> SI DOVREBBE GESTIRE MEGLIO
    regexNum = re.compile('|'.join(d))
    NumberPos = [m.start() for m in regexNum.finditer(Doc)]
    NumberValue = regexNum.findall(Doc)
    NumberTuples = list(zip(NumberValue, NumberPos))

    PossiblePrice = pd.DataFrame(NumberTuples, columns=['Price', 'Position'])

    Base['key'] = 0
    PossiblePrice['key'] = 0

    Prezzo = Base.merge(PossiblePrice, how='outer')

    import datetime
    try:
        Prezzo['Date'] = Prezzo.apply(lambda row: datetime.datetime.strptime(row.Price, '%d/%m/%Y'), axis=1)
        Prezzo = Prezzo[(Prezzo['Date'] > '01/11/2020') | (Prezzo['Date'].isnull())]
    except:
        pass

    Prezzo['dist'] = Prezzo.apply(lambda row: row.Position - row.PositionBase, axis=1)
    # FILTRO PER LE DISTANZE POSITIVE (IL NUMERO VIENE DOPO LA PAROLA, OPPURE NEGATIVE MOLTO PICCOLE DOVE QUINDI LA BASE VIENE IMMEDIATAMENTE DOPO )
    Prezzo = Prezzo[Prezzo['dist'] > 0]

    Prezzo.sort_values(['dist', 'Price'], ascending=[True, False])
    Prezzo = Prezzo.nsmallest(1, 'dist',
                              keep='last')  # in base al sort di prima, in caso di pari merito su distanza prendo la data più avanti

    ################################
    #####PER ENI, LA SCADENZA E' IN ALTO A DX, MA VIENE LETTA NEL PDF AL CONTRARIO E QUINDI POSSO (DEVO) ACCETTARE DISTANZE NEGATIVE
    ################################
    if len(Prezzo) == 0:

        try:
            d4 = 'DAL \d\d/\d\d/\d{2,4}.AL.\d\d/\d\d/\d{2,4}.{0,3}CONDIZIONI.{0,20}VALIDE'  # 10/10/20 AL 20/20/20 (con anni anche a 4)

            regexNum = re.compile(d4)
            NumberPos = [m.start() for m in regexNum.finditer(Doc)]
            NumberValue = regexNum.findall(Doc)[0]
            st = NumberValue.find(' AL') + 3
            se = st + 11
            NumberValue = NumberValue[st:se]
            Prezzo = Prezzo.append({'Price': NumberValue}, ignore_index=True)
        # sempre per eni nelle offerte dual lato gas non viene presa la parte in alto --> lo prendo da codice offerta ;
        except:
            d4 = '_\d{8,8}_\d{8,8}'
            regexNum = re.compile(d4)
            NumberPos = [m.start() for m in regexNum.finditer(Doc)]
            NumberValue = regexNum.findall(Doc)[0]
            NumberValue = NumberValue[10:18]
            NumberValue_2 = NumberValue[6:8] + "/" + NumberValue[4:6] + "/" + NumberValue[0:4]
            Prezzo = Prezzo.append({'Price': NumberValue_2}, ignore_index=True)

    return Prezzo['Price']


def PrezzoComponenteEnergia(Doc):
    PossiblePrice = []
    Base = []

    # le inserisco come regular expression perchè non so quanti spazi ci sono e se magari c'è una new line (\s+)
    r1 = 'CORRISPETTIVO.{0,10}LUCE.{0,10}'
    r2 = 'COMPONENTE.{0,10}PREZZO.{0,10}ENERGIA'
    r3 = 'PREZZO.{0,10}LUCE'
    r4 = 'PREZZO.{0,10}COMPONENTE.{0,10}ENERGIA'
    r5 = 'COMPONENTE.{0,10}ENERGIA'
    r6 = 'MONORARI'
    r7 = 'MONORARIO'
    r8 = 'F0'
    r9 = 'PREZZO.{0,10}ENERGIA'
    r10 = 'SPESA.{0,10}MATERIA.{0,10}ENERGIA'

    regex = [r1, r2, r3, r4, r5, r6, r7, r8, r9, r10]

    regex = re.compile('|'.join(regex))

    Base = [m.start() for m in regex.finditer(Doc)]
    Base = pd.DataFrame(Base, columns=['PositionBase'])

    # prendo i numeri positivi
    # regexNum1 = r'-?\d*\,.?\d+'
    # regexNum2 = r'-?\d*\..?\d+'

    regexNum1 = r'\d+\,?\d+'
    regexNum2 = r'\d+\.?\d+'

    regexNum = [regexNum1, regexNum2]

    regexNum = re.compile('|'.join(regexNum))

    NumberPos = [m.start() for m in regexNum.finditer(Doc)]
    NumberValue = regexNum.findall(Doc)
    NumberTuples = list(zip(NumberValue, NumberPos))

    PossiblePrice = pd.DataFrame(NumberTuples, columns=['Price', 'Position'])
    # converto in numero
    PossiblePrice['Price_NUM'] = PossiblePrice.apply(lambda row: row.Price.replace(",", "."), axis=1)
    PossiblePrice['Price_NUM'] = PossiblePrice.apply(lambda row: row.Price_NUM.replace(" ", ""), axis=1)
    PossiblePrice['Price_NUM'] = PossiblePrice.apply(lambda row: float(row.Price_NUM), axis=1)

    # filtro numeri < 1 e positivi
    PossiblePrice = PossiblePrice[(PossiblePrice['Price_NUM'] > 0.02) & (PossiblePrice['Price_NUM'] < 0.1)]

    Base['key'] = 0
    PossiblePrice['key'] = 0

    Prezzo = Base.merge(PossiblePrice, how='outer')
    Prezzo['dist'] = Prezzo.apply(lambda row: row.Position - row.PositionBase, axis=1)
    # FILTRO PER LE DISTANZE POSITIVE (IL NUMERO VIENE DOPO LA PAROLA, OPPURE NEGATIVE MOLTO PICCOLE DOVE QUINDI LA BASE VIENE IMMEDIATAMENTE DOPO )
    Prezzo = Prezzo[Prezzo['dist'] > - 30]

    Prezzo = Prezzo.nsmallest(1, 'dist')

    return Prezzo['Price_NUM']


import regex as re  # ATTENZIONE! DEVO IMPORTARE 3RD PARTY REGEX MODULO PERCHè QUESTO SUPPORTA I "NEGATIVE LOOKAHEAD
                    # DI LUNGHEZZA VARIABILE --> DEVO PRENDERE "VERDE" CHE NON SIA PRECEDUTO DA NUMERO O DA N° E QUESTO
                    # E' UN NEGATIVE LOOKAHEAD DI LUNGHEZZA VARIABILE CHE VA IN ERRORE SU MODULO STANDARD DI RE
                    # CFR (https://www.reddit.com/r/learnpython/comments/d5g4ow/regex_match_pattern_not_preceded_by_either_of_two/)

def TipoPrezzo(Doc):
    # VERIFICO VARIABILITA' PREZZO
    v1 = r'\bPUN\b'
    # v2 = r'^(?=.*\bPREZZO\b)(?=.*\bUNICO\b)(?=.*\bNAZIONALE\b).*$'
    v2 = r'^(?=.*\bPREZZO\b).{0,30}UNICO.{0,30}NAZIONALE'
    v3 = r'^(?=.*\bINGROSSO\b)(?=.*\bBORSA\b)(?=.*\bELETTRICA\b).*$'
    v4 = r'^(?=.*\bFORMULA\b)(?=.*\bPREZZO\b)(?=.*\bENERGIA\b).*$'
    v5 = r'PREZZO.{0,10}ENERGIA.{0,30}TIV'

    regexVar = [v1, v2, v3, v4, v5]
    regexVar = re.compile('|'.join(regexVar))

    PriceExplanation = []
    PriceExplanation = [m.start() for m in regexVar.finditer(Doc)]

    '''
    for i in Doc.split('\n'):
        if regexVar.match(i):
            PriceExplanation.append(i)
    '''
    #  VERIFICO SE SI PARLA DI COME VIENE CALCOLATO IL PREZZO DELLA COMPONENTE ENERGIA

    f1 = r'PREZZ.{1,30}ENERGIA.{1,50}FISS'
    f2 = r'PREZZ.{1,30}ENERGIA.{1,50}INVARIABIL'
    # f3 = r'PREZZ.{1,30}FISSO'
    f3 = r'(?<!PLACET.{1,30})PREZZO.{1,30}FISSO'

    regexFix = [f1, f2, f3]

    regexFix = re.compile('|'.join(regexFix))

    PriceFix = []
    PriceFix = [m.start() for m in regexFix.finditer(Doc)]

    Prezzo = pd.DataFrame(columns=['TipoPrezzo'])

    if len(PriceExplanation) == 0 or len(PriceFix) > 0:
        Prezzo.at[0, 'TipoPrezzo'] = 'Fisso'
    else:
        Prezzo.at[0, 'TipoPrezzo'] = 'Variabile'

    return Prezzo['TipoPrezzo']

import re


def PrezzoComponenteGAS(Doc):
    PossiblePrice = []
    Base = []

    # le inserisco come regular expression perchè non so quanti spazi ci sono e se magari c'è una new line (\s+)
    r1 = 'CORRISPETTIVO\s+GAS'
    r2 = 'COMPONENTE\s+PREZZO\s+ENERGIA'
    r3 = 'PREZZO\s+GAS'
    r4 = 'PREZZO.{0,10}COMPONENTE.{0,10}ENERGIA'
    r5 = 'COMPONENTE\s+GAS'
    r6 = 'PREZZO.{0,10}GAS'
    r7 = 'CORRISPETTIVO\s+PREZZO\s+FISSO'
    r8 = 'SPESA.{0,10}MATERIA.{0,10}GAS.{0,10}NATURALE'
    r9 = 'PREZZO.{0,20}MATERIA.{0,20}PRIMA'
    r10 = 'COSTI.{0,40}MATERIA.{0,20}PRIMA'
    r11 = 'PREZZO.{0,5}NETTO'
    regex = [r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11]

    regex = re.compile('|'.join(regex))

    Base = [m.start() for m in regex.finditer(Doc)]
    Base = pd.DataFrame(Base, columns=['PositionBase'])

    regexNum1 = r'\d+\,.?\d+'
    regexNum2 = r'\d+\..?\d+'

    regexNum = [regexNum1, regexNum2]

    regexNum = re.compile('|'.join(regexNum))

    NumberPos = [m.start() for m in regexNum.finditer(Doc)]
    NumberValue = regexNum.findall(Doc)
    NumberTuples = list(zip(NumberValue, NumberPos))

    PossiblePrice = pd.DataFrame(NumberTuples, columns=['Price', 'Position'])
    # converto in numero
    PossiblePrice['Price_NUM'] = PossiblePrice.apply(lambda row: row.Price.replace(",", "."), axis=1)
    PossiblePrice['Price_NUM'] = PossiblePrice.apply(lambda row: row.Price_NUM.replace(" ", ""), axis=1)
    PossiblePrice['Price_NUM'] = PossiblePrice.apply(lambda row: float(row.Price_NUM), axis=1)

    # filtro numeri < 1 e positivi
    PossiblePrice = PossiblePrice[(PossiblePrice['Price_NUM'] > 0.04) & (PossiblePrice['Price_NUM'] < 0.5)]

    Base['key'] = 0
    PossiblePrice['key'] = 0

    Prezzo = Base.merge(PossiblePrice, how='outer')
    Prezzo['dist'] = Prezzo.apply(lambda row: row.Position - row.PositionBase, axis=1)
    # FILTRO PER LE DISTANZE POSITIVE (IL NUMERO VIENE DOPO LA PAROLA, OPPURE NEGATIVE MOLTO PICCOLE DOVE QUINDI LA BASE VIENE IMMEDIATAMENTE DOPO )
    Prezzo = Prezzo[Prezzo['dist'] > - 25]

    Prezzo = Prezzo.nsmallest(1, 'dist')

    return Prezzo['Price_NUM']


import regex as re  # ATTENZIONE! DEVO IMPORTARE 3RD PARTY REGEX MODULO PERCHè QUESTO SUPPORTA I "NEGATIVE LOOKAHEAD
                    # DI LUNGHEZZA VARIABILE --> DEVO PRENDERE "VERDE" CHE NON SIA PRECEDUTO DA NUMERO O DA N° E QUESTO
                    # E' UN NEGATIVE LOOKAHEAD DI LUNGHEZZA VARIABILE CHE VA IN ERRORE SU MODULO STANDARD DI RE
                    # CFR (https://www.reddit.com/r/learnpython/comments/d5g4ow/regex_match_pattern_not_preceded_by_either_of_two/)


def TipoPrezzo_GAS(Doc):
    # VERIFICO VARIABILITA' PREZZO
    v1 = r'\bPSV\b'
    v2 = r'^(?=.*\bPREZZO\b)(?=.*\bACQUISTO\b)(?=.*\bGAS\b).*$'
    # v3 = r'^(?=.*\bMERCATO\b)(?=.*\bINGROSSO\b).*$'
    # v4=  r'^(?=.*\bMERCATI\b)(?=.*\bINGROSSO\b).*$'
    v5 = r'\bPFOR\b'
    v6 = r'\bOTC\b'

    regexVar = [v1, v2, v5, v6]

    regexVar = re.compile('|'.join(regexVar))

    PriceExplanation = []
    PriceExplanation = [m.start() for m in regexVar.finditer(Doc)]

    #  VERIFICO SE SI PARLA DI COME VIENE CALCOLATO IL PREZZO DELLA COMPONENTE ENERGIA

    f1 = r'(?<!PLACET.{1,30})PREZZ.{1,30}GAS.{1,50}FISS'
    f2 = r'(?<!PLACET.{1,30})PREZZ.{1,30}GAS.{1,50}INVARIABIL'
    f3 = r'(?<!PLACET.{1,30})PREZZO.{1,30}FISSO'
    f4 = r'PREZZO INVARIABILE'
    f5 = r'(?<!SPREAD.{1,130}|PARAMETRO.{1,20})FISS.{1,10}INVARIABIL'

    regexFix = [f1, f2, f3, f4, f5]

    regexFix = re.compile('|'.join(regexFix))

    PriceFix = []
    PriceFix = [m.start() for m in regexFix.finditer(Doc)]

    Prezzo = pd.DataFrame(columns=['TipoPrezzo'])

    if len(PriceExplanation) == 0 or len(PriceFix) > 0:
        Prezzo.at[0, 'TipoPrezzo'] = 'Fisso'
    else:
        Prezzo.at[0, 'TipoPrezzo'] = 'Variabile'

    return Prezzo['TipoPrezzo']


def fonts(doc, granularity=False):
    """Extracts fonts and their usage in PDF documents.
    :param doc: PDF document to iterate through
    :type doc: <class 'fitz.fitz.Document'>
    :param granularity: also use 'font', 'flags' and 'color' to discriminate text
    :type granularity: bool
    :rtype: [(font_size, count), (font_size, count}], dict
    :return: most used fonts sorted by count, font style information
    """
    styles = {}
    font_counts = {}

    for page in doc:
        blocks = page.getText("dict")["blocks"]
        for b in blocks:  # iterate through the text blocks
            if b['type'] == 0:  # block contains text
                for l in b["lines"]:  # iterate through the text lines
                    for s in l["spans"]:  # iterate through the text spans
                        if granularity:
                            identifier = "{0}_{1}_{2}_{3}".format(s['size'], s['flags'], s['font'], s['color'])
                            styles[identifier] = {'size': s['size'], 'flags': s['flags'], 'font': s['font'],
                                                  'color': s['color']}
                        else:
                            identifier = "{0}".format(s['size'])
                            styles[identifier] = {'size': s['size'], 'font': s['font']}

                        font_counts[identifier] = font_counts.get(identifier, 0) + 1  # count the fonts usage

    font_counts = sorted(font_counts.items(), key=itemgetter(1), reverse=True)

    if len(font_counts) < 1:
        raise ValueError("Zero discriminating fonts found!")

    return font_counts, styles


def headers_para(doc, size_tag):
    """Scrapes headers & paragraphs from PDF and return texts with element tags.
    :param doc: PDF document to iterate through
    :type doc: <class 'fitz.fitz.Document'>
    :param size_tag: textual element tags for each size
    :type size_tag: dict
    :rtype: list
    :return: texts with pre-prended element tags
    """
    header_para = []  # list with headers and paragraphs
    first = True  # boolean operator for first header
    previous_s = {}  # previous span

    for page in doc:
        blocks = page.getText("dict")["blocks"]
        for b in blocks:  # iterate through the text blocks
            if b['type'] == 0:  # this block contains text

                # REMEMBER: multiple fonts and sizes are possible IN one block

                block_string = ""  # text found in block
                for l in b["lines"]:  # iterate through the text lines
                    for s in l["spans"]:  # iterate through the text spans
                        if s['text'].strip():  # removing whitespaces:
                            if first:
                                previous_s = s
                                first = False
                                block_string = size_tag[s['size']] + s['text']
                            else:
                                if s['size'] == previous_s['size']:

                                    if block_string and all((c == "|") for c in block_string):
                                        # block_string only contains pipes
                                        block_string = size_tag[s['size']] + s['text']
                                    if block_string == "":
                                        # new block has started, so append size tag
                                        block_string = size_tag[s['size']] + s['text']
                                    else:  # in the same block, so concatenate strings
                                        block_string += " " + s['text']

                                else:
                                    header_para.append(block_string)
                                    block_string = size_tag[s['size']] + s['text']

                                previous_s = s

                    # new block started, indicating with a pipe
                    block_string += "|"

                header_para.append(block_string)

    return header_para


def font_tags(font_counts, styles):
    """Returns dictionary with font sizes as keys and tags as value.
    :param font_counts: (font_size, count) for all fonts occuring in document
    :type font_counts: list
    :param styles: all styles found in the document
    :type styles: dict
    :rtype: dict
    :return: all element tags based on font-sizes
    """
    p_style = styles[font_counts[0][0]]  # get style for most used font by count (paragraph)
    p_size = p_style['size']  # get the paragraph's size

    # sorting the font sizes high to low, so that we can append the right integer to each tag
    font_sizes = []
    for (font_size, count) in font_counts:
        font_sizes.append(float(font_size))
    font_sizes.sort(reverse=True)

    # aggregating the tags for each font size
    idx = 0
    size_tag = {}
    for size in font_sizes:
        idx += 1
        if size == p_size:
            idx = 0
            size_tag[size] = '<p>'
        if size > p_size:
            size_tag[size] = '<h{0}>'.format(idx)
        elif size < p_size:
            size_tag[size] = '<s{0}>'.format(idx)

    return size_tag


def main_Pdf_WithStructure(directory, filename):
    Doc = fitz.open(os.path.join(directory, filename))

    font_counts, styles = fonts(Doc, granularity=False)

    size_tag = font_tags(font_counts, styles)

    elements = headers_para(Doc, size_tag)

    return elements


def Name(directory, filename):
    Structure = main_Pdf_WithStructure(directory, filename)
    Structure = pd.DataFrame(Structure, columns=['text'])

    # estraggo i numeri dentro <h>
    r1 = '<h\d>'
    regex = [r1]

    regex = re.compile('|'.join(regex))
    Structure['Tag'] = Structure.apply(lambda row: regex.findall(row.text), axis=1)

    Structure['TagNum'] = Structure.apply(lambda row: str(row.Tag)[4:5], axis=1)

    Structure['text'] = Structure.apply(lambda row: row.text.upper(), axis=1)
    # faccio pulizie
    Structure['text'] = Structure.apply(lambda row: row.text[4:], axis=1)

    # in alcuni casi (es sinergas) la denominazione offerta commerciale non è in un "<h>", ma in un <p> --> cmq la tengo e gli do valore basso
    Structure = Structure[
        (Structure['TagNum'] != '') | (Structure['text'].str.contains("NOMINAZIONE OFFERTA COMMERCIALE"))]
    Structure['TagNum'] = np.where(Structure['text'].str.contains("NOMINAZIONE OFFERTA COMMERCIALE"), 0,
                                   Structure['TagNum'])

    # se inizia con OFFERTA abbasso il tagnum (esempio OFFERTA GREEN LUCE)!
    # anche se contiene offerta lo faccio (ma meno)
    Structure['Start'] = Structure.apply(lambda row: row.text[0:7], axis=1)
    Structure['StartOfferta'] = np.where(Structure['Start'] == "OFFERTA", 4, 0)
    Structure['ContainsOfferta'] = np.where(Structure['text'].str.contains("OFFERTA"), 0, 0)
    Structure['Denominazione'] = np.where(Structure['text'].str.contains('DENOMINAZIONE OFFERTA COMMERCIALE'), 2, 0)

    # se troppo Lungo penalizzo
    Structure['Len'] = Structure.apply(lambda row: len(row.text), axis=1)
    Structure['TooLong'] = np.where(Structure['Len'] > 40, -3, 0)

    # se non è tra il primo 20% dei record in alto (in alto), penalizzo
    # Structure = Structure.reset_index()
    Structure['Posizione'] = 0
    Soglia = round(len(Structure) / 5)
    Structure.loc[Structure.index[:Soglia], 'Posizione'] = 1

    Structure['TagNum'] = Structure.apply(lambda row: int(
        row.TagNum) - row.StartOfferta - row.ContainsOfferta - row.Denominazione - row.Posizione - row.TooLong, axis=1)

    d1 = '\d\d\\\d\d\\\d{2,4}'  # 10\10\20 oppure 10\10\2020
    d2 = '\d\d/\d\d/\d{2,4}'  # 10/10/20 oppure 10/10/2020
    d3 = '\d\d\\\d\d\\\d{2,4}.AL.\d\d\\\d\d\\\d{2,4}'  # 10\10\20 AL 20\20\20 (con anni anche a 4)
    d4 = '\d\d/\d\d/\d{2,4}.AL.\d\d/\d\d/\d{2,4}'  # 10/10/20 AL 20/20/20 (con anni anche a 4)

    v1 = '\d+\,?\d+'

    d = [d4, d3, d1, d2, v1]  # le regex potrebbero essere sovrapposte,metto prima
    # le più lunghe così se prende quelle si ferma a quella  --> SI DOVREBBE GESTIRE MEGLIO

    regexD = re.compile('|'.join(d))

    Structure = Structure[~Structure['text'].str.contains(regexD, na=False)]
    Structure = Structure[~Structure['text'].str.contains("FAC-SIMILE")]
    Structure = Structure[~Structure['text'].str.contains("FACSIMILE")]
    Structure = Structure[~Structure['text'].str.contains("FAC SIMILE")]
    Structure = Structure[~Structure['text'].str.contains("KWH")]
    Structure = Structure[~Structure['text'].str.contains("800 ")]
    Structure = Structure[~Structure['text'].str.contains("ACQUISTI PER TE")]
    Structure = Structure[~Structure['text'].str.contains("DOVE TROVARCI")]
    Structure = Structure[~Structure['text'].str.contains("SCHEDA DI CONFRONTABILI")]
    Structure = Structure[~Structure['text'].str.contains("SERVIZI AGGIUNTIVI E PROMOZIONI")]
    Structure = Structure[~Structure['text'].str.contains("PROPOSTA DI FORNITURA PER UTENZE DOMESTICHE")]

    Structure['text'] = Structure['text'].str.replace('  ', ' ')
    Structure['text'] = Structure['text'].str.replace('CONDIZIONI ECONOMICHE', '')
    Structure['text'] = Structure['text'].str.replace('CONDIZIONI TECNICO ECONOMICHE', '')
    Structure['text'] = Structure['text'].str.replace("SCHEDA DI CONFRONTABILITA'", '')
    Structure['text'] = Structure['text'].str.replace("|", '')
    Structure['text'] = Structure['text'].str.replace("ENERGIA ELETTRICA", '')
    Structure['text'] = Structure['text'].str.replace("GAS NATURALE", '')
    Structure['text'] = Structure['text'].str.replace("DENOMINAZIONE COMMERCIALE:", '')
    Structure['text'] = Structure['text'].str.replace("DENOMINAZIONE OFFERTA COMMERCIALE:", '')
    Structure['text'] = Structure['text'].str.replace("OFFERTA", '')
    Structure['text'] = Structure['text'].str.replace(":", '')
    Structure['text'] = Structure['text'].str.replace("ENOMINAZIONE", '')
    Structure['text'] = Structure['text'].str.replace("COMMERCIALE", '')
    Structure['text'] = Structure['text'].str.replace("SCHEDA PRODOTTO", '')
    Structure['text'] = Structure['text'].str.replace("ALLEGATO A", '')
    Structure['text'] = Structure['text'].str.replace("ALLEGATO B", '')
    Structure['text'] = Structure['text'].str.replace("CONDIZIONI PARTICOLARI DI FORNITURA", '')
    Structure['text'] = Structure['text'].str.replace("CONDIZIONI DI FORNITURA", '')

    Structure['App'] = Structure.apply(lambda row: len(row.text.replace(" ", "")), axis=1)
    Structure = Structure[Structure['App'] > 2]

    Structure = Structure[Structure['text'] != ""]

    Structure = Structure[Structure.TagNum == Structure.TagNum.min()]

    Structure.sort_values(['Len'], ascending=[True])
    Structure = Structure.nsmallest(1, 'TagNum', keep='last')  # in base al sort di prima, prendo quello più lungo

    # modifiche puntuali su Engie (nome offerta è un'immagine)
    if "223_E3" in filename:
        Structure['text'] = "Energia 3.0"

    return Structure['text']


def SplitPDF(pdf_document, OutDirSplitted):
    Pages = pd.DataFrame(columns=['Page', 'EnergiaTot', 'GasTot'])
    with open(pdf_document, "rb") as filehandle:

        NomeFile = os.path.basename(pdf_document)

        pdf = PdfFileReader(filehandle)
        info = pdf.getDocumentInfo()
        pages = pdf.getNumPages()

        for ppp in range(0, pages):
            PPP = pd.DataFrame()
            page = pdf.getPage(ppp)
            Text_ppp = page.extractText()
            Text_ppp = Text_ppp.upper()

            word = "ENERGIA"
            Count_Energia = 0
            Count_Energia = sum(1 for _ in re.finditer(r'\b%s\b' % re.escape(word), Text_ppp))

            word = "LUCE"
            Count_Luce = 0
            Count_Luce = sum(1 for _ in re.finditer(r'\b%s\b' % re.escape(word), Text_ppp))

            word = "KW"
            Count_Kw = 0
            Count_Kw = sum(1 for _ in re.finditer(r'\b%s\b' % re.escape(word), Text_ppp))

            word = "GAS"
            Count_Gas = 0
            Count_Gas = sum(1 for _ in re.finditer(r'\b%s\b' % re.escape(word), Text_ppp))

            word = "SMC"
            Count_Smc = 0
            Count_Smc = sum(1 for _ in re.finditer(r'\b%s\b' % re.escape(word), Text_ppp))

            Energia_Tot = Count_Energia + Count_Kw + Count_Luce
            Gas_Tot = Count_Gas + Count_Smc

            Dict = {
                "Page": ppp,
                "EnergiaTot": Energia_Tot,
                "GasTot": Gas_Tot
            }

            Pages = Pages.append(Dict, ignore_index=True)

    filehandle.close()

    Pages['Commodity'] = np.where(Pages['EnergiaTot'] > Pages['GasTot'] * 1.5, 'Energia',
                                  np.where(Pages['GasTot'] > Pages['EnergiaTot'] * 1.5, 'Gas', 'Unknown'))

    Pages = Pages[Pages['Commodity'] != 'Unknown']
    NCommodity = set(Pages['Commodity'])

    if len(NCommodity) <= 1:
        copyfile(pdf_document, os.path.join(OutDirSplitted, NomeFile))
    elif len(NCommodity) > 1:
        Energia = Pages[Pages['Commodity'] == "Energia"]
        Gas = Pages[Pages['Commodity'] == "Gas"]

        inputpdf = PdfFileReader(open(pdf_document, "rb"))
        pdfWriter = PdfFileWriter()
        for ii in Energia['Page']:
            pdfWriter.addPage(inputpdf.getPage(ii))
        with open(os.path.join(OutDirSplitted, '{0}_subset_Energia.pdf'.format(os.path.splitext(NomeFile)[0])),
                  'wb') as f:
            pdfWriter.write(f)
            f.close()

        pdfWriter = PdfFileWriter()
        for ii in Gas['Page']:
            pdfWriter.addPage(inputpdf.getPage(ii))
        with open(os.path.join(OutDirSplitted, '{0}_subset_Gas.pdf'.format(os.path.splitext(NomeFile)[0])), 'wb') as f:
            pdfWriter.write(f)
            f.close()

    return NCommodity

import regex as re  #ATTENZIONE! DEVO IMPORTARE 3RD PARTY REGEX MODULO PERCHè QUESTO SUPPORTA I "NEGATIVE LOOKAHEAD
                    #DI LUNGHEZZA VARIABILE --> DEVO PRENDERE "VERDE" CHE NON SIA PRECEDUTO DA NUMERO O DA N° E QUESTO
                    #E' UN NEGATIVE LOOKAHEAD DI LUNGHEZZA VARIABILE CHE VA IN ERRORE SU MODULO STANDARD DI RE
                    #CFR (https://www.reddit.com/r/learnpython/comments/d5g4ow/regex_match_pattern_not_preceded_by_either_of_two/)

def energiaVerde(Doc, PE):
    '''
    questa funzione consente di verificare se la cte prevede l'energia verde

    @keyword: lista di parole chiave
    @document: intero documento da esaminare
    '''

    PossiblePrice = []
    Base = []

    # le inserisco come regular expression perchè non so quanti spazi ci sono e se magari c'è una new line (\s+)
    r1 = r'GREEN(?!\s+NETWORK)'
    r2 = r'(?<!NUMERO.{0,20}|N°.{0,20}|N.{0,20})VERDE'
    r3 = r'100%.{0,10}FONTI.{0,20}RINNOVABILI'
    r4 = r'SOLO.{0,20}FONT.{0,20}RINNOVABIL'
    r5 = r'OPZIONE.{0,30}RINNOVABI'
    r6 = r'SOLTANTO.{0,10}ENERGIA.{0,25}RINNOVABILI'
    r7 = r'APPROVVIGION.{0,10}IMPIANTI.{0,25}RINNOVABIL'
    r8 = r'100%.{0,20}RINNOVABIL'
    r9 = r'RINNOVABIL.{0,20}100%'
    r10 = r'100.{0,10}ENERGIA.{0,10}PULITA'
    r11 = r'ENERGIA.{0,10}PULITA.{0,10}100'
    r12 = r'ESCLUSIVAMENTE.{0,10}FONTI.{0,10}RINNOVABILI'
    r13 = r'SOLO.{0,10}FONTI.{0,10}RINNOVABILI'
    r14 = r'CORRISPETTIVO.{0,5}ENERGIA.{0,10}VERDE'
    r15 = r'INTERAMENTE.{0,50}FONT.{0,10}RINNOVABI'
    r16 = r'ESCLUSIVA.{0,50}FONT.{0,10}RINNOVABI'

    regex = [r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12, r13, r14, r15, r16]

    regex = re.compile('|'.join(regex))

    Base = [m.start() for m in regex.finditer(Doc)]
    Base = pd.DataFrame(Base, columns=['PositionBase'])

    regexNum1 = r'-?\s?\d+\,?\d+'
    regexNum2 = r'-?\s?\d+\.?\d+'

    regexNum = [regexNum1, regexNum2]

    regexNum = re.compile('|'.join(regexNum))

    NumberPos = [m.start() for m in regexNum.finditer(Doc)]
    NumberValue = regexNum.findall(Doc)
    NumberTuples = list(zip(NumberValue, NumberPos))

    PossiblePrice = pd.DataFrame(NumberTuples, columns=['Price', 'Position'])
    # converto in numero
    PossiblePrice['Price_NUM'] = PossiblePrice.apply(lambda row: row.Price.replace(",", "."), axis=1)
    PossiblePrice['Price_NUM'] = PossiblePrice.apply(lambda row: row.Price_NUM.replace(" ", ""), axis=1)
    PossiblePrice['Price_NUM'] = PossiblePrice.apply(lambda row: float(row.Price_NUM), axis=1)

    # filtro numeri < 5 --> possono anche essere negativi?
    PossiblePrice = PossiblePrice[(PossiblePrice['Price_NUM'] > -0.05) & (PossiblePrice['Price_NUM'] < 5)]

    # elimino i numeri lunghi 2 che iniziano con zero, sono tendenzialmente date --> errori
    PossiblePrice['Lun'] = PossiblePrice.apply(lambda row: len(row.Price.replace(" ", "")), axis=1)
    PossiblePrice['Start'] = PossiblePrice.apply(lambda row: row.Price.replace(" ", "")[0], axis=1)
    PossiblePrice = PossiblePrice[(PossiblePrice['Lun'] != 2) | (PossiblePrice['Start'] != "0")]
    PossiblePrice = PossiblePrice[PossiblePrice['Price_NUM'] != PE]

    Base['key'] = 0
    PossiblePrice['key'] = 0

    Prezzo = Base.merge(PossiblePrice, how='outer')
    Prezzo['dist'] = Prezzo.apply(lambda row: row.Position - row.PositionBase, axis=1)
    # FILTRO PER LE DISTANZE POSITIVE (IL NUMERO VIENE DOPO LA PAROLA, OPPURE NEGATIVE MOLTO PICCOLE DOVE QUINDI LA BASE VIENE IMMEDIATAMENTE DOPO )
    Prezzo = Prezzo[(Prezzo['dist'] > - 25) & (Prezzo['dist'] < 300)]

    # se prezzo è > 1 non è ammontare a kwh, ma mensile, quindi mi aspetto cifra tonda..
    Prezzo = Prezzo[(Prezzo['Price_NUM'] < 1) | (Prezzo['Price_NUM'] % 0.5 == 0)]

    Prezzo = Prezzo.nsmallest(1, 'dist')

    # creo flag Y/N oltre a prezzo
    # se ho trovato delle parole in base ma poi non ho trovato match con prezzo, vuol dire che energia è green ma non si paga?
    if len(Base) > 0 and len(Prezzo) == 0:
        Prezzo = Prezzo.append({'FlagVerde': 'Y'}, ignore_index=True)
    elif len(Base) == 0:
        Prezzo = Prezzo.append({'FlagVerde': 'N'}, ignore_index=True)
    elif len(Base) > 0 and len(Prezzo) > 0:
        Prezzo['FlagVerde'] = "Y"

    return (Prezzo['FlagVerde'], Prezzo['Price_NUM'])

import re


def PrezzoComponenteEnergiaF1(Doc):
    PossiblePrice = []
    Base = []

    # le inserisco come regular expression perchè non so quanti spazi ci sono e se magari c'è una new line (\s+)
    # enel ha rinominato le fasce in blu / arancione
    r1 = 'F1'
    r2 = 'FASCIA.{0,10}ARANCIONE'

    regex = [r1, r2]

    regex = re.compile('|'.join(regex))

    Base = [m.start() for m in regex.finditer(Doc)]
    Base = pd.DataFrame(Base, columns=['PositionBase'])

    regexNum1 = r'\d+\,?\d+'
    regexNum2 = r'\d+\.?\d+'

    regexNum = [regexNum1, regexNum2]

    regexNum = re.compile('|'.join(regexNum))

    NumberPos = [m.start() for m in regexNum.finditer(Doc)]
    NumberValue = regexNum.findall(Doc)
    NumberTuples = list(zip(NumberValue, NumberPos))

    PossiblePrice = pd.DataFrame(NumberTuples, columns=['Price', 'Position'])
    # converto in numero
    PossiblePrice['Price_NUM'] = PossiblePrice.apply(lambda row: row.Price.replace(",", "."), axis=1)
    PossiblePrice['Price_NUM'] = PossiblePrice.apply(lambda row: row.Price_NUM.replace(" ", ""), axis=1)
    PossiblePrice['Price_NUM'] = PossiblePrice.apply(lambda row: float(row.Price_NUM), axis=1)

    # filtro numeri < 1 e positivi
    PossiblePrice = PossiblePrice[(PossiblePrice['Price_NUM'] > 0) & (PossiblePrice['Price_NUM'] < 0.3)]

    Base['key'] = 0
    PossiblePrice['key'] = 0

    Prezzo = Base.merge(PossiblePrice, how='outer')
    Prezzo['dist'] = Prezzo.apply(lambda row: row.Position - row.PositionBase, axis=1)
    # FILTRO PER LE DISTANZE POSITIVE (IL NUMERO VIENE DOPO LA PAROLA, OPPURE NEGATIVE MOLTO PICCOLE DOVE QUINDI LA BASE VIENE IMMEDIATAMENTE DOPO )
    Prezzo = Prezzo[(Prezzo['dist'] > - 15) & (Prezzo['dist'] < 250)]
    # AD OGNI MODO NELLE PRIORITA' PRENDO IL PIU PICCOLO IN VALORE ASSOLUTO
    Prezzo['dist'] = Prezzo['dist'].abs()

    Prezzo = Prezzo.nsmallest(1, 'dist')

    return Prezzo['Price_NUM']


def PrezzoComponenteEnergiaF2(Doc):
    PossiblePrice = []
    Base = []

    # le inserisco come regular expression perchè non so quanti spazi ci sono e se magari c'è una new line (\s+)
    r1 = 'F2'
    r2 = 'F23'
    r3 = 'FASCIA.{0,10}BLU'
    regex = [r1, r2, r3]

    regex = re.compile('|'.join(regex))

    Base = [m.start() for m in regex.finditer(Doc)]
    Base = pd.DataFrame(Base, columns=['PositionBase'])

    regexNum1 = r'\d+\,?\d+'
    regexNum2 = r'\d+\.?\d+'

    regexNum = [regexNum1, regexNum2]

    regexNum = re.compile('|'.join(regexNum))

    NumberPos = [m.start() for m in regexNum.finditer(Doc)]
    NumberValue = regexNum.findall(Doc)
    NumberTuples = list(zip(NumberValue, NumberPos))

    PossiblePrice = pd.DataFrame(NumberTuples, columns=['Price', 'Position'])
    # converto in numero
    PossiblePrice['Price_NUM'] = PossiblePrice.apply(lambda row: row.Price.replace(",", "."), axis=1)
    PossiblePrice['Price_NUM'] = PossiblePrice.apply(lambda row: row.Price_NUM.replace(" ", ""), axis=1)
    PossiblePrice['Price_NUM'] = PossiblePrice.apply(lambda row: float(row.Price_NUM), axis=1)

    # filtro numeri < 1 e positivi
    PossiblePrice = PossiblePrice[(PossiblePrice['Price_NUM'] > 0) & (PossiblePrice['Price_NUM'] < 0.3)]

    Base['key'] = 0
    PossiblePrice['key'] = 0

    Prezzo = Base.merge(PossiblePrice, how='outer')
    Prezzo['dist'] = Prezzo.apply(lambda row: row.Position - row.PositionBase, axis=1)
    # FILTRO PER LE DISTANZE POSITIVE (IL NUMERO VIENE DOPO LA PAROLA, OPPURE NEGATIVE MOLTO PICCOLE DOVE QUINDI LA BASE VIENE IMMEDIATAMENTE DOPO )
    Prezzo = Prezzo[(Prezzo['dist'] > - 15) & (Prezzo['dist'] < 250)]
    # AD OGNI MODO NELLE PRIORITA' PRENDO IL PIU PICCOLO IN VALORE ASSOLUTO
    Prezzo['dist'] = Prezzo['dist'].abs()

    Prezzo = Prezzo.nsmallest(1, 'dist')

    return Prezzo['Price_NUM']


def PrezzoComponenteEnergiaF3(Doc):
    PossiblePrice = []
    Base = []

    # le inserisco come regular expression perchè non so quanti spazi ci sono e se magari c'è una new line (\s+)
    r1 = 'F3'
    r2 = 'F23'
    r3 = 'FASCIA.{0,10}BLU'

    regex = [r1, r2, r3]

    regex = re.compile('|'.join(regex))

    Base = [m.start() for m in regex.finditer(Doc)]
    Base = pd.DataFrame(Base, columns=['PositionBase'])

    regexNum1 = r'\d+\,?\d+'
    regexNum2 = r'\d+\.?\d+'

    regexNum = [regexNum1, regexNum2]

    regexNum = re.compile('|'.join(regexNum))

    NumberPos = [m.start() for m in regexNum.finditer(Doc)]
    NumberValue = regexNum.findall(Doc)
    NumberTuples = list(zip(NumberValue, NumberPos))

    PossiblePrice = pd.DataFrame(NumberTuples, columns=['Price', 'Position'])
    # converto in numero
    PossiblePrice['Price_NUM'] = PossiblePrice.apply(lambda row: row.Price.replace(",", "."), axis=1)
    PossiblePrice['Price_NUM'] = PossiblePrice.apply(lambda row: row.Price_NUM.replace(" ", ""), axis=1)
    PossiblePrice['Price_NUM'] = PossiblePrice.apply(lambda row: float(row.Price_NUM), axis=1)

    # filtro numeri < 1 e positivi
    PossiblePrice = PossiblePrice[(PossiblePrice['Price_NUM'] > 0) & (PossiblePrice['Price_NUM'] < 0.3)]

    Base['key'] = 0
    PossiblePrice['key'] = 0

    Prezzo = Base.merge(PossiblePrice, how='outer')
    Prezzo['dist'] = Prezzo.apply(lambda row: row.Position - row.PositionBase, axis=1)
    # FILTRO PER LE DISTANZE POSITIVE (IL NUMERO VIENE DOPO LA PAROLA, OPPURE NEGATIVE MOLTO PICCOLE DOVE QUINDI LA BASE VIENE IMMEDIATAMENTE DOPO )
    Prezzo = Prezzo[(Prezzo['dist'] > - 15) & (Prezzo['dist'] < 250)]
    # AD OGNI MODO NELLE PRIORITA' PRENDO IL PIU PICCOLO IN VALORE ASSOLUTO
    Prezzo['dist'] = Prezzo['dist'].abs()

    Prezzo = Prezzo.nsmallest(1, 'dist')

    return Prezzo['Price_NUM']

import re

def CodiceOfferta(Doc):
    # lista di codici che vengono fuori con le regular expression ma che sono sbagliati
    CandidatiErrati = ['REABO-481345',  # iscrizione alla camera di commercio di wekiwi
                       'BX100',  # sigla in scheda confrontabilità
                       'BOLLETTA2',
                       'F1',
                       'F2',
                       'F3',
                       'F0',
                       'F23',
                       'PF0',
                       'PF1',
                       'PF2',
                       'PF3',
                       'PF23',
                       'MHIEWPR77DBP8DFC6',
                       'C2X1'
                       ]

    # prima cerco reg exp con trattini e underscore
    # d1 = '[A-Z]+\d*-*_*\w*\d+\w*'
    d1 = '[A-Z]+[\d_-]+[A-Z\d_-]+'

    d = [d1]
    regexNum = re.compile('|'.join(d))
    NumberPos = [m.start() for m in regexNum.finditer(Doc)]
    NumberValue = regexNum.findall(Doc)
    NumberTuples = list(zip(NumberValue, NumberPos))
    PossiblePrice = pd.DataFrame(NumberTuples, columns=['Price', 'Position'])

    # filtro però che regex debba avere almeno un numero & un carattere
    d2_1 = '\d'
    d = [d2_1]
    regexNum = re.compile('|'.join(d))

    PossiblePrice['Num'] = PossiblePrice.apply(lambda row: regexNum.findall(row.Price), axis=1)
    PossiblePrice = PossiblePrice[PossiblePrice['Num'].astype(bool)]  # filtro via le liste vuote

    d2_2 = '[A-Z]'
    d = [d2_2]
    regexNum = re.compile('|'.join(d))

    PossiblePrice['Char'] = PossiblePrice.apply(lambda row: regexNum.findall(row.Price), axis=1)
    PossiblePrice = PossiblePrice[PossiblePrice['Char'].astype(bool)]

    # se c'è almeno 1 con underscore o trattini, prendo quello
    PossiblePrice['SpecUnderscore'] = PossiblePrice.apply(lambda row: "_" in row.Price, axis=1)
    PossiblePrice['SpecTrattino'] = PossiblePrice.apply(lambda row: "-" in row.Price, axis=1)
    PossiblePrice['Lunghezza'] = PossiblePrice.apply(lambda row: len(row.Price), axis=1)

    PossiblePrice = PossiblePrice[~PossiblePrice['Price'].isin(CandidatiErrati)]
    PossiblePrice = PossiblePrice[~PossiblePrice['Price'].str.contains('SHOP')]
    PossiblePrice = PossiblePrice[PossiblePrice['Lunghezza'] >= 5]

    Cod = PossiblePrice[PossiblePrice['SpecUnderscore'] == True].nlargest(1, 'Lunghezza')
    if len(Cod) == 0:
        Cod = PossiblePrice[PossiblePrice['SpecTrattino'] == True].nlargest(1, 'Lunghezza')

        if len(Cod) == 0:
            Cod = PossiblePrice.nlargest(1, 'Lunghezza')

    return Cod['Price']


def ClassifyDoc(Doc):
    word = "ENERGIA"
    Count_Energia = 0
    Count_Energia = sum(1 for _ in re.finditer(r'%s' % re.escape(word), Doc))

    word = "LUCE"
    Count_Luce = 0
    Count_Luce = sum(1 for _ in re.finditer(r'%s' % re.escape(word), Doc))

    word = "KW"
    Count_Kw = 0
    Count_Kw = sum(1 for _ in re.finditer(r'%s' % re.escape(word), Doc))

    word = "GAS"
    Count_Gas = 0
    Count_Gas = sum(1 for _ in re.finditer(r'%s' % re.escape(word), Doc))

    word = "SMC"
    Count_Smc = 0
    Count_Smc = sum(1 for _ in re.finditer(r'%s' % re.escape(word), Doc))

    # se trovo enel energia tolgo da energia (perchè se no anche nelle offerte gas ne trovo sempre)
    word = "ENEL ENERGIA"
    Count_EnelEnergia = 0
    Count_EnelEnergia = sum(1 for _ in re.finditer(r'%s' % re.escape(word), Doc))

    word = "AUTORITÀ DI REGOLAZIONE PER ENERGIA"
    Count_Autorita = 0
    Count_Autorita = sum(1 for _ in re.finditer(r'%s' % re.escape(word), Doc))

    word = "MERCATO LIBERO  DELL’ENERGIA"
    Count_Mercato = 0
    Count_Mercato = sum(1 for _ in re.finditer(r'%s' % re.escape(word), Doc))

    Energia_Tot = Count_Energia + Count_Kw + Count_Luce - Count_EnelEnergia - Count_Autorita - Count_Mercato
    Gas_Tot = Count_Gas + Count_Smc

    if Energia_Tot > Gas_Tot:
        return "Energia"
    elif Gas_Tot > Energia_Tot:
        return "Gas"
    elif Energia_Tot == Gas_Tot:
        return "Unknown"


def replaceNumber(Str):
    Str = Str.replace(" TRE ", "3")
    Str = Str.replace(" QUATTRO ", "4")
    Str = Str.replace(" CINQUE ", "5")
    Str = Str.replace(" SEI ", "6")
    Str = Str.replace(" SETTE ", "7")
    Str = Str.replace(" OTTO ", "8")
    Str = Str.replace(" NOVE ", "9")
    Str = Str.replace(" DIECI ", "10")
    Str = Str.replace(" UNDICI ", "11")
    Str = Str.replace(" DODICI ", "12")
    Str = Str.replace(" TREDICI ", "13")
    Str = Str.replace(" QUATTORDICI ", "14")
    Str = Str.replace(" QUINDICI ", "15")
    Str = Str.replace(" SEDICI ", "16")
    Str = Str.replace(" DICIASSETTE ", "17")
    Str = Str.replace(" DICIOTTO ", "18")
    Str = Str.replace(" DICIANNOVE ", "19")
    Str = Str.replace(" VENTI ", "20")

    return Str


def Promozioni(Doc):
    ListaPromo = []

    KeyWords = ["REGALO", "REGALI", "VOUCHER", "PREMIO", "PREMI", "PROMOZIONE", "PROMOZIONI", "REGOLAMENTO", "CONCORSO",
                "OPERAZIONE A PREMI", "MANIFESTAZIONE A PREMI", "INZIATIVA", "BUONO", "AMAZON", "GIFT CARD", "FEDELTA'",
                "RISPARMIO", "PROGRAMMA FEDELTA'", "PROGRAMMA", "VANTAGGIO", "NOVITA'", "SCONTO"]

    for ww in Doc.split():
        for kk in KeyWords:
            if ww == kk:
                ListaPromo.append(ww)

    ListaPromo = list(dict.fromkeys(ListaPromo))

    return ListaPromo 