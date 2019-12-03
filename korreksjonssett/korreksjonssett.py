import pickle

from korreksjonssett import korreksjon


class Korreksjonssett:
    def __init__(self, config, auth, typeid, propertyid, readtimestamp):
        self.korreksjoner = {}
        self.config = config
        self.auth = auth
        self.nvdb_type_id = typeid
        self.nvdb_property_id = propertyid
        self.readtimestamp = readtimestamp

    def legg_til_korreksjon(self, label, nvdbid, versjon, verdi):
        if label not in self.korreksjoner.keys():
            self.korreksjoner[label] = korreksjon.Korreksjon(self.config, self.auth, label, self.nvdb_type_id, self.nvdb_property_id, self.readtimestamp)
        korreksjoner_for_label = self.korreksjoner.get(label)
        korreksjoner_for_label.add_korreksjon(nvdbid, versjon, verdi)

    def list_korreksjoner(self):
        for label, korreksjon in self.korreksjoner.items():
            korreksjon.skriv()

    def post_and_start(self):
        for label, korreksjon in self.korreksjoner.items():
            korreksjon.post()
            korreksjon.start()

    def start(self):
        for label, korreksjon in self.korreksjoner.items():
            korreksjon.start()

    def poll(self, force_start=False):
        for label, korreksjon in self.korreksjoner.items():
            if force_start:
                korreksjon.start()
            korreksjon.poll()

    def list_avviste(self):
        avviste = []
        for l, k in self.korreksjoner.items():
            if k.fremdrift == "AVVIST":
                avviste.append(k.uri)
        return avviste

    def store(self, filename="jobs.p"):
        with open(filename, "wb") as outfile:
            pickle.dump(self, outfile)