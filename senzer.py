import tweepy, csv, sqlite3, re, string, datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

print("""
   _____         _____            
  / ___/___  ___/__  /  ___  _____
  \__ \/ _ \/ __ \/ /  / _ \/ ___/
 ___/ /  __/ / / / /__/  __/ /    
/____/\___/_/ /_/____/\___/_/     
Sentiment AnalyZer using Python                                  
""")
keyword = input("Please enter the sentiment keyword(s): ")

print("""Welcome! Please input a number to continue.
        1. Update Data
        2. Update Sentiment Score
        3. Display Data
        4. Visualize Data
        5. Exit Program
    """)
hasilinput = (input("Your Input :"))
#Menggunakan 5 sebagai mark,
while(hasilinput!='5'):    
    if(hasilinput=='1'):
        try:
            print("Please check your Twitter Developer Account for the keys.")
            consumer_key = input("Please enter your consumer key: ")
            consumer_secret = input("Please enter your secret consumer key: ")
            access_token = input("Please enter your access token: ")
            access_token_secret = input("Please enter your secret access token: ")
            auth = tweepy.OAuthHandler(consumer_key,consumer_secret)
            auth.set_access_token(access_token,access_token_secret)

            print("Checking tokens... please hold on.")
            #Checking Tokens
            api = tweepy.API(auth)
            test_array=[]
            test_tokens = tweepy.Cursor(api.search, q="test",
                tweet_mode='extended', lang='id').items(5)
            for x in test_tokens:
                test_array.append(str(x.created_at))

            print("\nTokens confirmed as valid.\n")
            n_scrapes = int(input("Number of tweets to scrape : "))
            print("Updating data... please hold on.\n")
            #Mencari tanggal pencarian

            def caritanggal():
                date = datetime.datetime.now()
                month = int(date.strftime("%m"))
                day = int(date.strftime("%d"))
                year = int(date.strftime("%Y"))

                longmonths = [1,3,5,7,8,10,12]
                shortmonths = [4,6,9,11]

                daysago = day-2
                monthsago = month
                yearsago = year

                if (day==1 or day == 2):
                    if month == 1:
                        yearsago = year-1
                        monthsago = 12
                        if day == 1:
                            daysago = 30
                        elif day ==2:
                            daysago = 31
                    elif month-1 in longmonths:
                        if day == 1:
                            daysago = 30
                            monthsago = month-1
                        elif day == 2:
                            daysago = 31
                            monthsago = month-1
                    elif month-1 in shortmonths:
                        if day == 1:
                            daysago = 29
                            monthsago = month-1
                        elif day == 2:
                            daysago = 30
                            monthsago = month-1
                    elif month-1 == 2:
                        if year%4==0:
                            monthsago = 2
                            if day == 1:
                                daysago = 28
                            elif day ==2:
                                daysago = 29
                        else:
                            if day == 1:
                                daysago = 27
                            elif day == 2:
                                daysago = 28

                newdate = ("{}-{}-{}".format(yearsago,monthsago,daysago))
                return (newdate)

            #Filtering Tweets
            search_words=keyword
            new_search = search_words+"-filter:retweets"
            date_since=caritanggal()

            #Tweet Search Parameters
            tweets = tweepy.Cursor(api.search, q=new_search,
                tweet_mode='extended', lang='id',since=date_since).items(n_scrapes) 
            #Tweet Preprocessing
            tweetdate = []
            items = []
            user = []
            sentiment_sql = []
            for tweet in tweets:
                create_date=(str(tweet.created_at))
                user.append("@"+tweet.user.screen_name)
                tweetdate.append(str(create_date[0:11]))
                items.append(' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet.full_text).split()))
            #Move tweet to CSV
            hasil2 = pd.DataFrame(items, columns = ['tweet'])
            hasil = pd.DataFrame(tweetdate, columns = ['date'])
            hasil3 = pd.DataFrame(user, columns = ['user'])
            hasil4 = pd.DataFrame(sentiment_sql,columns = ['sentiment'])

            hasil['user'] = hasil3
            hasil['tweet']=hasil2
            hasil['sentiment']=hasil4

            hasil.to_csv('tweetscraping.csv',index=False)

            #Move tweet to SQL Database
            connection = sqlite3.connect('tweetdatabase.db')
            cursor = connection.cursor()

            sql = """
                CREATE TABLE IF NOT EXISTS Tweets (
                    date TEXT,
                    user TEXT,
                    tweet VARCHAR UNIQUE,
                    sentiment INT
                    )"""

            cursor.execute(sql)

            with open ('tweetscraping.csv','r') as csvfile:
                next(csvfile)
                for row in csvfile:
                    cursor.execute("INSERT OR IGNORE INTO Tweets VALUES (?,?,?,?)", row.split(","))
                    
            connection.commit()
            connection.close()
            print("Data updated.")
            #End
        except:
            print("\nTokens were invalid. Please recheck your inputs.")
            print("Hint : Check your Twitter Developer Account Dashboard for the keys.\n")
    elif (hasilinput=='2'):
        print("Updating... please hold on.")
        #Open Connection to DB
        connection = sqlite3.connect('tweetdatabase.db')
        query = "SELECT * from Tweets;" 
        cursor = connection.cursor()
        cursor.execute(query) 
        hasil = cursor.fetchall()

        df = pd.DataFrame(hasil, columns= ['date','user','tweet','sentiment'])

        #Ambil tweet dari DB, masukkan dalam 'items'
        items = df['tweet']

        pos_list = open("kata_positif.txt", "r")
        pos_kata = pos_list.readlines()
        neg_list = open("kata_negatif.txt","r")
        neg_kata = neg_list.readlines()

        #Hitung sentiment dari tweet
        Sentiment = []
        for item in items:
            item = item.strip().lower().translate(str.maketrans('','',string.punctuation))
            count_p = 0
            count_n = 0
            for kata_pos in pos_kata:
                kata_pos = kata_pos.strip().lower().translate(str.maketrans('','',string.punctuation))
                if kata_pos in item:
                    count_p +=1
            for kata_neg in neg_kata:
                kata_neg = kata_neg.strip().lower().translate(str.maketrans('','',string.punctuation))
                if kata_neg in item:
                    count_n +=1
            Sentiment.append(count_p - count_n)

        #Buat dataframe baru isinya tweet dan hasil sentiment
        df['sentiment'] = Sentiment
        df_sentiment = pd.DataFrame(Sentiment, columns = ['sentiment'])
        df_sentiment['tweet'] = items
        df_sentiment.to_csv('updatesentiment.csv',index=False)

        #Update isi DB dengan hasil sentiment
        with open ('updatesentiment.csv','r') as csvtest:
            csvfile = csv.reader(csvtest,delimiter=',')
            next(csvfile)
            for row in csvfile:
                querysent = "UPDATE Tweets set sentiment=? where tweet=?;"
                cursor.execute(querysent,(row[0],row[1]))
        connection.commit()
        connection.close()
        print("Sentiment data updated.")
    elif (hasilinput=='3'):
        connection = sqlite3.connect('tweetdatabase.db')
        query = "SELECT * from Tweets;" 
        cursor = connection.cursor()
        cursor.execute(query) 
        hasil = cursor.fetchall()

        #Ambil batas tanggal
        try:
            awal=str(input("From... (format: 2020-04-24) : "))
            akhir=str(input("until... (format: 2020-04-24) : "))
            awal = (awal.split('-'))
            akhir = (akhir.split('-'))

            awal = datetime.date(int(awal[0]),int(awal[1]),int(awal[2]))
            akhir = datetime.date(int(akhir[0]),int(akhir[1]),int(akhir[2]))
            print("Fetching results...")
            delta = int((akhir-awal).days)

            in_range = []

            #Fetch Columns yang masuk range
            df = pd.DataFrame(hasil, columns= ['date','user','tweet','sentiment'])
            for i in range(df.shape[0]):
                temp_split = (str(df['date'][i])).split('-')
                temp_split = datetime.date(int(temp_split[0]),int(temp_split[1]),int(temp_split[2]))
                day_diff = int((temp_split-awal).days)
                if (0<=day_diff<=delta):
                    in_range.append(df.loc[i])

            #Oper ke DF baru
            time_in_range= pd.DataFrame(in_range)
            print(time_in_range)

            connection.commit()
            connection.close()
        except:
            print("\nInputs were invalid. Please recheck your input, and double-check your input format. Also consider checking if the database exists.\n")
    elif (hasilinput=='4'):
        #Open Connection
        connection = sqlite3.connect('tweetdatabase.db')
        query = "SELECT * from Tweets;" 
        cursor = connection.cursor()
        cursor.execute(query) 
        hasil = cursor.fetchall()
        try:
            #Ambil batas tanggal
            awal=str(input("From... (format: 2020-04-24) : "))
            akhir=str(input("until... (format: 2020-04-24) : "))
            
            awal = (awal.split('-'))
            akhir = (akhir.split('-'))

            awal = datetime.date(int(awal[0]),int(awal[1]),int(awal[2]))
            akhir = datetime.date(int(akhir[0]),int(akhir[1]),int(akhir[2]))
            print("Fetching results...")
            delta = int((akhir-awal).days)

            in_range = []

            #Fetch Columns yang masuk range
            df = pd.DataFrame(hasil, columns= ['date','user','tweet','sentiment'])
            for i in range(df.shape[0]):
                temp_split = (str(df['date'][i])).split('-')
                temp_split = datetime.date(int(temp_split[0]),int(temp_split[1]),int(temp_split[2]))
                day_diff = int((temp_split-awal).days)
                if (0<=day_diff<=delta):
                    in_range.append(df.loc[i])

            #Oper ke DF baru
            df= pd.DataFrame(in_range)

            #Print Stdev, Median, Mean
            print("Mean: "+str(np.mean(df["sentiment"])))
            print("Median: "+str(np.median(df["sentiment"])))
            print("Standard Deviation: "+str(np.std(df["sentiment"])))

            #Visualisasi Data
            labels, counts = np.unique(df["sentiment"], return_counts=True)
            plt.bar(labels,counts,align='center')
            plt.gca().set_xticks(labels)
            plt.show()
        except:
            print("\nInputs were invalid. Please recheck your input, and double-check your input format. Also consider checking if the database exists.\n")

    else:
        print("Please enter a valid input.")
    print("""Please input a number to continue.
        1. Update Data
        2. Update Sentiment Score
        3. Display Data
        4. Visualize Data
        5. Exit Program
    """)
    hasilinput = (input("Your Input :\n"))
print("Thank you!")