from Crypto.PublicKey.RSA import construct
from Crypto.Cipher import PKCS1_v1_5
import base64
import json
import time
from my_fake_useragent import UserAgent
from lxml import html
import os

import requests
session = requests.Session()

accounts = [

]

loginpage_url = 'https://steamcommunity.com/login/'
rendercaptcha_url = 'https://steamcommunity.com/login/rendercaptcha/?gid='
refreshcaptcha_url = 'https://steamcommunity.com/login/refreshcaptcha/'
getrsakey_url = 'https://steamcommunity.com/login/getrsakey/'
dologin_url = 'https://steamcommunity.com/login/dologin/'

approved_accounts_abspath = 'abspath/approved-accounts.txt'

for account in accounts:
    USERNAME = account.split(':')[0]
    PASSWORD = account.split(':')[1]

    ua = 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.17 Safari/537.36'
    try:
        ua = UserAgent(os_family='android')
    except Exception as e:
        pass

    headers = {
        'User-Agent': ua.random(),
    }

    session.headers.update(headers)

    tmp = session.post(getrsakey_url, data={'username': USERNAME})
    if tmp.status_code == 200:
        getrsakey_resultdata = json.loads(tmp.content.decode())
        e = int(getrsakey_resultdata['publickey_exp'], 16)
        n = int(getrsakey_resultdata['publickey_mod'], 16)
        pubkey = construct((n, e))

        cipher = PKCS1_v1_5.new(pubkey)
        ciphertext = cipher.encrypt(PASSWORD.encode())

        base64_bytes = base64.b64encode(ciphertext)

        tmp = session.get(loginpage_url)
        if tmp.status_code == 200:
            tmp = session.get(refreshcaptcha_url)
            if tmp.status_code == 200:
                captcha_gid = json.loads(tmp.content.decode())['gid']

                img_data = session.get(rendercaptcha_url + str(captcha_gid))
                img_name = str(captcha_gid) + '.png'
                with open(img_name, 'wb') as f:
                    f.write(img_data.content)
                    f.close()

                captcha_text = input('Enter captcha: ')

                os.remove(img_name)

                login_data = {
                    'password': base64_bytes,
                    'username': USERNAME,
                    'captcha_text': captcha_text,
                    'captchagid': captcha_gid,
                    'emailauth': '',
                    'emailsteamid': '',
                    'loginfriendlyname': '',
                    'remember_login': True,
                    'rsatimestamp': getrsakey_resultdata['timestamp'],
                    'twofactorcode': '',
                }
                tmp = session.post(dologin_url, data=login_data)
                if tmp.status_code == 200:
                    login_resultdata = json.loads(tmp.content.decode())
                    if login_resultdata['success'] == True:
                        print(USERNAME, 'Success')
                        with open(approved_accounts_abspath, 'a') as f:
                            f.write(f'{USERNAME}:{PASSWORD}\n')
                            f.close()
                    else:
                        if login_resultdata['message'] == 'Please verify your humanity by re-entering the characters in the captcha.':
                            print('aboba')
                        else:
                            print(USERNAME, 'Suck cock')
    time.sleep(1)