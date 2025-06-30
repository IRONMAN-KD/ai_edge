#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库连接和操作模块
"""

import os
import json
import pymysql
from typing import Dict, List, Optional, Any
from pymysql.cursors import DictCursor
from contextlib import contextmanager
from utils.logging import get_logger
import mysql.connector
from mysql.connector import Error, pooling
from dotenv import load_dotenv
import mysql.connector.locales.eng.client_error
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

logger = get_logger(__name__)

load_dotenv()

class DatabaseManager:
    _pool = None
    _engine = None
    _SessionLocal = None

    def __init__(self):
        self._get_pool()
        self._get_engine()
        self.connection = None
        self.cursor = None

    @classmethod
    def _get_engine(cls):
        if cls._engine is None:
            try:
                print("Creating SQLAlchemy engine...")
                db_user = os.getenv('MYSQL_USER', 'ai_edge_user')
                db_password = os.getenv('MYSQL_PASSWORD', 'your_strong_password')
                db_host = os.getenv('MYSQL_HOST', 'db')
                db_port = os.getenv('MYSQL_PORT', '3306')
                db_name = os.getenv('MYSQL_DATABASE', 'ai_edge')
                
                # SQLAlchemy uses mysqlclient or PyMySQL, not mysql-connector-python for engine URL
                # Ensure you have PyMySQL installed: pip install PyMySQL
                database_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
                
                cls._engine = create_engine(database_url, pool_pre_ping=True)
                cls._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls._engine)
                print("SQLAlchemy engine and session maker created successfully.")
            except Exception as e:
                print(f"Error creating SQLAlchemy engine: {e}")
                raise
        return cls._engine

    @classmethod
    def _get_pool(cls):
        if cls._pool is None:
            try:
                print("Creating database connection pool...")
                cls._pool = mysql.connector.pooling.MySQLConnectionPool(
                    pool_name="ai_edge_pool",
                    pool_size=10,
                    host=os.getenv('MYSQL_HOST', 'db'),
                    port=int(os.getenv('MYSQL_PORT', '3306')),
                    user=os.getenv('MYSQL_USER', 'ai_edge_user'),
                    password=os.getenv('MYSQL_PASSWORD', 'your_strong_password'),
                    database=os.getenv('MYSQL_DATABASE', 'ai_edge')
                )
                print("Database connection pool created successfully.")
            except Error as e:
                print(f"Error creating connection pool: {e}")
                raise
        return cls._pool

    @contextmanager
    def get_session(self) -> Session:
        """Provide a transactional scope around a series of operations."""
        if self._SessionLocal is None:
            self._get_engine()
            
        session = self._SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def start_transaction(self):
        """Starts a new database transaction."""
        self.connection = self._get_pool().get_connection()
        self.connection.start_transaction()
        self.cursor = self.connection.cursor(dictionary=True)

    def commit(self):
        """Commits the current transaction."""
        if self.connection:
            self.connection.commit()

    def rollback(self):
        """Rolls back the current transaction."""
        if self.connection:
            self.connection.rollback()

    def close_transaction(self):
        """Closes the cursor and connection."""
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute_query(self, query: str, params: Optional[tuple] = None, fetch: Optional[str] = "all", commit: bool = False, last_row_id: bool = False) -> Any:
        # If in a transaction, use the existing cursor
        if self.cursor:
            self.cursor.execute(query, params or ())
            if fetch == 'one':
                return self.cursor.fetchone()
            elif fetch == 'all':
                return self.cursor.fetchall()
            else: # fetch is None or something else
                return self.cursor.rowcount

        # Original logic for non-transactional queries
        pool = self._get_pool()
        connection = None
        try:
            connection = pool.get_connection()
            if connection.is_connected():
                cursor = connection.cursor(dictionary=True)
                cursor.execute(query, params or ())
                
                if commit:
                    connection.commit()
                    if last_row_id:
                        result = cursor.lastrowid
                    else:
                        result = cursor.rowcount
                elif fetch == 'one':
                    result = cursor.fetchone()
                elif fetch == 'all':
                    result = cursor.fetchall()
                else: # fetch is None
                    result = None

                cursor.close()
                return result
            else:
                raise Error("Failed to get a connected connection from the pool.")
        except Error as e:
            print(f"Error during query execution: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection and connection.is_connected():
                connection.close() # Returns the connection to the pool

    def close_pool(self):
        # This method might be useful for graceful shutdown
        if self._pool is not None:
            # Closing the pool will close all connections.
            # No need to loop through connections.
            print("Closing all connections in the pool...")
            # The pool itself doesn't have a close method.
            # Connections are closed when the application exits.
            self._pool = None
            print("Connection pool resources released.") 