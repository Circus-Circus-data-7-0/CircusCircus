"""
Flask configuration variables.
This file stores all the settings Flask needs to run the app, including
database connection details. It reads settings from environment variables,
but has safe defaults if those variables aren't set.
"""
from os import environ, path
import pymysql

basedir = path.abspath(path.dirname(__file__))
# load_dotenv(path.join(basedir, '.env'))


def try_admin_connection():
    """
    Try to connect to MySQL as root using multiple methods.
    Returns a tuple of (connection, method) if successful, or (None, None) if all fail.
    
    This tries:
    1. Socket connection (Unix socket, no password needed on fresh installs)
    2. TCP/IP localhost with no password
    3. TCP/IP localhost with password from MYSQL_ROOT_PASSWORD env var
    """
    # Common socket locations on macOS
    socket_paths = [
        "/tmp/mysql.sock",
        "/var/run/mysql/mysql.sock",
        "/usr/local/var/run/mysql.sock"
    ]
    
    # Try socket connections first (no password needed on fresh installs)
    for socket_path in socket_paths:
        try:
            admin_conn = pymysql.connect(
                user="root",
                unix_socket=socket_path,
                charset='utf8mb4'
            )
            return (admin_conn, f"socket ({socket_path})")
        except Exception:
            continue
    
    # Try TCP/IP localhost with no password
    try:
        admin_conn = pymysql.connect(
            host="127.0.0.1",
            port=3306,
            user="root",
            password="",
            charset='utf8mb4'
        )
        return (admin_conn, "TCP/IP (no password)")
    except Exception:
        pass
    
    # Try TCP/IP with a password from environment variable (if user set one)
    root_password = environ.get("MYSQL_ROOT_PASSWORD", "")
    if root_password:
        try:
            admin_conn = pymysql.connect(
                host="127.0.0.1",
                port=3306,
                user="root",
                password=root_password,
                charset='utf8mb4'
            )
            return (admin_conn, "TCP/IP (with password)")
        except Exception:
            pass
    
    # All connection methods failed
    return (None, None)


def setup_database_and_user():
    """
    Ensure the database and app user exist in MySQL.
    This creates the database and app user during initial setup.
    
    Uses hardcoded 'root' for admin tasks and 'zipchat_app' for the app.
    This keeps setup separate from app connection logic.
    """
    # Setup always creates these - don't read from environment for these
    app_user = "zipchat_app"
    app_password = "password"
    db_host = "127.0.0.1"
    db_name = "ZipChat"
    
    # Try to connect as admin (root)
    admin_conn, method = try_admin_connection()
    
    if admin_conn is None:
        print(f"\n⚠ Could not connect to MySQL as root")
        print(f"  Socket connection not available (fresh installs should have this)")
        print(f"  TCP/IP connection with no password didn't work either")
        print(f"\n  To fix:")
        print(f"    A) If you just installed MySQL, try: brew services restart mysql")
        print(f"    B) If you set a root password, provide it for setup:")
        print(f"       export MYSQL_ROOT_PASSWORD='your_root_password'")
        print(f"       bash ./run.sh")
        print(f"    C) Or manually create the database and user:")
        print(f"       mysql -u root -p")
        print(f"       CREATE DATABASE {db_name};")
        print(f"       CREATE USER '{app_user}'@'{db_host}' IDENTIFIED BY '{app_password}';")
        print(f"       GRANT ALL PRIVILEGES ON {db_name}.* TO '{app_user}'@'{db_host}';")
        print(f"       FLUSH PRIVILEGES;")
        print(f"       EXIT;\n")
        return False
    
    try:
        print(f"✓ Connected to MySQL as root via {method}")
        
        with admin_conn.cursor() as cursor:
            # Create database
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`;")
            print(f"  ✓ Database '{db_name}' ready")
            
            # Create app user
            try:
                cursor.execute(f"CREATE USER IF NOT EXISTS '{app_user}'@'{db_host}' IDENTIFIED BY '{app_password}';")
                print(f"  ✓ App user '{app_user}' created")
            except pymysql.err.OperationalError as e:
                if "already exists" in str(e):
                    print(f"  ✓ App user '{app_user}' already exists")
                else:
                    raise
            
            # Grant permissions
            cursor.execute(f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{app_user}'@'{db_host}';")
            cursor.execute("FLUSH PRIVILEGES;")
            print(f"  ✓ Permissions granted")
            
        admin_conn.commit()
        admin_conn.close()
        print(f"✓ MySQL setup complete\n")
        return True
        
    except Exception as e:
        print(f"⚠ Error during setup: {e}\n")
        admin_conn.close()
        return False


def check_mysql_connection():
    """
    Verify the app can connect using the configured app credentials.
    Shows helpful errors if something is wrong.
    """
    # App uses these (can override with environment variables)
    app_user = environ.get("DB_USER", "zipchat_app")
    app_password = environ.get("DB_PASSWORD", "password")
    db_host = environ.get("DB_HOST", "127.0.0.1")
    db_port = int(environ.get("DB_PORT", "3306"))
    db_name = environ.get("DB_NAME", "ZipChat")
    
    try:
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=app_user,
            password=app_password,
            database=db_name,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        connection.close()
        print(f"✓ MySQL ready: {app_user}@{db_name}\n")
        return True
        
    except pymysql.err.OperationalError as e:
        error_code = e.args[0] if e.args else None
        
        if error_code == 2003:
            print(f"❌ MySQL not running on {db_host}:{db_port}")
            print(f"Start it: brew services start mysql\n")
            return False
            
        elif error_code == 1045:
            print(f"❌ Cannot login as '{app_user}'")
            print(f"Either the user doesn't exist or the password is wrong.")
            print(f"Make sure setup completed successfully above.\n")
            return False
            
        elif error_code == 1049:
            print(f"❌ Database '{db_name}' doesn't exist")
            print(f"Make sure setup completed successfully above.\n")
            return False
            
        else:
            print(f"❌ MySQL error ({error_code}): {e}\n")
            return False


def check_mysql_and_setup():
    """Initialize MySQL and check connection on app startup."""
    print("Checking MySQL setup...")
    setup_database_and_user()
    check_mysql_connection()


class Config:
    """
    Configuration class that stores all settings Flask needs.
    This includes database connection info, secret keys, and SQLAlchemy options.
    
    Settings can be customized by setting environment variables:
      - DB_USER: MySQL username (default: "zipchat_app")
      - DB_PASSWORD: MySQL password (default: "password")
      - DB_HOST: MySQL server address (default: "127.0.0.1")
      - DB_PORT: MySQL server port (default: "3306")
      - DB_NAME: Database name (default: "ZipChat")
    """
    
    # ========== GENERAL SETTINGS ==========
    # This is a secret key used to encrypt session data and CSRF tokens.
    # In production, this should be a long random string, not hardcoded!
    SECRET_KEY = 'kristofer'
    
    # Tell Flask which app module to use
    FLASK_APP = 'forum.app'

    
    # ========== DATABASE SETTINGS ==========
    # All these settings can be overridden with environment variables.
    # If not set, we use the defaults shown here.
    
    # Username for MySQL (the app will connect as this user)
    DB_USER = environ.get("DB_USER", "zipchat_app")
    
    # Password for that MySQL user
    # Default is "password" - change this or set via environment variable
    DB_PASSWORD = environ.get("DB_PASSWORD", "password")
    
    # Where MySQL is running (localhost = 127.0.0.1 on your own computer)
    DB_HOST = environ.get("DB_HOST", "127.0.0.1")
    
    # Port MySQL listens on (3306 is the standard MySQL port)
    DB_PORT = environ.get("DB_PORT", "3306")
    
    # Name of the database to use
    DB_NAME = environ.get("DB_NAME", "ZipChat")

    # Build the full database URL that SQLAlchemy uses to connect
    # Format: mysql+pymysql://username:password@host:port/database
    # This tells Python how to connect to the MySQL database
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # SQLALCHEMY_ECHO prints SQL queries to the console (useful for debugging)
    # Set to True if you want to see what SQL is being run
    SQLALCHEMY_ECHO = False
    
    # SQLALCHEMY_TRACK_MODIFICATIONS is usually set to False for better performance
    # It tells SQLAlchemy not to track every single change to objects
    SQLALCHEMY_TRACK_MODIFICATIONS = False


# Run the MySQL setup check when this config file is imported
# This ensures MySQL is ready before the app tries to use it
try:
    check_mysql_and_setup()
except Exception as e:
    print(f"⚠ Warning during MySQL setup: {e}")