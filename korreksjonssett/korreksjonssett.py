import pickle
import requests
import json

from korreksjonssett import endringssett


class Korreksjonssett:
    def __init__(self, config, auth, typeid, propertyid, readtimestamp):
        self.endringssett = {}
        self.config = config
        self.auth = auth
        self.nvdb_type_id = typeid
        self.nvdb_property_id = propertyid
        self.readtimestamp = readtimestamp
        self.headers = {'content-type': 'application/json', 'Accept': 'application/json', 'X-Client': 'Gatenavnimport'}

        self.url_template_lesforskriv = config.get('skriv', 'url_template_lesforskriv')
        self.url_template_lesobjekt = config.get('gate', 'url_template_enkeltgate')
        self.url_skriv = config.get('skriv', 'url_skriv')


    def sjekk_objektforekomst(self, nvdbid, versjon):
        lurl = self.url_template_lesforskriv.format(self.nvdb_type_id, nvdbid, versjon)
        tr = requests.get(lurl, cookies=self.auth)
        print(tr.status_code, lurl)
        return tr.status_code == 200


    def legg_til_korreksjon(self, label, nvdbid, versjon, verdi):
        if self.sjekk_objektforekomst(nvdbid, versjon):
            if label not in self.endringssett.keys():   
                self.endringssett[label] = endringssett.Endringssett(label, self.readtimestamp)
            endringssett_for_label = self.endringssett.get(label)
            endringssett_for_label.add_korreksjon(self.nvdb_type_id, nvdbid, versjon, self.nvdb_property_id, verdi)
        else:
            print(nvdbid, versjon, "finnes ikke i NVDB.")

    def endringssett_liste(self):
        return self.endringssett


    def finn_versjon(self, nvdbid):
        url = self.url_template_lesobjekt.format(nvdbid)
        data = requests.get(url).json()
        versjon = data.get('metadata', {}).get('versjon')
        return versjon


    def utvid_korreksjon_med_konfliktobjekter(self, label, korreksjonsobjekt, konfliktobjekter):
        if not label in self.endringssett.keys():
            print("Finner ikke endringssett for:", label)
            return

        endringssett = self.endringssett.get(label)
        korreksjonsobjekt_nvdbid = korreksjonsobjekt.get('nvdbId')
        korreksjonsobjekt_versjon = korreksjonsobjekt.get('versjon')        
        verdi = endringssett.les_korreksjonsverdi(korreksjonsobjekt_nvdbid, korreksjonsobjekt_versjon)
        if not verdi:
            print("finner ikke verdi for: ", korreksjonsobjekt_nvdbid, korreksjonsobjekt_versjon)
            return

        for ko in konfliktobjekter:
            ko_versjon = self.finn_versjon(ko)
            lagt_til = endringssett.add_korreksjon(self.nvdb_type_id, ko, ko_versjon, self.nvdb_property_id, verdi)
            if lagt_til:
                print("la til: ", ko, "({})".format(ko_versjon))
            endringssett.fremdrift = None


    def fjern_objekt_fra_endringssett(self, label, korreksjonsobjekt):
        print("fjerner", korreksjonsobjekt.get('nvdbId'))
        if not label in self.endringssett.keys():
            print("Finner ikke endringssett for:", label)
            return

        endringssett = self.endringssett.get(label)
        korreksjonsobjekt_nvdbid = korreksjonsobjekt.get('nvdbId')
        korreksjonsobjekt_versjon = korreksjonsobjekt.get('versjon')

        fjernet = endringssett.fjern_korreksjon(korreksjonsobjekt_nvdbid, korreksjonsobjekt_versjon)
        if fjernet:
            print("fjernet: ", korreksjonsobjekt_nvdbid, "({})".format(korreksjonsobjekt_versjon))



    def list_endringssett(self):
        for label, endringssett in self.endringssett.items():
            endringssett.skriv()

    def post_and_start(self):
        for label, endringssett in self.endringssett.items():
            self.post(endringssett)
            self.start(endringssett)


    def post(self, endringssett):
        r = requests.post(self.url_skriv, cookies=self.auth, data=json.dumps(endringssett.lag_payload()), headers=self.headers)
        print("posting: ", endringssett.key, r.status_code)
        if r.status_code == 201:
            endringssett.uri = r.json()[0].get('src')
            endringssett.fremdrift = "POSTED"
        else:
            endringssett.fremdrift = "FAILED POST"
            endringssett.uri = None



    def start(self, endringssett):
        if endringssett.uri and (endringssett.fremdrift in ["POSTED", "FAILED START", "IKKE STARTET"]):
            r = requests.post(endringssett.uri + '/start', cookies=self.auth, headers=self.headers)
            print("starting: ", endringssett.key, r.status_code)

            if r.status_code == 202:
                endringssett.fremdrift = "STARTED"
            else:
                endringssett.fremdrift = "FAILED START"
                print(r.text)


    def poll(self, force_start=False):
        for label, endringssett in self.endringssett.items():
            if force_start:
                self.start()
            if endringssett.fremdrift not in ["UTFØRT", "AVVIST", "UTFØRT_OG_ETTERBEHANDLET", "FAILED_POST"]:
                if endringssett.uri:
                    r = requests.get(endringssett.uri + '/fremdrift', cookies=self.auth, headers=self.headers)
                    endringssett.fremdrift = r.text.replace('"', '')
                    print("polled :", endringssett.key, endringssett.fremdrift)
                else:
                    endringssett.fremdrift = "FAILED POLL"

    def resultat_fra_skriv(self, label):
        url = self.endringssett.get(label, {}).uri
        if url:
            data = requests.get(url, cookies=self.auth, headers=self.headers).json()
            return data.get('status', {}).get('resultat', {})
        return None

    def hent_endringssett_fra_skriv(self, label):
        url = self.endringssett.get(label, {}).uri
        if url:
            data = requests.get(url, cookies=self.auth, headers=self.headers).json()
            return data
        return None



    def list_avviste(self):
        avviste = []
        for l, k in self.endringssett.items():
            if k.fremdrift == "AVVIST":
                avviste.append(k.uri)
        return avviste

    def store(self, filename="jobs.p"):
        with open(filename, "wb") as outfile:
            pickle.dump(self, outfile)

    def finn_label_for_endringssett_uri(self, uri):
        for l, k in self.endringssett.items():
            if k.uri == uri:
                return l
        return None

