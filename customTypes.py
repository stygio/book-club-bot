from typing import TypedDict, Literal


class CommandRequirements(TypedDict):
    chatTypes: list[Literal['private', 'group', 'supergroup', 'channel']] | None
    activeMeeting: bool | None
    onlyMasterUser: bool | None
    stage: Literal['private', 'group', 'supergroup', 'channel'] | None

class BookVolume(TypedDict):
    id: str
    title: str
    subtitle: str | None
    authors: list[str]
    categories: list[str] | None
    description: str | None
    pageCount: int | None
    googleBooksLink: str
    imageLink: str | None

BookVolumes = list[BookVolume]
UserSearchResults = dict[int, BookVolumes]
