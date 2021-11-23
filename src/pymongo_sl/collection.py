from pymongo.collection import Collection, _UJOIN

from pymongo_sl.cursor import CursorSL
from pymongo_sl.errors import MissingArgsError
from pymongo_sl.common import override
from pymongo_sl.keywords import KW


class CollectionSL(Collection):
    """pymongo Collection for SnapLogic
     This will be transparent to user and work just like the native :class:`~pymongo.collection.Collection`
     with extended caching logic before delegating the actual query to the native class.
    """

    @override
    def __init__(self, *args, **kwargs):
        self.__cache_client = kwargs.pop("cache_client", None)
        if self.__cache_client is None:
            raise MissingArgsError("cache_client is not provided")
        self.__collection = Collection(*args, **kwargs)
        self.__dict__.update(self.__collection.__dict__)

    @override
    def __getitem__(self, name):
        return CollectionSL(self.__database,
                            _UJOIN % (self.__name, name),
                            False,
                            self.codec_options,
                            self.read_preference,
                            self.write_concern,
                            self.read_concern)

    def ensure_region(self, filter, projection):
        """Construct particular filter and projection that ensure the existence of field `region`
        when queried to be used to store in cache using `~pymongo_sl.cache_client.CacheClient`.

        :Parameters:
          - `filter`: Same as parameter `filter` used in :meth:`~pymongo.collection.Collection.find`.
          - `projection`: Same as parameter `filter` used in :meth:`~pymongo.collection.Collection.find`.

        :Returns:
          - `An instance of tuple structured as tuple[dict, dict, bool]`
            fist 2 dict is modified filter and projection respectively
            last is boolean indicating whether field `region` was forced
            to project or not
        """
        forced_projection = False
        if filter and KW.region not in filter:
            region = self.__cache_client.get(filter[KW.id])
            if region is not None:
                filter[KW.region] = region
            else:
                if isinstance(projection, dict) and projection:
                    if KW.region not in projection and next(iter(projection.values())):
                        forced_projection = True
                        projection[KW.region] = True
        return {KW.filter: filter,
                KW.projection: projection,
                KW.forced_projection: forced_projection}

    @override
    def find(self, filter=None, projection=None, *args, **kwargs):
        updated_kwargs = self.ensure_region(filter, projection)
        kwargs.update(updated_kwargs)
        return CursorSL(self, *args, cache_client=self.__cache_client, **kwargs)

    def _find_one_with_region(self, filter=None, projection=None, *args, **kwargs):
        updated_kwargs = self.ensure_region(filter, projection)
        document = self.__collection.find_one(filter=updated_kwargs[KW.filter],
                                              projection=updated_kwargs[KW.projection],
                                              *args, **kwargs)
        if document is not None:
            if KW.id in document and KW.region in document:
                self.__cache_client.set(document[KW.id], document[KW.region])
            else:
                pass
        if updated_kwargs[KW.forced_projection]:
            document.pop(KW.region)
        return document

    @override
    def find_one(self, filter=None, *args, **kwargs):
        if filter and KW.id in filter and KW.region not in filter \
                and """TODO: Implement the schema validation that ensure the region field
                        of the queried collection, so we won't have a miss force projection to
                        collection that doesn't have `region` field
                    """:
            document = self._find_one_with_region(filter, *args, **kwargs)
        else:
            document = self.__collection.find_one(filter, *args, **kwargs)
        return document

    @override
    def update(self, *args, **kwargs):
        """TODO: Add caching logic here"""

        return self.__collection.update(*args, **kwargs)

    @override
    def update_many(self, *args, **kwargs):
        """TODO: Add caching logic here"""

        return self.__collection.update_many(*args, **kwargs)

    @override
    def update_one(self, *args, **kwargs):
        """TODO: Add caching logic here"""

        return self.__collection.update_one(*args, **kwargs)