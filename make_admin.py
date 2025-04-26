#!/usr/bin/env python
# make_admin.py - Script to update a user's tier level

import sys
import argparse
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import User, UserProfile

def update_user_tier(user_id: int, tier_level: int):
    """
    Update a user's account tier level
    
    Args:
        user_id: The ID of the user to update
        tier_level: The new tier level to set
    
    Returns:
        bool: True if successful, False otherwise
    """
    db = SessionLocal()
    try:
        # First check if the user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"Error: User with ID {user_id} not found")
            return False
        
        # Validate tier level
        if tier_level < 0 or tier_level > 5:
            print(f"Error: Invalid tier level {tier_level}. Must be between 0 and 5.")
            return False
            
        # Get tier name for display
        tier_names = {
            0: "Unregistered",
            1: "Registered",
            2: "Customer",
            3: "Moderator",
            4: "Administrator",
            5: "Owner"
        }
        tier_name = tier_names.get(tier_level, "Unknown")
            
        # Check if the user has a profile
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            # Create a profile if it doesn't exist
            print(f"Creating profile for user {user.username} (ID: {user_id})")
            profile = UserProfile(
                user_id=user_id,
                account_tier=tier_level
            )
            db.add(profile)
        else:
            # Update the existing profile
            old_tier = profile.tier_name
            print(f"Updating profile for user {user.username} (ID: {user_id})")
            print(f"Changing tier from {old_tier} to {tier_name}")
            profile.account_tier = tier_level
            
        # Commit the changes
        db.commit()
        print(f"Success: User {user.username} (ID: {user_id}) is now a {tier_name}")
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

def list_users():
    """List all users with their IDs and current tier"""
    db = SessionLocal()
    try:
        users = db.query(User, UserProfile).outerjoin(
            UserProfile, User.id == UserProfile.user_id
        ).all()
        
        print("\nUser List:")
        print("-" * 80)
        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Current Tier':<15} {'Level':<5}")
        print("-" * 80)
        
        for user, profile in users:
            tier = profile.tier_name if profile else "No Profile"
            level = profile.account_tier if profile else "-"
            print(f"{user.id:<5} {user.username:<20} {user.email:<30} {tier:<15} {level:<5}")
            
        print("-" * 80)
        print("Tier Levels: 0=Unregistered, 1=Registered, 2=Customer, 3=Moderator, 4=Admin, 5=Owner")
    except Exception as e:
        print(f"Error listing users: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update a user's tier level")
    parser.add_argument("-i", "--id", type=int, help="ID of the user to update")
    parser.add_argument("-l", "--level", type=int, help="New tier level (0-5)")
    parser.add_argument("--list", action="store_true", help="List all users with their IDs and current tier")
    
    args = parser.parse_args()
    
    if args.list:
        list_users()
    elif args.id is not None and args.level is not None:
        update_user_tier(args.id, args.level)
    else:
        parser.print_help()
