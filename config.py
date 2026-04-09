"""
Flask configuration variables.
This file stores all the settings Flask needs to run the app, including
database connection details. It reads settings from environment variables,
but has safe defaults if those variables aren't set.
 
This file also does a small amount of startup work for MySQL so the app can
try to prepare its database automatically before Flask builds tables.
"""
from os import environ, path
import pymysql

basedir = path.abspath(path.dirname(__file__))
# If we ever want to load a local .env file again, this is the place to do it.
# It is left commented out because the project currently relies on environment
# variables provided by the launcher script instead of a separate .env file.
# from dotenv import load_dotenv
# load_dotenv(path.join(basedir, '.env'))


def try_admin_connection():
    """
    Try to connect to MySQL as the local admin user.

    Why this exists:
    - The app needs a way to create the database and app user on first run.
    - On some machines MySQL allows local admin access through a socket.
    - On other machines the root account may need a password.

    What it returns:
    - (connection, method) if one of the connection attempts worked.
    - (None, None) if every attempt failed.

    The function tries the most common local MySQL access paths first and only
    falls back to a root password if the environment provides one.
    """
    # Common socket locations on macOS.
    # A socket connection is the most convenient option when MySQL is installed
    # locally because it may work without needing a password at all.
    socket_paths = [
        "/tmp/mysql.sock",
        "/var/run/mysql/mysql.sock",
        "/usr/local/var/run/mysql.sock"
    ]
    
    # Try socket connections first.
    # We stop at the first one that works because the exact socket path can
    # vary depending on how MySQL was installed.
    for socket_path in socket_paths:
        try:
            admin_conn = pymysql.connect(
                user="root",
                unix_socket=socket_path,
                charset='utf8mb4'
            )
            return (admin_conn, f"socket ({socket_path})")
        except Exception:
            # If this socket does not exist or the server rejects the connection,
            # we just move on to the next possible path.
            continue
    
    # Try plain TCP/IP next.
    # This is the simplest network-style connection to local MySQL.
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
    
    # If the machine has a root password, allow the launcher to supply it.
    # This keeps the code flexible for teams with different MySQL setups.
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
                # A password was provided, but it still did not work.
                # The caller will handle the failure message.
            pass
    
            # If we get here, MySQL admin access is not available through any of the
            # local methods we tried.
    return (None, None)


def setup_database_and_user():
    """
        Ensure the database and app user exist in MySQL.

        What this does:
        - creates the database if it does not exist
        - creates the app user if it does not exist
        - grants the app user access to the database

        Why it is here:
        - A teammate should be able to run the app without manually preparing MySQL
            every time.
        - This is best-effort bootstrapping, not a replacement for proper database
            administration in production.

        Important detail:
        - This function uses a local MySQL admin connection only for setup tasks.
        - The actual app still connects as the normal application user.
    """
        # These values define the default app database identity.
        # We keep them simple and consistent so the launcher and config agree.
    app_user = "zipchat_app"
    app_password = "password"
    db_host = "127.0.0.1"
    db_name = "ZipChat"
    
        # Try to connect as the local MySQL admin user.
        # If this fails, we can still continue later and let the normal app
        # connection path explain what is missing.
    admin_conn, method = try_admin_connection()
    
    if admin_conn is None:
                # We could not obtain admin access, so we cannot auto-create anything.
                # The printed instructions are meant to tell a teammate exactly what to
                # do next without having to inspect the code.
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
            # Create the database if it does not already exist.
            # Backticks around the name make the SQL a little safer if the
            # database name ever contains special characters.
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`;")
            print(f"  ✓ Database '{db_name}' ready")
            
            # Create the application user.
            # This is the user the Flask app itself will use during normal
            # runtime, not the root/admin account.
            try:
                cursor.execute(f"CREATE USER IF NOT EXISTS '{app_user}'@'{db_host}' IDENTIFIED BY '{app_password}';")
                print(f"  ✓ App user '{app_user}' created")
            except pymysql.err.OperationalError as e:
                if "already exists" in str(e):
                    print(f"  ✓ App user '{app_user}' already exists")
                else:
                    raise
            
            # Grant the app user permission to work only with this database.
            # This keeps the account scoped to the project instead of giving it
            # access to every database on the server.
            cursor.execute(f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{app_user}'@'{db_host}';")
            cursor.execute("FLUSH PRIVILEGES;")
            print(f"  ✓ Permissions granted")
            
        admin_conn.commit()
        admin_conn.close()
        print(f"✓ MySQL setup complete\n")
        return True
        
    except Exception as e:
        # If anything unexpected happens during setup, print the exception so a
        # teammate can see what went wrong instead of getting a silent failure.
        print(f"⚠ Error during setup: {e}\n")
        admin_conn.close()
        return False


def check_mysql_connection():
    """
    Verify the app can connect using the configured app credentials.

    This is the real runtime check for the Flask app.
    If this succeeds, the database settings are good enough for normal use.
    If it fails, we print a human-friendly explanation of the problem so the
    user does not have to decode a long stack trace first.
    """
    # Read the values the actual Flask app will use.
    # These can still be overridden from the environment when needed.
    app_user = environ.get("DB_USER", "zipchat_app")
    app_password = environ.get("DB_PASSWORD", "password")
    db_host = environ.get("DB_HOST", "127.0.0.1")
    db_port = int(environ.get("DB_PORT", "3306"))
    db_name = environ.get("DB_NAME", "ZipChat")
    
    try:
        # This is the same style of connection SQLAlchemy will use when it
        # creates tables and runs ORM queries.
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
        # PyMySQL returns MySQL error codes, so we can match common failures and
        # print a specific fix for each one.
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
            # If we do not recognize the error code, still show the raw error so
            # the team has something concrete to debug.
            print(f"❌ MySQL error ({error_code}): {e}\n")
            return False


def check_mysql_and_setup():
    """
    Run the MySQL bootstrap sequence during app startup.

    The order matters:
    1. Try to create the database and app user.
    2. Verify that the app can connect with the runtime credentials.

    This function is intentionally small because it is called when the config
    module is imported, so it should be easy to read and easy to debug.
    """
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

    The class is used by Flask-SQLAlchemy and the app factory, so keeping the
    settings here makes startup predictable and easy to trace.
    """
    
    # ========== GENERAL SETTINGS ==========
    # SECRET_KEY signs Flask sessions and CSRF tokens.
    # In a real deployment this should come from the environment, not be hard-
    # coded in source control.
    SECRET_KEY = 'kristofer'
    
    # Flask can use this to know which module contains the app entry point.
    FLASK_APP = 'forum.app'

    
    # ========== DATABASE SETTINGS ==========
    # These values describe the database connection the application will use.
    # Each one can be overridden from the shell, which keeps local development
    # simple while still allowing other environments to customize the values.
    
    # Username for the MySQL account the app uses at runtime.
    DB_USER = environ.get("DB_USER", "zipchat_app")
    
    # Password for the runtime MySQL account.
    # The launcher defaults to "password" so a new clone can start without
    # asking the user to configure secrets first.
    DB_PASSWORD = environ.get("DB_PASSWORD", "password")
    
    # Hostname or IP address where MySQL is running.
    DB_HOST = environ.get("DB_HOST", "127.0.0.1")
    
    # TCP port MySQL listens on.
    DB_PORT = environ.get("DB_PORT", "3306")
    
    # Name of the database the app reads and writes to.
    DB_NAME = environ.get("DB_NAME", "ZipChat")

    # SQLAlchemy wants a single database URL instead of separate pieces.
    # The format below means:
    #   mysql+pymysql -> use MySQL with the PyMySQL driver
    #   username      -> the runtime MySQL user
    #   password      -> that user's password
    #   host:port     -> where MySQL is listening
    #   database      -> which schema to use
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # When True, SQLAlchemy prints every SQL statement it sends to MySQL.
    # This is useful for debugging but noisy for normal use, so we keep it off.
    SQLALCHEMY_ECHO = False
    
    # This is usually False because it avoids extra bookkeeping overhead.
    # Keeping it off makes the app lighter and is the normal Flask-SQLAlchemy
    # setting for most projects.
    SQLALCHEMY_TRACK_MODIFICATIONS = False


# Run the MySQL setup check as soon as config.py is imported.
# That means the app gets a chance to prepare MySQL before Flask starts using
# the database for table creation and queries.
try:
    check_mysql_and_setup()
except Exception as e:
    print(f"⚠ Warning during MySQL setup: {e}")