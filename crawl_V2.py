# -*- coding: utf-8 -*-

import json
import requests
import math
import logging
import datetime
import io
import codecs
import argparse

from clint.textui import progress
from config import config


nvdb_gater = {}
gater_uten_lokasjon = {}
total_count = 0


parser = argparse.ArgumentParser()
parser.add_argument("-gatenavnfil", "-f", required=True)
parser.add_argument("-utfilnavn", "-u", required=True)
parser.add_argument("-config", "-c", required=True)
parser.add_argument("-apigatefil", "-a")


def skriv_apistatus():
    status = requests.get(cfg.get('gate', 'url_status')).json()
    print(status.get('datagrunnlag'))


def loggoppsett():
    logger = logging.getLogger(cfg.get('log', 'loggnavn'))
    log_filehandler = logging.FileHandler(cfg.get('log', 'loggfilnavn'))
    log_formatter = logging.Formatter(cfg.get('log', 'loggformat'))
    log_filehandler.setFormatter(log_formatter)
    logger.addHandler(log_filehandler)
    logger.setLevel(logging.INFO)
    return logger


def hent_kommunenr(nvdbid):
    kommuneurl = cfg.get('gate', 'url_template_kommune').format(cfg.get('gate','kommune_typeid'), nvdbid)
    print(kommuneurl)
    data = requests.get(kommuneurl).json()
    for e in data.get('egenskaper', []):
        if e.get('navn') == 'Kommunenummer':
            return e.get('verdi')
    return None

def hent_kommune_fra_relasjon(nvdbid):
    url = cfg.get('gate','url_template_enkeltgate').format(nvdbid)
    data = requests.get(url).json()
    print(url)
    barn = data.get('relasjoner', {}).get('barn', [])
    for b in barn:
        if b.get('type', {}).get('id', None) == int(cfg.get('gate','kommune_typeid')):
            kommune_objekter = b.get('vegobjekter', [])
            if len(kommune_objekter) > 0:
                return hent_kommunenr(kommune_objekter[0])
            else:
                return None


def legg_til_gate_uten_sted(gate):
    global gater_uten_lokasjon
    kommunenr = hent_kommune_fra_relasjon(gate['id'])
    if kommunenr is None:
        kommunenr = 'Ukjent'
    if kommunenr not in gater_uten_lokasjon.keys():
        gater_uten_lokasjon[kommunenr] = {}

    kommune_gater = gater_uten_lokasjon[kommunenr]
    if gate['kode'] not in kommune_gater.keys():
        kommune_gater[gate['kode']] = []

    kommune_gater_kode = kommune_gater[gate['kode']]

    gate_objekt = {
        'nvdbid': gate['id'],
        'versjon': gate['versjon'],
        'gatenavn': gate.get('navn', None)
    }

    kommune_gater_kode.append(gate_objekt)



def behandle(objekter):
    global total_count
    for o in objekter:
        gate = {}
        gate['id'] = o.get('id', None)
        gate['versjon'] = o['metadata']['versjon']
        k = o['lokasjon'].get('kommuner', [])
        for e in o['egenskaper']:
            if e['navn'] == 'Gatekode':
                gate['kode'] = e['verdi']
            if e['navn'] == 'Gatenavn':
                gate['navn'] = e['verdi'].strip()

        if k:
            gate['kommune'] = "{:04}".format(k[0])

            if not nvdb_gater.get(gate['kommune']):
                nvdb_gater[gate['kommune']] = [gate]
            else:
                nvdb_gater[gate['kommune']].append(gate)
        else:
            #legg_til_gate_uten_sted(gate)
            log.info("Gate uten stedfesting: {} ({})".format(gate['id'], gate['versjon']))

        total_count = total_count + 1


def hent(url):
    r = requests.get(url)
    data = r.json()
    behandle(data.get('objekter',[]))
    return data.get('metadata', {}).get('neste', {}).get('href')



def hent_nvdb_gater(bar):
    bar.label = "Laster ned... "
    antall = requests.get(cfg.get('gate', 'url_statistikk')).json().get('antall')
    neste = cfg.get('gate', 'url_gater') 
    forrige = ''
    while neste != forrige:
        forrige = neste
        neste = hent(neste)
        bar.show(math.floor((total_count * 100)/antall))


def les_matrikkel_gater(gatefil):
    matrikkel_gater = {}
    with io.open(gatefil, encoding='utf-8') as g_file:
        for line in g_file:
            try:
                line = line.strip()
                if line and line[0].isdigit():
                    k, a, n = line.split(None, 2)
                    #print k, a, n
                    gate = {
                        'kommune': k.strip(),
                        'navn': n.strip(),
                        'kode': a.strip()
                    }
                    k_list = matrikkel_gater.get(k, [])
                    if not k_list:
                        matrikkel_gater[k] = [gate]
                    else:
                        matrikkel_gater[k].append(gate)
            except Exception as e:
                print ("Error:", line)
            except ValueError:
                print("ValueError: ", line)
    return matrikkel_gater



def compare_too(bar, utfilnavn="forslag_test.txt"):
    bar.label = "Sammenlikner... "
    file = codecs.open(utfilnavn, "w", "utf-8")
    count = 0
    for k in matrikkel_gater.keys():
        count += 1
        ng = nvdb_gater.get(k, [])
        for g in matrikkel_gater.get(k, []):
            for n in ng:
                try:
                    #print int(g['kode']), int(n['kode']), int(g['kode']) == int(n['kode']) or ""
                    if int(g['kode']) == int(n['kode']):
                        if ('navn' not in n.keys()) or (n['navn'] != g['navn']):
                            file.write(u"{},{},{},{},{}\n".format(n['id'], n['versjon'], n['kode'], g['kommune'], g['navn']))
                except KeyError:
                    print (g, n)
        bar.show(math.floor((count * 100) / len(matrikkel_gater.keys())))
    file.close()




if __name__ == "__main__":
    args = parser.parse_args()
    cfg = config.Config(args.config)
    log = loggoppsett()

    print (args.gatenavnfil, " -> ", args.utfilnavn)
    skriv_apistatus()

    with progress.Bar(label="Starter.....", width=100, expected_size=100) as bar:
        if args.apigatefil:
            with open(args.apigatefil) as f:
                nvdb_gater = json.load(f)
        else:
            hent_nvdb_gater(bar)
        matrikkel_gater = les_matrikkel_gater(args.gatenavnfil)
        compare_too(bar, args.utfilnavn)

    prefix = datetime.date.today().isoformat()
    filnavn_allegater = cfg.get('gate', 'filnavn_template_apigater').format(prefix)
    with open(filnavn_allegater, 'w') as fp:
        json.dump(nvdb_gater, fp)
    filnavn_utensted = cfg.get('gate', 'filnavn_template_gaterutensted').format(prefix)
    with open(filnavn_utensted, 'w') as fp:
        json.dump(gater_uten_lokasjon, fp)