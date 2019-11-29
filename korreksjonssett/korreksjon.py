import requests
import datetime
import json


class Korreksjon:
    def __init__(self, config, auth, label, typeid, propertyid, date='', datakatalogversjon="2.18"):
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
        self.skriv_url = config.get('skriv_url')
        self.les = config.get('les_template')
        self.fremdrift = None
        self.uri = None
        self.label = label
        print("Oppretter korreksjoner for {}".format(label))

    def sjekk_objektforekomst(self, nvdb_id, versjon):
        lurl = self.les.format(self.nvdb_type_id, nvdb_id, versjon)
        tr = requests.get(lurl, cookies=self.cookies)
        print(tr.status_code, lurl)
        return tr.status_code == 200

    def add_korreksjon(self, nvdb_id, versjon, verdi):
        if self.sjekk_objektforekomst(nvdb_id, versjon):
            objekt = {
                "typeId": self.nvdb_type_id,
                "nvdbId": nvdb_id,
                "versjon": versjon,
                "egenskaper": [{
                    'typeId': self.nvdb_property_id,
                    'verdi': [verdi],
                    'operasjon': "oppdater"
                }]
            }
            self.payload.get('delvisKorriger').get('vegObjekter').append(objekt)

    def post(self):
        r = requests.post(self.skriv_url, cookies=self.cookies, data=json.dumps(self.payload), headers=self.headers)
        print("posting: ", self.label, r.status_code, r.url)

        if r.status_code == 201:
            self.uri = r.json()[0].get('src')
            self.fremdrift = "POSTED"
        else:
            self.fremdrift = "FAILED POST"

    def start(self):
        if self.uri and (self.fremdrift in ["POSTED", "IKKE STARTET"]):
            r = requests.post(self.uri + '/start', cookies=self.cookies)
            print("starting: ", self.label, r.status_code)

            if r.status_code == 202:
                self.fremdrift = "STARTED"
            else:
                self.fremdrift = "FAILED START"

    def json(self):
        print(json.dumps(self.payload))

    def poll(self):
        if self.fremdrift not in ["UTFØRT", "AVVIST"]:
            if self.uri:
                r = requests.get(self.uri + '/fremdrift', cookies=self.cookies, headers=self.headers)
                self.fremdrift = r.text.replace('"', '')
                print("polled :", self.label, self.fremdrift)
            else:
                self.fremdrift = "FAILED POLL"

    def skriv(self):
        print(self.label, len(self.payload.get('delvisKorriger').get('vegObjekter')), self.fremdrift)