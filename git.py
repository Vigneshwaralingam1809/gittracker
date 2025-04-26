#!/usr/bin/env python3
import pandas as pd
import requests
from datetime import datetime

# Function to load tokens from a file
def load_tokens(file_path='tokens.txt'):
    tokens = {}
    with open(file_path, 'r') as f:
        for line in f:
            if ':' in line:
                username, token = line.strip().split(':', 1)
                tokens[username.strip()] = token.strip()
    return tokens

# 1. Load Excel file
df = pd.read_excel('/home/vignesh/gittracker/git.xlsx')
df['Pushed_Today'] = 'NO'

# 2. Date for today's comparison
TODAY = datetime.utcnow().date()

# 3. Load user tokens
user_tokens = load_tokens('tokens.txt')
default_token = user_tokens.get('vigneshwaralingam m')  # fallback token

# 4. Loop through each user
for idx, row in df.iterrows():
    username = row['NAME'].strip()
    token = user_tokens.get(username, default_token)
    headers = {'Private-Token': token}

    # Get user ID first (API needs user ID, not username)
    search_url = f'https://gitlab.com/api/v4/users?username={username}'
    search_resp = requests.get(search_url, headers=headers)

    if search_resp.status_code != 200 or not search_resp.json():
        print(f"❌ User {username} not found or API error")
        continue

    user_id = search_resp.json()[0]['id']

    # Fetch events for that user
    events_url = f'https://gitlab.com/api/v4/users/{user_id}/events'
    events_resp = requests.get(events_url, headers=headers)

    if events_resp.status_code != 200:
        print(f"❌ Error fetching events for {username}")
        continue

    events = events_resp.json()
    for event in events:
        if event.get('action_name') == 'pushed to':
            pushed_date = datetime.strptime(event['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ').date()
            if pushed_date == TODAY:
                df.at[idx, 'Pushed_Today'] = 'YES'
                print(f"✅ {username} pushed today.")
                break

# 5. Save updated Excel file
df.to_excel('/home/vignesh/gittracker/gitusers_updated.xlsx', index=False)
print("✅ Done — updated file saved as gitusers_updated.xlsx")
