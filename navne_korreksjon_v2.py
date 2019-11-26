# -*- coding: utf-8 -*-

import requests
import json
import datetime
import time
import sys
import codecs
import argparse
import yaml
import os

from login import login

# nvdb_id, versjon, gatekode, kommune, navn
# 2099991,1,1001,0536,Hasselvegen
# 2099992,1,1002,0536,Klinkenbergvegen

parser = argparse.ArgumentParser()
parser.add_argument("-gatenavnfil", "-f", required=True)
parser.add_argument("-config", "-c", required=True)

nvdb_typeid = 538
nvdb_propertyid_gatenavn = 4589
url_list = []


def last_config_fil(config_file):
    if config_file:
        if not os.path.exists(config_file):
            # log.error("Config file was not found..")
            sys.exit(1)
        try:
            with open(config_file, 'r') as f:
                cfg = yaml.load(f, Loader=yaml.BaseLoader)
        except yaml.scanner.ScannerError as se:
            sys.exit(1)

    return cfg


class Korreksjon:
    def __init__(self, config, auth, date='', datakatalogversjon="2.10"):
        self.payload = {
            'delvisKorriger': {
                'vegObjekter': []
            },
            'effektDato': date or datetime.datetime.now().date().isoformat(),
            'datakatalogversjon': datakatalogversjon
        }
        self.headers = {'content-type': 'application/json', 'Accept': 'application/json', 'X-Client': 'Gatenavnimport'}
        self.cookies = auth
        print(self.cookies)
        self.url = config.get('skriv_url')
        self.les = config.get('les_template')

    def sjekk_objektforekomst(self, nvdb_id, versjon):
        lurl = self.les.format(nvdb_typeid, nvdb_id, versjon)
        tr = requests.get(lurl, cookies=self.cookies)
        print(tr.status_code, lurl)
        return tr.status_code == 200

    def add_navne_korreksjon(self, nvdb_id, versjon, gatenavn):
        if self.sjekk_objektforekomst(nvdb_id, versjon):
            objekt = {
                "typeId": nvdb_typeid,
                "nvdbId": nvdb_id,
                "versjon": versjon,
                "egenskaper": [{
                    'typeId': nvdb_propertyid_gatenavn,
                    'verdi': [gatenavn],
                    'operasjon': "oppdater"
                }]
            }
            self.payload.get('delvisKorriger').get('vegObjekter').append(objekt)

    def post(self):

        r = requests.post(self.url, cookies=self.cookies, data=json.dumps(self.payload), headers=self.headers)

        with open('drit.json', 'w') as debugjson:
            debugjson.write(json.dumps(self.payload))

        print(r.url)
        print(r.status_code)
        print(r.encoding)

        self.uri = r.json()[0].get('src')
        url_list.append(self.uri)

    def start(self):
        if self.uri:
            r = requests.post(self.uri + '/start', cookies=self.cookies)
            print(r.status_code)

    def json(self):
        print(json.dumps(self.payload))

    def poll(self):
        if self.uri:
            r = requests.get(self.uri + '/fremdrift', cookies=self.cookies, headers=self.headers)
            return r.text


def les_navnekorreksjoner(filnavn, config, auth):
    with codecs.open(filnavn, 'r', encoding='utf8') as f:
        i = 0
        korr = Korreksjon(config, auth)
        for line in f:
            try:
                nid, vid, gk, kom, navn = line.strip().split(',', 4)
                korr.add_navne_korreksjon(nid, vid, navn)
                posted = False
            except:
                print("err:", line)
            i = i + 1
            if i % 202 == 0:
                korr.post()
                korr = Korreksjon(config, auth)
                posted = True
        if not posted:
            korr.post()


if __name__ == "__main__":
    args = parser.parse_args()
    cfg = last_config_fil(args.config)

    auth_cookie = login.get_token(cfg.get('auth'), 'terbra')
    t_start = time.time()

    filnavn = args.gatenavnfil

    les_navnekorreksjoner(filnavn, cfg.get('skriv'), auth_cookie)
    with open('jobs.json', 'w') as fp:
        json.dump(url_list, fp)

    t_stop = time.time()
    print("post time: {}".format(t_stop - t_start))
