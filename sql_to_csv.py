import mysql.connector
import csv
import os

mydb = mysql.connector.connect(
    host='localhost',
    user='root',
    database='YoutubeAds'
)
mycursor = mydb.cursor(buffered=True)
mycursor.execute('SELECT * FROM Ad_Views;')
rows = mycursor.fetchall()

# Read the Count from File
with open(f'/home/linuxah/Downloads/Updated_csv/COUNT', 'r') as f:
    COUNT = int(f.read())
    f.close()

# Check if the file Exists
if not os.path.isfile(f'/home/linuxah/Downloads/Views_CSV/view_dataset_v{COUNT}.csv'):
    with open(f'/home/linuxah/Downloads/Views_CSV/view_dataset_v{COUNT}.csv', 'w') as f:
        myfile = csv.writer(f)
        myfile.writerow(['ad_title','ad_url','view_count','hour', 'date'])
        myfile.writerows(rows)
        f.close()
