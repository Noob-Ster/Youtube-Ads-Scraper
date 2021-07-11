import mysql.connector
import requests
from bs4 import BeautifulSoup
import time
import multiprocessing
import concurrent.futures
from fake_useragent import UserAgent
from datetime import datetime
import pymysql


# # mycursor.execute('''
#     # CREATE TABLE IF NOT EXISTS Ad_Views
#     # (
#     #     ad_title TEXT,
#     #     ad_url TEXT,
#     #     view_count TEXT,
#     #     hour TEXT
#     # )
# # ''')

def clean_duplicates():
    mydb = mysql.connector.connect(
        host='localhost',
        user='root',
        database='YoutubeAds')

    mycursor = mydb.cursor(buffered=True)
    mycursor.execute('''
        DELETE FROM Ads_info
        WHERE
            id IN (
            SELECT
                id
            FROM (
                SELECT
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY ad_title
                        ORDER BY ad_title) AS row_num
                FROM
                    Ads_info

            ) t
            WHERE row_num > 1
        );
    ''')
    mydb.commit()
    mycursor.execute('ALTER TABLE Ads_info DROP id;')
    mydb.commit()
    mycursor.execute(
        'ALTER TABLE Ads_info ADD id INT NOT NULL AUTO_INCREMENT PRIMARY KEY FIRST;')
    mydb.commit()
    mycursor.close()
    mydb.close()


def get_ad_information():
    # mydb = mysql.connector.connect(
    #     host='localhost',
    #     user='root',
    #     database='YoutubeAds')
    # mycursor = mydb.cursor(buffered=True)
    # mycursor.execute('SELECT ad_title, ad_url FROM Ads_info;')
    # info = [(row[0], row[1]) for row in mycursor]
    # mycursor.close()
    # mydb.close()
    # return info
    mydb = pymysql.connect('localhost', 'root', '', 'YoutubeAds')
    cursor = mydb.cursor()
    cursor.execute('SELECT ad_title, ad_url FROM Ads_info;')
    info = [(row[0], row[1]) for row in cursor]
    cursor.close()
    mydb.close()
    return info


def get_views(record):
    ua = UserAgent(verify_ssl=False)
    user_agent = ua.random
    headers = {'User-Agent': f'{user_agent}'}
    response = requests.get(record[1], headers=headers)
    soup = BeautifulSoup(response.text, 'lxml')
    try:
        view_count = soup.find('meta', {'itemprop': 'interactionCount'})[
            'content']
    except Exception as e:
        return True
    else:
        return (record[0], record[1], view_count, datetime.now().strftime("%H:%M"), datetime.now().strftime('%a %d-%b-%Y'))


def store_Ad_Views(records_list):
    mydb = mysql.connector.connect(
        host='localhost',
        user='root',
        database='YoutubeAds')
    mycursor = mydb.cursor(buffered=True)
    query = 'INSERT INTO Ad_Views (ad_title, ad_url, view_count, hour, date) VALUES (%s,%s,%s,%s,%s)'
    try:
        mycursor.executemany(query, records_list)
        mydb.commit()
    except Exception:
        mydb.rollback()
    finally:
        mycursor.close()
        mydb.close()


def main():
    start_time = time.perf_counter()
    clean_duplicates()
    records = get_ad_information()
    records_list = list()
    with concurrent.futures.ProcessPoolExecutor(15) as executor:
        results = executor.map(get_views, records)
        for record in results:
            if record != True:
                records_list.append(record)

    store_Ad_Views(records_list)
    end_time = time.perf_counter()
    print(f"Seconds: {round(end_time-start_time,2)} second's")


if __name__ == "__main__":
    main()
