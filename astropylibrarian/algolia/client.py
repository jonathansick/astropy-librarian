# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""High-level interface to the Algolia Search client and a mock-client for
dry-run operations.
"""

from __future__ import annotations

import logging
from copy import deepcopy
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterator,
    List,
    Optional,
    Type,
    Union,
)

from algoliasearch.search_client import SearchClient

if TYPE_CHECKING:
    from types import TracebackType

    from algoliasearch.search_index_async import SearchIndexAsync


AlgoliaIndexType = Union["SearchIndexAsync", "MockAlgoliaIndex"]
"""Type annotation alias supporting the return types of the `AlgoliaIndex` and
`MockAlgoliaIndex` context managers.
"""


class BaseAlgoliaIndex:
    """Base class for an Algolia index client.

    Parameters
    ----------
    key : str
        The Algolia API key.
    app_id : str
        The Algolia application ID.
    name : str
        Name of the Algolia index.
    """

    def __init__(self, *, key: str, app_id: str, name: str):
        self._key = key
        self._app_id = app_id
        self._index_name = name
        self._logger = logging.getLogger(__name__)

    @property
    def name(self) -> str:
        """The index's name."""
        return self._index_name

    @property
    def app_id(self) -> str:
        """The Algolia application ID."""
        return self._app_id


class AlgoliaIndex(BaseAlgoliaIndex):
    """An Algolia index client.

    This client wraps both the ``algoliasearch`` package's ``SearchClient``
    and ``index`` classes.

    Parameters
    ----------
    key : str
        The Algolia API key.
    appid : str
        The Algolia application ID.
    name : str
        Name of the Algolia index.
    """

    async def __aenter__(self) -> SearchIndexAsync:
        self._logger.debug("Opening algolia client")
        self.algolia_client = SearchClient.create(self.app_id, self._key)
        self._logger.debug("Initializing algolia index")
        self.index = self.algolia_client.init_index(self.name)
        return self.index

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[Exception],
        tb: Optional[TracebackType],
    ) -> None:
        self._logger.debug("Closing algolia client")
        await self.algolia_client.close_async()
        self._logger.debug("Finished closing algolia client")


class MockAlgoliaIndex(BaseAlgoliaIndex):
    """A mock Algolia index client.

    Use this client as a drop-in replaceemnt to `AlgoliaIndex` in situations
    where you do not want to make real network requests to Algolia, such as in
    testing or in dry-run applications. This client keeps tracks of what calls
    it would have made so that you can understand how your application uses
    Algolia.

    Parameters
    ----------
    key : str
        The Algolia API key.
    appid : str
        The Algolia application ID.
    index : str
        Name of the Algolia index.
    """

    async def __aenter__(self) -> "MockAlgoliaIndex":
        self._logger.debug("Creating mock Algolia index")
        self._saved_objects: List[Dict] = []
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[Exception],
        tb: Optional[TracebackType],
    ) -> None:
        self._logger.debug("Closing MockAlgoliaIndex")

    async def save_objects_async(
        self,
        objects: Union[List[Dict], Iterator[Dict]],
        request_options: Optional[Dict[str, Any]] = None,
    ) -> MockMultiResponse:
        """Mock implementation of save_objects_async."""
        for obj in objects:
            self._saved_objects.append(deepcopy(obj))
        return MockMultiResponse()


class MockMultiResponse:
    """Mock of an algolia resonse."""