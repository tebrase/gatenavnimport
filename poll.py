import argparse
import pickle

from config import config
from login import login
from korreksjonssett import korreksjonssett, korreksjonssett

parser = argparse.ArgumentParser()
parser.add_argument("-config", "-c", required=True)


if __name__ == '__main__':
	args = parser.parse_args()
	cfg = config.Config(args.config)
	auth_cookie = login.get_token(cfg.get_module('auth'), 'terbra')

	with open("jobs.p", "rb") as infile:
		korreksjonssett = pickle.load(infile)
		korreksjonssett.auth = auth_cookie
		korreksjonssett.poll()
		korreksjonssett.list_endringssett()
		korreksjonssett.store()