import argparse
import pickle
import requests
import re
import json

from config import config
from login import login
from korreksjonssett import korreksjonssett, korreksjonssett

parser = argparse.ArgumentParser()
parser.add_argument("-config", "-c", required=True)
parser.add_argument("-utensted", "-u", required=True)


headers = {'content-type': 'application/json', 'Accept': 'application/json', 'X-Client': 'Gatenavnimport'}

atest = "https://www.test.vegvesen.no/nvdb/apiskriv/rest/v3/endringssett/6a5330f5-d365-44e3-92b1-4b48460783d3"


def hent_uten_sted(filnavn):
	with open(filnavn) as infile:
		return json.load(infile)

def uten_sted(nvdbid):
	for kommunenummer, gateobjekter in gater_uten_sted.items():
		for gatekode, objekter in gateobjekter.items():
			for o in objekter:
				if o.get('nvdbid') == nvdbid:
					return True
	return False

def heltall_fra_streng(str):
	return [int(s) for s in re.findall(r'\b\d+\b', str)]


def hent_endringssett_resultat(auth, url):
	data = requests.get(url, cookies=auth, headers=headers).json()
	return data.get('status', {}).get('resultat', {})


def hent_dato(auth, nvdbid):
	url = "https://www.test.vegvesen.no/nvdb/api/v3/vegobjekter/538/{}".format(nvdbid)
	data = requests.get(url, cookies=auth, headers=headers).json()
	return data.get('metadata', {}).get('sluttdato', None)

def hent_gatekode_og_navn(auth, nvdbid):
	url = "https://www.test.vegvesen.no/nvdb/api/v3/vegobjekter/538/{}".format(nvdbid)
	data = requests.get(url, cookies=auth, headers=headers).json()
	gatekode = None
	gatenavn = None
	versjon = data.get('metadata', {}).get('versjon')
	egenskaper = data.get('egenskaper', [])
	for e in egenskaper:
		if e.get('navn') == 'Gatenavn':
			gatenavn = e.get('verdi')
		if e.get('navn') == 'Gatekode':
			gatekode = e.get('verdi')

	return gatekode, gatenavn, versjon




def amend(k, nvdbid, versjon, verdi):
	print("legger til", nvdbid, versjon, verdi)
	k.add_korreksjon(nvdbid, versjon, verdi)


if __name__ == '__main__':
	args = parser.parse_args()
	cfg = config.Config(args.config)
	auth_cookie = login.get_token(cfg.get_module('auth'), 'terbra')

	gater_uten_sted = hent_uten_sted(args.utensted)

	with open("jobs.p", "rb") as infile:
		korreksjonssett = pickle.load(infile)
		for l, k in korreksjonssett.korreksjoner.items():
			if k.fremdrift == 'AVVIST' and k.uri == atest:
				print(k.uri)
				a = k.uri
				k.cookies = auth_cookie
				label = l
				resultat = hent_endringssett_resultat(auth_cookie, a)
				vegobjekter = resultat.get('vegobjekter', [])
				objekter_i_endringssett = []
				for vo in vegobjekter:
					objekter_i_endringssett.append(vo.get('nvdbId'))
				for vo in vegobjekter:
					if vo.get('feil'):
						feil = vo.get('feil')
						for f in feil:
							#print(vo.get('nvdbId'), vo.get('versjon'), f.get('kode'), heltall_fra_streng(f.get('melding')))
							#print(vo.get('nvdbId'), ">") #, hent_dato(auth_cookie, vo.get('nvdbId')))

							feilobjekt = vo.get('nvdbId')
							feilversjon = vo.get('versjon')
							feilverdi = k.les_korreksjonsverdi(feilobjekt, feilversjon)
							print(feilobjekt, feilversjon, feilverdi)
							tall = heltall_fra_streng(f.get('melding'))
							#print(tall)
							for nid in tall[1:]:
								if nid not in objekter_i_endringssett:
									mangler_sted = uten_sted(nid)
									gatekode, gatenavn, versjon = hent_gatekode_og_navn(auth_cookie, nid)

									if mangler_sted:
										print(nid, "ugyldig_stedfesting", label, gatekode, gatenavn)
										if atest == a:
											amend(k, nid, versjon, feilverdi)
											print(vo)
									else:
										sluttdato = hent_dato(auth_cookie, nid)
										if sluttdato:
											print(nid, sluttdato, label, gatekode, gatenavn)
											if atest == a:
												amend(k, nid, versjon, feilverdi)
										else:
											print(feilobjekt, "<", nid, "??")


				k.post()
				k.start()
