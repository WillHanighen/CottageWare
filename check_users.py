"""
Script to check and update user tiers
"""
from database import SessionLocal
from models import User, UserProfile

# Create database session
db = SessionLocal()

# Get all users with their profiles
users = db.query(User).all()

print("Users and their tiers:")
for user in users:
    tier = user.profile.account_tier if hasattr(user, 'profile') and user.profile else "No profile"
    print(f"Username: {user.username}, Tier: {tier}")

# Check for admin user
admin = db.query(User).filter(User.username == "admin").first()
if admin:
    # Ensure admin has profile
    if not hasattr(admin, 'profile') or not admin.profile:
        print("\nCreating profile for admin user...")
        admin_profile = UserProfile(
            user_id=admin.id,
            bio="Site administrator",
            location="Server Room",
            signature="CottageWare Administrator",
            account_tier=4  # Set to admin tier
        )
        db.add(admin_profile)
        db.commit()
    else:
        # Update admin tier if needed
        if admin.profile.account_tier < 4:
            print(f"\nUpdating admin tier from {admin.profile.account_tier} to 4")
            admin.profile.account_tier = 4
            db.commit()
        else:
            print(f"\nAdmin already has sufficient privileges (Tier {admin.profile.account_tier})")
else:
    print("\nNo admin user found")

# Close the database session
db.close()
