import requests
import datetime
import json


class Korreksjon:
    def __init__(self, config, auth, kommune, date='', datakatalogversjon="2.10", typeid=538, propertyid=4589):
        self.payload = {
            'delvisKorriger': {
                'vegObjekter': []
            },
            'effektDato': date or datetime.datetime.now().date().isoformat(),
            'datakatalogversjon': datakatalogversjon
        }
        self.headers = {'content-type': 'application/json', 'Accept': 'application/json', 'X-Client': 'Gatenavnimport'}

        self.cookies = auth
        self.nvdb_type_id = typeid
        self.nvdb_property_id = propertyid
        self.url = config.get('skriv_url')
        self.les = config.get('les_template')
        self.fremdrift = None
        self.uri = None
        self.kommune_nr = kommune
        print("Oppretter korreksjoner for {}".format(kommune))

    def sjekk_objektforekomst(self, nvdb_id, versjon):
        lurl = self.les.format(self.nvdb_type_id, nvdb_id, versjon)
        tr = requests.get(lurl, cookies=self.cookies)
        print(tr.status_code, lurl)
        return tr.status_code == 200

    def add_navne_korreksjon(self, nvdb_id, versjon, gatenavn):
        if self.sjekk_objektforekomst(nvdb_id, versjon):
            objekt = {
                "typeId": self.nvdb_type_id,
                "nvdbId": nvdb_id,
                "versjon": versjon,
                "egenskaper": [{
                    'typeId': self.nvdb_property_id,
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
        if r.status_code == 201:
            self.uri = r.json()[0].get('src')
            self.fremdrift = "POSTED"

    def start(self):
        if self.uri:
            r = requests.post(self.uri + '/start', cookies=self.cookies)
            if r.status_code == 201:
                self.fremdrift = "STARTED"

    def json(self):
        print(json.dumps(self.payload))

    def poll(self):
        if self.uri:
            r = requests.get(self.uri + '/fremdrift', cookies=self.cookies, headers=self.headers)
            self.fremdrift == r.text

    def skriv(self):
        print(self.kommune_nr, len(self.payload.get('delvisKorriger').get('vegObjekter')), self.fremdrift)