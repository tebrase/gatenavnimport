# -*- coding: utf-8 -*-

import argparse
import codecs
import traceback

from config import config
from korreksjonssett import korreksjonssett, endringssett
from login import login

# nvdb_id, versjon, gatekode, kommune, navn
# 2099991,1,1001,0536,Hasselvegen
# 2099992,1,1002,0536,Klinkenbergvegen


parser = argparse.ArgumentParser()
parser.add_argument("-gatenavnfil", "-f", required=True)
parser.add_argument("-config", "-c", required=True)
parser.add_argument("-read_timestamp", "-t", required=True)


nvdb_typeid = 538
nvdb_propertyid_gatenavn = 4589


def les_navnekorreksjoner(filnavn, config, auth, read_timestamp):

    korreksjonssett_per_kommune = korreksjonssett.Korreksjonssett(config, auth, nvdb_typeid, nvdb_propertyid_gatenavn, read_timestamp)

    with codecs.open(filnavn, 'r', encoding='utf8') as f:
        for line in f:
            try:
                nid, vid, gk, kom, navn = line.strip().split(',', 4)
                korreksjonssett_per_kommune.legg_til_korreksjon(kom, nid, vid, navn)
            except Exception as ex:
                print("err:", line.strip())
                traceback.print_exc()
    return korreksjonssett_per_kommune


if __name__ == "__main__":
    args = parser.parse_args()
    cfg = config.Config(args.config)

    auth_cookie = login.get_token(cfg.get_module('auth'), 'terbra')
    filnavn = args.gatenavnfil

    korreksjonssett = les_navnekorreksjoner(filnavn, cfg, auth_cookie, args.read_timestamp)
    korreksjonssett.post_and_start()
    korreksjonssett.list_endringssett()
    korreksjonssett.store()

    # with open('jobs.json', 'w') as fp:
    #    json.dump(url_list, fp)

 