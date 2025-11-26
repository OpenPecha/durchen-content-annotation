"""Tests for durchen annotation functionality."""

import re
from durchen_content_annotation.annotation import (
    insert_durchen_tags,
    _build_tag_position_map_from_durchen,
    get_segment_with_tags,
    get_all_segments_with_tags, 
)

def test_insert_durchen_tags():
    """Test inserting durchen tags into text."""
    text = "I have a dream to become the world best singer"
    
    durchen_data = [
        {"span": {"start": 0, "end": 10}, "note": "A is a good boy"},
        {"span": {"start": 10, "end": 20}, "note": "B is a good boy"},
        {"span": {"start": 20, "end": 30}, "note": "C is a good girl"},
    ]
    
    result = insert_durchen_tags(text, durchen_data)
    
    # Verify tags are inserted (HTML format)
    assert '<sup class="footnote-marker"></sup><i class="footnote">A is a good boy</i>' in result
    assert '<sup class="footnote-marker"></sup><i class="footnote">B is a good boy</i>' in result
    assert '<sup class="footnote-marker"></sup><i class="footnote">C is a good girl</i>' in result
    
    # Verify text before first tag
    assert result.startswith("I have a d")
    
    # Verify tag positions (tags inserted in descending order)
    cumulative_offset = 0
    sorted_durchen = sorted(durchen_data, key=lambda x: x["span"]["end"])
    
    for item in sorted_durchen:
        end_pos = item["span"]["end"]
        note = item["note"]
        tag = f'<sup class="footnote-marker"></sup><i class="footnote">{note}</i>'
        expected_pos = end_pos + cumulative_offset
        
        assert result[expected_pos:expected_pos+len(tag)] == tag
        cumulative_offset += len(tag)


def test_build_tag_position_map_from_durchen():
    """Test building tag position map from durchen_data."""
    durchen_data = [
        {"span": {"start": 0, "end": 10}, "note": "A"},
        {"span": {"start": 20, "end": 30}, "note": "B"},
        {"span": {"start": 10, "end": 20}, "note": "C"},
    ]
    
    tag_position_map = _build_tag_position_map_from_durchen(durchen_data)
    
    # Verify structure
    assert len(tag_position_map) == 3
    
    # Verify sorted by original_pos (ascending)
    positions = [item['original_pos'] for item in tag_position_map]
    assert positions == [10, 20, 30]
    
    # Verify tags are correct (HTML format)
    assert tag_position_map[0]['tag'] == '<sup class="footnote-marker"></sup><i class="footnote">A</i>'
    assert tag_position_map[0]['original_pos'] == 10
    assert tag_position_map[1]['tag'] == '<sup class="footnote-marker"></sup><i class="footnote">C</i>'
    assert tag_position_map[1]['original_pos'] == 20
    assert tag_position_map[2]['tag'] == '<sup class="footnote-marker"></sup><i class="footnote">B</i>'
    assert tag_position_map[2]['original_pos'] == 30


def test_get_segment_with_tags():
    """Test extracting segment with tags using tag_position_map."""
    original_text = "I have a dream to become the world best singer"
    
    durchen_data = [
        {"span": {"start": 0, "end": 10}, "note": "A is a good boy"},
        {"span": {"start": 10, "end": 20}, "note": "B is a good boy"},
        {"span": {"start": 20, "end": 30}, "note": "C is a good girl"},
    ]
    
    # Build tag position map
    tag_position_map = _build_tag_position_map_from_durchen(durchen_data)
    
    # Extract segment [0, 20] - should include tags at positions 10 and 20
    segment = get_segment_with_tags(original_text, tag_position_map, 0, 20)
    
    # Verify original content is present (remove all HTML tags and note content for comparison)
    # Remove the entire footnote marker: <sup...></sup><i...>note</i>
    content_without_tags = re.sub(r'<sup[^>]*></sup><i[^>]*>.*?</i>', '', segment)
    assert content_without_tags == original_text[0:20]
    
    # Verify tags within range are included (HTML format)
    assert '<sup class="footnote-marker"></sup><i class="footnote">A is a good boy</i>' in segment
    assert '<sup class="footnote-marker"></sup><i class="footnote">B is a good boy</i>' in segment
    
    # Tag at position 30 should not be included
    assert '<sup class="footnote-marker"></sup><i class="footnote">C is a good girl</i>' not in segment


def test_get_segment_with_tags_no_tags_in_range():
    """Test extracting segment when no tags fall within the range."""
    original_text = "I have a dream"
    
    durchen_data = [
        {"span": {"start": 0, "end": 20}, "note": "A"},
    ]
    
    tag_position_map = _build_tag_position_map_from_durchen(durchen_data)
    
    # Extract segment [0, 10] - no tags in this range
    segment = get_segment_with_tags(original_text, tag_position_map, 0, 10)
    
    # Should return original segment without tags
    assert segment == original_text[0:10]
    assert '<sup class="footnote-marker"></sup><i class="footnote">A</i>' not in segment


def test_get_all_segments_with_tags():
    """Test extracting all segments with tags."""
    original_text = "I have a dream to become the world best singer"
    
    durchen_data = [
        {"span": {"start": 0, "end": 10}, "note": "A"},
        {"span": {"start": 20, "end": 30}, "note": "B"},
    ]
    
    segmentation_data = [
        {"id": "seg1", "span": {"start": 0, "end": 20}},
        {"id": "seg2", "span": {"start": 20, "end": 40}},
    ]
    
    # Use durchen_data
    segments = get_all_segments_with_tags(
        original_text, segmentation_data, durchen_data=durchen_data
    )
    
    # Verify structure
    assert len(segments) == 2
    
    # First segment [0, 20] should include tag at position 10
    assert segments[0]["id"] == "seg1"
    assert segments[0]["span"] == {"start": 0, "end": 20}
    assert '<sup class="footnote-marker"></sup><i class="footnote">A</i>' in segments[0]["content"]
    assert '<sup class="footnote-marker"></sup><i class="footnote">B</i>' not in segments[0]["content"]
    
    # Second segment [20, 40] should include tag at position 30
    assert segments[1]["id"] == "seg2"
    assert segments[1]["span"] == {"start": 20, "end": 40}
    assert '<sup class="footnote-marker"></sup><i class="footnote">B</i>' in segments[1]["content"]
    assert '<sup class="footnote-marker"></sup><i class="footnote">A</i>' not in segments[1]["content"]
    
    # Verify content includes original text (remove all HTML tags and note content for comparison)
    # Remove the entire footnote marker: <sup...></sup><i...>note</i>
    content_without_tags_0 = re.sub(r'<sup[^>]*></sup><i[^>]*>.*?</i>', '', segments[0]["content"])
    assert content_without_tags_0 == original_text[0:20]
    
    content_without_tags_1 = re.sub(r'<sup[^>]*></sup><i[^>]*>.*?</i>', '', segments[1]["content"])
    assert content_without_tags_1 == original_text[20:40]

