import datetime
import requests
from bs4 import BeautifulSoup as bs


def ismart_crawler(user_id, password):

    LOGIN_INFO = {
        'userId': user_id,
        'password': password
    }

    with requests.Session() as sess:

        login_req = sess.post(
            'https://pccs.kepco.co.kr/iSmart/cm/login.do', data=LOGIN_INFO)
        print(login_req.status_code)

        first_page = sess.get(
            'https://pccs.kepco.co.kr/iSmart/pccs/usage/getGlobalUsageStats.do?year=2019&month=12&day=12')
        print(first_page.text)
        # soup = bs(html, 'html.parser')
        # data = soup.select(
        #     '# printArea > div:nth-child(6) > table > tbody > tr:nth-child(3) > td:nth-child(1)')

        # print(data)

        sess.close()


print(datetime.datetime.today().replace(
    hour=0, minute=0, second=0, microsecond=0))
