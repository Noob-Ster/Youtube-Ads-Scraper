import mysql.connector
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os

mydb = mysql.connector.connect(
    host='localhost',
    user='root',
    database='YoutubeAds'
)

chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--headless')
chrome_options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36')

driver = webdriver.Chrome(executable_path='/usr/bin/chromedriver', options=chrome_options)

mycursor = mydb.cursor(buffered=True)

mycursor.execute('SELECT ad_title, ad_cta_link FROM Ads_info;')

driver.set_window_size(1080,1080)

for rows in mycursor.fetchall():
    driver.maximize_window()
    # Maximum Size
    # driver.set_window_size(7680,4320)    
    driver.implicitly_wait(30)
    driver.get(rows[1])
    if not os.path.exists(f'/home/linuxah/Downloads/Project-S/Original Project-YoutubeAds/cta_screenshot/{rows[0]}.png'):
        driver.save_screenshot(f'/home/linuxah/Downloads/Project-S/Original Project-YoutubeAds/cta_screenshot/{rows[0]}.png')
    else:
        continue
    
