# -*- coding: utf-8 -*-

import requests
import getpass
import pickle

headers_simple = {'content-type': 'application/json','Accept': 'application/json'}


def create_cookie(token_name, token):
    return {token_name: token}


def logg_inn(auth_url, user):
    login_url = auth_url + 'autentiser'
    print (login_url)

    inputstring = "pwd for {}: ".format(user)
    p = getpass.getpass(inputstring)

    r = requests.post(login_url, json={'username': user, 'password': p}, headers=headers_simple).json()
    token = r.get('token', None)
    token_name = r.get('tokenname', None)
    auth_state = {
        'username': user,
        'tokenname': token_name,
        'token': token
    }
    pickle.dump(auth_state, open("auth.p", "wb"))
    return create_cookie(token_name, token)


def validate(auth_url, auth_state, user):
    validate_url = auth_url + 'validate'
    stored_username = auth_state.get('username')
    if stored_username != user:
        return False
    stored_token = auth_state.get('token')
    stored_tokenname = auth_state.get('tokenname')
    r = requests.post(validate_url, json={'token':stored_token}, headers=headers_simple).json()
    return r.get('valid', None)    


def get_token(auth_config, user):
    try:
        auth_state = pickle.load(open("auth.p", "rb"))
    except Exception:
        auth_state = None

    auth_url = auth_config.get('login_url')

    if not auth_state:
        return logg_inn(auth_url, user)

    valid_token = validate(auth_url, auth_state, user)

    if valid_token:
        return {auth_state.get('tokenname'): auth_state.get('token')}

    return logg_inn(auth_url, user)