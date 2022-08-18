from functools import lru_cache
from typing import Optional

import orjson
from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from elasticsearch_dsl import Search
from fastapi import Depends

try:
    from src.db.elastic import get_elastic
    from src.db.redis import get_redis
    from src.models.film import DetailFilmResponse, Film, FilmResponse
    from src.models.genre import DetailGenre
    from src.models.person import FilmPerson
except ModuleNotFoundError:
    from db.elastic import get_elastic
    from db.redis import get_redis
    from models.film import DetailFilmResponse, Film, FilmResponse
    from models.genre import DetailGenre
    from models.person import FilmPerson

from .utils import create_key

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5


class FilmService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch, index: str = 'movies'):
        """
        Args:
            redis: Соединение с Redis.
            elastic: Соединение с Elasticsearch.
        """

        self.redis = redis
        self.elastic = elastic
        self.index = index

    async def get_by_id(self, film_id: str) -> Optional[DetailFilmResponse]:
        """Получение и запись информации о фильме.

        Args:
            film_id: id фильма.

        Returns:
            Optional[DetailFilmResponse]: Объект модели DetailFilmResponse | None.
        """

        film = await self._film_from_cache(film_id)
        if not film:
            try:
                data = await self._get_film_from_elastic(film_id)
                genre_list = [DetailGenre(uuid=item.get('id'), name=item.get('name')) for item in data.genre]
                actors_list = [FilmPerson(uuid=item.get('id'), full_name=item.get('name')) for item in data.actors]
                writers_list = [FilmPerson(uuid=item.get('id'), full_name=item.get('name')) for item in data.writers]
                directors_list = [FilmPerson(uuid=item.get('id'), full_name=item.get('name')) for item in data.director]
                film = DetailFilmResponse(
                    uuid=data.id,
                    title=data.title,
                    imdb_rating=data.imdb_rating,
                    description=data.description,
                    actors=actors_list,
                    genre=genre_list,
                    writers=writers_list,
                    directors=directors_list,
                )
            except NotFoundError as ex:  # noqa: F841
                #  TODO logging
                return None
            await self._put_film_to_cache(film)
        return film

    async def get_by_search(self, search: Search, key: str) -> Optional[list[FilmResponse]]:
        """
        Получение и запись списка данных о фильмах.

        Args:
            search: Объект класса Search.
            key: Запрос к сервису

        Returns:
            Optional[list[FilmResponse]]: Список объектов модели FilmResponse | None.
        """

        key = create_key(key)
        films = await self._search_from_cache(key)
        if not films:
            try:
                data = await self._get_search_from_elastic(search)
                films = [FilmResponse(uuid=row.id, title=row.title, imdb_rating=row.imdb_rating) for row in data]
            except NotFoundError as ex:  # noqa: F841
                #  TODO logging
                return None
            await self._put_search_to_cache(key, films)
        return films

    async def _get_film_from_elastic(self, film_id: str) -> Optional[Film]:
        """Получение данных о фильме из Elasticsearch.

        Args:
            film_id: id фильма.

        Returns:
            Optional[Film]: Объект модели Film | None.
        """

        try:
            doc = await self.elastic.get('movies', film_id)
        except NotFoundError as ex:  # noqa: F841
            #  TODO logging
            return None
        return Film(**doc['_source'])

    async def _get_search_from_elastic(self, search: Search) -> Optional[list[Film]]:
        """
        Получение списка данных о фильмах из Elasticsearch.

        Args:
            search: Объект класса Search.

        Returns:
            Optional[list[Film]]: Список объектов модели Film | None.
        """

        try:
            query = search.to_dict()
            index = search._index[0]
            data = await self.elastic.search(index=index, body=query)
            hits = data['hits']['hits']
            films = [Film(**row['_source']) for row in hits]
        except NotFoundError as ex:  # noqa: F841
            #  TODO logging
            return None
        return films

    async def _film_from_cache(
        self,
        key: str,
    ) -> Optional[DetailFilmResponse]:
        """Получение данных о фильме из Redis.

        Args:
            key: Ключ.

        Returns:
            Optional[DetailFilmResponse]: Объект модели DetailFilmResponse | None.
        """

        data = await self.redis.get(key)
        if not data:
            return None
        return DetailFilmResponse.parse_raw(data)

    async def _search_from_cache(self, key: str) -> Optional[list[FilmResponse]]:
        """Получение списка данных о фильмах из Redis.

        Args:
            key: ключ.

        Returns:
            Optional[list[FilmResponse]]:
                Список объектов модели FilmResponse | None.
        """
        data = await self.redis.get(key)
        if not data:
            return None
        data = orjson.loads(data)
        return [FilmResponse(**film) for film in data]

    async def _put_film_to_cache(self, film: DetailFilmResponse) -> None:
        """Запись данных о фильме в кеш.

        Args:
            film: Объект модели DetailFilmResponse.
        """

        await self.redis.set(film.uuid, film.json(), ex=FILM_CACHE_EXPIRE_IN_SECONDS)

    async def _put_search_to_cache(self, key: str, films: list[FilmResponse]) -> None:
        """Запись данных о фильмах в кеш.

        Args:
            films: Список объектов модели FilmResponse.
            key: Ключ.
        """

        data = orjson.dumps([film.dict() for film in films])
        await self.redis.set(key, data, ex=FILM_CACHE_EXPIRE_IN_SECONDS)


@lru_cache()
def get_film_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    """Провайдер для FilmService.

    Args:
        redis: Соединение с Redis.
        elastic: Соединение с Elasticsearch.

        Returns:
            FilmService: Объект класса FilmService для API.
    """

    return FilmService(redis, elastic)


if __name__ == '__main__':
    ...
