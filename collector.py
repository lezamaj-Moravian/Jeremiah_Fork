import os
from dotenv import load_dotenv
import datetime
import time
import requests
import database

#info about the athlete is stored in the database, so no need to store it here

load_dotenv()

def exchange_code_for_tokens(code):
    client_id = os.getenv("STRAVA_CLIENT_ID")
    client_secret = os.getenv("STRAVA_CLIENT_SECRET")

    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'grant_type': 'authorization_code'
    }
    response = requests.post("https://www.strava.com/oauth/token", data=payload)

    if response.status_code != 200:
        print(f"Error exchanging code: {response.text}")
        response.raise_for_status()

    return response.json()

def authorize_and_save_user(code, user_id):
    data = exchange_code_for_tokens(code)

    access_token = data.get('access_token')
    refresh_token = data.get('refresh_token')
    expires_at = data.get('expires_at')

    athlete_info = data.get('athlete', {})

    strava_id = athlete_info.get('id')
    first_name = athlete_info.get('firstname')
    last_name = athlete_info.get('lastname')
    gender = athlete_info.get('sex')

    database.save_user_tokens_and_info(
        user_id,
        access_token,
        refresh_token,
        expires_at,
        strava_id,
        first_name,
        last_name,
        gender
    )


def fetch_athlete_data(user_id):
    print(f"updating user data for ID: {user_id}")
    user_row = database.get_user_by_id(user_id)

    if user_row == None:
        print(f"Could not find User ID: {user_id}")
        return
    username = user_row["username"]

    try:
        athlete_row = database.get_row_from_athletes_table(username)
        add_initial_activities_to_db(username)
        print(f"Sync complete for {username}")
    except Exception as e:
        print(f"Sync failed for {username}")

def get_valid_access_token(user_id):
    tokens = database.get_user_tokens(user_id)

    if not tokens:
        print(f"No tokens found for User: {user_id}")
        return None
    
    access_token = tokens['strava_access_token']
    refresh_token = tokens['strava_refresh_token']
    token_expiration = tokens['token_expiration']

#FIXME take this out eventually
    if token_expiration is None:
        print(f"DEBUG: Expiration is None for User {user_id}. Forcing refresh...")
        # If we have a refresh token, use it to fix the DB
        if refresh_token:
            return refresh_access_token(user_id, refresh_token)
        else:
            print("ERROR: No refresh token available. User must re-connect.")
            return None

    if token_expiration < time.time() and token_expiration > (token_expiration - 300):
        return refresh_access_token(user_id, refresh_token)
    
    return access_token


def refresh_access_token(user_id, refresh_token):
    client_id = os.getenv('STRAVA_CLIENT_ID')
    client_secret = os.getenv('STRAVA_CLIENT_SECRET')
    """Refresh Strava access token. Returns new access token."""
    token_url = "https://www.strava.com/oauth/token"
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    
    response = requests.post(token_url, data=payload)
    response.raise_for_status()
    data = response.json()

    database.save_user_tokens_and_info(
        user_id,
        data['access_token'],
        data['refresh_token'],
        data['expires_at']
    )

    return data['access_token']

def get_current_user_information(username):
    #username is the session username
    client_id = database.get_client_id_from_username(username)
    client_secret = database.get_client_secret_by_username(username)
    refresh_token = database.get_refresh_token_by_username(username)

    access_token = refresh_access_token(client_id, client_secret, refresh_token)

    athlete_url = "https://www.strava.com/api/v3/athlete"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(athlete_url, headers=headers)
    response.raise_for_status()
    athlete_info = response.json()

    return athlete_info


def fetch_activities(username):
    """Fetches activities from Strava API and stores them in cache. Returns activities or raises exception."""

    print(f"DEBUG: fetch_activities called for username: {username}")
    client_id = database.get_client_id_from_username(username)
    client_secret = database.get_client_secret_by_username(username)
    refresh_token = database.get_refresh_token_by_username(username)
    
    print(f"DEBUG: Retrieved credentials - client_id: {client_id}, has_secret: {bool(client_secret)}, has_refresh: {bool(refresh_token)}")
    
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
    
    print(f"DEBUG: Making API call to fetch activities from Strava")
    print(f"DEBUG: Using access token (first 20 chars): {access_token[:20] if access_token else 'None'}...")
    response = requests.get(activities_url, headers=headers)
    
    # Log response details for debugging
    print(f"DEBUG: Response status code: {response.status_code}")
    if response.status_code != 200:
        print(f"DEBUG: Response text: {response.text[:500]}")
        try:
            error_json = response.json()
            print(f"DEBUG: Error JSON: {error_json}")
            # Check for scope/permission errors
            if 'errors' in error_json:
                for error in error_json.get('errors', []):
                    if 'activity:read' in str(error.get('field', '')):
                        print(f"ERROR: Access token is missing 'activity:read' scope!")
                        print(f"ERROR: You need to re-authenticate with Strava to get a token with the correct scopes.")
                        print(f"ERROR: Use the OAuth flow at /connect/strava or get a new refresh token with 'activity:read_all' scope.")
        except:
            pass
        print(f"DEBUG: Response headers: {dict(response.headers)}")
        print(f"DEBUG: Request URL: {activities_url}")
        print(f"DEBUG: Request headers: {headers}")
    
    response.raise_for_status()
    activities = response.json()
    print(f"DEBUG: Successfully fetched {len(activities)} activities from Strava")
    
    # Store activities in cache
    activities_cache = activities
    last_fetch_date = datetime.datetime.now()
    
    return activities

def fetch_and_save_user_data(user_id):
    seconds_in_30_days = 2592000

    try:
        token = get_valid_access_token(user_id)

        start_date = int(time.time()) - seconds_in_30_days

        url = "https://www.strava.com/api/v3/athlete/activities"
        headers = {"Authorization": f"Bearer {token}"}
        params = {"after": start_date, "per_page": 50}

        response = requests.get(url,headers=headers, params=params)
        response.raise_for_status()
        activities = response.json()

        count = 0
        for activity in activities:
            miles = round(activity['distance'] * 0.000621371, 2)
            date_str = activity['start_date_local'].split('T')[0]
            title = activity['name']

            database.create_activity(
                user_id=user_id,
                date=date_str,
                distance=miles,
                title=title

            )
            count += 1

        print(f"Imported {count} activities for User: {user_id}")

    except Exception as e:
        print(f"Error for User {user_id}: {e}")




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