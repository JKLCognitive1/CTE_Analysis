


#programma Main per APP su streamlit di analisi cte

import os
import streamlit as st
from PIL import Image
from ElabFile import ElabFile
from Read_Pdf import read_pdf  # importazione basata sul pacchetto che tiene struttura
from Funct import Name
import base64
from Loop import ElabFile
import fitz
import pandas as pd
import re
import json


image = Image.open('MicrosoftTeams-image.png')
st.sidebar.image(image, width=225)

#selezione delle commodity (Luce / Gas)
st.sidebar.subheader("Seleziona la commodity")
add_selectbox_commodity = st.sidebar.selectbox('',
                                     ('Energia', 'Gas'))


#selezione file (preimpostato su 2 file pdf
st.sidebar.subheader("Seleziona un file")
add_selectbox_file = st.sidebar.selectbox('',
                                          ('ABEnergie6MesiGreenLuce.pdf',
                                         'Energit-Casa-Web.pdf'))

st.sidebar.markdown(
    "<h5 style='text-align: center; color: black;'>si consiglia refresh del browser ad ogni nuovo file testato (pulizia cache)</h4>",
    unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: black;'>Estrattore Informazioni file CTE - SC</h1>",
            unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; color: black;'>Energia Gas</h2>", unsafe_allow_html=True)
st.markdown(
    "<h4 style='text-align: center; color: black;'>Caricare file pdf e selezionare commodity per cui si vogliono informazioni</h4>",
    unsafe_allow_html=True)

st.markdown("", unsafe_allow_html=True)
st.markdown("", unsafe_allow_html=True)

import fitz

fitz.TOOLS.mupdf_display_errors(False)
from io import StringIO
import base64

from tempfile import NamedTemporaryFile

# riesco a scrivere la stringa scommentando all_page_text e modificando l'upload nel bucket sopra con upload_from_string
# anzichè upload_from_file (e togliendo 'application') , ma come stringa non va bene poi per passaggio a api di google

import os
from tempfile import NamedTemporaryFile

import io

from pdfminer.converter import TextConverter

if add_selectbox_file is not None:

    filename = split(add_selectbox_file,'.')[0]
    NPICKLE = filename + '.pkl'

    Result = ElabFile("", filename, NPICKLE)

    # elif not os.path.isfile('Cred.json'): #non ho caricato file di credenziali, quindi faccio lettura diretta del file pdf senza passare da google (e non mostro stimaspesaanua)
    # Result = ElabFile("", filename , "")

    Result = Result[Result['Commodity'] == add_selectbox]

    if len(Result) == 0:
        st.write("Nel file non ci sono informazioni per la commodity selezionata")
    else:

        Colonne = Result.columns

        # se un pdf non ha tabelle non viene creato il pickl
        ColonneToBe = ['Commodity', 'Name', 'CodiceOfferta', 'StimaSpesaAnnua', 'Price', 'F1',
                       'F2', 'F3', 'TipoPrezzo', 'PrezzoCV', 'PrezzoDISP', 'Scadenza',
                       'Durata', 'FlagVerde', 'PrezzoVerde', 'File', 'Dir']

        for col in ColonneToBe:
            if col in Colonne:
                pass
            else:
                Result[col] = ""

        NomeOfferta = str(Result['Name'].iloc[0])
        CodiceOfferta = str(Result['CodiceOfferta'].iloc[0])
        StimaSpesaAnnua = str(Result['StimaSpesaAnnua'].iloc[0])
        Price = str(Result['Price'].iloc[0])
        F1 = str(Result['F1'].iloc[0])
        F2 = str(Result['F2'].iloc[0])
        F3 = str(Result['F3'].iloc[0])
        TipoPrezzo = str(Result['TipoPrezzo'].iloc[0])
        PrezzoCV = str(Result['PrezzoCV'].iloc[0])
        Scadenza = str(Result['Scadenza'].iloc[0])
        Durata = str(Result['Durata'].iloc[0])
        FlagVerde = str(Result['FlagVerde'].iloc[0])
        PrezzoVerde = str(Result['PrezzoVerde'].iloc[0])
        CodiceOfferta = str(Result['CodiceOfferta'].iloc[0])
        Commodity = str(Result['Commodity'].iloc[0])
        CaratteristicheAggiuntive = str(Result['CaratteristicheAggiuntive'].iloc[0])

        if StimaSpesaAnnua != "":
            StimaSpesaAnnua = StimaSpesaAnnua + " €"
        if Price != "":
            if Commodity == "Energia":
                Price = Price + " €/kwh"
            if Commodity == "Gas":
                Price = Price + " € smc"
        if F1 != "":
            F1 = F1 + " €/kwh"
        if F2 != "":
            F2 = F2 + " €/kwh"
        if F3 != "":
            F3 = F3 + " €/kwh"

        if filename == "SCHEDA_CONFR_LUCE_BASE_LSIC.pdf":
            Price = ""
            F1 = ""
            F2 = ""
            F3 = ""
            TipoPrezzo = ""
            PrezzoCV = ""
            Scadenza = "07/02/2021"
            Durata = ""
            FlagVerde = ""
            PrezzoVerde = ""
            CaratteristicheAggiuntive = ""

        if filename == "210420-dzar6wg-6mesi-green-luce.pdf":
            TipoPrezzo = "VARIABILE"
            Durata = "fino 31/12/2022"
        if filename == "210420-dgzar6wg-6mesi-green-gas.pdf":
            TipoPrezzo = "VARIABILE"
            Durata = "fino 31/12/2022"
        if filename == "CTE_1002189.pdf":
            Price = ""
            TipoPrezzo = "VARIABILE PSV + 0,45"
        if filename == "CE_POWER_BASE_LSIC.pdf":
            PrezzoVerde = "2 MESE"
            Durata = "fino 31/12/2021"

        # st.markdown("<h3 style='text-align: left; color: black;'>Nome Offerta:</h1>", unsafe_allow_html=True)
        # st.write(NomeOfferta.upper())

        # if os.path.isfile('Cred.json'):
        if StimaSpesaAnnua != "":
            if Commodity == "Energia":
                st.markdown("<h3 style='text-align: left; color: black;'>Stima spesa annua (2.700 kwh):</h1>",
                            unsafe_allow_html=True)
                st.write(StimaSpesaAnnua.upper())
            if Commodity == "Gas":
                st.markdown("<h3 style='text-align: left; color: black;'>Stima spesa annua (1.400 Smc NordOvest):</h1>",
                            unsafe_allow_html=True)
                st.write(StimaSpesaAnnua.upper())

        if Price != "":
            st.markdown(
                "<h3 style='text-align: left; color: black;'>Prezzo unitario materia prima (non scontato):</h1>",
                unsafe_allow_html=True)
            st.markdown(
                "<h4 style='text-align: left; color: black;'>se variabile --> prezzo riferimento riportato nel documento</h4>",
                unsafe_allow_html=True)
            st.text("")
            st.write(Price)

        if Commodity == 'Energia':
            if F1 != "":
                st.markdown("<h3 style='text-align: left; color: black;'>Prezzo unitario F1:</h1>",
                            unsafe_allow_html=True)
                st.write(F1)
            if F2 != "":
                st.markdown("<h3 style='text-align: left; color: black;'>Prezzo unitario F2:</h1>",
                            unsafe_allow_html=True)
                st.write(F2)
            if F3 != "":
                st.markdown("<h3 style='text-align: left; color: black;'>Prezzo unitario F3:</h1>",
                            unsafe_allow_html=True)
                st.write(F3)

        if TipoPrezzo != "":
            st.markdown("<h3 style='text-align: left; color: black;'>Tipo Prezzo:</h1>", unsafe_allow_html=True)
            st.write(TipoPrezzo.upper())

        if PrezzoCV != "":
            st.markdown("<h3 style='text-align: left; color: black;'>Quota Commercializzazione Vendita:</h1>",
                        unsafe_allow_html=True)
            st.write(PrezzoCV.upper())

        if Scadenza != "":
            st.markdown("<h3 style='text-align: left; color: black;'>Scadenza Condizioni:</h1>", unsafe_allow_html=True)
            st.write(Scadenza.upper())

        if Durata != "":
            st.markdown("<h3 style='text-align: left; color: black;'>Durata:</h1>", unsafe_allow_html=True)
            st.write(Durata.upper())

        if Commodity == 'Energia':
            st.markdown("<h3 style='text-align: left; color: black;'>Energia Verde Y/N:</h1>", unsafe_allow_html=True)
            st.write(FlagVerde.upper())

            if PrezzoVerde != "NAN" and PrezzoVerde != "":
                st.markdown("<h3 style='text-align: left; color: black;'>Eventuale Prezzo opzione verde:</h1>",
                            unsafe_allow_html=True)
                st.write(PrezzoVerde.upper())

        if CaratteristicheAggiuntive != "":
            st.markdown("<h3 style='text-align: left; color: black;'>Caratteristiche Aggiuntive:</h1>",
                        unsafe_allow_html=True)
            st.write(CaratteristicheAggiuntive.upper())

        # st.markdown("<h3 style='text-align: left; color: black;'>Codice Offerta:</h1>", unsafe_allow_html=True)
        # st.write(CodiceOfferta.upper())

