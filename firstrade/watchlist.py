from firstrade import urls
from firstrade.account import FTSession


class Watchlist:
    """Provides watchlist management for a Firstrade session.

    Supports creating and deleting watchlists, adding and removing symbols
    from watchlists, and retrieving watchlist contents.

    Attributes:
        ft_session (FTSession): The session object used for API requests.

    """

    def __init__(self, ft_session: FTSession) -> None:
        """Initialize Watchlist with a Firstrade session.

        Args:
            ft_session (FTSession): An authenticated Firstrade session.

        """
        self.ft_session: FTSession = ft_session

    # ------------------------------------------------------------------
    # Watchlist CRUD
    # ------------------------------------------------------------------

    def get_watchlists(self) -> dict:
        """Retrieve all watchlists for the current user.

        Returns:
            dict: API response containing a list of watchlists under ``items``.
                  Each entry contains ``list_id``, ``name``, and ``isDefault``.

        """
        response = self.ft_session._request("get", url=urls.watchlists())
        return response.json()

    def create_watchlist(self, name: str) -> dict:
        """Create a new watchlist.

        Args:
            name (str): Display name for the new watchlist.

        Returns:
            dict: API response containing ``result.list_id`` of the created watchlist.

        """
        data = {"name": name}
        response = self.ft_session._request("post", url=urls.watchlists(), data=data)
        return response.json()

    def get_watchlist(self, list_id: int) -> dict:
        """Retrieve the contents of a specific watchlist.

        Args:
            list_id (int): The ID of the watchlist to retrieve.

        Returns:
            dict: API response containing ``result.list_items`` with each symbol's
                  quote data.

        """
        response = self.ft_session._request("get", url=urls.watchlist(list_id))
        return response.json()

    def delete_watchlist(self, list_id: int) -> dict:
        """Delete a watchlist.

        Args:
            list_id (int): The ID of the watchlist to delete.

        Returns:
            dict: API response confirming deletion via ``result.result == "success"``.

        """
        response = self.ft_session._request("delete", url=urls.watchlist(list_id))
        return response.json()

    # ------------------------------------------------------------------
    # Watchlist item management
    # ------------------------------------------------------------------

    def get_all_watchlist_items(self) -> dict:
        """Retrieve every item across all watchlists.

        Returns:
            dict: API response with all watchlist symbols under ``items``.

        """
        response = self.ft_session._request("get", url=urls.watchlist_items())
        return response.json()

    def add_symbol(self, list_id: int, symbol: str, sec_type: str = "1") -> dict:
        """Add a symbol to a watchlist.

        Args:
            list_id (int): The ID of the watchlist to add the symbol to.
            symbol (str): The ticker symbol to add (e.g. ``"AAPL"``).
            sec_type (str, optional): Security type. ``"1"`` for equities/ETFs.
                Defaults to ``"1"``.

        Returns:
            dict: API response containing ``result.watchlist_id`` of the new item.

        """
        data = {"symbol": symbol, "sec_type": sec_type}
        response = self.ft_session._request("post", url=urls.watchlist_item(list_id), data=data)
        return response.json()

    def remove_symbol(self, watchlist_id: int) -> dict:
        """Remove a symbol from a watchlist by its watchlist item ID.

        Note:
            ``watchlist_id`` here refers to the per-item ID returned by
            :meth:`add_symbol` (``result.watchlist_id``), **not** the
            ``list_id`` of the watchlist itself.

        Args:
            watchlist_id (int): The item-level watchlist ID to remove.

        Returns:
            dict: API response confirming deletion via ``result.result == "success"``.

        """
        response = self.ft_session._request(
            "delete", url=urls.watchlist_item_delete(watchlist_id)
        )
        return response.json()
