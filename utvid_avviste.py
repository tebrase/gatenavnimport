import argparse
import pickle
import requests
import re
import json

from config import config
from login import login
from korreksjonssett import korreksjonssett

parser = argparse.ArgumentParser()
parser.add_argument("-config", "-c", required=True)


headers = {'content-type': 'application/json', 'Accept': 'application/json', 'X-Client': 'Gatenavnimport'}




def finn_konfliktobjekter(melding):
	konfliktobjektliste = re.search(r'\(id(.*?)\)',melding).group(1)
	return [int(s) for s in re.findall(r'\b\d+\b', konfliktobjektliste)]



def skriv_feil(endringssett, resultat_objekt):
	if resultat_objekt.get('feil'):
		for f in resultat_objekt.get('feil', []):
			feilkode = f.get('kode')
			if feilkode == "INKONSISTENT_GATENAVN":
				konfliktobjekter = finn_konfliktobjekter(f.get('melding'))
				print(feilkode, resultat_objekt.get('nvdbId'), resultat_objekt.get('versjon'), konfliktobjekter)
			else:
				print(feilkode, resultat_objekt.get('nvdbId'), resultat_objekt.get('versjon'))


def finn_utvidelser(resultat):
	utvidelser = []
	for resultat_objekt in resultat.get('vegobjekter', []):
		for feil in resultat_objekt.get('feil', []):
			feilkode = feil.get('kode')
			if feilkode == "INKONSISTENT_GATENAVN":
				konfliktobjekter = finn_konfliktobjekter(f.get('melding'))
				for ko in konfliktobjekter:
					ko_versjon = hent_versjon(auth_cookie, ko)





if __name__ == '__main__':
	args = parser.parse_args()
	cfg = config.Config(args.config)
	auth_cookie = login.get_token(cfg.get_module('auth'), 'terbra')


	with open("jobs.p", "rb") as infile:
		korreksjonssett = pickle.load(infile)
		korreksjonssett.auth = auth_cookie

		korrigerte_endringssett = []

		for l, es in korreksjonssett.endringssett_liste().items():
			if es.fremdrift == 'AVVIST':
				print(es.uri)
				resultat = korreksjonssett.resultat_fra_skriv(l)
				
				for resultat_objekt in resultat.get('vegobjekter', []):
					skriv_feil(es, resultat_objekt)
					
					
					for feil in resultat_objekt.get('feil', []):
						feilkode = feil.get('kode')
						if feilkode == "TVETYDIG_KOMMUNETILHØRIGHET":					
							korreksjonssett.fjern_objekt_fra_endringssett(l, resultat_objekt)
							if es not in korrigerte_endringssett:
								korrigerte_endringssett.append(es)

						if feilkode == "VEGOBJEKTVERSJON_OVERSKREVET_AV_ANDRE":
							es.fremdrift = "UTFØRT"
		
						if feilkode == "INKONSISTENT_GATENAVN":
							konfliktobjekter = finn_konfliktobjekter(feil.get('melding'))
							korreksjonssett.utvid_korreksjon_med_konfliktobjekter(l, resultat_objekt, konfliktobjekter)
							if es not in korrigerte_endringssett:
								korrigerte_endringssett.append(es)
						'''
						else:
							korreksjonssett.fjern_objekt_fra_endringssett(l, resultat_objekt)
							if es not in korrigerte_endringssett:
								korrigerte_endringssett.append(es)
						'''	

		for es in korrigerte_endringssett:
			print("Restarter: ", es.key)
			print(es.skriv_korreksjoner())
			korreksjonssett.post(es)
			korreksjonssett.start(es)
		korreksjonssett.store()

