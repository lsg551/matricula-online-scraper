"""Unit tests for the custom images pipeline."""

import pytest

from matricula_online_scraper.pipelines.images_pipeline import (
    _extract_image_extension,
    _extract_last_path_segment,
)

LOWERCASE_URL = (
    "http://hosted-images.matricula-online.eu/images/matricula/DAG/"
    "MatrikenGraz-Seckau/Ardning/6014/Taufbuch/01/1786-1830/"
    "Ardning_6014_Taufbuch_01_1786-1830___Seite__S0004.jpg"
)

UPPERCASE_URL = (
    "http://hosted-images.matricula-online.eu/images/matricula/DZG53/"
    "ADG-Matrikenportal/Digitales%20Matrikenportal/Pusarnitz/P12_037-1/"
    "P12_037-1_fol0021.JPG"
)


@pytest.mark.parametrize(
    ("image_url", "expected"),
    [
        (LOWERCASE_URL, "Ardning_6014_Taufbuch_01_1786-1830___Seite__S0004"),
        # https://github.com/lsg551/matricula-online-scraper/issues/115
        (UPPERCASE_URL, "P12_037-1_fol0021"),
        (UPPERCASE_URL.replace(".JPG", ".jpeg"), "P12_037-1_fol0021"),
        (UPPERCASE_URL.replace(".JPG", ".PNG"), "P12_037-1_fol0021"),
    ],
)
def test_extract_last_path_segment_is_case_insensitive(image_url, expected):
    """Test that the image extension is matched regardless of its case."""
    assert _extract_last_path_segment(image_url) == expected


def test_extract_last_path_segment_raises_on_non_image_url():
    """Test that a non-image URL still raises a ValueError."""
    with pytest.raises(ValueError, match="Could not extract last path segment"):
        _extract_last_path_segment("http://example.com/images/foo.gif")


@pytest.mark.parametrize(
    ("image_url", "expected"),
    [
        (LOWERCASE_URL, ".jpg"),
        (UPPERCASE_URL, ".JPG"),
        (UPPERCASE_URL.replace(".JPG", ".jpeg"), ".jpeg"),
        (UPPERCASE_URL.replace(".JPG", ".PNG"), ".PNG"),
    ],
)
def test_extract_image_extension_preserves_case(image_url, expected):
    """Test that the original extension (including its case) is kept."""
    assert _extract_image_extension(image_url) == expected
