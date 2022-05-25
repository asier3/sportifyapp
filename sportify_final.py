# SPORTIFY APP

# 1. IMPORT LIBRARIES

import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

from opencage.geocoder import OpenCageGeocode  #must install opencage with pip first
import spotipy
from spotipy.oauth2 import SpotifyOAuth

from getpass import getpass
import webbrowser
from termcolor import colored  #must install termcolor package with conda first

from IPython import display
import sys
sys.tracebacklimit = 0



# 2. DEFINE PARAMETERS FOR API CONNECTIONS

# OpenCage Geocoding
geocoder_key =   #(Insert user's key)
geocoder = OpenCageGeocode(geocoder_key)

# Spotipy (Spotify wrapper)
client_id = # (Insert user's client_id)
client_secret = # (Insert user's client_secret)
redirect_uri = # (Insert redirect_uri)

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                               client_secret=client_secret,
                                               redirect_uri=redirect_uri,
                                               scope="user-library-read"))

# Decathlon 
url_d = 'https://sportplaces.api.decathlon.com/api/v1/places'

# Webscrapping
places = ['lisboa-green-trail','lisbon-marathon','lisbon-womens-run', 'lisbon-half-marathon']
url_list = ['https://worldsmarathons.com/marathon/' + place for place in places]
user_agent = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36'}



# 3. DATA EXTRACTION FROM DIFFERENT SOURCES

# 3.1 Get Spotify music categories ids from Spotipy
## This returns Spotify's categories names and categories ids
## It is not needed to run the app, but we used it to get categories ids
## for other endpoints
music_categories = sp.categories(limit=50)['categories']['items']
music_categories_df = pd.DataFrame(music_categories)[['name','id']]


# 3.2 Runners playlist options
## This generates a list with 5 playlist suggestions for intense workout
results_running = sp.category_playlists(category_id='workout')
running_lst = results_running['playlists']['items']
running_df = pd.DataFrame(running_lst)[['name','external_urls']]
## This is a function we need to unwrap results for both options:
def unwrapf(row):
    return row['external_urls']['spotify']
# We use the function and continue extracting the data we need:
running_df['link'] = running_df.apply(unwrapf, axis=1)
running_df = running_df[['name','link']].head(5) 
running_df.index += 1 


# 3.3 Yoga playlist options
## Apply same steps as above to build the list for yoga
## We reuse the same function to unwrap
results_yoga = sp.category_playlists(category_id='wellness')
yoga_lst = results_yoga['playlists']['items']
yoga_df = pd.DataFrame(yoga_lst)[['name','external_urls']]
yoga_df['link'] = yoga_df.apply(unwrapf, axis=1)
yoga_df = yoga_df[['name','link']]
yoga_df.index += 1


#3.4 Webscrapping 
run_events = []

for link in url_list:
    #print(link)
    try: 
        response = requests.get(url=link, headers=user_agent)
        soup = BeautifulSoup(response.content, features="lxml")
        time.sleep(1)

        #get event_name

        result_event_name = soup.find_all('h4', attrs={'class' : 'event-title'})

        result_event_main_title = result_event_name[0].text

        #get event_details

        result_event_details = soup.find_all('div', attrs={'class': 'event-subtitle-details'})

        event_green_trail_details = [location.text.replace('\n', ' ').strip() for location in result_event_details[0].find_all('p')]

        #get event_country

        result_event_country = event_green_trail_details[0].split(', ')[1]

        #get event_city

        result_event_city = event_green_trail_details[0].split(', ')[0]

        #get event_date

        result_event_date = event_green_trail_details[1]

        
        if len(event_green_trail_details[2]) > 5:

            #get event_min_distance

            result_event_min_distance = event_green_trail_details[2].split(', ')[1]
        

            #get event_max_distance

            result_event_max_distance = event_green_trail_details[2].split(', ')[0]
       
        else:

            result_event_min_distance  = '0km'

            result_event_max_distance = event_green_trail_details[2]
        
        #get event_prices

        result_event_prices = soup.find_all('div', attrs={'class' : 'event-ticket-price'})

        event_green_trail_prices = [price.text.replace('\n', ' ').strip() for price in result_event_prices]

        #get event_min_price

        result_event_min_price = event_green_trail_prices[0]

        #get event_max_price

        result_event_max_price = event_green_trail_prices[-1]

        run_events.append({'event_name': result_event_main_title, 'event_country': result_event_country, 
        'event_city' : result_event_city, 'event_date': result_event_date, 'event_min_distance': result_event_min_distance, 
        'event_min_price': result_event_min_price, 'event_max_distance': result_event_max_distance, 'event_max_price': result_event_max_price})
    
    except:
        print(link)


run_events_df = pd.DataFrame(run_events)

def clean_event_date(event_date):
    end_index = event_date.find('(')
    return event_date[0:end_index-1]

event_date = run_events_df['event_date'].apply(clean_event_date)

pd.DataFrame(event_date)

def clean_event_min_distance(event_min_distance):
    return event_min_distance[0:-2].strip() + ' km'

event_min_distance = run_events_df['event_min_distance'].apply(clean_event_min_distance)

pd.DataFrame(event_min_distance)

def clean_event_min_price(event_min_price):
    min_price_list = event_min_price.split()
    return min_price_list[-2] + ' ' + min_price_list[-1] 

event_min_price = run_events_df['event_min_price'].apply(clean_event_min_price)

pd.DataFrame(event_min_price)

def clean_event_max_price(event_max_price):
    max_price_list = event_max_price.split()
    return max_price_list[-2] + ' ' + max_price_list[-1] 

event_max_price_df = run_events_df['event_max_price'].apply(clean_event_max_price)

run_events_final_df = pd.concat([run_events_df['event_name'], event_date, event_min_distance, event_min_price], axis=1)

run_events_final_df.index += 1



# 4. DEFINE FUNCTIONS

# 4.1 Line Break function

def linebreak():
    """
    Print a line break
    """
    print("\n\n")


# 4.2 Geolocation Function

def get_coordinates():
    """
    Takes a city name as user's input and provides the coordinates 
    as required by Decathlon's Sport Places API. Steps:
    1. Define values needed to call OpenCage Geocoding API (+ API key).
    2. Asks the user for an input (a city name).
    3. Searches if the user's input matches the locations in the API.
    4.a. If there is a match: selects from the API's output the required fields +
    transforms it to match the format of Decathlon's API input.
    4.b. If there is no match, it prints an error message and asks the user for a 
    different location
    """
    
    city = input('\nInsert your location: ').lower()

    try:
        response = geocoder.geocode(city)
        lat = response[0]['geometry']['lat']
        lng = response[0]['geometry']['lng']
        lng_lat = str(lng) + ',' + str(lat)
        return lng_lat
        #print('\nThese are your coordinates:', lng_lat)     # This is temporary, just to check it works. Change to return (above) later
        #linebreak()  #temporary, to be removed
    except:
        print('\nLocation not found. Please try another name.\n')
        get_coordinates()
    

# 4.3 Get Sports ID function

def choose_a_sport():
    sport = input('What sport would you like to practice? (type): ').lower().strip()
    if sport == 'swimming':
        return str(224)
    elif sport == 'yoga':
        return str(292)
    elif sport == 'running':
        return str(257)
    else:
        print('Invalid input. Please enter another sport.\n')
        choose_a_sport()


# 4.4 Get Sports Venue function

def get_sports_venue():
    linebreak()
    sport = choose_a_sport()
    sport
    linebreak
    lng_lat = get_coordinates()
    lng_lat
    linebreak()
    print('These are the venues we found near you!')
    linebreak()
    parameters_d = {'origin':lng_lat, 'radius':'99', 'sports':sport, 'limit':'10'}
    response_d = requests.get(url=url_d, params=parameters_d)
    
    df1 = pd.json_normalize(response_d.json())                # Unwrap
    df2 = pd.DataFrame(df1['data.features'][0])             # Unwrap
    features = pd.DataFrame(dict(df2['properties'])).T      # Unwrap
    features2 = features[['name','proximity']].copy()
    features2.index += 1  # Change the index of the table to eliminate the 0
    def prox_short(row):
        a = round(row['proximity'], 2)
        return str(a) + ' Km'                                    # Create a function to round the 'proximity' column and add 'Km' string
    
    rounded_prox_column = features2.apply(prox_short, axis=1)       # Apply the function to the dataframe
    features2.loc[:,'proximity'] = rounded_prox_column            # Substitute the column with the rounded values
    print(features2)
    
    linebreak()
    next = input('Can we help with something else? [y/n]: ').lower().strip()
    if next == 'y':
        select_goal()
    else:
        quit()
   

# 4.5 Get Sports Events function

def get_sports_events():
    linebreak()
    print (run_events_final_df)

    linebreak()
    next = input('Can we help with something else? [y/n]: ').lower().strip()
    if next == 'y':
        select_goal()
    else:
        quit() 


# 4.6 Get a playlist function

def open_playlist():
    linebreak()
    sport = choose_a_sport()
    sport
    if sport == '292':
        print('\nHere are the playlist suggestions for your yoga session!\n')
        print(yoga_df[['name']])
        n = int(input('\nSelect the number of the playlist you prefer: '))
        if n in yoga_df.index:
            link_music = str(yoga_df.loc[n, 'link'])
            webbrowser.open(link_music, new=2)
            try:
                sp.start_playback(uris=['spotify:track:6oL6yOWVL8zJfwg2mlkMag'])
            except:
                pass
        else:
            print('\nInvalid value. Please enter a number of playlist')
            open_playlist()
    elif sport == '257':
        print('\nHere are the playlist suggestions for your run!\n')
        print(running_df[['name']])
        n = int(input('\nSelect the number of the playlist you prefer: '))
        if n in running_df.index:
            link_music = str(running_df.loc[n, 'link'])
            webbrowser.open(link_music, new=2)
            try:
                sp.start_playback(uris=['spotify:track:3AzjcOeAmA57TIOr9zF1ZW'])
            except:
                pass
        else:
            print('\nInvalid value. Please enter a number of playlist')
            open_playlist()
    
    linebreak()
    next = input('Can we help with something else? [y/n]: ').lower().strip()
    if next == 'y':
        select_goal()
    else:
        quit()
    

# 4.7 Select goal function

def select_goal():
    """
    Prints menu with actions available in selected location.
    Asks users input and triggers function accordingly.
    """

    goal = input('''\nWhat do you want to do today?
    1 - Find places nearby for my workout.
    2 - Find sports events near me.
    3 - Get a playlist for my workout session.\n
    Please select an option ['1'/'2'/'3']: ''')
    if int(goal) == 1:
        get_sports_venue()
    elif int(goal) == 2:
        get_sports_events() 
    elif int(goal) == 3:
        open_playlist() 
    else:
        print('\nPlease enter a valid option [1/2/3]:')
        select_goal()


# 4.8 Start app function

def start_app():
    """
    Prints greeting and triggers get_location function
    """
    print(colored("\nSPORTIFY\n", "blue", attrs=["bold"]))
    print('Welcome to Sportify!\n')
    print('All you need for your workouts, anywhere you go.\n')
    select_goal()



# 5. RUN APP
start_app()


    
