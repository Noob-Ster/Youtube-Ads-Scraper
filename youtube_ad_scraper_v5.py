from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from fake_useragent import UserAgent
from yt_database import store_in_db, check_Ad_Title
from bs4 import BeautifulSoup
from datetime import datetime
import concurrent.futures
import random
import time
import math
import sys
import os
import re

start = time.perf_counter()


def chromeOptions():
    ua = UserAgent(verify_ssl=False)
    user_agent = ua.random
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument("--window-size=1366,738")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--disable-dev-shm-using")
    chrome_options.add_argument('--mute-audio')
    chrome_options.add_argument('--incognito')
    chrome_options.add_argument(f'user-agent={user_agent}')
    return chrome_options


def chromeDriver(link):
    chrome_options = chromeOptions()
    # Create Instance of Chrome Driver
    driver = webdriver.Chrome(
        executable_path='/usr/bin/chromedriver', options=chrome_options)
    driver.implicitly_wait(20)
    driver = open_VideoLink(driver=driver, link=link)
    if driver == False:
        return chromeDriver(link)
    else:
        time.sleep(3)
        operate(driver=driver, COUNT=1, link=link)
        driver.close()


def open_VideoLink(driver, link):
    try:
        driver.get(link)
        if link != driver.current_url:
            driver = False
    except Exception:
        print('No Connectivity !!!')
        return False
    else:
        return driver


def cta_Link(driver):
    try:
        cta = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
            (By.XPATH, '//button[@class="ytp-ad-button ytp-ad-visit-advertiser-button ytp-ad-button-link"]')))
    except Exception:
        return 1
    else:
        outer_cta = cta.get_attribute('aria-label')
        cta.click()
        handler = driver.window_handles
        driver.switch_to.window(handler[1])
        cta = driver.current_url
        driver.close()
        driver.switch_to.window(handler[0])
        return {'cta': cta, 'outer_cta': outer_cta}


def operate(driver, COUNT, link):
    if COUNT != 3:
        try:
            # Find Overlay Ad Element and Remove it to procede to the next step!
            try:
                element = WebDriverWait(driver, 3).until(EC.presence_of_element_located(
                    (By.XPATH, "//paper-dialog[@class='style-scope ytd-popup-container']")))
            except Exception as e:
                pass
            else:
                driver.execute_script("arguments[0].remove();", element)
            # Find Video Container
            videoContainer = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@class="html5-video-container"]')))
            # start the video
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                (By.XPATH, '//button[@class="ytp-play-button ytp-button"]'))).click()
        except Exception:
            return 'Skipping link Invalid!'
        else:
            # get CTA
            cta_link = cta_Link(driver)
            if cta_link == 1:
                print(f"Ad Not Found!")
                print(f"Refreshing Page to check Again!")
                driver.delete_all_cookies()
                driver.refresh()
                operate(driver=driver, COUNT=COUNT+1, link=link)
            else:
                videoContainer = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//div[@class="html5-video-container"]')))
                # Perform Right Click on Video Container
                action = ActionChains(driver)
                action.context_click(on_element=videoContainer).perform()
                # Click `Stats For Nerds` option
                statsForNerds = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                    (By.XPATH, '(//div[@class="ytp-menuitem-label"])[7]'))).click()
                # Current Video Link
                extracted_link = link.split('=')[-1]
                # Video Id
                video_id = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                    (By.XPATH, '(//div[@class="html5-video-info-panel-content"]/div/span)[1]'))).text.split('/')[0].strip()
                # Now Scrape Ad Information
                details = get_Details(
                    driver, Video_ID=video_id, link=link, cta_link=cta_link)
                if details != 1:
                    check_info = check_information(details)
                    if check_info == 1:
                        # `1` mean error go back to get_details function to get correct info.
                        get_Details(driver, Video_ID=video_id,
                                    link=link, cta_link=cta_link)
                    else:
                        # display
                        display(details)
                        # store in database
                        set_database(details)


def get_Details(driver, Video_ID, link, cta_link):
    details = dict()
    print("----------------------------Ad on Video------------------------------------")
    if Video_ID != 'undefined':
        url = f'https://www.youtube.com/watch?v={Video_ID}'
        driver.execute_script(f'window.open("{url}");')
        handles = driver.window_handles
        driver.switch_to.window(handles[1])
        driver.refresh()
        # Find Overlay Ad Element and Remove it to procede to the next step!
        # try:
        #     element = WebDriverWait(driver, 3).until(EC.presence_of_element_located(
        #         (By.XPATH, "//paper-dialog[@class='style-scope ytd-popup-container']")))
        # except Exception as e:
        #     pass
        # else:
        #     driver.execute_script("arguments[0].remove();", element)
        # Ad Title
        ad_title = ''
        try:
            raw_title = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
                (By.XPATH, '//h1[@class="title style-scope ytd-video-primary-info-renderer"]/yt-formatted-string'))).text.strip()
            for i in range(len(raw_title)):
                if (ord(raw_title[i]) >= 0 and ord(raw_title[i]) <= 127):
                    ad_title = ad_title + raw_title[i]
        except Exception:
            ad_title = 'N/A'

        check_title = check_Ad_Title(ad_title=ad_title)

        if check_title == '1':
            print(f'Skipping Ad Exists! `{ad_title}`')
            driver.close()
            driver.switch_to.window(handles[0])
            return 1

        elif check_title == None:
            ad_url = driver.current_url
            # Upload Date
            try:
                soup = BeautifulSoup(driver.page_source, 'lxml')
                upload_date = soup.findAll(
                    'yt-formatted-string', {'class': 'style-scope ytd-video-primary-info-renderer'})[1].text
            except Exception:
                upload_date = 'N/A'

            # View Count
            try:
                soup = BeautifulSoup(driver.page_source, 'lxml')
                views_count = soup.find(
                    'meta', {'itemprop': 'interactionCount'})['content']
            except Exception:
                views_count = 'N/A'

            # Duration Time
            try:
                soup = BeautifulSoup(driver.page_source, 'lxml')
                duration_time = soup.find(
                    'span', {'class': 'ytp-time-duration'}).text
            except Exception:
                duration_time = 'N/A'

            # Channel Name
            try:
                ad_channel_name = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
                    (By.XPATH, '//yt-formatted-string[@class="style-scope ytd-channel-name"]/a'))).text.strip()
            except Exception:
                ad_channel_name = 'N/A'

            # Unlisted
            try:
                soup = BeautifulSoup(driver.page_source, 'lxml')
                ad_unlisted = soup.find(
                    'meta', {'itemprop': 'unlisted'})['content']
                if ad_unlisted == 'True':
                    ad_unlisted = 'Yes'
                elif ad_unlisted == 'False':
                    ad_unlisted = 'No'
            except Exception:
                ad_unlisted = 'N/A'

            # Genre type
            try:
                soup = BeautifulSoup(driver.page_source, 'lxml')
                ad_genre = soup.find('meta', {'itemprop': 'genre'})['content']
            except Exception:
                ad_genre = 'N/A'
            # Channel Link
            try:
                soup = BeautifulSoup(driver.page_source, 'lxml')
                ad_channel_link = soup.find(
                    'yt-formatted-string', {'class': 'style-scope ytd-channel-name'}).find('a')['href']
            except Exception:
                ad_channel_link = 'N/A'

            # Channel Subscriber
            try:
                ad_channel_subscriber = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((
                    By.XPATH, '//yt-formatted-string[@class="style-scope ytd-video-owner-renderer"]'))).text.strip()
                if ad_channel_subscriber == '':
                    ad_channel_subscriber = '0'
            except Exception:
                ad_channel_subscriber = '0'
            finally:
                if ad_channel_subscriber == '0':
                    pass
                else:
                    if 'K' in ad_channel_subscriber.strip(' subscribers'):
                        ad_channel_subscriber = ad_channel_subscriber.strip(
                            'K subscribers')
                        if ad_channel_subscriber.isdigit():
                            ad_channel_subscriber = str(
                                math.floor(int(ad_channel_subscriber)*1000))
                        else:
                            ad_channel_subscriber = str(math.floor(
                                float(ad_channel_subscriber)*1000))
                    elif 'M' in ad_channel_subscriber.strip(' subscribers'):
                        ad_channel_subscriber = ad_channel_subscriber.strip(
                            'M subscribers')
                        if ad_channel_subscriber.isdigit():
                            ad_channel_subscriber = str(math.float(
                                int(ad_channel_subscriber)*1000000))
                        else:
                            ad_channel_subscriber = str(math.floor(
                                float(ad_channel_subscriber)*1000000))

            # Likes
            try:
                likes = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
                    (By.XPATH, '(//yt-formatted-string[@class="style-scope ytd-toggle-button-renderer style-text"])[1]'))).get_attribute('aria-label').strip()
                if likes == 'No likes':
                    likes = '0'
            except Exception:
                likes = '0'

            # Dislikes
            try:
                dislikes = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
                    (By.XPATH, '(//yt-formatted-string[@class="style-scope ytd-toggle-button-renderer style-text"])[2]'))).get_attribute('aria-label').strip()
                if dislikes == 'No dislikes':
                    dislikes = '0'
            except Exception:
                dislikes = '0'

            # Extract Description
            soup = BeautifulSoup(driver.page_source, 'lxml')
            desc_list = list()
            raw_descp = ''
            descp = ''
            try:
                ad_description = soup.find('div', {'id': 'description'})
                for description in ad_description.findAll('yt-formatted-string', {'class': 'content style-scope ytd-video-secondary-info-renderer'}):
                    desc_list.append(description.text.strip())
            except Exception:
                descp = 'N/A'
            finally:
                raw_descp = ' '.join([str(desc) for desc in desc_list])
                for i in range(len(raw_descp)):
                    if (ord(raw_descp[i]) >= 0 and ord(raw_descp[i]) <= 127):
                        descp = descp + raw_descp[i]
                if descp == '':
                    descp = 'N/A'
                elif descp == ' ':
                    descp = 'N/A'

            # Extract Links
            linkS = list()
            raw_links = ''
            links = ''
            try:
                ad_description = soup.find('div', {'id': 'description'})
                linkS = [link.text.strip()
                         for link in ad_description.findAll('a')]
            except Exception:
                links = 'N/A'
            finally:
                raw_links = ' ,'.join([str(link) for link in linkS])
                for i in range(len(raw_links)):
                    if (ord(raw_links[i]) >= 0 and ord(raw_links[i]) <= 127):
                        links = links + raw_links[i]
                if links == '':
                    links = 'N/A'
                elif links == ' ':
                    links = 'N/A'

            # Transcript
            ad_subtitles = ''
            try:
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                    (By.XPATH, '(//button[@class="style-scope yt-icon-button"])[12]'))).click()
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                    (By.XPATH, '//ytd-menu-service-item-renderer[@class="style-scope ytd-menu-popup-renderer"]'))).click()
                time.sleep(5)
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                    (By.XPATH, '(//div[@class="style-scope ytd-watch-flexy"])[23]')))
            except Exception:
                ad_subtitles = 'N/A'
            else:
                soup = BeautifulSoup(driver.page_source, 'lxml')
                subs = soup.findAll(
                    'div', {'class': 'cue style-scope ytd-transcript-body-renderer'})
                for sub in subs:
                    ad_subtitles = ad_subtitles + sub.text.strip() + ' '

            # Channel Created Date
            channel_created_date = ''
            try:
                driver.find_element_by_xpath(
                    '//yt-formatted-string[@class="style-scope ytd-channel-name"]/a').click()
                time.sleep(2)
                tabs = driver.find_elements_by_xpath(
                    '//div[@class="tab-content style-scope paper-tab"]')
                for tab in tabs:
                    if tab.text == 'ABOUT':
                        tab.click()
                        time.sleep(3)
                        soup = BeautifulSoup(driver.page_source, 'lxml')
                        right_col = soup.find('div', {'id': 'right-column'}).find('yt-formatted-string', {
                            'class': 'style-scope ytd-channel-about-metadata-renderer'})
                        channel_created_date = right_col.findAll(
                            'span', {'class': 'style-scope yt-formatted-string'})[1].text
            except Exception:
                channel_created_date = 'N/A'

            # Total Videos
            try:
                driver.find_element_by_xpath(
                    '(//div[@class="tab-content style-scope paper-tab"])[2]').click()
                time.sleep(2)
                driver.find_element_by_xpath(
                    '(//yt-formatted-string[@class="style-scope ytd-button-renderer style-text size-default"])[1]').click()
                time.sleep(3)
                total_videos = driver.find_element_by_xpath(
                    '(//yt-formatted-string[@class="index-message style-scope ytd-playlist-panel-renderer"]/span[3])[1]').text.strip()
            except Exception:
                total_videos = '0'

            details = {
                'ad_title': ad_title,
                'ad_url': ad_url,
                'organic_url': link,
                'upload_date': upload_date,
                'views_count': views_count,
                'duration_time': duration_time,
                'ad_channel_name': ad_channel_name,
                'ad_unlisted': ad_unlisted,
                'ad_genre': ad_genre,
                'ad_channel_link': ad_channel_link,
                'ad_channel_subscriber': ad_channel_subscriber,
                'ad_likes': likes,
                'ad_dislikes': dislikes,
                'ad_cta_tag': cta_link.get('outer_cta'),
                'cta_link': cta_link.get('cta'),
                'descp': descp,
                'links': links,
                'ad_subtitles': ad_subtitles,
                'channel_created_date': channel_created_date,
                'total_videos': total_videos,
            }

            driver.close()
            driver.switch_to.window(handles[0])

            return details


def check_information(details):
    if details.get('ad_genre') == 'N/A' or details.get('channel_created_date') == 'N/A' or details.get('views_count') == 'N/A' or details.get('ad_unlisted') == 'N/A':
        return 1


def get_vpn_city():
    status = os.popen('nordvpn status').read()
    pattern = re.compile('City:.*')
    try:
        city = pattern.search(status).group().strip('City: ')
    except Exception:
        city = 'No Connection'
    finally:
        return city


def display(details):
    print(f"Organic Video Url: {details.get('organic_url')}")
    print(f"Ad Url: {details.get('ad_url')}")
    print(f"Ad Title: {details.get('ad_title')}")
    print(f"Ad Upload Date: {details.get('upload_date')}")
    print(f"Ad Views Count:  {details.get('views_count').strip('views')}")
    print(f"Ad Duration Time:  {details.get('duration_time')}")
    print(f"Ad Channel Name: {details.get('ad_channel_name')}")
    print(f"Ad Unlisted: {details.get('ad_unlisted')}")
    print(f"Ad Genre: {details.get('ad_genre')}")
    print(f"Ad Channel Link: https://www.youtube.com{details.get('ad_channel_link')}")
    print(f"Ad Channel Subscriber: {details.get('ad_channel_subscriber').strip('subscribers')}")
    print(f"Ad Likes: {details.get('ad_likes').strip('likes')}")
    print(f"Ad Dislikes: {details.get('ad_dislikes').strip('dislikes')}")
    print(f"Ad CTA tag link: {details.get('ad_cta_tag')}")
    print(f"Ad CTA full link: {details.get('cta_link')}")
    print(f"Ad Description: {details.get('descp').strip()}")
    print(f"Ad Links: {details.get('links')}")
    print(f"Transcripts: {details.get('ad_subtitles')}")
    print(f"Ad Channel Created Date: {details.get('channel_created_date')}")
    print(f"Total Videos: {details.get('total_videos')}")


def set_database(details):
    store_in_db(
        ad_title=details.get('ad_title'),
        organic_video_url=details.get('organic_url'),
        ad_url=details.get('ad_url'),
        upload_date=details.get('upload_date'),
        ad_genre=details.get('ad_genre'),
        views_count=details.get('views_count').strip('views'),
        duration_time=details.get('duration_time'),
        channel_name=details.get('ad_channel_name'),
        ad_unlisted=details.get('ad_unlisted'),
        channel_created_date=details.get('channel_created_date'),
        ad_channel_link=f"https://www.youtube.com{details.get('ad_channel_link')}",
        ad_channel_subscriber=details.get('ad_channel_subscriber').strip('subscribers'),
        ad_likes=details.get('ad_likes').strip('likes'),
        ad_dislikes=details.get('ad_dislikes').strip('dislikes'),
        ad_cta_tag=details.get('ad_cta_tag'),
        ad_cta_link=details.get('cta_link'),
        cta_capture_time=datetime.now().strftime('%a %d-%b-%Y %X'),
        ad_description=details.get('descp').strip(),
        ad_subtitles=details.get('ad_subtitles'),
        ad_links=details.get('links'),
        total_videos=details.get('total_videos'),
        vpn_city=get_vpn_city(),
        count=1)


def main(Links):
    count = 1
    for link in Links:
        chromeDriver(link=link)
        print(f'------------------Link {count} Completed------------------')
        count = count + 1
    # with concurrent.futures.ProcessPoolExecutor(5) as executor:
    #     executor.map(chromeDriver, Links)



if __name__ == "__main__":
    # Read link file as an cammand line argument
    with open(sys.argv[1], 'r') as f:
        raw_links = f.readlines()
        f.close()
    # Store links in a list
    Links = [link.strip() for link in raw_links]
    # create lock and semaphore object
    main(Links)
    finish = time.perf_counter()
    print(f'Ends in: {round((finish-start),2)} seconds')
