from typing import Optional

from pydantic import BaseModel

from .genre import DetailGenre
from .mixin import BaseModelMixin
from .person import FilmPerson


class Film(BaseModel):
    """Модель описывающая document в Elasticserch."""

    id: str  # noqa: VNE003
    title: str
    description: Optional[str]
    imdb_rating: float
    director: Optional[list[dict]]
    actors_names: Optional[list[str]]
    writers_names: Optional[list[str]]
    actors: Optional[list[dict]]
    writers: Optional[list[dict]]
    genre: Optional[list[dict]]


class FilmResponse(BaseModelMixin):
    """Информация о фильме на главной странице | странице поиска."""

    title: str
    imdb_rating: float


class DetailFilmResponse(FilmResponse):
    """Полная информация по фильму."""

    description: Optional[str] = ''
    genre: Optional[list[DetailGenre]]
    actors: Optional[list[FilmPerson]]
    writers: Optional[list[FilmPerson]] = []
    directors: Optional[list[FilmPerson]]
