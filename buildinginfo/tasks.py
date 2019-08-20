'''tasks for buildinginfo app'''
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.db import connection

from celery import shared_task

from .models import Ismart, Building, WeatherStation, Weather
from scheduler.models import Event

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import os
import datetime
import numpy as np
import pandas as pd

from django.db import connection




def login_check(ismart_id, ismart_pw):
    '''ismart id verification'''
    chromedriver_path_ = "%s/chromedriver" %(os.path.dirname(__file__))
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('headless')
    driver = webdriver.Chrome(executable_path=chromedriver_path_, chrome_options=chrome_options)
    driver.implicitly_wait(30)
    driver.get('https://pccs.kepco.co.kr/iSmart/')
    driver.switch_to.frame('topFrame')
    try:
        driver.find_element_by_name('userId').send_keys(ismart_id)
        driver.find_element_by_name('password').send_keys(ismart_pw)
        driver.find_element_by_xpath('//*[@id="contents_main"]/div/form/div[1]/div[2]/input').click()
        driver.find_element_by_xpath('//*[@id="gnb"]/ul/li[3]/a').click()
        driver.get('https://pccs.kepco.co.kr/iSmart/pccs/usage/getGlobalUsageStats.do')
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        check = soup.find_all(class_='user_infor')
        driver.quit()
        if check is not None:
            return True

    except ValueError:
        print("아이스마트 계정이 유효하지 않습니다.")
        raise



@shared_task
def ismart_scrap(ismart_id, ismart_pw, start_time, end_time=datetime.datetime.today().strftime('%Y-%m-%d')):
    '''ismart data scrap'''

    start_year, start_month, start_day = (int(x) for x in start_time.split('-'))
    start_date = datetime.datetime(start_year, start_month, start_day)
    end_year, end_month, end_day = (int(x) for x in end_time.split('-'))
    end_date = datetime.datetime(end_year, end_month, end_day)

    days = (end_date-start_date).days
    date = []
    for i in range(days+1):
        date_ = start_date + datetime.timedelta(i,0,0)
        date.append(date_)

    existing_data_date = Ismart.objects.filter(building__ismart_id=ismart_id).values('datetime')
    dt_list = []
    for dt in existing_data_date:
        dt = dt['datetime']
        dt = datetime.datetime(dt.year, dt.month, dt.day)
        if dt in dt_list:
            pass
        else:
            dt_list.append(dt)

    date_list = []
    for j in date:
        if j in dt_list:
            pass
        else:
            date_list.append(j)
    print(date_list)

    if len(date_list) > 0:

        file_path_chromedriver = '{}/chromedriver'.format(os.path.dirname(__file__))
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(executable_path=file_path_chromedriver, chrome_options=options)

        driver.implicitly_wait(30)
        driver.get('https://pccs.kepco.co.kr/iSmart/')
        driver.switch_to.frame('topFrame')
        driver.find_element_by_name('userId').send_keys(str(ismart_id))
        driver.find_element_by_name('password').send_keys(str(ismart_pw))
        driver.find_element_by_xpath('//*[@id="contents_main"]/div/form/div[1]/div[2]/input').click()
        driver.find_element_by_xpath('//*[@id="gnb"]/ul/li[3]/a').click()

        for i in range(len(date_list)):
            driver.get('https://pccs.kepco.co.kr/iSmart/pccs/usage/getGlobalUsageStats.do?year=%s&month=%s&day=%s'\
                       % (str(date_list[i].year), str(date_list[i].month).rjust(2,'0'), str(date_list[i].day).rjust(2,'0'))
                      )
            driver.implicitly_wait(3)
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            table = soup.find_all(class_='basic_table')
            print('\r', '%d-%d-%d...scraping...' % (date_list[i].year, date_list[i].month, date_list[i].day))
            data = []
            for tr in table[0].find_all('td'):
                tds = tr.text
                if tds == '-':
                    tds = 0
                    data.append(tds)
                else :
                    tds = str(tds)
                    tds = tds.replace(',','')
                    data.append(tds)
            for tr in table[1].find_all('td'):
                tds = tr.text
                if tds == '-':
                    tds = 0
                    data.append(tds)
                else :
                    tds = str(tds)
                    tds = tds.replace(',','')
                    data.append(tds)
            data = np.array(data, dtype=object).reshape(24,8)
            data = np.insert(data, 0, date_list[i], axis=1)
            building = Building.objects.get(ismart_id=ismart_id)

            for j in range(0, 24):
                yy=data[j][0].year
                mm=data[j][0].month
                dd=data[j][0].day
                hh=int(data[j][1])
                datetime_ = datetime.datetime(yy, mm, dd, hh-1)+datetime.timedelta(hours=1)
                kWh = data[j][2]
                kW_peak = data[j][3]
                kVarh_lag = data[j][4]
                kVarh_lead = data[j][5]
                tCO2 = data[j][6]
                pf_lag = data[j][7]
                pf_lead = data[j][8]
                Ismart.objects.update_or_create(building=building, datetime=datetime_,
                    defaults = {'kWh' : kWh,
                        'kW_peak' : kW_peak,
                        'kVarh_lag' : kVarh_lag,
                        'kVarh_lead' : kVarh_lead,
                        'tCO2' : tCO2,
                        'pf_lag' : pf_lag,
                        'pf_lead' : pf_lead,
                        })

        driver.quit()
        return print('데이터 수집이 완료되었습니다.')

    else:
        return print('수집할 데이터가 없습니다.')


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


def energy_assessment(building_pk):
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
    df_q = pd.read_sql_query(query, connection)
    df_q[['date']] = df_q[['date']].apply(pd.to_datetime)
    df_q['month'] = df_q['date'].dt.month
    df_q = df_q[df_q['kWh'] > 0]

    from sklearn.cluster import KMeans
    from sklearn import linear_model
    from sklearn.ensemble import IsolationForest

    ### 1. 기온 구간을 쪼갠 후 월/전력량을 feature로 2개 그룹으로 클러스터링

    df_clustered_temp = pd.DataFrame()
    temp_min = min(df_q['temp'])
    temp_max = max(df_q['temp'])
    times = 20
    temp_var = (temp_max - temp_min)/times

    for i in range(times):

        df_batch = df_q[(df_q['temp'] >= (temp_min+temp_var*i)) & (df_q['temp'] < (temp_min+temp_var*(i+1)))]
        df_batch = df_batch.reset_index()

        feature = df_batch[['month', 'kWh']]
        model = KMeans(n_clusters=2)
        model.fit(feature)

        predict = pd.DataFrame(model.predict(feature))
        predict.columns = ['predict']
        result = pd.concat([df_batch, predict], axis=1)

        centers = pd.DataFrame(model.cluster_centers_, columns=['month', 'kWh'])
        centers.loc[:, 'predict'] = list(range(0, len(centers)))
        centers = centers.sort_values(['kWh'], ascending=True)
        centers.loc[:, 'load'] = list(range(1, len(centers)+1))
        centers = centers.loc[:, 'predict':]

        result = pd.merge(result, centers, on='predict', how='left')
        result = result.set_index('index')
        df_clustered_temp = pd.concat([df_clustered_temp, result])

    df_clustered_temp = df_clustered_temp.sort_index()

    df_clustered_temp['workingday'] = df_clustered_temp.apply(lambda x: 1 if x.load >= 2 else 0, axis=1)
    df_clustered_temp = df_clustered_temp.drop(['predict'], axis=1)    
    df_clustered_temp = df_clustered_temp.drop(['load'], axis=1)    

    # workingday_line, holiday_line 계산
    workingday_line_1 = round(df_clustered_temp[df_clustered_temp['workingday'] == 1].describe()['kWh'][1] - df_clustered_temp[df_clustered_temp['workingday'] == 1].describe()['kWh'][2]*1.5, 2)
    workingday_line_2 = round(min(df_clustered_temp[df_clustered_temp['workingday'] == 1]['kWh']), 2)
    workingday_line = max(workingday_line_1, workingday_line_2)

    holiday_line_1 = round(df_clustered_temp[df_clustered_temp['workingday'] == 0].describe()['kWh'][1] - df_clustered_temp[df_clustered_temp['workingday'] == 0].describe()['kWh'][2]*1.5, 2)
    holiday_line_2 = round(min(df_clustered_temp[df_clustered_temp['workingday'] == 0]['kWh']), 2)
    holiday_line = max(holiday_line_1, holiday_line_2)


    data_ss = df_clustered_temp[(df_clustered_temp['kWh'] < workingday_line*1.1) & (df_clustered_temp['month'] >= 4) & (df_clustered_temp['month'] <= 11)]
    spring_start = min(data_ss['date'])
    spring_end = max(data_ss[(data_ss['month'] >= 4) & (data_ss['month'] <= 6)]['date'])
    autumn_start = min(data_ss[(data_ss['month'] >= 9) & (data_ss['month'] <= 11)]['date'])
    autumn_end = max(data_ss['date'])

    # 2차 환절기 분류
    dataset_spring = df_clustered_temp[(df_clustered_temp['date'] >= spring_start) & (df_clustered_temp['date'] <= spring_end) & (df_clustered_temp['kWh'] < workingday_line*1.5)]
    dataset_autumn = df_clustered_temp[(df_clustered_temp['date'] >= autumn_start) & (df_clustered_temp['date'] <= autumn_end) & (df_clustered_temp['kWh'] < workingday_line*1.5)]
    df_ss = pd.concat([dataset_spring, dataset_autumn])

    df_clustered_month = pd.DataFrame()
    temp_min = min(df_ss['temp'])
    temp_max = max(df_ss['temp'])
    times = 5
    temp_var = (temp_max - temp_min)/times


    for i in range(times):

        df_batch = df_ss[(df_ss['temp'] >= (temp_min+temp_var*i)) & (df_ss['temp'] < (temp_min+temp_var*(i+1)))]
        df_batch = df_batch.reset_index()
        feature = df_batch[['month', 'kWh']]

        model = KMeans(n_clusters=2)

        model.fit(feature)
        predict = pd.DataFrame(model.predict(feature))
        predict.columns = ['predict']
        result = pd.concat([df_batch, predict], axis=1)

        centers = pd.DataFrame(model.cluster_centers_, columns=['month', 'kWh'])
        centers.loc[:, 'predict'] = list(range(0, len(centers)))
        centers = centers.sort_values(['kWh'], ascending=True)
        centers.loc[:, 'load'] = list(range(1, len(centers)+1))
        centers = centers.loc[:, 'predict':]

        result = pd.merge(result, centers, on='predict', how='left')
        result = result.set_index('index')
        df_clustered_month = pd.concat([df_clustered_month, result])

    df_clustered_month = df_clustered_month.sort_index()

    df_clustered_month['workingday_ss'] = df_clustered_month.apply(lambda x: 1 if x.load >= 2 else 0, axis=1)

    df_clustered_month = df_clustered_month[['date', 'workingday_ss']]

    df_temp = pd.merge(df_clustered_temp, df_clustered_month, on='date', how='left')
    df_temp['workingday'] = df_temp.apply(lambda x: 1 if x.workingday_ss == 1 else x.workingday, axis=1)
    df_temp = df_temp.drop(['workingday_ss'], axis=1)

    
    ### 2. 2주 단위로 데이터를 쪼갠 후 월/전력량을 feature로 2개 그룹으로 클러스터링
    df_date = pd.DataFrame()
    batch_size = 14

    for i in range(0, round(len(df_q)/batch_size)+1) : 

        df_batch = df_q[i*batch_size:(i+1)*batch_size]
        df_batch = df_batch.reset_index()
        feature = df_batch[['month', 'kWh']]

        model = KMeans(n_clusters=2)

        if len(df_batch) == batch_size:

            model.fit(feature)
            predict = pd.DataFrame(model.predict(feature))
            predict.columns = ['predict']
            result = pd.concat([df_batch, predict], axis=1)

            centers = pd.DataFrame(model.cluster_centers_, columns=['month', 'kWh'])
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

            centers = pd.DataFrame(model.cluster_centers_, columns=['month','kWh'])
            centers.loc[:, 'predict'] = list(range(0, len(centers)))
            centers = centers.sort_values(['kWh'], ascending=True)
            centers.loc[:, 'load'] = list(range(1, len(centers)+1))
            centers = centers.loc[:, 'predict':]

            result = pd.merge(result, centers, on='predict', how='left')
            result = result.set_index('index')
            result = result[batch_size:]
            df_date = pd.concat([df_date, result])


    df_date['workingday'] = df_date.apply(lambda x: 1 if x.load >= 2 else 0, axis=1)

    # 2차 환절기 분류
    df_date = pd.merge(df_date, df_clustered_month, on='date', how='left')
    df_date['workingday'] = df_date.apply(lambda x: 1 if x.workingday_ss == 1 else x.workingday, axis=1)
    df_date = df_date.drop(['workingday_ss'], axis=1)
    



    # Step1-3. 평일/휴일 선택된 2가지 케이스 중 휴일이 더 적은 데이터 선택
    df_seleted = df_temp if len(df_temp[df_temp['workingday'] == 0]) < len(df_temp[df_temp['workingday'] == 0]) else df_date



    # Step2. 하절기와 동절기를 구분한다.

    # Step2-1. 환절기 일자 계산
    workingday_line_1 = round(df_seleted[df_seleted['workingday'] == 1].describe()['kWh'][1] - df_seleted[df_seleted['workingday'] == 1].describe()['kWh'][2]*1.5, 2)
    workingday_line_2 = round(min(df_seleted[df_seleted['workingday'] == 1]['kWh']), 2)
    workingday_line = max(workingday_line_1, workingday_line_2)

    holiday_line_1 = round(df_seleted[df_seleted['workingday'] == 0].describe()['kWh'][1] - df_seleted[df_seleted['workingday'] == 0].describe()['kWh'][2]*1.5, 2)
    holiday_line_2 = round(min(df_seleted[df_seleted['workingday'] == 0]['kWh']), 2)
    holiday_line = max(holiday_line_1, holiday_line_2)

    data_ss = df_seleted[(df_seleted['kWh'] < workingday_line*1.1) & (df_seleted['month'] >= 4) & (df_seleted['month'] <= 11)]
    spring_start = min(data_ss['date'])
    spring_end = max(data_ss[(data_ss['month'] >= 4) & (data_ss['month'] <= 6)]['date'])
    autumn_start = min(data_ss[(data_ss['month'] >= 9) & (data_ss['month'] <= 11)]['date'])
    autumn_end = max(data_ss['date'])



    # balance point 계산

    df_seleted_workingday = df_seleted[df_seleted['workingday'] == 1]

    output = []

    for i in range(5, 20):

        try:
            df_clustered_tempemp = df_seleted_workingday[(df_seleted_workingday['temp'] > i-0.5) & (df_seleted_workingday['temp'] < i+0.5)]
            average = df_clustered_tempemp['kWh'].mean()
            output.append(average)

        except:
            pass

    output = pd.DataFrame(output, columns=['kWh_avg'], index=range(5, 20))
    balance_point = output.sort_values(['kWh_avg'], ascending=True).index[0]
    

    df_seleted['season'] = df_seleted.apply(lambda x: 2 if (x.date >= spring_start) & (x.date <= autumn_end) & (x.temp >= balance_point) else 1, axis=1)

    # 휴일을 데이터베이스에 저장
    df_holiday = df_seleted[df_seleted['workingday'] == 0]
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

    # cooling coefficient 구하기

    # data 준비
    reg_data = df_seleted[(df_seleted['workingday'] == 1) & (df_seleted['season'] == 2) & (df_seleted['temp'] >= min(balance_point+10, balance_point*1.5, 23))]
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
    cooling_coef = reg.coef_
    print(cooling_coef)


    # heating coefficient 구하기

    # data 준비
    reg_data = df_seleted[(df_seleted['workingday'] == 1) & (df_seleted['season'] == 1) & (df_seleted['temp'] <= max(balance_point-10, balance_point/2, 0))]
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
    heating_coef = abs(reg.coef_)
    print(heating_coef)


    # baseload, cooling_load, heating_load 계산
    df_seleted['baseload'] = df_seleted.apply(lambda x: workingday_line if x.workingday == 1 else holiday_line, axis=1)
    df_seleted['baseload'] = df_seleted.apply(lambda x: x.baseload if x.kWh > x.baseload else x.kWh, axis=1)

    df_seleted['cooling_load'] = df_seleted.apply(lambda x: x.kWh-x.baseload if (x.season == 2) & (x.kWh > x.baseload) else 0, axis=1)
    df_seleted['heating_load'] = df_seleted.apply(lambda x: x.kWh-x.baseload if (x.cooling_load == 0) & (x.kWh > x.baseload) else 0, axis=1)

    # Final Report

    baseload = sum(df_seleted['baseload'])
    cooling_load = sum(df_seleted['cooling_load'])
    heating_load = sum(df_seleted['heating_load'])
    total_load = baseload+cooling_load+heating_load

    print('Total_load : %s(%s)' %(round(total_load, 2), round(sum(df_seleted['kWh'], 2))))
    print('baseload : %s(%s%%)' %(round(baseload, 2), round(baseload/total_load*100, 2)))
    print('cooling : %s(%s%%)' %(round(cooling_load, 2), round(cooling_load/total_load*100, 2)))
    print('heating : %s(%s%%)' %(round(heating_load, 2), round(heating_load/total_load*100, 2)))
    print(df_seleted.head())


    # 예상절감률을 구한다....
    saving_potential = forest_regressor(df_q, 'kWh')


    analysis = {
        'balance_point': float(balance_point),
        'cooling_coefficient': float(cooling_coef),
        'heating_coefficient': float(heating_coef),
        'baseload': float(baseload),
        'cooling_load': float(cooling_load),
        'heating_load': float(heating_load),
        'total_load': float(total_load),
        'saving_potential': saving_potential,
    }

    return analysis


from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
    
def forest_regressor(dataset, target):

    train, test = train_test_split(dataset, test_size=0.3, random_state=1)

    X_train = train.drop(['date', target], axis=1)
    Y_train = train[target]

    X_test = test.drop(['date', target], axis=1)
    Y_test = test[target]

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