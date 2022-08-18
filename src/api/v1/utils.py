from typing import Optional

from elasticsearch_dsl import Q, Search


def get_search(
    index: str,
    query: Optional[str] = None,
    sort: str = '-imdb_rating',
    page_num: int = 1,
    page_size: int = 50,
    _filter: Optional[str] = None,
) -> Search:
    """
    Получение Search.

    Args:
        index: Индекс для поиска
        query: Параметр поиска.
        sort: Параметр сортировки.
        page_num: Номер страницы.
        page_size: Размер страницы.
        _filter: Параметр фильтрации по жанрам.

    Returns:
        Search: Объект Search.
    """
    start = (page_num - 1) * page_size
    stop = page_size * page_num
    search = Search(index=index).query('match_all').sort(sort)[start:stop]
    if _filter:
        search = search.query('bool', filter=[Q('terms', tags=['genre', _filter])])
    if query:
        search = search.query('multi_match', query=query, fuzziness='auto')[start:stop]
    return search


if __name__ == '__main__':
    body = get_search(query=None, sort='-imdb_rating', page_num=1, page_size=50, _filter=None, index='movies')
