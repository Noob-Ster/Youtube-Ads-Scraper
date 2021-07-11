import mysql.connector



mydb = mysql.connector.connect(
    host='localhost',
    user='root',
    database='YoutubeAds'
)
mycursor = mydb.cursor(buffered=True)


def store_in_db(ad_title, organic_video_url, ad_url, upload_date, ad_genre, views_count, duration_time, channel_name, ad_unlisted, channel_created_date, ad_channel_link, ad_channel_subscriber, ad_likes, ad_dislikes, ad_cta_tag, ad_cta_link, cta_capture_time, ad_description, ad_subtitles, ad_links, total_videos, vpn_city, count):

    # CREATE DATABASE
    # mycursor.execute("CREATE DATABASE IF NOT EXISTS YoutubeAds;")

    # CREATE TABLE
    # mycursor.execute('''

    # CREATE TABLE IF NOT EXISTS Ads_info
    # (
    # 	id INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
    # 	ad_title VARCHAR(255) PRIMARY KEY,
    #   organic_video_url TEXT,
    # 	ad_url TEXT,
    #   ad_unlisted TEXT,
    # 	upload_date TEXT,
    #   ad_genre TEXT,
    # 	views_count TEXT,
    # 	duration_time TEXT,
    # 	ad_likes TEXT,
    # 	ad_dislikes TEXT,
    #   ad_cta_tag TEXT,
    # 	ad_cta_link TEXT,
    #   cta_capture_time TEXT,
    # 	ad_description TEXT,
    #   ad_subtitles TEXT,
    # 	ad_links TEXT,
    # 	count INT,
    #   vpn_city TEXT,
    #   channel_name VARCHAR(255)
    # );

    # CREATE TABLE IF NOT EXISTS Channel_info
    # (
    # 	channel_name VARCHAR(255) PRIMARY KEY,
    # 	ad_channel_link TEXT,
    # 	ad_channel_subscriber TEXT,
    #   channel_created_date TEXT,
    # 	total_videos TEXT
    # );

    sql = '''INSERT INTO Ads_info (ad_title,organic_video_url,ad_url,ad_unlisted,upload_date,ad_genre,views_count,duration_time,ad_likes,ad_dislikes,ad_cta_tag,ad_cta_link,cta_capture_time,ad_description,ad_subtitles,ad_links,count,vpn_city,channel_name) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
    val = (ad_title, organic_video_url, ad_url, ad_unlisted, upload_date, ad_genre, views_count, duration_time, ad_likes,
           ad_dislikes, ad_cta_tag, ad_cta_link, cta_capture_time, ad_description, ad_subtitles, ad_links, count, vpn_city, channel_name)
    mycursor.execute(sql, val)
    mydb.commit()
    add_check_Channel(channel_name=channel_name, ad_channel_link=ad_channel_link,
                      ad_channel_subscriber=ad_channel_subscriber, channel_created_date=channel_created_date, total_videos=total_videos)


def add_check_Channel(channel_name, ad_channel_link, ad_channel_subscriber, channel_created_date, total_videos):
    sql = 'SELECT EXISTS (SELECT channel_name FROM Channel_info WHERE channel_name = %s)'
    mycursor.execute(sql, (channel_name,))
    for row in mycursor:
        if row[0] == 0:
            sql = 'INSERT INTO Channel_info (channel_name,ad_channel_link,ad_channel_subscriber,channel_created_date,total_videos) VALUES (%s,%s,%s,%s,%s)'
            val = (channel_name, ad_channel_link,
                   ad_channel_subscriber, channel_created_date, total_videos)
            mycursor.execute(sql, val)
            mydb.commit()
        elif row[0] == 1:
            pass


def check_Ad_Title(ad_title):
    sql = 'UPDATE Ads_info SET count = count + 1 WHERE ad_title = %s'
    mycursor.execute(sql, (ad_title,))
    mydb.commit()
    if mycursor.rowcount > 0:
        return '1'
