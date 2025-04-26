import os
import pandas as pd
import requests
from datetime import datetime, timezone

# Load tokens
def load_tokens(file_path='tokens.txt'):
    tokens = {}
    with open(file_path, 'r') as f:
        for line in f:
            if ':' in line:
                username, token = line.strip().split(':', 1)
                tokens[username.strip()] = token.strip()
    return tokens

# File path
file_path = '/home/vignesh/gittracker/gitusers_updated.xlsx'
TODAY = datetime.now(timezone.utc).date().strftime('%d-%m-%Y')

# Load or create DataFrame
if os.path.exists(file_path):
    df = pd.read_excel(file_path)
else:
    df = pd.DataFrame(columns=['NAME', 'GITLINK'])

# Load user tokens
user_tokens = load_tokens('tokens.txt')
default_token = user_tokens.get('vigneshwaralingam m')

# Add today’s column if not exists
if TODAY not in df.columns:
    df[TODAY] = 'Not checked'

# Loop through each user
for idx, row in df.iterrows():
    username = row['NAME'].strip()
    token = user_tokens.get(username, default_token)
    headers = {'Private-Token': token}

    # Search user
    search_url = f'https://gitlab.com/api/v4/users?username={username}'
    search_resp = requests.get(search_url, headers=headers)

    if search_resp.status_code != 200 or not search_resp.json():
        print(f"❌ User {username} not found or API error")
        df.at[idx, TODAY] = 'Not found'
        continue

    user_info = search_resp.json()[0]
    user_id = user_info['id']

    # Update correct GITLINK if empty
    if pd.isna(row['GITLINK']) or row['GITLINK'].strip() == '':
        df.at[idx, 'GITLINK'] = user_info['web_url']

    # Fetch events
    events_url = f'https://gitlab.com/api/v4/users/{user_id}/events'
    events_resp = requests.get(events_url, headers=headers)

    if events_resp.status_code != 200:
        print(f"❌ Error fetching events for {username}")
        df.at[idx, TODAY] = 'Error'
        continue

    events = events_resp.json()
    push_count = 0

    for event in events:
        if event.get('action_name') == 'pushed to':
            pushed_date = datetime.strptime(event['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ').date()
            if pushed_date.strftime('%d-%m-%Y') == TODAY:
                push_count += 1

    if push_count > 0:
        df.at[idx, TODAY] = f'{push_count} pushes'
        print(f"✅ {username} pushed today ({push_count} times).")
    else:
        df.at[idx, TODAY] = 'Not pushed'
        print(f"⚠️ {username} did not push today.")

# Save updated Excel
df.to_excel(file_path, index=False)
print(f"✅ Done — updated file saved at {file_path}")
