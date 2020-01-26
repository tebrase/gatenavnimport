import requests
import datetime
import json

from korreksjonssett import korreksjon


class Endringssett:
    def __init__(self, key, readtimestamp, datakatalogversjon="2.18"):
        
        self.fremdrift = None
        self.uri = None
        self.key = key
        self.readtimestamp = readtimestamp
        self.korreksjoner = []
        self.datakatalogversjon = datakatalogversjon

        print("Oppretter endringssett for {}".format(key))


    def lag_payload(self):
        payload_objekter = []
        for korreksjonsobjekt in self.korreksjoner:
            payload_objekt = {
                "typeId": korreksjonsobjekt.nvdb_type_id,
                "nvdbId": korreksjonsobjekt.nvdb_id,
                "versjon": korreksjonsobjekt.versjon,
                "overskriv": "JA",
                "validering": {
                    "lestFraNvdb": self.readtimestamp 
                },
                "egenskaper": [{
                    'typeId': korreksjonsobjekt.nvdb_property_id,
                    'verdi': [korreksjonsobjekt.verdi],
                    'operasjon': "oppdater"
                }]
            }
            payload_objekter.append(payload_objekt)

        payload = {
            'delvisOppdater': {
                'vegobjekter': payload_objekter
            },
            'datakatalogversjon': self.datakatalogversjon
        }


        return payload


    def add_korreksjon(self, nvdb_type_id, nvdb_id, versjon, nvdb_property_type, verdi):
        if not self.exists(nvdb_id, versjon):
            self.korreksjoner.append(korreksjon.Korreksjon(nvdb_type_id, nvdb_id, versjon, nvdb_property_type, verdi))
            return True
        else:
            return False


    def fjern_korreksjon(self, nvdb_id, versjon):
        for ko in self.korreksjoner:
            if ko.nvdb_id == str(nvdb_id) and ko.versjon == str(versjon): 
                self.korreksjoner.remove(ko)
                return True
        return False

    def skriv_korreksjoner(self):
        for ko in self.korreksjoner:
            print(ko.nvdb_id, ko.versjon, ko.verdi)



    def exists(self, nvdb_id, versjon):
        for ko in self.korreksjoner:
            if ko.nvdb_id == nvdb_id and ko.versjon == versjon:
                return True
        return False


    def les_korreksjonsverdi(self, nvdb_id, versjon):
        for ko in self.korreksjoner:
            if ko.nvdb_id == str(nvdb_id) and ko.versjon == str(versjon):
                return ko.verdi
        return None

    def skriv(self):
        print(self.key, self.uri, self.fremdrift)

    def json(self):
        print(json.dumps(self.lag_payload()))