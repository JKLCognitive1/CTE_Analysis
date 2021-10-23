# CTE_Analysis
App to extract information from CTE (condizioni tecnico economiche) and SC (schede di confrontabilità)


Permette elaborazione dei due file .pdf nel repository per estrarre informazioni rilevanti (prezzo, spesa stimata, durata delle condizioni ...) 

***** Ottobre 2021 ******
Nell'app originale (di dicembre 2020) era prevista possibilità di selezionare qualsiasi file pdf
Algoritmo però utilizzava chiamate a DocumenAI di Google tramite account personale di Marco Goglio (non era previsto account JKL all'epoca)
Le chiamate a DocumentAI servivano a identificare eventuali tabelle nel file pdf --> risultato dell'elaborazione di DocumenAI veniva salvato in un file .pkl salvato in bucket di Goglio

Attualmente l'app permette di elaborare i due file pdf del repository, e vengono utilizzati i due file .pkl salvati nel pdf (per leggere le tabelle all'interno del pdf)
Questi pkl sono risultato dell'elaborazione di DocumentAI che è stata fatta originariamente (file .pkl spostati dal bucket di Goglio al presente repository)

Contando che inizialmente algoritmo girava su qualsiasi file pdf, è sicuramente più complesso di quanto necessario per l'analisi dei due file previsti attualmente
