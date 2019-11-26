# -*- coding: utf-8 -*-
import sys
import json
import requests
import time
import argparse
import yaml
import os

from login import login

parser = argparse.ArgumentParser()
parser.add_argument("-config", "-c", required=True)

job_fil = 'jobs.json'
to_go = []
started = []
done = []
rejected = []

headers = {'content-type': 'application/json', 'Accept': 'application/json', 'X-Client': 'Gatenavnimport'}


def last_config_fil(config_file):
    if config_file:
        if not os.path.exists(config_file):
            log.error("Config file was not found..")
            sys.exit(1)
        try:
            with open(config_file, 'r') as f:
                cfg = yaml.load(f, Loader=yaml.BaseLoader)
        except yaml.scanner.ScannerError as se:
            sys.exit(1)

    return cfg


def les_jobber():
    with open(job_fil) as f:
        return json.load(f, encoding='utf-8')


def start_up(fra, til):
    for j in to_go:
        r = requests.post(j + '/start', cookies=auth, headers=headers)
        sj = {'url': j, 'start_tid': time.time()}
        started.append(sj)


def hent_status(url):
    r = requests.get(url + '/fremdrift', cookies=auth, headers=headers)
    return r.text


def print_status(status):
    sys.stdout.write(u"\r{}".format(status.encode('utf-8')))
    sys.stdout.flush()


def poll():
    global done, rejected
    while len(started) > 0:
        for i, j in enumerate(started):
            status = hent_status(j['url'])
            print_status(u"J:{}, S:{}".format(i, status))
            if status == u'"UTFØRT"':
                j['slutt_tid'] = time.time()
                j['total_tid'] = j['slutt_tid'] - j['start_tid']
                done.append(j)
                started.pop(i)
            if status == u'"AVVIST"':
                j['slutt_tid'] = time.time()
                j['total_tid'] = j['slutt_tid'] - j['start_tid']
                rejected.append(j)
                started.pop(i)


def stats(l, name):
    avg = 0
    for j in l:
        print (j.get('url'))
        print (j.get('total_tid'))
        avg += j.get('total_tid')
    print (u"AVG: {}".format(avg / len(l)))


if __name__ == "__main__":
    args = parser.parse_args()
    cfg = last_config_fil(args.config)
    print ('starting')
    t_start = time.time()
    to_go = les_jobber()
    auth = login.get_token(cfg.get('auth'), 'terbra')
    start_up(0, 0)
    t_started = time.time()
    print ("startup time: {}".format(t_started - t_start))
    poll()
    t_stop = time.time()
    print ("run time: {}".format(t_stop - t_start))
    stats(done, "done")
    #stats(rejected, "rejected")

    with open('rejected.json', 'w') as fp:
        json.dump(rejected, fp)
