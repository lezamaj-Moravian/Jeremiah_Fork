import datetime
import time
import requests
import database

#info about the athlete is stored in the database, so no need to store it here

global activities_cache #idk how this is workin atm
global last_fetch_date #last fetch date for activities

def refresh_access_token(client_id, client_secret, refresh_token):
    token_url = "https://www.strava.com/oauth/token"
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    response = requests.post(token_url, data=payload)
    response.raise_for_status()
    tokens = response.json()
    return tokens['access_token']

def get_current_user_information(username):
    #username is the session username
    client_id = database.get_client_id_from_username(username)
    client_secret = database.get_client_secret_by_username(username)
    refresh_token = database.get_refresh_token_by_username(username)

    access_token = refresh_access_token(client_id, client_secret, refresh_token)

    athlete_url = "https://www.strava.com/api/v3/athlete/athlete"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(athlete_url, headers=headers)
    response.raise_for_status()
    athlete_info = response.json()

    return athlete_info

def update_athlete_info_in_db(username):
    athlete_info = get_current_user_information(username)
    database.update_athlete_with_collector_info(username, athlete_info['firstname'], athlete_info['lastname'], athlete_info['sex'])


def fetch_activities(username):
    """Fetches activities from Strava API and stores them in cache. Returns activities or raises exception."""
    
    global activities_cache
    global last_fetch_date

    client_id = database.get_client_id_from_username(username)
    client_secret = database.get_client_secret_by_username(username)
    refresh_token = database.get_refresh_token_by_username(username)
    
    if not all([client_id, client_secret, refresh_token]):
        raise ValueError('Missing Strava credentials in database')
    
    # Refresh access token
    access_token = refresh_access_token(client_id, client_secret, refresh_token)
    
    # Get activities from Strava API
    activities_url = "https://www.strava.com/api/v3/athlete/activities"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    # params = {
    #     "per_page": 10
    # }
    
    response = requests.get(activities_url, headers=headers)
    response.raise_for_status()
    activities = response.json()
    
    # Store activities in cache
    activities_cache = activities
    last_fetch_date = datetime.datetime.now()
    
    return activities

def add_new_activities_to_db(username):
    activities = fetch_activities()
    user_id = database.get_user_id_from_username(username)
    for activity in activities:
        database.create_activity(user_id, activity['date'], activity['distance'], activity['name'])


def fetch_activities_after_date(username, date):
    """Fetches activities from Strava API and stores them in cache. Returns activities or raises exception."""
    global activities_cache
    global last_fetch_date
    
    date_utc = datetime.datetime.strptime(date, "%Y-%m-%d")
    date_timestamp = int(time.mktime(date_utc.timetuple()))

    client_id = database.get_client_id_from_username(username)
    client_secret = database.get_client_secret_by_username(username)
    refresh_token = database.get_refresh_token_by_username(username)
    
    if not all([client_id, client_secret, refresh_token]):
        raise ValueError('Missing Strava credentials in database')
    
    # Refresh access token
    access_token = refresh_access_token(client_id, client_secret, refresh_token)
    
    # Get activities from Strava API
    activities_url = "https://www.strava.com/api/v3/athlete/activities"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "after": date_timestamp
    }
    
    response = requests.get(activities_url, headers=headers, params=params)
    response.raise_for_status()
    activities = response.json()
    
    # Store activities in cache
    activities_cache = activities
    last_fetch_date = datetime.datetime.now()
    
    return activities