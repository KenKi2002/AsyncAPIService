from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query
from starlette.requests import Request

from core.config import settings
from core.logger import logger as _logger
from models.film import FilmResponse
from models.person import DetailPerson
from services.person import PersonService, get_person_service

logger = _logger(__name__)
router = APIRouter()


@router.get('/search', response_model=list[DetailPerson])
async def search_person_response(
    request: Request,
    query: str,
    person_service: PersonService = Depends(get_person_service),
    page_num: int = Query(default=1, alias='page[number]', ge=1),
    page_size: int = Query(default=50, alias='page[size]', ge=1),
) -> list[DetailPerson] | None:
    index = 'persons'
    url = str(request.url.include_query_params())
    person = await person_service.get_person_by_search(
        query=query,
        page_num=page_num,
        page_size=page_size,
        index=index,
        url=url,
    )
    if not person:
        logger.debug(f'[-] {settings.person_msg}. url:{url}')  # noqa: PIE803
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=settings.person_msg)
    return person


@router.get('/{person_id}', response_model=DetailPerson)
async def person_details(
    request: Request,
    person_id: str,
    person_service: PersonService = Depends(get_person_service),
) -> DetailPerson | None:
    url = str(request.url.include_query_params())
    person = await person_service.get_by_id(person_id=person_id, url=url)
    if not person:
        logger.debug(f'[-] {settings.person_msg}. url:{url}')  # noqa: PIE803
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=settings.person_msg)
    return person


@router.get('/{person_id}/film', response_model=list[FilmResponse])
async def person_films(
    request: Request,
    person_id: str,
    person_service: PersonService = Depends(get_person_service),
) -> list[FilmResponse] | None:
    sort = '-imdb_rating'
    index = 'movies'
    url = str(request.url.include_query_params())
    person_films = await person_service.get_film_person_by_search(index=index, sort=sort, _person=person_id, url=url)
    if not person_films:
        logger.debug(f'[-] {settings.film_msg}. url:{url}')  # noqa: PIE803
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=settings.film_msg)
    return person_films
