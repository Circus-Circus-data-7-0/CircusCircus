def try_admin_connection():
    """Try common local root login methods and return (connection, method)."""
    socket_paths = [
        "/tmp/mysql.sock",
        "/var/run/mysql/mysql.sock",
        "/usr/local/var/run/mysql.sock",
    ]

    for socket_path in socket_paths:
        try:
            admin_conn = pymysql.connect(
                user="root",
                unix_socket=socket_path,
                charset="utf8mb4",
            )
            return (admin_conn, f"socket ({socket_path})")
        except Exception:
            continue

    try:
        admin_conn = pymysql.connect(
            host="127.0.0.1",
            port=3306,
            user="root",
            password="",
            charset="utf8mb4",
        )
        return (admin_conn, "TCP/IP (no password)")
    except Exception:
        pass

    root_password = environ.get("MYSQL_ROOT_PASSWORD", "")
    if root_password:
        try:
            admin_conn = pymysql.connect(
                host="127.0.0.1",
                port=3306,
                user="root",
                password=root_password,
                charset="utf8mb4",
            )
            return (admin_conn, "TCP/IP (with password)")
        except Exception:
            pass

    return (None, None)


def setup_database_and_user():
    """Best-effort local setup for app database and app user."""
    app_user = "zipchat_app"
    app_password = "password"
    db_host = "127.0.0.1"
    db_name = "ZipChat"

    admin_conn, method = try_admin_connection()

    if admin_conn is None:
        print("\nCould not connect to MySQL as root")
        print("  Socket connection not available")
        print("  TCP/IP connection with no password did not work")
        print("\n  To fix:")
        print("    A) brew services restart mysql")
        print("    B) export MYSQL_ROOT_PASSWORD='your_root_password' && bash ./run.sh")
        print("    C) Or create database and user manually")
        print("")
        return False

    try:
        print(f"Connected to MySQL as root via {method}")

        with admin_conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`;")

            try:
                cursor.execute(
                    f"CREATE USER IF NOT EXISTS '{app_user}'@'{db_host}' IDENTIFIED BY '{app_password}';"
                )
            except pymysql.err.OperationalError as err:
                if "already exists" not in str(err):
                    raise

            cursor.execute(
                f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{app_user}'@'{db_host}';"
            )
            cursor.execute("FLUSH PRIVILEGES;")

        admin_conn.commit()
        admin_conn.close()
        print("MySQL setup complete\n")
        return True

    except Exception as err:
        print(f"Error during setup: {err}\n")
        admin_conn.close()
        return False


def check_mysql_connection():
    """Verify runtime app credentials can connect to MySQL."""
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
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
        connection.close()
        print(f"MySQL ready: {app_user}@{db_name}\n")
        return True

    except pymysql.err.OperationalError as err:
        error_code = err.args[0] if err.args else None

        if error_code == 2003:
            print(f"MySQL not running on {db_host}:{db_port}")
            print("Start it: brew services start mysql\n")
            return False

        if error_code == 1045:
            print(f"Cannot login as '{app_user}'")
            print("Either the user does not exist or the password is wrong.\n")
            return False

        if error_code == 1049:
            print(f"Database '{db_name}' does not exist\n")
            return False

        print(f"MySQL error ({error_code}): {err}\n")
        return False


def check_mysql_and_setup():
    """Run setup then verify runtime MySQL connectivity."""
    print("Checking MySQL setup...")
    setup_database_and_user()
    check_mysql_connection()