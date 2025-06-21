from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from typing_extensions import LiteralString


class IPersistenceService(ABC):
    """
    Interface for persistence services, defining the contract for data storage and retrieval.
    """

    @abstractmethod
    async def initialize(self):
        """Initializes the persistence service, e.g., setting up connection pools."""
        pass

    @abstractmethod
    async def close(self):
        """Closes the persistence service, e.g., closing connection pools."""
        pass

    @abstractmethod
    async def upsert(
        self, table_name: str, data: Dict[str, Any], on_conflict: List[str]
    ) -> None:
        """
        Inserts or updates a record in the specified table.

        Args:
            table_name: The name of the table.
            data: A dictionary containing the data to upsert.
            on_conflict: A list of column names to use for conflict resolution.
        """
        pass

    @abstractmethod
    async def upsert_all(self, items: List[Any]) -> None:
        """
        Inserts or updates multiple records in the specified table.

        Args:
            items: A list of Pydantic models to upsert.
        """
        pass

    @abstractmethod
    async def get_all(
        self, table_name: str, condition: Optional[str] = None, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves all records from a table that match a given condition.

        Args:
            table_name: The name of the table.
            condition: An optional SQL-like condition string.
            params: Optional dictionary of parameters for the condition.

        Returns:
            A list of dictionaries representing the records.
        """
        pass

    @abstractmethod
    async def get_one(
        self, table_name: str, condition: str, params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single record from a table that matches a given condition.

        Args:
            table_name: The name of the table.
            condition: An SQL-like condition string.
            params: Optional dictionary of parameters for the condition.

        Returns:
            A dictionary representing the record, or None if not found.
        """
        pass

    @abstractmethod
    async def delete(self, table_name: str, condition: str, params: Optional[Dict[str, Any]] = None) -> None:
        """
        Deletes records from a table that match a given condition.

        Args:
            table_name: The name of the table.
            condition: An SQL-like condition string.
            params: Optional dictionary of parameters for the condition.
        """
        pass

    @abstractmethod
    async def upsert_trade(self, trade_data: Dict[str, Any]) -> None:
        """
        Upserts a trade into the 'trades' table.

        Args:
            trade_data: A dictionary containing the trade data.
        """
        pass

    @abstractmethod
    async def get_user_configuration(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a user configuration record.

        Args:
            user_id: The ID of the user.

        Returns:
            A dictionary representing the user configuration, or None if not found.
        """
        pass

    @abstractmethod
    async def execute_raw_sql(
        self, query: LiteralString, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes a raw SQL query.

        Args:
            query: The SQL query to execute.
            params: Optional dictionary of parameters for the query.

        Returns:
            A list of dictionaries representing the query result.
        """
        pass

    @abstractmethod
    async def upsert_user_configuration(self, user_config_data: Dict[str, Any]) -> None:
        """
        Inserts or updates a user configuration record.

        Args:
            user_config_data: A dictionary containing the user configuration data.
        """
        pass

    @abstractmethod
    async def get_trades_with_filters(
        self,
        user_id: str,
        trading_mode: str,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        symbol: Optional[str] = None,
        start_date: Optional[Any] = None,
        end_date: Optional[Any] = None,
    ) -> List[Any]:
        """
        Retrieves trades with dynamic filters.
        """
        pass
