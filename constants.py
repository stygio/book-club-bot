from dotenv import load_dotenv
import os


expectedEnvVars = ['TELEGRAM_TOKEN', 'GOOGLE_BOOKS_API_KEY', 'MASTER_USER_ID', 'MASTER_CHAT_ID']
def loadSecrets() -> dict[str, str]:
    load_dotenv()
    secrets = {}
    for envVar in expectedEnvVars:
        value = os.getenv(envVar)
        if not value:
            raise Exception(f'Missing environment variable: {envVar}')
        secrets[envVar] = value
    return secrets
secrets = loadSecrets()

MAX_SEARCH_RESULTS = 10

regex = {
    'SUBMIT_TITLE': r"title:\"([\w\s]+)\"",
    'SUBMIT_AUTHOR': r"author:\"([\w\s]+)\"",
    'SUBMIT_ISBN': r"isbn:([\d]+)",
    'CHOOSE': r"/choose (\d+)",
    'VOTE': r"/vote (\d+) (\d+) (\d+)",
}

fonts = {
    'DEFAULT': 'Roboto-Light.ttf',
    'BOLD': 'Roboto-SemiBold.ttf',
    'ITALIC': 'Roboto-LightItalic.ttf',
    'BOLD-ITALIC': 'Roboto-SemiBoldItalic.ttf',
}

images = {
    'COVER_NOT_FOUND': 'cover-not-found.png',
    'GOOGLE_BOOKS_LINK': 'google-books-link.png',
    'LOGO': 'logo.png',
}