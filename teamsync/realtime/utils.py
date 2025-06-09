from django.core.cache import cache

def add_online_user(workspace_id, user_id):
    key = f"workspace_{workspace_id}_online_users"
    online_users = set(cache.get(key, []))
    online_users.add(user_id)
    cache.set(key, list(online_users), timeout=None)

def remove_online_user(workspace_id, user_id):
    key = f"workspace_{workspace_id}_online_users"
    online_users = set(cache.get(key, []))
    online_users.discard(user_id)
    cache.set(key, list(online_users), timeout=None)

def is_user_online_in_workspace(workspace_id, user_id):
    key = f"workspace_{workspace_id}_online_users" 
    online_users = cache.get(key, [])
    print(f"🟡 Checking {user_id} in {key}: {online_users}")
    return str(user_id) in map(str, online_users)


def get_online_users_in_workspace(workspace_id):
    key = f"workspace_{workspace_id}_online_users"
    return cache.get(key, [])
