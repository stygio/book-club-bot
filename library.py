import requests
import re
import os

import customTypes as types
from constants import regex, MAX_SEARCH_RESULTS


# Process the user input string to build a search string matching the google books API specifications
def parseSearchTerms(input: str):
    searchTerms = {}
    input = re.sub(r"(/search )", '', input)

    titleMatch = re.search(regex['SUBMIT_TITLE'], input)
    if titleMatch:
        titleGroup = titleMatch.group(1)
        searchTerms['intitle'] = re.sub(r"(\s+)", '+', titleGroup)
        input = re.sub(regex['SUBMIT_TITLE'], '', input)

    authorMatch = re.search(regex['SUBMIT_AUTHOR'], input)
    if authorMatch:
        authorGroup = authorMatch.group(1)
        searchTerms['inauthor'] = re.sub(r"(\s+)", '+', authorGroup)
        input = re.sub(regex['SUBMIT_AUTHOR'], '', input)

    isbnMatch = re.search(regex['SUBMIT_ISBN'], input)
    if isbnMatch:
        searchTerms['isbn'] = isbnMatch.group(1)
        input = re.sub(regex['SUBMIT_ISBN'], '', input)

    searchString = ''
    generalTerms = re.sub(r"(\s+)", '+', input.strip())
    if generalTerms:
        searchString += generalTerms + '+'
    if len(searchTerms) > 0:
        searchString += '+'.join(f'{k}:{v}' for [k, v] in searchTerms.items())

    return searchString


# Process book volumes collected from Google Books API
def processBookVolumes(items: dict) -> types.BookVolumes:
    results = []

    for item in items:
        imageLinks = item['volumeInfo'].get('imageLinks')
        imageLink = list(imageLinks.values())[0] if imageLinks else None
        results.append({
            'id': item.get('id'),
            'title': item['volumeInfo'].get('title'),
            'subtitle': item['volumeInfo'].get('subtitle'),
            'authors': item['volumeInfo'].get('authors'),
            'categories': item['volumeInfo'].get('categories'),
            'description': item['volumeInfo'].get('description'),
            'pageCount': item['volumeInfo'].get('pageCount'),
            'googleBooksLink': f"https://books.google.pl/books?id={item.get('id')}",
            'imageLink': imageLink,
        })

    return results


# Find books based on user input
def findBookVolumes(input: str) -> tuple[int, types.BookVolumes]:
    queryParams = {
        'q': parseSearchTerms(input),
        'maxResults': MAX_SEARCH_RESULTS,
        'orderBy': 'relevance',
        'key': os.getenv('GOOGLE_BOOKS_API_KEY')
    } 
    r = requests.request(method = 'GET', url = 'https://www.googleapis.com/books/v1/volumes', params = queryParams)
    if r.status_code != 200:
        print(f"Request to Google Books API failed with: {r.status_code} {r.reason}")
        return 0, []

    numFound = r.json()['totalItems']
    if numFound == 0:
        return 0, []
    bookVolumes = processBookVolumes(r.json()['items'])

    return numFound, bookVolumes


# Find books based on user input
def getBookVolume(volumeId: str) -> types.BookVolume | None:
    queryParams = {
        'key': os.getenv('GOOGLE_BOOKS_API_KEY')
    } 
    r = requests.request(method = 'GET', url = f'https://www.googleapis.com/books/v1/volumes/{volumeId}', params = queryParams)
    if r.status_code != 200:
        print(f"Request to Google Books API failed with: {r.status_code} {r.reason}")
        return None

    bookVolume = processBookVolumes([r.json()])[0]

    return bookVolume


def formatAuthors(authors: list[str], prefix: str = '') -> str:
    if not authors:
        return ''
    return prefix + (', '.join(authors) if len(authors) > 1 else authors[0])

def formatBookVolume(book: types.BookVolume) -> str:
    def processSubtitle(subtitle: str | None) -> str:
        return f' ({subtitle})' if subtitle else ''
    
    return f"[{book['title']}{processSubtitle(book['subtitle'])} {formatAuthors(book['authors'], 'by ')}]({book['googleBooksLink']})"

def formatBookVolumeList(books: types.BookVolumes) -> str:
    return '\n'.join([f'{idx}. {formatBookVolume(book)}' for idx, book in enumerate(books, 1)])
