import json
import configparser
import pandas as pd
import telegram_send
import ccxt
import os. path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FormatStrFormatter

#Cet import + le code suivant permettent d'éviter les warnings dans les logs
import warnings; warnings.simplefilter('ignore')

def load_graph(symbol):
    global ax
    global plt
    data=getData(symbol)
    data=data[len(data)-len(x):]['close']
    price_series = pd.Series(data)
    evolution=[]
    for i in price_series.pct_change() :
        if len(evolution)==0 :   
            evolution.append(initialInv)
        else :
            evolution.append(evolution[-1]*i+evolution[-1])

    ind = np.argmin(data)
    evolution2=[]
    j=0
    for i in price_series.pct_change() :
        if j<ind :
            evolution2.append(0.0)
        else :
            if len(evolution2)==0 or evolution2[-1]==0.0 :   
                evolution2.append(initialInv)
            else :
                evolution2.append(evolution2[-1]*i+evolution2[-1])
        j+=1
    ax.plot(x, evolution, label=f'Solde si vous aviez investi {initialInv}$ sur {symbol.split("/")[0]} au moment où vous avez lancé votre bot le {x[0].split(" ")[0]}')
    ax.plot(x, evolution2, label=f'Solde si vous aviez investi {initialInv}$ sur {symbol.split("/")[0]} au meilleur moment le {x[ind].split(" ")[0]}')

def getData(symbol) :
    result = pd.DataFrame(ccxt.ftx().fetch_ohlcv(symbol=symbol, timeframe="1h", limit=5000))
    result = result.rename(columns={0: 'timestamp', 1: 'open', 2: 'high', 3: 'low', 4: 'close', 5: 'volume'})
    result = result.set_index(result['timestamp'])
    result.index = pd.to_datetime(result.index, unit='ms')
    del result['timestamp']
    return result

initialInv=0
path="/home/moutonneux/bots/dashbot/"
figH=20
figL=50

#Mettre selon lequel vous voulez baser l'axe Y
botPathList = [
            '/home/moutonneux/bots/bot-miracle/',
            '/home/moutonneux/bots/bot-vp1/',
            '/home/moutonneux/bots/bot-miracle-mono/',
            '/home/moutonneux/bots/bot-superreversal/'
            ]

botList = {}
#On créer un graphique du solde à partir de ce fichier, on génère le fichier au format PDF
fig, ax = plt.subplots()
fig.set_figheight(figH)
fig.set_figwidth(figL)
globalSolde=[]
#On récupérè les informations spécifiques à chaque bots à partir du repertoire
for botPath in botPathList :
    botDict={}
    try :
        files = os.listdir(botPath)
        for file in files :
            if ("bot_" in file or "bot" in file) and ("config-bot.cfg" != file and "cBot_perp_ftx.py" != file):
                bot_file_name=file
                with open(botPath+bot_file_name, "r+") as f:
                    for line in f:
                        if "botname" in line :
                            botname=str(line.split("=")[1].split('"')[1])
                        if "version" in line :
                            version=float(line.split("=")[1].split('"')[1])
                            break
                            
        config = configparser.ConfigParser()
        config.read(botPath+'config-bot.cfg')
        with open(botPath+'/data/'+'historiques-soldes.dat', 'r') as f:
            data = f.readlines()[-1].split()
            solde=float(data[5])
        #On sauvegarde le chemin vers le repertoire du bot
        botDict['name'] = botname
        botDict['version'] = version
        botDict['apiKey'] = str(config['FTX.AUTHENTIFICATION']['apiKey'])
        botDict['paths'] = { 'path': botPath, 'solde_file': botPath+'data/'+'historiques-soldes.dat', 'config_file': botPath+'config-bot.cfg', 'bot_file': botPath+bot_file_name}
        performance = round((float(solde)-float(config['SOLDE']['totalInvestment']))/float(solde)*100, 3)
        if performance>0.0 :
            performance=float("+"+str(performance))
        botDict['solde'] = { 'totalInvestment' : float(config['SOLDE']['totalInvestment']), 'currentSolde' : float(solde), 'performance' : performance}
        botDict['timeframe'] = str(config['STRATEGIE']['timeframe'])
        botDict['levier'] = str(config['STRATEGIE']['defaultLeverage'])
        initialInv=initialInv+float(config['SOLDE']['totalInvestment'])
        botList[botDict['name']]=botDict
        print(f'{botname} traité.')
    except Exception as err :
        print(f"Impossible de traiter {botname} : {err}")
    
    #Génération du fichier avec les soldes
    if botPathList[0]==botPath :
        x=[]
    y=[]
    try :
        with open(botPath+'/data/'+'historiques-soldes.dat', "r") as f:
            i=0
            for line in f:
                if "#" in line:
                    continue
                data = line.split()
                jour=int(data[0])
                mois=int(data[1])
                annee=int(data[2])
                heure=int(data[3])
                minutes=int(data[4])
                solde=float(data[5])
                if botPathList[0]==botPath :
                    x.append(f"{jour}-{mois}-{annee} {heure}:{minutes}")
                y.append(solde)
                i+=1
    except :
        print(f"WARNING : Le fichier {botPath}+'/data/'+'historiques-soldes.dat' est introuvable.")
    if len(x)!=len(y) :
        newY=[]
        if len(x)>len(y) :
            for i in range(0, len(x)) :
                if i<=(len(x)-len(y)) :
                    newY.append(0)
                else :
                    newY.append(y[i-(len(x)-len(y))])
        else :
            for i in range(0, len(x)) :
                newY.append(y[i])
        y=newY
    globalSolde=[globalSolde[i]+y[i] for i in range(min(len(globalSolde),len(y)))]+max(globalSolde,y,key=len)[min(len(globalSolde),len(y)):]
    plt.plot(x, y, label=f'{botname}')


plt.title('Soldes des différents bots')
plt.legend(prop={'size': 30})
plt.xlabel("Date", fontsize=20)
plt.ylabel("Solde", fontsize=20)
ax.plot(x,y)
ax.set_xticks(x[::int(4000/figL)])
ax.set_xticklabels(x[::int(4000/figL)], rotation=45)
ax.grid(axis='y')
try :
    plt.savefig(f"{path}soldes_par_bots.pdf", dpi=1000)
    print(f"Fichier {path}soldes_par_bots.pdf créé.")
except Exception as err :
    print(f"Détails : {err}")

try :
    jsonFile = open(f"{path}bots.json", "w", encoding ='utf8')
    json.dump(botList, jsonFile, indent = 4)
    jsonFile.close()
    print(f"Fichier {path}bots.json créé.")
except : 
    print("Impossible de créer le fichier JSON")

fig, ax = plt.subplots()
fig.set_figheight(figH)
fig.set_figwidth(figL)

plt.title('Solde global de tous les bots')
plt.xlabel("Date", fontsize=20)
plt.ylabel("Solde", fontsize=20)



evolution3=[]
for i in x :
    evolution3.append(initialInv)
ax.plot(x, globalSolde, label=f'Solde de tous les bots pour un investissement total de {initialInv}$')
ax.plot(x, evolution3, label=f'Solde si vous n\'aviez jamais investi et que vous aviez gardé vos {initialInv}$')


load_graph("BTC/USD")
#load_graph("ETH/USD")
#load_graph("SOL/USD")

plt.legend(prop={'size': 20})
ax.set_xticks(x[::int(4000/figL)])
ax.set_xticklabels(x[::int(4000/figL)], rotation=45)
ax.grid(axis='y')
try :
    plt.savefig(f"{path}soldes_global.pdf", dpi=1000)
    print(f"Fichier {path}soldes_global.pdf créé.")
except Exception as err :
    print(f"Détails : {err}")