"""
Database seeding script for CottageWare
Creates initial categories, forums, users, and sample content
"""

from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import User, Role, Category, Forum, Thread, Post, Shoutbox, Product, UserProfile
from auth import get_password_hash
import datetime

def seed_database():
    db = SessionLocal()
    
    # Create roles
    admin_role = get_or_create_role(db, "Admin", "Administrator with full access")
    moderator_role = get_or_create_role(db, "Moderator", "Forum moderator")
    user_role = get_or_create_role(db, "User", "Regular user")
    
    db.commit()
    
    # Create admin user
    admin_user = User(
        username="admin",
        email="admin@cottageware.com",
        hashed_password=get_password_hash("admin123"),
        is_active=True,
        avatar_url="/static/images/avatars/admin.png"
    )
    admin_user.roles.append(admin_role)
    
    # Create moderator user
    mod_user = User(
        username="moderator",
        email="mod@cottageware.com",
        hashed_password=get_password_hash("mod123"),
        is_active=True,
        avatar_url="/static/images/avatars/mod.png"
    )
    mod_user.roles.append(moderator_role)
    
    # Create regular users
    user1 = User(
        username="user1",
        email="user1@example.com",
        hashed_password=get_password_hash("user123"),
        is_active=True,
        avatar_url="/static/images/avatars/user1.png"
    )
    user1.roles.append(user_role)
    
    user2 = User(
        username="user2",
        email="user2@example.com",
        hashed_password=get_password_hash("user123"),
        is_active=True,
        avatar_url="/static/images/avatars/user2.png"
    )
    user2.roles.append(user_role)
    
    db.add_all([admin_user, mod_user, user1, user2])
    db.commit()
    
    # Create user profiles
    admin_profile = UserProfile(
        user_id=admin_user.id,
        bio="Site administrator",
        location="Server Room",
        signature="CottageWare Administrator"
    )
    
    mod_profile = UserProfile(
        user_id=mod_user.id,
        bio="Forum moderator",
        location="Forums",
        signature="Here to help!"
    )
    
    user1_profile = UserProfile(
        user_id=user1.id,
        bio="Regular user",
        location="Somewhere",
        signature="Just browsing"
    )
    
    user2_profile = UserProfile(
        user_id=user2.id,
        bio="Another user",
        location="Elsewhere",
        signature="Happy to be here"
    )
    
    db.add_all([admin_profile, mod_profile, user1_profile, user2_profile])
    db.commit()
    
    # Create categories
    announcements_category = Category(
        name="Announcements",
        description="Official announcements and news",
        order=1,
        is_public=True
    )
    
    general_category = Category(
        name="General",
        description="General discussion",
        order=2,
        is_public=True
    )
    
    reseller_category = Category(
        name="Reseller",
        description="Reseller discussions and products",
        order=3,
        is_public=True
    )
    
    support_category = Category(
        name="Support",
        description="Support forums",
        order=4,
        is_public=True
    )
    
    db.add_all([announcements_category, general_category, reseller_category, support_category])
    db.commit()
    
    # Create forums
    news_forum = Forum(
        category_id=announcements_category.id,
        name="News",
        description="Latest news and updates",
        order=1,
        is_public=True
    )
    
    official_forum = Forum(
        category_id=announcements_category.id,
        name="Official",
        description="Official announcements",
        order=2,
        is_public=True
    )
    
    general_forum = Forum(
        category_id=general_category.id,
        name="General Discussion",
        description="General discussion forum",
        order=1,
        is_public=True
    )
    
    introductions_forum = Forum(
        category_id=general_category.id,
        name="Introductions",
        description="Introduce yourself to the community",
        order=2,
        is_public=True
    )
    
    products_forum = Forum(
        category_id=reseller_category.id,
        name="Products",
        description="Discussion about products",
        order=1,
        is_public=True
    )
    
    reselling_forum = Forum(
        category_id=reseller_category.id,
        name="Reselling",
        description="Reselling information and guides",
        order=2,
        is_public=True
    )
    
    support_forum = Forum(
        category_id=support_category.id,
        name="General Support",
        description="General support questions",
        order=1,
        is_public=True
    )
    
    presale_forum = Forum(
        category_id=support_category.id,
        name="Presale Questions",
        description="Questions before purchasing",
        order=2,
        is_public=True
    )
    
    db.add_all([
        news_forum, official_forum, general_forum, introductions_forum,
        products_forum, reselling_forum, support_forum, presale_forum
    ])
    db.commit()
    
    # Create threads and posts
    welcome_thread = Thread(
        forum_id=news_forum.id,
        author_id=admin_user.id,
        title="Welcome to CottageWare",
        content="Welcome to the CottageWare forums! This is the place to discuss all things related to our reseller platform.",
        created_at=datetime.datetime.now(),
        is_sticky=True,
        views=42
    )
    
    db.add(welcome_thread)
    db.commit()
    
    welcome_reply = Post(
        thread_id=welcome_thread.id,
        author_id=mod_user.id,
        content="Thanks for the welcome! Looking forward to helping out here.",
        created_at=datetime.datetime.now() + datetime.timedelta(hours=1)
    )
    
    db.add(welcome_reply)
    db.commit()
    
    rules_thread = Thread(
        forum_id=official_forum.id,
        author_id=admin_user.id,
        title="Forum Rules",
        content="Please read and follow these forum rules:\n\n1. Be respectful to others\n2. No spamming\n3. Keep discussions on-topic\n4. No illegal content",
        created_at=datetime.datetime.now() - datetime.timedelta(days=1),
        is_sticky=True,
        views=35
    )
    
    db.add(rules_thread)
    db.commit()
    
    intro_thread = Thread(
        forum_id=introductions_forum.id,
        author_id=user1.id,
        title="Hello everyone!",
        content="Hi all, I'm new here. Looking forward to being part of the community!",
        created_at=datetime.datetime.now() - datetime.timedelta(days=2),
        views=12
    )
    
    db.add(intro_thread)
    db.commit()
    
    intro_reply = Post(
        thread_id=intro_thread.id,
        author_id=user2.id,
        content="Welcome to the forums! Let us know if you need any help.",
        created_at=datetime.datetime.now() - datetime.timedelta(days=2, hours=-3)
    )
    
    db.add(intro_reply)
    db.commit()
    
    product_thread = Thread(
        forum_id=products_forum.id,
        author_id=mod_user.id,
        title="Product Showcase",
        content="Check out our latest products available for reselling!",
        created_at=datetime.datetime.now() - datetime.timedelta(days=3),
        views=28
    )
    
    db.add(product_thread)
    db.commit()
    
    # Create shoutbox messages
    shout1 = Shoutbox(
        user_id=admin_user.id,
        message="Welcome to the new CottageWare forums!",
        created_at=datetime.datetime.now() - datetime.timedelta(hours=5)
    )
    
    shout2 = Shoutbox(
        user_id=user1.id,
        message="Thanks for the welcome!",
        created_at=datetime.datetime.now() - datetime.timedelta(hours=4)
    )
    
    shout3 = Shoutbox(
        user_id=user2.id,
        message="How do I get started with reselling?",
        created_at=datetime.datetime.now() - datetime.timedelta(hours=3)
    )
    
    shout4 = Shoutbox(
        user_id=mod_user.id,
        message="Check out the guides in the Reselling forum!",
        created_at=datetime.datetime.now() - datetime.timedelta(hours=2)
    )
    
    db.add_all([shout1, shout2, shout3, shout4])
    db.commit()
    
    # Create products
    product1 = Product(
        name="CompKiller CS2",
        description="Premium CS2 cheat with aimbot, ESP, and more features",
        price="$19.99/month",
        image_url="/static/images/products/cs2.jpg",
        external_url="https://example.com/compkiller-cs2",
        is_featured=True,
        created_at=datetime.datetime.now() - datetime.timedelta(days=30)
    )
    
    product2 = Product(
        name="CompKiller Valorant",
        description="Undetected Valorant cheat with advanced features",
        price="$24.99/month",
        image_url="/static/images/products/valorant.jpg",
        external_url="https://example.com/compkiller-valorant",
        is_featured=True,
        created_at=datetime.datetime.now() - datetime.timedelta(days=20)
    )
    
    product3 = Product(
        name="CompKiller Apex",
        description="Apex Legends cheat with aim assist and ESP",
        price="$17.99/month",
        image_url="/static/images/products/apex.jpg",
        external_url="https://example.com/compkiller-apex",
        is_featured=False,
        created_at=datetime.datetime.now() - datetime.timedelta(days=15)
    )
    
    db.add_all([product1, product2, product3])
    db.commit()
    
    print("Database seeded successfully!")

def check_if_tables_exist():
    """Check if tables already exist in the database"""
    inspector = sqlalchemy.inspect(engine)
    tables = inspector.get_table_names()
    return len(tables) > 0

def check_if_data_exists():
    """Check if data already exists in the database"""
    db = SessionLocal()
    try:
        # Check if roles exist
        roles_exist = db.query(Role).count() > 0
        # Check if users exist
        users_exist = db.query(User).count() > 0
        # Check if categories exist
        categories_exist = db.query(Category).count() > 0
        
        return roles_exist and users_exist and categories_exist
    except Exception as e:
        print(f"Error checking if data exists: {e}")
        return False
    finally:
        db.close()

def get_or_create_role(db, name, description):
    """Get or create a role"""
    role = db.query(Role).filter(Role.name == name).first()
    if not role:
        role = Role(name=name, description=description)
        db.add(role)
        db.flush()
    return role

if __name__ == "__main__":
    import sqlalchemy
    
    # Create all tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Check if data already exists
    if not check_if_data_exists():
        print("Seeding database...")
        seed_database()
        print("Database seeded successfully!")
    else:
        print("Database already contains data. Skipping seeding.")
