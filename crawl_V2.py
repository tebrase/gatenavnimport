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


url = 'https://www.vegvesen.no/nvdb/api/v2/vegobjekter/538.json?inkluder=lokasjon,metadata,egenskaper&inkludergeometri=ingen&antall=10000'
#url_test = 'https://www.test.vegvesen.no/nvdb/api/v2/vegobjekter/538.json?inkluder=lokasjon,metadata,egenskaper&inkludergeometri=ingen&antall=10000'

nvdb_gater = {}
total_count = 0

parser = argparse.ArgumentParser()
parser.add_argument("-gatenavnfil", "-f", required=True)
parser.add_argument("-utfilnavn", "-u", required=True)
parser.add_argument("-apigatefil", "-a")

def skriv_apistatus():
    status = requests.get("https://www.vegvesen.no/nvdb/api/v2/status").json()
    print(status.get('datagrunnlag'))


def behandle(objekter):
    global total_count
    for o in objekter:
        gate = {}
        gate['id'] = o.get('id', None)
        gate['versjon'] = o['metadata']['versjon']
        k = o['lokasjon'].get('kommuner', [])
        if k:
            gate['kommune'] = "{:04}".format(k[0])
            for e in o['egenskaper']:
                if e['navn'] == 'Gatekode':
                    gate['kode'] = e['verdi']
                if e['navn'] == 'Gatenavn':
                    gate['navn'] = e['verdi'].strip()
            if not nvdb_gater.get(gate['kommune']):
                nvdb_gater[gate['kommune']] = [gate]
            else:
                nvdb_gater[gate['kommune']].append(gate)
        else:
            log.info("Gate uten stedfesting: {} ({})".format(gate['id'], gate['versjon']))

        total_count = total_count + 1


def hent(url):
    r = requests.get(url)
    data = r.json()
    behandle(data.get('objekter',[]))
    return data.get('metadata', {}).get('neste', {}).get('href')



def hent_nvdb_gater(bar):
    bar.label = "Laster ned... "
    antall = requests.get("https://www.vegvesen.no/nvdb/api/v2/vegobjekter/538/statistikk.json").json().get('antall')
    neste = url  
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
    log = logging.getLogger("Gatecrawler")
    log_filehandler = logging.FileHandler("gatecrawl.log")
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_filehandler.setFormatter(log_formatter)
    log.addHandler(log_filehandler)
    log.setLevel(logging.INFO)
    args = parser.parse_args()
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
    gatefilnavn = "{}_NvdbAPIGater.json".format(prefix)
    with open(gatefilnavn, 'w') as fp:
        json.dump(nvdb_gater, fp)