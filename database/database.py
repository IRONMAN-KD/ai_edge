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

logger = get_logger(__name__)

load_dotenv()

class DatabaseManager:
    _pool = None

    def __init__(self):
        self._get_pool()
        self.connection = None
        self.cursor = None

    @classmethod
    def _get_pool(cls):
        if cls._pool is None:
            try:
                print("Creating database connection pool...")
                cls._pool = mysql.connector.pooling.MySQLConnectionPool(
                    pool_name="ai_edge_pool",
                    pool_size=10,
                    host=os.getenv('MYSQL_HOST', '117.72.37.51'),
                    port=int(os.getenv('MYSQL_PORT', '3306')),
                    user=os.getenv('MYSQL_USER', 'root'),
                    password=os.getenv('MYSQL_PASSWORD', 'Lkd@2025'),
                    database=os.getenv('MYSQL_DATABASE', 'ai_edge_hw')
                )
                print("Database connection pool created successfully.")
            except Error as e:
                print(f"Error creating connection pool: {e}")
                raise
        return cls._pool

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