# set_owner.py - One-time script to set user ID 1 to account tier 5 (Owner)

from sqlalchemy.orm import Session
from database import SessionLocal
from models import User, UserProfile

uid = int(input("Enter user ID: "))
level = int(input("Enter account tier: "))

def set_level():
    """Set user ID {uid} to account tier {level}"""

    db = SessionLocal()
    try:
        # Find user with ID 1
        user = db.query(User).filter(User.id == uid).first()
        if not user:
            print(f"User with ID {uid} not found")
            return
        
        # Ensure user has a profile
        if not user.profile:
            profile = UserProfile(user_id=user.id)
            db.add(profile)
            db.commit()
            user = db.query(User).filter(User.id == uid).first()
        
        # Set account tier to level
        user.profile.account_tier = level
        db.commit()
        
        print(f"User {user.username} (ID: {user.id}) has been set to account tier {user.profile.account_tier} ({user.profile.tier_name})")
    
    except Exception as e:
        print(f"Error setting account tier: {e}")
    finally:
        db.close()

if level == 1:
    if input(f"Are you sure you want to set user ID {uid} to account tier 1 (Free)? (y/n): ") != "y":
        set_level()
    else:
        print("canceled")
elif level == 2:
    if input(f"Are you sure you want to set user ID {uid} to account tier 2 (Basic)? (y/n): ") != "y":
        set_level()
    else:
        print("canceled")
elif level == 3:
    if input(f"Are you sure you want to set user ID {uid} to account tier 3 (Standard)? (y/n): ") != "y":
        set_level()
    else:
        print("canceled")
elif level == 4:
    if input(f"Are you sure you want to set user ID {uid} to account tier 4 (Premium)? (y/n): ") != "y":
        set_level()
    else:
        print("canceled")
elif level == 5:
    if input(f"Are you sure you want to set user ID {uid} to account tier 5 (Owner)? (y/n): ") != "y":
        set_level()
    else:
        print("canceled")
