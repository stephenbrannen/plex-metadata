from unittest.mock import MagicMock

from libraries.repositories.plex_libraries import PlexLibrariesRepository


def test_list_libraries() -> None:
    section_one = MagicMock(title="Movies", type="movie")
    section_two = MagicMock(title="TV Shows", type="show")
    plex = MagicMock()
    plex.library.sections.return_value = [section_one, section_two]

    repo = PlexLibrariesRepository(plex=plex)
    libraries = repo.list_libraries()

    assert [lib.title for lib in libraries] == ["Movies", "TV Shows"]
    assert [lib.type for lib in libraries] == ["movie", "show"]
