# CottageWare

CottageWare is a comprehensive web forum and e-commerce platform built with FastAPI, featuring real-time communication, user authentication, and an administrative interface.

## Features

### Forum System
- Public and private forum areas with different access levels
- Thread and post management
- Real-time updates via WebSockets
- Shoutbox for quick community interaction
- Markdown support for rich text formatting
- Thread view tracking

### User Management
- Role-based access control
- User profiles with customizable avatars and signatures
- OAuth integration with Google
- Traditional username/password authentication

### E-Commerce
- Product listing and management
- Featured products showcase

### Admin Panel
- Comprehensive dashboard with statistics
- Product management (add, edit, delete)
- User management
- Forum and category configuration
- Site settings

## Technology Stack

- **Backend**: FastAPI (Python)
- **Database**: SQLAlchemy with SQLite
- **Frontend**: Jinja2 Templates, JavaScript
- **Authentication**: JWT, OAuth (Google)
- **Real-time Communication**: WebSockets

## Requirements

- Python 3.7+
- Dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/WillHanighen/CottageWare.git
   cd cottageware
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables by creating a `.env` file:
   ```
   SECRET_KEY=your_secret_key
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   ```

5. Initialize the database:
   ```
   python seed_db.py
   ```

6. Create an admin user:
   ```
   python create_admin.py
   ```

## Running the Application

Start the application with:
```
uvicorn main:app --reload
```

The application will be available at `http://localhost:8000`

## Admin Access

The admin panel is accessible at `/admin` for users with admin privileges (tier 4 or higher).

## Project Structure

- `main.py`: Entry point and route definitions
- `models.py`: Database models
- `auth.py`: Authentication functionality
- `admin.py`: Admin panel functionality
- `database.py`: Database configuration
- `utils.py`: Utility functions
- `templates/`: HTML templates
- `static/`: CSS, JavaScript, and other static files
- `content/`: User-uploaded content

## WebSocket Features

The application uses WebSockets for real-time features:
- Live chat in forums
- Online user tracking
- Instant notifications

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
