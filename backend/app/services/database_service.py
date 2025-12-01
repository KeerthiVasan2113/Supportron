"""
Universal database service for dynamic CRUD operations.
"""

import re
from typing import Dict, Any, List, Optional
from sqlite3 import IntegrityError

from app.core.logging_config import logger
from app.db.session import db_manager


class DatabaseService:
    """Service for performing dynamic database operations."""
    
    # SQL identifier pattern - only alphanumeric, underscore, and hyphen
    _IDENTIFIER_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_-]*$')
    
    @staticmethod
    def _sanitize_identifier(identifier: str) -> str:
        """
        Sanitize SQL identifier (table/column name) to prevent injection.
        
        Args:
            identifier: Identifier to sanitize
            
        Returns:
            Sanitized identifier
            
        Raises:
            ValueError: If identifier is invalid
        """
        if not identifier or not isinstance(identifier, str):
            raise ValueError("Identifier must be a non-empty string")
        
        # Remove any whitespace
        identifier = identifier.strip()
        
        # Validate pattern
        if not DatabaseService._IDENTIFIER_PATTERN.match(identifier):
            raise ValueError(f"Invalid identifier: {identifier}. Only alphanumeric, underscore, and hyphen allowed.")
        
        # SQLite doesn't require quoting for valid identifiers, but we validate strictly
        return identifier
    
    @staticmethod
    def _sanitize_identifiers(identifiers: List[str]) -> List[str]:
        """
        Sanitize a list of SQL identifiers.
        
        Args:
            identifiers: List of identifiers to sanitize
            
        Returns:
            List of sanitized identifiers
        """
        return [DatabaseService._sanitize_identifier(ident) for ident in identifiers]
    
    @staticmethod
    def validate_table_exists(db_name: str, table_name: str) -> None:
        """
        Validate that a table exists.
        
        Args:
            db_name: Name of the database
            table_name: Name of the table
            
        Raises:
            ValueError: If table doesn't exist
        """
        if not db_manager.table_exists(db_name, table_name):
            raise ValueError(f"Table '{table_name}' does not exist in database '{db_name}'")
    
    @staticmethod
    def validate_columns(db_name: str, table_name: str, columns: List[str]) -> None:
        """
        Validate that columns exist in the table.
        
        Args:
            db_name: Name of the database
            table_name: Name of the table
            columns: List of column names to validate
            
        Raises:
            ValueError: If any column doesn't exist
        """
        schema = db_manager.get_table_schema(db_name, table_name)
        existing_columns = {col["name"] for col in schema}
        
        invalid_columns = set(columns) - existing_columns
        if invalid_columns:
            raise ValueError(
                f"Columns {invalid_columns} do not exist in table '{table_name}'. "
                f"Available columns: {sorted(existing_columns)}"
            )
    
    @staticmethod
    def validate_values(schema: List[Dict[str, Any]], values: Dict[str, Any]) -> None:
        """
        Validate values against table schema.
        
        Args:
            schema: Table schema from get_table_schema
            values: Dictionary of column names and values
            
        Raises:
            ValueError: If values don't match schema constraints
        """
        schema_dict = {col["name"]: col for col in schema}
        
        for col_name, value in values.items():
            if col_name not in schema_dict:
                continue  # Skip unknown columns (they'll be filtered out)
            
            col_info = schema_dict[col_name]
            
            # Check NOT NULL constraint
            if col_info["not_null"] and value is None:
                raise ValueError(f"Column '{col_name}' cannot be NULL")
            
            # Type validation (basic)
            if value is not None:
                col_type = col_info["type"].upper()
                if "INT" in col_type and not isinstance(value, (int, str)):
                    try:
                        int(value)
                    except (ValueError, TypeError):
                        raise ValueError(f"Column '{col_name}' expects integer type")
                elif "REAL" in col_type or "FLOAT" in col_type or "DOUBLE" in col_type:
                    if not isinstance(value, (int, float, str)):
                        try:
                            float(value)
                        except (ValueError, TypeError):
                            raise ValueError(f"Column '{col_name}' expects numeric type")
                elif "TEXT" in col_type or "VARCHAR" in col_type or "CHAR" in col_type:
                    if not isinstance(value, str):
                        value = str(value)
    
    @staticmethod
    def create(db_name: str, table_name: str, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new record (INSERT).
        
        Args:
            db_name: Name of the database
            table_name: Name of the table
            values: Dictionary of column names and values
            
        Returns:
            Dictionary with created record and rowid
        """
        # Sanitize identifiers
        db_name = DatabaseService._sanitize_identifier(db_name)
        table_name = DatabaseService._sanitize_identifier(table_name)
        
        DatabaseService.validate_table_exists(db_name, table_name)
        
        schema = db_manager.get_table_schema(db_name, table_name)
        DatabaseService.validate_values(schema, values)
        
        # Filter values to only include existing columns and sanitize column names
        existing_columns = {col["name"] for col in schema}
        filtered_values = {
            DatabaseService._sanitize_identifier(k): v 
            for k, v in values.items() 
            if k in existing_columns
        }
        
        if not filtered_values:
            raise ValueError("No valid columns provided")
        
        columns = DatabaseService._sanitize_identifiers(list(filtered_values.keys()))
        placeholders = ", ".join(["?" for _ in columns])
        column_names = ", ".join(columns)
        values_list = [filtered_values[col] for col in columns]
        
        # Use parameterized query with validated identifiers
        query = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
        
        try:
            with db_manager.get_connection(db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(query, values_list)
                rowid = cursor.lastrowid
                
                # Fetch the created record (table_name is already sanitized)
                cursor.execute(f"SELECT * FROM {table_name} WHERE rowid = ?", (rowid,))
                record = dict(cursor.fetchone())
                
                logger.info(f"Created record in {db_name}.{table_name} with rowid {rowid}")
                return {"rowid": rowid, "record": record}
        except IntegrityError as e:
            logger.error(f"Integrity error creating record: {e}")
            raise ValueError(f"Database integrity error: {str(e)}")
    
    @staticmethod
    def read(
        db_name: str, 
        table_name: str, 
        columns: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Read records (SELECT).
        
        Args:
            db_name: Name of the database
            table_name: Name of the table
            columns: List of columns to select (None for all)
            filters: Dictionary of column:value filters (WHERE clause)
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of record dictionaries
        """
        # Sanitize identifiers
        db_name = DatabaseService._sanitize_identifier(db_name)
        table_name = DatabaseService._sanitize_identifier(table_name)
        
        DatabaseService.validate_table_exists(db_name, table_name)
        
        schema = db_manager.get_table_schema(db_name, table_name)
        existing_columns = {col["name"] for col in schema}
        
        # Validate and sanitize columns if specified
        if columns:
            DatabaseService.validate_columns(db_name, table_name, columns)
            sanitized_columns = DatabaseService._sanitize_identifiers(columns)
            column_list = ", ".join(sanitized_columns)
        else:
            column_list = "*"
        
        query = f"SELECT {column_list} FROM {table_name}"
        params = []
        
        # Add WHERE clause if filters provided
        if filters:
            filter_columns = DatabaseService._sanitize_identifiers(list(filters.keys()))
            DatabaseService.validate_columns(db_name, table_name, filter_columns)
            where_clauses = [f"{col} = ?" for col in filter_columns]
            query += " WHERE " + " AND ".join(where_clauses)
            params.extend([filters[col] for col in filter_columns])
        
        # Add LIMIT and OFFSET with validation
        if limit is not None:
            if not isinstance(limit, int) or limit < 0:
                raise ValueError("Limit must be a non-negative integer")
            query += " LIMIT ?"
            params.append(limit)
            if offset is not None:
                if not isinstance(offset, int) or offset < 0:
                    raise ValueError("Offset must be a non-negative integer")
                query += " OFFSET ?"
                params.append(offset)
        
        with db_manager.get_connection(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            records = [dict(row) for row in cursor.fetchall()]
            
            logger.info(f"Read {len(records)} records from {db_name}.{table_name}")
            return records
    
    @staticmethod
    def update(
        db_name: str, 
        table_name: str, 
        values: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update records (UPDATE).
        
        Args:
            db_name: Name of the database
            table_name: Name of the table
            values: Dictionary of column names and new values
            filters: Dictionary of column:value filters (WHERE clause)
            
        Returns:
            Dictionary with number of affected rows
        """
        # Sanitize identifiers
        db_name = DatabaseService._sanitize_identifier(db_name)
        table_name = DatabaseService._sanitize_identifier(table_name)
        
        DatabaseService.validate_table_exists(db_name, table_name)
        
        if not filters:
            raise ValueError("Filters are required for UPDATE operations")
        
        schema = db_manager.get_table_schema(db_name, table_name)
        DatabaseService.validate_values(schema, values)
        DatabaseService.validate_columns(db_name, table_name, list(values.keys()))
        DatabaseService.validate_columns(db_name, table_name, list(filters.keys()))
        
        # Filter values to only include existing columns and sanitize
        existing_columns = {col["name"] for col in schema}
        filtered_values = {
            DatabaseService._sanitize_identifier(k): v 
            for k, v in values.items() 
            if k in existing_columns
        }
        
        if not filtered_values:
            raise ValueError("No valid columns provided for update")
        
        # Sanitize filter column names
        sanitized_filter_keys = DatabaseService._sanitize_identifiers(list(filters.keys()))
        sanitized_value_keys = DatabaseService._sanitize_identifiers(list(filtered_values.keys()))
        
        set_clauses = [f"{col} = ?" for col in sanitized_value_keys]
        where_clauses = [f"{col} = ?" for col in sanitized_filter_keys]
        
        query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE {' AND '.join(where_clauses)}"
        params = list(filtered_values.values()) + [filters[k] for k in filters.keys()]
        
        try:
            with db_manager.get_connection(db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                affected_rows = cursor.rowcount
                
                logger.info(f"Updated {affected_rows} records in {db_name}.{table_name}")
                return {"affected_rows": affected_rows}
        except IntegrityError as e:
            logger.error(f"Integrity error updating records: {e}")
            raise ValueError(f"Database integrity error: {str(e)}")
    
    @staticmethod
    def delete(db_name: str, table_name: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delete records (DELETE).
        
        Args:
            db_name: Name of the database
            table_name: Name of the table
            filters: Dictionary of column:value filters (WHERE clause)
            
        Returns:
            Dictionary with number of affected rows
        """
        # Sanitize identifiers
        db_name = DatabaseService._sanitize_identifier(db_name)
        table_name = DatabaseService._sanitize_identifier(table_name)
        
        DatabaseService.validate_table_exists(db_name, table_name)
        
        if not filters:
            raise ValueError("Filters are required for DELETE operations")
        
        DatabaseService.validate_columns(db_name, table_name, list(filters.keys()))
        
        # Sanitize filter column names
        sanitized_filter_keys = DatabaseService._sanitize_identifiers(list(filters.keys()))
        where_clauses = [f"{col} = ?" for col in sanitized_filter_keys]
        query = f"DELETE FROM {table_name} WHERE {' AND '.join(where_clauses)}"
        params = [filters[k] for k in filters.keys()]
        
        with db_manager.get_connection(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            affected_rows = cursor.rowcount
            
            logger.info(f"Deleted {affected_rows} records from {db_name}.{table_name}")
            return {"affected_rows": affected_rows}
    
    @staticmethod
    def get_table_info(db_name: str, table_name: str) -> Dict[str, Any]:
        """
        Get information about a table.
        
        Args:
            db_name: Name of the database
            table_name: Name of the table
            
        Returns:
            Dictionary with table schema and metadata
        """
        # Sanitize identifiers
        db_name = DatabaseService._sanitize_identifier(db_name)
        table_name = DatabaseService._sanitize_identifier(table_name)
        
        DatabaseService.validate_table_exists(db_name, table_name)
        
        schema = db_manager.get_table_schema(db_name, table_name)
        
        # Get row count using parameterized query
        with db_manager.get_connection(db_name) as conn:
            cursor = conn.cursor()
            # Note: SQLite doesn't support table name as parameter, but we've sanitized it
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
        
        return {
            "table_name": table_name,
            "columns": schema,
            "row_count": row_count
        }

