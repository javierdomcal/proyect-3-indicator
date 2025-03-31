"""
Database connection management for the computational chemistry project.
Handles connection creation, pooling, and lifecycle management.
"""

import sqlite3
import time
import logging
import threading
import queue
from contextlib import contextmanager
from pathlib import Path
from .schema import get_db_path, ensure_db_directory

logger = logging.getLogger(__name__)

class ConnectionPool:
    """
    A simple connection pool for SQLite connections.
    Helps manage concurrent access to the database.
    """

    def __init__(self, max_connections=5, timeout=5.0):
        """
        Initialize the connection pool.

        Args:
            max_connections: Maximum number of connections to maintain
            timeout: Time in seconds to wait for a connection
        """
        self.max_connections = max_connections
        self.timeout = timeout
        self.db_path = ensure_db_directory()
        self.pool = queue.Queue(maxsize=max_connections)
        self.active_connections = 0
        self.lock = threading.RLock()

        # Pre-populate the pool with connections
        for _ in range(max_connections // 2):  # Start with half capacity
            self._create_connection()

    def _create_connection(self):
        """Create a new SQLite connection and add it to the pool"""
        try:
            conn = sqlite3.connect(self.db_path,
                               detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                               isolation_level="EXCLUSIVE")  # Use exclusive transactions

            # Enable foreign key support
            conn.execute("PRAGMA foreign_keys = ON")

            # Configure connection for better concurrency
            conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging
            conn.execute("PRAGMA synchronous = NORMAL")  # Balance durability with performance

            self.pool.put(conn)
            with self.lock:
                self.active_connections += 1

            logger.debug(f"Created new database connection (total: {self.active_connections})")
            return True
        except Exception as e:
            logger.error(f"Error creating database connection: {str(e)}")
            return False

    @contextmanager
    def get_connection(self):
        """
        Get a connection from the pool. If none are available, wait or create a new one.
        Returns a context manager, so use with: `with pool.get_connection() as conn:`
        """
        conn = None
        try:
            # Try to get a connection from the pool
            try:
                conn = self.pool.get(block=True, timeout=self.timeout)
                logger.debug("Got connection from pool")
            except queue.Empty:
                # If the pool is empty but we haven't reached max connections, create a new one
                with self.lock:
                    if self.active_connections < self.max_connections:
                        if self._create_connection():
                            conn = self.pool.get(block=True, timeout=self.timeout)
                        else:
                            raise Exception("Failed to create new database connection")
                    else:
                        # We've reached max connections, so wait again for one to become available
                        logger.warning("Maximum connections reached, waiting for an available connection")
                        conn = self.pool.get(block=True, timeout=self.timeout * 2)

            # Return the connection for use in the with block
            yield conn

            # When the with block exits, return the connection to the pool
            self.pool.put(conn)
            conn = None  # Prevent connection from being closed in finally block

        except Exception as e:
            logger.error(f"Error getting database connection: {str(e)}")
            raise
        finally:
            # If something went wrong and we have a connection that wasn't returned to the pool
            if conn is not None:
                try:
                    # Return the connection to the pool
                    self.pool.put(conn)
                except:
                    # If we can't return it (e.g. pool is full), close it
                    try:
                        conn.close()
                        with self.lock:
                            self.active_connections -= 1
                        logger.debug(f"Closed database connection (total: {self.active_connections})")
                    except:
                        pass

    def close_all(self):
        """Close all connections in the pool"""
        logger.info("Closing all database connections")
        try:
            # Close all connections in the pool
            while not self.pool.empty():
                try:
                    conn = self.pool.get(block=False)
                    conn.close()
                    with self.lock:
                        self.active_connections -= 1
                except queue.Empty:
                    break
                except Exception as e:
                    logger.error(f"Error closing connection: {str(e)}")

            logger.info(f"All connections closed (remaining: {self.active_connections})")
        except Exception as e:
            logger.error(f"Error during pool shutdown: {str(e)}")


# Global connection pool instance
_pool = None

def get_connection_pool(max_connections=5):
    """Get the global connection pool instance, creating it if necessary"""
    global _pool
    if _pool is None:
        _pool = ConnectionPool(max_connections=max_connections)
    return _pool

@contextmanager
def get_db_connection():
    """Convenience function to get a database connection from the pool"""
    pool = get_connection_pool()
    with pool.get_connection() as conn:
        yield conn

def close_connections():
    """Close all database connections - call this at application shutdown"""
    global _pool
    if _pool is not None:
        _pool.close_all()
        _pool = None