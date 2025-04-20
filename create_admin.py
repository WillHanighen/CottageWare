"""
Script to create an admin user for CottageWare
"""
from database import SessionLocal
from models import User, UserProfile, Role
from auth import get_password_hash

# Create database session
db = SessionLocal()

# Create admin user
print("Creating admin user...")
admin_password = "admin123"  # You should change this to a secure password
admin_user = User(
    username="admin",
    email="admin@cottageware.com",
    hashed_password=get_password_hash(admin_password),
    is_active=True,
    avatar_url="/static/images/avatars/admin.png"
)

# Check if user already exists
existing_user = db.query(User).filter(User.username == "admin").first()
if existing_user:
    print(f"Admin user already exists (ID: {existing_user.id})")
    admin_user = existing_user
else:
    db.add(admin_user)
    db.commit()
    print(f"Created admin user (ID: {admin_user.id})")

# Add admin role if it exists
admin_role = db.query(Role).filter(Role.name == "Admin").first()
if admin_role and admin_role not in admin_user.roles:
    admin_user.roles.append(admin_role)
    db.commit()
    print("Added Admin role to user")

# Create or update admin profile with tier 4 (admin)
admin_profile = db.query(UserProfile).filter(UserProfile.user_id == admin_user.id).first()
if not admin_profile:
    admin_profile = UserProfile(
        user_id=admin_user.id,
        bio="Site administrator",
        location="Admin Panel",
        signature="CottageWare Administrator",
        account_tier=4  # Set to admin tier
    )
    db.add(admin_profile)
    db.commit()
    print("Created admin profile with tier 4")
else:
    # Update admin tier if needed
    if admin_profile.account_tier < 4:
        print(f"Updating admin tier from {admin_profile.account_tier} to 4")
        admin_profile.account_tier = 4
        db.commit()
    else:
        print(f"Admin profile already has sufficient privileges (Tier {admin_profile.account_tier})")

print("\nAdmin user details:")
print(f"Username: admin")
print(f"Password: {admin_password}")
print(f"Email: admin@cottageware.com")
print(f"Tier: {admin_profile.account_tier}")
print("\nYou can now log in with these credentials to access the admin panel.")

# Close the database session
db.close()
