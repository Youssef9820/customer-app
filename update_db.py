# update_db.py
import sqlite3

# Connect to database
conn = sqlite3.connect('instance/customers.db')
cursor = conn.cursor()

try:
    # Add role column
    cursor.execute('ALTER TABLE user ADD COLUMN role VARCHAR(20) DEFAULT "user" NOT NULL')
    print("✅ Added role column!")
except Exception as e:
    print(f"Column might already exist: {e}")

# Make first user admin
cursor.execute('UPDATE user SET role = "admin" WHERE id = (SELECT MIN(id) FROM user)')
conn.commit()

# Check it worked
cursor.execute('SELECT id, username, role FROM user')
users = cursor.fetchall()
print("\n📋 Current users:")
for user in users:
    print(f"  ID: {user[0]}, Username: {user[1]}, Role: {user[2]}")

conn.close()
print("\n✅ Database updated successfully!")