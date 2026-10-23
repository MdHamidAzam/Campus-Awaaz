"""
FIXED ADMIN ACCOUNTS  (there is no admin signup anywhere in the app)

To change an admin later: edit email / password below, save, and restart the backend.
On every start-up these rows are synced into the database:
  * email or password changed  -> old login stops working, new one works (old sessions are logged out)
  * an admin removed from here -> that admin account is deleted
Keep this file private (do not push it to a public GitHub repo).
"""
ADMIN_ACCOUNTS = [
    {"name": "Admin 1", "email": "itsaashique01@gmail.com",      "password": "6200260817"},
    {"name": "Admin 2", "email": "hm2563749@gmail.com",          "password": "7061790653"},
    {"name": "Admin 3", "email": "shivangimaurya9125@gmail.com", "password": "7307734638"},
]
