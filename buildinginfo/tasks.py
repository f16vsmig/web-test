'''tasks for buildinginfo app'''
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.db import connection
from django.db.models import Sum
from django.utils import timezone

from celery import shared_task, current_app, Task
from benchmark.celery import app

from .models import Ismart, Building, WeatherStation, Weather, Analysis
from scheduler.models import Event

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import os
import datetime
import numpy as np

from sklearn.cluster import KMeans
from sklearn import linear_model
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.model_selection import train_test_split
import pandas as pd


### postgresql 접속 커서 ###
cursor = connection.cursor()


def login_check(ismart_id, ismart_pw):
    '''ismart id verification'''
    chromedriver_path_ = "%s/chromedriver" % (os.path.dirname(__file__))
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('headless')
    driver = webdriver.Chrome(
        executable_path=chromedriver_path_, chrome_options=chrome_options)
    driver.implicitly_wait(30)
    driver.get('https://pccs.kepco.co.kr/iSmart/')
    driver.switch_to.frame('topFrame')
    try:
        driver.find_element_by_name('userId').send_keys(ismart_id)
        driver.find_element_by_name('password').send_keys(ismart_pw)
        driver.find_element_by_xpath(
            '//*[@id="contents_main"]/div/form/div[1]/div[2]/input').click()
        driver.find_element_by_xpath('//*[@id="gnb"]/ul/li[3]/a').click()
        driver.get(
            'https://pccs.kepco.co.kr/iSmart/pccs/usage/getGlobalUsageStats.do')
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        check = soup.find_all(class_='user_infor')
        driver.quit()
        if check is not None:
            return True

    except:
        print("아이스마트 계정이 유효하지 않습니다.")
        return False


class IsmartCrawlerTask(Task):

    # name = 'ismart_crawler'

    def get_date_list(self):
        ''' 데이터 리스트를 반환한다. '''

        existing_date_list = Ismart.objects.filter(building__ismart_id=self.ismart_id).values_list(
            'datetime', flat=True).order_by('datetime')
        existing_date_list = list(set(existing_date_list))
        print(type(self.start_day), type(self.end_day))
        days = (self.end_day - self.start_day).days
        dt_list = []
        for i in range(days + 1):
            dt_ = self.start_day + datetime.timedelta(i, 0, 0)
            if dt_ in existing_date_list:
                pass
            else:
                dt_list.append(dt_)

        return dt_list

    def run(self, ismart_id, ismart_pw, start_day, end_day):
        self.ismart_id = str(ismart_id)
        ismart_pw = str(ismart_pw)
        self.start_day = datetime.datetime.strptime(
            start_day, '%Y-%m-%d') or datetime.datetime.today() - datetime.timedelta(-1, 0, 0)
        # self.start_day = start_day.replace(hour=0, minute=0, second=0, microsecond=0)
        self.end_day = datetime.datetime.strptime(
            end_day, '%Y-%m-%d') or datetime.datetime.today()
        # self.end_day = end_day.replace(hour=0, minute=0, second=0, microsecond=0)
        date_list = self.get_date_list()
        building = Building.objects.get(ismart_id=ismart_id)

        if len(date_list) > 0:

            file_path_chromedriver = '{}/chromedriver'.format(
                os.path.dirname(__file__))
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            driver = webdriver.Chrome(
                executable_path=file_path_chromedriver, chrome_options=options)
            driver.implicitly_wait(30)
            driver.get('https://pccs.kepco.co.kr/iSmart/')
            driver.switch_to.frame('topFrame')
            driver.find_element_by_name('userId').send_keys(self.ismart_id)
            driver.find_element_by_name('password').send_keys(ismart_pw)
            driver.find_element_by_xpath(
                '//*[@id="contents_main"]/div/form/div[1]/div[2]/input').click()
            driver.find_element_by_xpath('//*[@id="gnb"]/ul/li[3]/a').click()
            for i in range(len(date_list)):
                driver.get('https://pccs.kepco.co.kr/iSmart/pccs/usage/getGlobalUsageStats.do?year=%s&month=%s&day=%s'
                           % (str(date_list[i].year), str(date_list[i].month).rjust(2, '0'), str(date_list[i].day).rjust(2, '0'))
                           )
                driver.implicitly_wait(3)
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                table = soup.find_all(class_='basic_table')
                print('\r', '%d-%d-%d...scraping...' %
                      (date_list[i].year, date_list[i].month, date_list[i].day))
                data = []
                for tr in table[0].find_all('td'):
                    tds = tr.text
                    if tds == '-':
                        tds = 0
                        data.append(tds)
                    else:
                        tds = str(tds)
                        tds = tds.replace(',', '')
                        data.append(tds)
                for tr in table[1].find_all('td'):
                    tds = tr.text
                    if tds == '-':
                        tds = 0
                        data.append(tds)
                    else:
                        tds = str(tds)
                        tds = tds.replace(',', '')
                        data.append(tds)
                data = np.array(data, dtype=object).reshape(24, 8)
                data = np.insert(data, 0, date_list[i], axis=1)

                for j in range(0, 24):
                    yy = data[j][0].year
                    mm = data[j][0].month
                    dd = data[j][0].day
                    hh = int(data[j][1])
                    datetime_ = datetime.datetime(
                        yy, mm, dd, hh-1)+datetime.timedelta(hours=1)
                    kWh = data[j][2]
                    kW_peak = data[j][3]
                    kVarh_lag = data[j][4]
                    kVarh_lead = data[j][5]
                    tCO2 = data[j][6]
                    pf_lag = data[j][7]
                    pf_lead = data[j][8]
                    Ismart.objects.update_or_create(building=building, datetime=datetime_,
                                                    defaults={
                                                        'kWh': kWh,
                                                        'kW_peak': kW_peak,
                                                        'kVarh_lag': kVarh_lag,
                                                        'kVarh_lead': kVarh_lead,
                                                        'tCO2': tCO2,
                                                        'pf_lag': pf_lag,
                                                        'pf_lead': pf_lead,
                                                    }
                                                    )

            driver.quit()
            return print('데이터 수집이 완료되었습니다.')

        else:
            return print('수집할 데이터가 없습니다.')


IsmartCrawlerTask = app.register_task(IsmartCrawlerTask())


@shared_task
def weather_file_upload(csv):
    ''''''
    for row in csv:
        Weather.objects.update_or_create(
            weather_station=WeatherStation.objects.get(station_id=row[0]),
            datetime=datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M"),
            defaults={
                'temp': (None if row[2] == '' else float(row[2])),
                'rain': (None if row[3] == '' else float(row[3])),
                'wind': (None if row[4] == '' else float(row[4])),
                'wind_direction': (None if row[5] == '' else int(row[5])),
                'humidity': (None if row[6] == '' else int(row[6])),
                'vapor_pressure': (None if row[7] == '' else float(row[7])),
                'dewpoint': (None if row[8] == '' else float(row[8])),
                'field_elecation_pressure': (None if row[9] == '' else float(row[9])),
                'sealevel_pressure': (None if row[10] == '' else float(row[10])),
                'daylight_hours': (None if row[11] == '' else float(row[11])),
                'irradiation_amount': (None if row[12] == '' else float(row[12])),
                'snowfall_amount': (None if row[13] == '' else float(row[13])),
                'snowfall_3h': (None if row[14] == '' else float(row[14])),
                'cloud_total': (None if row[15] == '' else int(row[15])),
                'cloud_lower': (None if row[16] == '' else int(row[16])),
                'cloud_shape': str(row[17]),
                'cloud_ft': (None if row[18] == '' else int(row[18])),
                'visibility': (None if row[19] == '' else int(row[19])),
                'WMO_code': (None if row[20] == '' else int(row[20])),
                'phenomenon_no': (None if row[21] == '' else int(row[21])),
                'temp_surfice': (None if row[22] == '' else float(row[22])),
                'temp_under_5cm': (None if row[23] == '' else float(row[23])),
                'temp_under_10cm': (None if row[24] == '' else float(row[24])),
                'temp_under_20cm': (None if row[25] == '' else float(row[25])),
                'temp_under_30cm': (None if row[26] == '' else float(row[26])),
            }
        )
        print('{}번행 저장 완료'.format(row[1]), end='\r')


class EnergyAssessment(Task):

    def get_dataframe(self, building_pk):
        query = f'''
            SELECT \
                DATE(buildinginfo_ismart.datetime - interval '1' hour) AS date, \
                SUM(buildinginfo_ismart."kWh") AS "kWh", \
                ROUND(AVG(buildinginfo_weather.temp)::numeric, 2) AS temp \
            FROM \
                buildinginfo_ismart, buildinginfo_weather \
            WHERE \
                (buildinginfo_ismart.datetime=buildinginfo_weather.datetime) AND (buildinginfo_ismart.building_id={building_pk}) \
            GROUP BY \
                date \
            ORDER BY \
                date ASC \
            '''
        df = pd.read_sql_query(query, connection)
        print(df)
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        # df[['date']] = df[['date']].apply(pd.to_datetime)
        df['month'] = df['date'].dt.month
        df = df[df['kWh'] > 0]
        return df

    def get_first_dataframe(self, dataframe):
        df = dataframe

        temp_min = min(df['temp'])
        temp_max = max(df['temp'])
        times = 20
        temp_var = (temp_max - temp_min) / times

        df_clustered_by_temp = pd.DataFrame()
        for i in range(times):
            df_batch = df[(df['temp'] >= (temp_min+temp_var*i))
                          & (df['temp'] < (temp_min+temp_var*(i+1)))]
            df_batch = df_batch.reset_index()
            feature = df_batch[['month', 'kWh']]
            model = KMeans(n_clusters=2)
            model.fit(feature)

            predict = pd.DataFrame(model.predict(feature))
            predict.columns = ['predict']
            result = pd.concat([df_batch, predict], axis=1)

            centers = pd.DataFrame(
                model.cluster_centers_, columns=['month', 'kWh'])
            centers.loc[:, 'predict'] = list(range(0, len(centers)))
            centers = centers.sort_values(['kWh'], ascending=True)
            centers.loc[:, 'load'] = list(range(1, len(centers)+1))
            centers = centers.loc[:, 'predict':]

            result = pd.merge(result, centers, on='predict', how='left')
            result = result.set_index('index')
            df_clustered_by_temp = pd.concat([df_clustered_by_temp, result])

        df_clustered_by_temp = df_clustered_by_temp.sort_index()
        df_clustered_by_temp['workingday'] = df_clustered_by_temp.apply(
            lambda x: 1 if x.load >= 2 else 0, axis=1)
        df_clustered_by_temp = df_clustered_by_temp.drop(['predict'], axis=1)
        df_clustered_by_temp = df_clustered_by_temp.drop(['load'], axis=1)

        # workingday_line, holiday_line 계산
        workingday_line_1 = round(df_clustered_by_temp[df_clustered_by_temp['workingday'] == 1].describe()[
                                  'kWh'][1] - df_clustered_by_temp[df_clustered_by_temp['workingday'] == 1].describe()['kWh'][2]*1.5, 2)
        workingday_line_2 = round(
            min(df_clustered_by_temp[df_clustered_by_temp['workingday'] == 1]['kWh']), 2)
        workingday_line = max(workingday_line_1, workingday_line_2)
        self.workingday_line = workingday_line
        self.baseload_workingday = workingday_line

        holiday_line_1 = round(df_clustered_by_temp[df_clustered_by_temp['workingday'] == 0].describe()[
                               'kWh'][1] - df_clustered_by_temp[df_clustered_by_temp['workingday'] == 0].describe()['kWh'][2]*1.5, 2)
        holiday_line_2 = round(
            min(df_clustered_by_temp[df_clustered_by_temp['workingday'] == 0]['kWh']), 2)
        holiday_line = max(holiday_line_1, holiday_line_2)
        self.holiday_line = holiday_line
        self.baseload_holiday = holiday_line

        data_ss = df_clustered_by_temp[(df_clustered_by_temp['kWh'] < workingday_line*1.1) & (
            df_clustered_by_temp['month'] >= 4) & (df_clustered_by_temp['month'] <= 11)]
        spring_start = min(data_ss['date'])
        spring_end = max(data_ss[(data_ss['month'] >= 4)
                                 & (data_ss['month'] <= 6)]['date'])
        autumn_start = min(
            data_ss[(data_ss['month'] >= 9) & (data_ss['month'] <= 11)]['date'])
        autumn_end = max(data_ss['date'])

        # 2차 환절기 분류
        dataset_spring = df_clustered_by_temp[(df_clustered_by_temp['date'] >= spring_start) & (
            df_clustered_by_temp['date'] <= spring_end) & (df_clustered_by_temp['kWh'] < workingday_line*1.5)]
        dataset_autumn = df_clustered_by_temp[(df_clustered_by_temp['date'] >= autumn_start) & (
            df_clustered_by_temp['date'] <= autumn_end) & (df_clustered_by_temp['kWh'] < workingday_line*1.5)]
        df_ss = pd.concat([dataset_spring, dataset_autumn])

        df_clustered_month = pd.DataFrame()
        temp_min = min(df_ss['temp'])
        temp_max = max(df_ss['temp'])
        times = 5
        temp_var = (temp_max - temp_min)/times

        for i in range(times):

            df_batch = df_ss[(df_ss['temp'] >= (temp_min+temp_var*i))
                             & (df_ss['temp'] < (temp_min+temp_var*(i+1)))]
            df_batch = df_batch.reset_index()
            feature = df_batch[['month', 'kWh']]

            model = KMeans(n_clusters=2)

            model.fit(feature)
            predict = pd.DataFrame(model.predict(feature))
            predict.columns = ['predict']
            result = pd.concat([df_batch, predict], axis=1)

            centers = pd.DataFrame(
                model.cluster_centers_, columns=['month', 'kWh'])
            centers.loc[:, 'predict'] = list(range(0, len(centers)))
            centers = centers.sort_values(['kWh'], ascending=True)
            centers.loc[:, 'load'] = list(range(1, len(centers)+1))
            centers = centers.loc[:, 'predict':]

            result = pd.merge(result, centers, on='predict', how='left')
            result = result.set_index('index')
            df_clustered_month = pd.concat([df_clustered_month, result])

        df_clustered_month = df_clustered_month.sort_index()

        df_clustered_month['workingday_ss'] = df_clustered_month.apply(
            lambda x: 1 if x.load >= 2 else 0, axis=1)

        df_clustered_month = df_clustered_month[['date', 'workingday_ss']]

        df_temp = pd.merge(df_clustered_by_temp,
                           df_clustered_month, on='date', how='left')
        df_temp['workingday'] = df_temp.apply(
            lambda x: 1 if x.workingday_ss == 1 else x.workingday, axis=1)
        df_temp = df_temp.drop(['workingday_ss'], axis=1)
        self.df_clustered_month = df_clustered_month
        return df_temp

    def get_second_dataframe(self, dataframe):
        df_q = dataframe
        df_date = pd.DataFrame()
        batch_size = 14

        for i in range(0, round(len(df_q)/batch_size)+1):

            df_batch = df_q[i*batch_size:(i+1)*batch_size]
            df_batch = df_batch.reset_index()
            feature = df_batch[['month', 'kWh']]

            model = KMeans(n_clusters=2)

            if len(df_batch) == batch_size:

                model.fit(feature)
                predict = pd.DataFrame(model.predict(feature))
                predict.columns = ['predict']
                result = pd.concat([df_batch, predict], axis=1)

                centers = pd.DataFrame(
                    model.cluster_centers_, columns=['month', 'kWh'])
                centers.loc[:, 'predict'] = list(range(0, len(centers)))
                centers = centers.sort_values(['kWh'], ascending=True)
                centers.loc[:, 'load'] = list(range(1, len(centers)+1))
                centers = centers.loc[:, 'predict':]

                result = pd.merge(result, centers, on='predict', how='left')
                result = result.set_index('index')
                df_date = pd.concat([df_date, result])

            else:

                df_batch = df_q[(i-1)*batch_size:(i+1)*batch_size]
                df_batch = df_batch.reset_index()
                feature = df_batch[['month', 'kWh']]

                model.fit(feature)
                predict = pd.DataFrame(model.predict(feature))
                predict.columns = ['predict']
                result = pd.concat([df_batch, predict], axis=1)

                centers = pd.DataFrame(
                    model.cluster_centers_, columns=['month', 'kWh'])
                centers.loc[:, 'predict'] = list(range(0, len(centers)))
                centers = centers.sort_values(['kWh'], ascending=True)
                centers.loc[:, 'load'] = list(range(1, len(centers)+1))
                centers = centers.loc[:, 'predict':]

                result = pd.merge(result, centers, on='predict', how='left')
                result = result.set_index('index')
                result = result[batch_size:]
                df_date = pd.concat([df_date, result])

        df_date['workingday'] = df_date.apply(
            lambda x: 1 if x.load >= 2 else 0, axis=1)

        # 2차 환절기 분류
        df_date = pd.merge(df_date, self.df_clustered_month,
                           on='date', how='left')
        df_date['workingday'] = df_date.apply(
            lambda x: 1 if x.workingday_ss == 1 else x.workingday, axis=1)
        df_date = df_date.drop(['workingday_ss'], axis=1)
        return df_date

    def select_dataframe(self, first_dataframe, second_dataframe):
        # Step1-3. 평일/휴일 선택된 2가지 케이스 중 휴일이 더 적은 데이터 선택
        df_selected = first_dataframe if len(first_dataframe[first_dataframe['workingday'] == 0]) < len(
            first_dataframe[first_dataframe['workingday'] == 0]) else second_dataframe

        return df_selected

    def add_season_column(self, dataframe):

        # Step2. 하절기와 동절기를 구분한다.

        # Step2-1. 환절기 일자 계산
        workingday_line_1 = round(dataframe[dataframe['workingday'] == 1].describe()[
                                  'kWh'][1] - dataframe[dataframe['workingday'] == 1].describe()['kWh'][2]*1.5, 2)
        workingday_line_2 = round(
            min(dataframe[dataframe['workingday'] == 1]['kWh']), 2)
        workingday_line = max(workingday_line_1, workingday_line_2)

        holiday_line_1 = round(dataframe[dataframe['workingday'] == 0].describe()[
                               'kWh'][1] - dataframe[dataframe['workingday'] == 0].describe()['kWh'][2]*1.5, 2)
        holiday_line_2 = round(
            min(dataframe[dataframe['workingday'] == 0]['kWh']), 2)
        holiday_line = max(holiday_line_1, holiday_line_2)

        data_ss = dataframe[(dataframe['kWh'] < workingday_line*1.1)
                            & (dataframe['month'] >= 4) & (dataframe['month'] <= 11)]
        spring_start = min(data_ss['date'])
        spring_end = max(data_ss[(data_ss['month'] >= 4)
                                 & (data_ss['month'] <= 6)]['date'])
        autumn_start = min(
            data_ss[(data_ss['month'] >= 9) & (data_ss['month'] <= 11)]['date'])
        autumn_end = max(data_ss['date'])

        # balance point 계산

        balance_point = self.get_balance_point(dataframe)

        dataframe['season'] = dataframe.apply(lambda x: 2 if (x.date >= spring_start) & (
            x.date <= autumn_end) & (x.temp >= balance_point) else 1, axis=1)

        return dataframe

    def add_energy_breakdown_columns(self, dataframe):
        # baseload, cooling_load, heating_load 계산
        dataframe['baseload'] = dataframe.apply(
            lambda x: self.workingday_line if x.workingday == 1 else self.holiday_line, axis=1)
        dataframe['baseload'] = dataframe.apply(
            lambda x: x.baseload if x.kWh > x.baseload else x.kWh, axis=1)

        dataframe['cooling_load'] = dataframe.apply(
            lambda x: x.kWh-x.baseload if (x.season == 2) & (x.kWh > x.baseload) else 0, axis=1)
        dataframe['heating_load'] = dataframe.apply(
            lambda x: x.kWh - x.baseload if (x.cooling_load == 0) & (x.kWh > x.baseload) else 0, axis=1)

        return dataframe

    def prepare_dataframe(self, building_pk):
        dataframe = self.get_dataframe(building_pk)
        first = self.get_first_dataframe(dataframe)
        second = self.get_second_dataframe(dataframe)
        selected = self.select_dataframe(first, second)
        selected = self.add_season_column(selected)
        selected = self.add_energy_breakdown_columns(selected)

        return selected

    def get_cooling_coef(self, dataframe):
        # data 준비
        reg_data = dataframe[(dataframe['workingday'] == 1) & (dataframe['season'] == 2) & (
            dataframe['temp'] >= min(self.balance_point+10, self.balance_point*1.5, 23))]
        reg_data = reg_data[['kWh', 'temp']]

        # outlier 제거

        feature = reg_data.reset_index()
        feature = feature[['kWh', 'temp']]

        clf = IsolationForest(max_samples=20, random_state=1)
        clf.fit(feature)
        y_pred = clf.predict(feature)

        out = pd.DataFrame(y_pred, columns=['outlier'], dtype='float')
        result = pd.concat([reg_data.reset_index(drop=True), out], axis=1)

        reg_data = result[result['outlier'] == 1]
        reg_data = reg_data.drop(['outlier'], axis=1)

        # 냉방계수 계산
        x_train = reg_data.drop('kWh', axis=1)
        y_train = reg_data['kWh']

        reg = linear_model.LinearRegression()
        reg.fit(x_train, y_train)
        cooling_coef = reg.coef_[0]
        return cooling_coef

    def get_heating_coef(self, dataframe):

        # heating coefficient 구하기

        # data 준비
        reg_data = dataframe[(dataframe['workingday'] == 1) & (dataframe['season'] == 1) & (
            dataframe['temp'] <= max(self.balance_point-10, self.balance_point/2, 0))]
        reg_data = reg_data[['kWh', 'temp']]

        # outlier 제거

        feature = reg_data.reset_index()
        feature = feature[['kWh', 'temp']]

        clf = IsolationForest(max_samples=20, random_state=1)
        clf.fit(feature)
        y_pred = clf.predict(feature)

        out = pd.DataFrame(y_pred, columns=['outlier'], dtype='float')
        result = pd.concat([reg_data.reset_index(drop=True), out], axis=1)

        reg_data = result[result['outlier'] == 1]
        reg_data = reg_data.drop(['outlier'], axis=1)

        # 난방계수 계산
        x_train = reg_data.drop('kWh', axis=1)
        y_train = reg_data['kWh']

        reg = linear_model.LinearRegression()
        reg.fit(x_train, y_train)
        heating_coef = abs(reg.coef_[0])
        return heating_coef

    def get_total_baseload(self, dataframe):
        baseload = sum(dataframe['baseload'])
        return baseload

    def get_total_cooling_load(self, dataframe):
        cooling_load = sum(dataframe['cooling_load'])
        return cooling_load

    def get_total_heating_load(self, dataframe):
        heating_load = sum(dataframe['heating_load'])
        return heating_load

    def get_saving_potential(self, dataframe):

        train, test = train_test_split(
            dataframe, test_size=0.3, random_state=1)

        X_train = train.drop(['date', 'kWh'], axis=1)
        Y_train = train['kWh']

        X_test = test.drop(['date', 'kWh'], axis=1)
        Y_test = test['kWh']

        regressor = RandomForestRegressor(
            random_state=None,
            n_estimators=300,
            max_depth=None,
            max_features='auto',
            min_samples_leaf=1,
            min_samples_split=2,
            bootstrap=True
        )
        regressor.fit(X_train, Y_train)
        Y_pred = regressor.predict(X_test)

        df_hist = pd.DataFrame(Y_test.reset_index(drop=True))
        df_hist['BL'] = pd.Series(Y_pred)
        df_hist['gap'] = df_hist['kWh'] - df_hist['BL']
        df_hist['gap_ratio'] = df_hist['gap'] / df_hist['BL']

        df_sav = df_hist[df_hist['gap_ratio'] > 0.0]
        saving_potential = df_sav.gap.sum()/df_hist.BL.sum()

        return saving_potential

    def get_balance_point(self, dataframe):
        df_seleted_workingday = dataframe[dataframe['workingday'] == 1]
        output = []
        for i in range(5, 20):
            try:
                df_clustered_tempemp = df_seleted_workingday[(
                    df_seleted_workingday['temp'] > i-0.5) & (df_seleted_workingday['temp'] < i+0.5)]
                average = df_clustered_tempemp['kWh'].mean()
                output.append(average)
            except:
                pass
        output = pd.DataFrame(output, columns=['kWh_avg'], index=range(5, 20))
        balance_point = output.sort_values(
            ['kWh_avg'], ascending=True).index[0]
        self.balance_point = balance_point
        return balance_point

    def event_db_update(self, dataframe, building_pk):
        df_holiday = dataframe[dataframe['workingday'] == 0]
        for index, row in df_holiday.iterrows():
            Event.objects.update_or_create(
                building=Building.objects.get(pk=building_pk),
                start_time=row['date'],
                end_time=row['date'] + datetime.timedelta(days=1),
                event='HOL(auto)',
                defaults={
                    'notes': '',
                }
            )

    def get_total_workingday_load(self, dataframe):
        df_workingday = dataframe[dataframe['workingday'] == 1]
        load = sum(df_workingday['kWh'])
        return load

    def get_total_holiday_load(self, dataframe):
        df_holiday = dataframe[dataframe['workingday'] == 0]
        load = sum(df_holiday['kWh'])
        return load

    def run(self, building_pk):
        dataframe = self.prepare_dataframe(building_pk)

        Analysis.objects.update_or_create(
            building=Building.objects.get(pk=building_pk),
            defaults={
                'baseload_workingday': self.baseload_workingday,
                'baseload_holiday': self.baseload_holiday,
                'balance_point': self.get_balance_point(dataframe),
                'saving_potential': self.get_saving_potential(dataframe),
                'registration': timezone.now
            }
        )

        self.event_db_update(dataframe, building_pk)


EnergyAssessment = app.register_task(EnergyAssessment())


def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]


def dictfetchone(cursor):
    return dictfetchall(cursor)[0]


class EnergyStatistics:

    def __init__(self, start=None, end=None):

        if start is None:
            year = datetime.datetime.today().year
            self.start = datetime.datetime(
                year, 1, 1, 1).strftime("%Y-%m-%d %H:00:00")
        elif start is not None:
            self.start = start

        if end is None:
            year = datetime.datetime.today().year
            self.end = datetime.datetime(
                year + 1, 1, 1, 0).strftime("%Y-%m-%d %H:00:00")
        elif end is not None:
            self.end = end

    def base_table(self):

        subquery = f'''
                SELECT
                    t1.building_id AS building_id,
                    t1.datetime AS datetime,
                    t1."kWh" AS kwh,
                    t2.temp AS temp
                FROM
                    buildinginfo_ismart AS t1,
                    buildinginfo_weather AS t2
                WHERE
                    (t1.datetime >= '{self.start}') AND
                    (t1.datetime <= '{self.end}') AND
                    t1.datetime = t2.datetime
                '''

        query = f'''
                SELECT
                    t.building_id AS building_id,
                    DATE(t.datetime - interval '1' hour) AS date,
                    SUM(t.kwh) AS kwh,
                    AVG(t.temp) AS temp
                FROM
                    ({subquery}) AS t
                GROUP BY
                    building_id, date
                ORDER BY
                    date ASC
                '''

        return query

    def holiday_table(self):

        subquery = f'''
                SELECT DISTINCT \
                    t1.building_id AS building_id,
                    t1.datetime AS datetime \
                FROM \
                    buildinginfo_ismart AS t1, scheduler_event AS t2 \
                WHERE \
                    t2.event = 'HOL(auto)' AND \
                    (t1.datetime >= t2.start_time) AND \
                    (t1.datetime < t2.end_time) AND \
                    (t1.datetime >= '{self.start}') AND \
                    (t1.datetime <= '{self.end}')
                '''

        query = f'''
                SELECT DISTINCT \
                    t.building_id AS building_id,
                    DATE(t.datetime) AS date, \
                    0 AS workingday \
                FROM \
                    ({subquery}) AS t\
                GROUP BY
                    building_id, date
                ORDER BY \
                    date ASC \
                '''
        return query

    def join_table(self):
        subquery = self.base_table()
        sub2query = self.holiday_table()
        query = f'''
                SELECT \
                    t1.building_id, t1.date, t1.temp, t1.kwh, \
                    coalesce(t2.workingday, 1) AS workingday \
                FROM \
                    ({subquery}) AS t1 \
                    LEFT OUTER JOIN \
                    ({sub2query}) AS t2 \
                    ON \
                    t1.building_id = t2.building_id AND
                    t1.date = t2.date
                '''
        return query

    def add_degree_days(self):
        subquery = self.join_table()

        query = f'''
                SELECT \
                    t1.building_id AS building_id,
                    t1.date AS date, \
                    t1.kwh AS kwh, \
                    t1.temp AS temp,
                    t1.workingday AS workingday,
                    CASE
                        WHEN (t1.temp > t2.balance_point) THEN t1.temp - t2.balance_point
                        ELSE 0
                    END AS cdd,
                    CASE
                        WHEN (t1.temp <= t2.balance_point) THEN t2.balance_point - t1.temp
                        ELSE 0
                    END AS hdd,
                    CASE \
                        WHEN (t1.workingday = 1) AND (t1.kwh >= t2.baseload_workingday) THEN t2.baseload_workingday \
                        WHEN (t1.workingday = 1) AND (t1.kwh < t2.baseload_workingday) THEN t1.kwh \
                        WHEN (t1.workingday = 0) AND (t1.kwh >= t2.baseload_holiday) THEN t2.baseload_holiday
                        WHEN (t1.workingday = 0) AND (t1.kwh < t2.baseload_holiday) THEN t1.kwh
                        ELSE NULL \
                    END AS baseload
                FROM \
                    ({subquery}) as t1, buildinginfo_analysis as t2 \
                WHERE
                    t1.building_id = t2.building_id
                '''
        return query

    def useage_breakdown(self):
        subquery = self.add_degree_days()
        query = f'''
            SELECT \
                t.building_id AS building_id,
                t.date AS date, \
                t.temp,
                t.cdd AS cdd, \
                t.hdd AS hdd,
                t.cdd + t.hdd AS tdd,
                CASE
                    WHEN (t.kwh > baseload) AND (t.cdd > 0) THEN t.cdd
                    ELSE 0
                END AS cdd_cooling,
                CASE
                    WHEN (t.kwh > baseload) AND (t.hdd > 0) THEN t.hdd
                    ELSE 0
                END AS hdd_heating,
                t.kwh AS kwh, \
                t.baseload AS baseload, \
                CASE
                    WHEN (t.cdd > 0) THEN t.kwh - t.baseload
                    ELSE 0
                END AS cooling,
                CASE
                    WHEN (t.hdd > 0) THEN t.kwh - t.baseload
                    ELSE 0
                END AS heating,
                CASE
                    WHEN (t.workingday = 1) THEN t.kwh
                    ELSE 0
                END AS workingday,
                CASE
                    WHEN (t.workingday = 0) THEN t.kwh
                    ELSE 0
                END AS holiday
            FROM \
                ({subquery}) AS t
            '''
        return query

    def group_by_buildings(self):
        subquery = self.useage_breakdown()
        query = f'''
                SELECT \
                    t.building_id AS building_id,
                    SUM(t.cdd) AS cdd,
                    SUM(t.hdd) AS hdd,
                    SUM(t.tdd) AS tdd,
                    SUM(t.cdd_cooling) AS cdd_cooling,
                    SUM(t.hdd_heating) AS hdd_heating,
                    SUM(t.kwh) AS kwh,
                    SUM(t.baseload) AS baseload,
                    SUM(t.cooling) AS cooling,
                    SUM(t.heating) AS heating, \
                    SUM(t.workingday) AS workingday,
                    SUM(t.holiday) AS holiday
                FROM \
                    ({subquery}) AS t
                GROUP BY
                    building_id
                '''
        return query

    def add_coef(self):
        subquery = self.group_by_buildings()
        query = f'''
                SELECT \
                    *,
                    CASE
                        WHEN t.cdd_cooling = 0 THEN 0
                        ELSE (t.cooling / t.cdd_cooling)
                    END AS cooling_coef,
                    CASE
                        WHEN t.hdd_heating = 0 THEN 0
                        ELSE (t.heating / t.hdd_heating)
                    END AS heating_coef
                FROM \
                    ({subquery}) AS t
                '''
        return query

    def add_buildinginfo(self):
        subquery = self.add_coef()
        query = f'''
                SELECT
                    t1.*,
                    t2.weather_station_id,
                    t4.city,
                    t2.name,
                    t2.owner,
                    t2.use,
                    to_char(t2.construction_date, 'YYYY-MM-DD') AS const_date,
                    t2.total_area::int,
                    t2.rentable_area::int,
                    t2.wall,
                    t2.cooling_source,
                    t2.heating_source,
                    t2.fm,
                    t3.balance_point,
                    t3.saving_potential,
                    to_char(t3.registration, 'YYYY-MM-DD') AS registration
                FROM
                    ({subquery}) AS t1
                    LEFT JOIN
                        buildinginfo_building AS t2
                        ON
                        t1.building_id = t2.id
                    LEFT JOIN
                        buildinginfo_analysis AS t3
                        ON
                        t1.building_id = t3.building_id
                    LEFT JOIN
                        buildinginfo_weatherstation AS t4
                        ON
                        t2.weather_station_id = t4.id
                '''
        return query

    def add_density(self):
        subquery = self.add_buildinginfo()
        query = f'''
                SELECT
                    *,
                    t.kwh / t.total_area AS total_density,
                    t.baseload / t.total_area AS base_density,
                    t.cooling / t.total_area AS cooling_density,
                    t.heating / t.total_area AS heating_density
                FROM
                    ({subquery}) AS t
                '''
        return query

    def order_by_building(self, obj):
        subquery = self.add_density()
        query = f'''
                SELECT
                    *
                FROM
                    ({subquery}) AS t
                ORDER BY
                    t.building_id = {obj.pk} DESC
                '''

        return query

    def get_annual_statistics(self, obj):

        subquery = self.add_density()
        query = f'''
                SELECT
                    *
                FROM
                    ({subquery}) AS t
                WHERE
                    t.building_id = {obj.pk}
                '''
        cursor.execute(query)
        try:
            result = dictfetchone(cursor)
            return result
        except:
            return

    def get_annual_statistics_all(self):

        subquery = self.add_density()
        query = f'''
                SELECT
                    *
                FROM
                    ({subquery}) AS t
                '''
        cursor.execute(query)
        result = dictfetchall(cursor)
        return result

    def get_daily_data(self, obj, x_axis, y_axis):

        subquery = self.useage_breakdown()
        if x_axis == 'date':
            query = f'''
                    SELECT
                        TO_CHAR(t.date, 'YYYY-MM-DD') AS date,
                        EXTRACT(YEAR FROM t.date) AS year,
                        t.{y_axis} AS {y_axis}
                    FROM
                        ({subquery}) AS t
                    WHERE
                        t.building_id = {obj.pk} AND
                        t.{y_axis} > 0
                    ORDER BY
                        t.date ASC
                    '''
        else:
            query = f'''
                    SELECT
                        TO_CHAR(t.date, 'YYYY-MM-DD') AS date,
                        EXTRACT(YEAR FROM t.date) AS year,
                        t.{x_axis},
                        t.{y_axis} AS {y_axis}
                    FROM
                        ({subquery}) AS t
                    WHERE
                        t.building_id = {obj.pk} AND
                        t.{y_axis} > 0
                    ORDER BY
                        t.date ASC
                    '''
        cursor.execute(query)
        result = dictfetchall(cursor)
        return result

    def get_annual_data_for_one(self, obj, x_axis, y_axis):

        subquery = self.order_by_building(obj)

        query = f"SELECT t.{x_axis}"
        for y in y_axis:
            query += f", SUM(t.{y}) AS {y}"
        query += f'''
                FROM
                    ({subquery}) AS t
                WHERE
                    t.building_id = {obj.pk}
                GROUP BY
                    t.{x_axis}
                '''

        cursor.execute(query)
        result = dictfetchone(cursor)
        print(query)
        return result

    def get_annual_data(self, x_axis, y_axis, annotation=None):

        subquery = self.add_density()

        query = f"SELECT t.{x_axis}"

        for y in y_axis:
            query += f", t.{y} AS {y}"

        if annotation is not None:
            query += f", t.{annotation} AS {annotation}"

        query += f'''
                FROM
                    ({subquery}) AS t
                '''

        cursor.execute(query)
        result = dictfetchall(cursor)
        return result

    def get_annual_data_group_by(self, x_axis, y_axis):

        subquery = self.add_density()

        query = f"SELECT t.{x_axis}"

        for y in y_axis:
            if "density" or "coef" in y:
                query += f", AVG(t.{y}) AS {y}"
            else:
                query += f", SUM(t.{y}) AS {y}"

        query += f'''
                FROM
                    ({subquery}) AS t
                GROUP BY
                    t.{x_axis}
                '''

        cursor.execute(query)
        result = dictfetchall(cursor)
        print(query)
        return result

    def get_monthly_data(self, obj, x_axis, y_axis):

        subquery = self.useage_breakdown()

        select = ''
        for y in y_axis:
            select += f"SUM(t.{y}) AS {y},"
        select = select[:-1]

        query = f'''
                SELECT
                    to_char(t.date,'YY-MM') AS date,
                    {select}
                FROM
                    ({subquery}) AS t
                WHERE
                    t.building_id = {obj.pk}
                GROUP BY
                    1
                ORDER BY
                    date
                '''

        cursor.execute(query)
        result = dictfetchall(cursor)
        return result

    def get_pie_data(self, obj, y_axis):

        subquery = self.order_by_building(obj)

        select = ''
        for y in y_axis:
            select += f"SUM(t.{y}) AS {y},"
        select = select[:-1]

        query = f'''
                SELECT
                    {select}
                FROM
                    ({subquery}) AS t
                WHERE
                    t.building_id = {obj.pk}
                '''

        cursor.execute(query)
        result = dictfetchall(cursor)
        return result
