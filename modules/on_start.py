import os
from db import db
from utils.utils import DIR, data

SCHEMA = data["DB"]["SCHEMA"]

def on_ready():
    if not os.path.isdir(f"{DIR}/data"):
        os.mkdir(f"{DIR}/data")
    if not os.path.isdir(f"{DIR}/data/extensions"):
        os.mkdir(f"{DIR}/data/extensions")
    if not os.path.isdir(f"{DIR}/extensions"):
        os.mkdir(f"{DIR}/extensions")

    db.connection.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};")

    # permissions table
    db.connection.execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA}.permissions (
            server_id BIGINT NOT NULL,
            permission TEXT NOT NULL,
            id BIGINT NOT NULL,
            value BOOLEAN,
            PRIMARY KEY (server_id, id, permission)
        );
    """)

    # user data table
    db.cursor.execute(f"""
            connection TABLE IF NOT EXISTS {SCHEMA}.user (
                server_id BIGINT,
                user_id BIGINT,
                data JSONB,
                PRIMARY KEY (server_id, user_id)
            );
        """)

    # server data table
    db.connection.execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA}.server (
            server_id BIGINT PRIMARY KEY,
            extensions JSONB,
            default_user_data JSONB,
            command_prefix TEXT
        );
    """)

    # permission metadata table
    db.connection.execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA}.perm (
            name TEXT PRIMARY KEY,
            display_name TEXT,
            toggleable BOOLEAN,
            default_enabled BOOLEAN,
            role_assignable BOOLEAN
        );    
    """)

    # message history table
    db.connection.execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA}.history (
            message BIGINT PRIMARY KEY,
            reply BIGINT,
        );
    """)
    
    db.logger._logger.info("Defined Schema and Tables")

on_ready()
