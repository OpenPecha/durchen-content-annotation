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
    assert '<sup class="footnote-marker"></sup><i class="footnote">A</i>' in segments[0]["content"]
    assert '<sup class="footnote-marker"></sup><i class="footnote">B</i>' not in segments[0]["content"]
    
    # Second segment [20, 40] should include tag at position 30
    assert segments[1]["id"] == "seg2"
    assert '<sup class="footnote-marker"></sup><i class="footnote">B</i>' in segments[1]["content"]
    assert '<sup class="footnote-marker"></sup><i class="footnote">A</i>' not in segments[1]["content"]
    
    # Verify content includes original text (remove all HTML tags and note content for comparison)
    # Remove the entire footnote marker: <sup...></sup><i...>note</i>
    content_without_tags_0 = re.sub(r'<sup[^>]*></sup><i[^>]*>.*?</i>', '', segments[0]["content"])
    assert content_without_tags_0 == original_text[0:20]
    
    content_without_tags_1 = re.sub(r'<sup[^>]*></sup><i[^>]*>.*?</i>', '', segments[1]["content"])
    assert content_without_tags_1 == original_text[20:40]


def test_get_segment_with_tags_excludes_tag_at_start():
    """Test that tags at the exact start position are excluded (start < pos, not <=)."""
    original_text = "I have a dream to become the world best singer"
    
    durchen_data = [
        {"span": {"start": 0, "end": 0}, "note": "Tag at start"},
        {"span": {"start": 0, "end": 5}, "note": "Tag just after start"},
        {"span": {"start": 0, "end": 10}, "note": "Tag at position 10"},
    ]
    
    tag_position_map = _build_tag_position_map_from_durchen(durchen_data)
    
    # Extract segment [0, 15] - tag at position 0 should be EXCLUDED
    # Tag at position 5 should be INCLUDED
    # Tag at position 10 should be INCLUDED
    segment = get_segment_with_tags(original_text, tag_position_map, 0, 15)
    
    # Tag at exact start (position 0) should NOT be included
    assert '<sup class="footnote-marker"></sup><i class="footnote">Tag at start</i>' not in segment
    
    # Tags after start should be included
    assert '<sup class="footnote-marker"></sup><i class="footnote">Tag just after start</i>' in segment
    assert '<sup class="footnote-marker"></sup><i class="footnote">Tag at position 10</i>' in segment
    
    # Verify original content is present
    content_without_tags = re.sub(r'<sup[^>]*></sup><i[^>]*>.*?</i>', '', segment)
    assert content_without_tags == original_text[0:15]


def test_get_segment_with_tags_boundary_conditions():
    """Test boundary conditions: tag at start (excluded) vs tag just after start (included)."""
    original_text = "Hello world"
    
    durchen_data = [
        {"span": {"start": 0, "end": 0}, "note": "At start"},
        {"span": {"start": 0, "end": 1}, "note": "Just after start"},
        {"span": {"start": 0, "end": 5}, "note": "At end"},
    ]
    
    tag_position_map = _build_tag_position_map_from_durchen(durchen_data)
    
    # Extract segment [0, 5]
    segment = get_segment_with_tags(original_text, tag_position_map, 0, 5)
    
    # Tag at exact start (position 0) should be EXCLUDED
    assert '<sup class="footnote-marker"></sup><i class="footnote">At start</i>' not in segment
    
    # Tags after start should be INCLUDED
    assert '<sup class="footnote-marker"></sup><i class="footnote">Just after start</i>' in segment
    assert '<sup class="footnote-marker"></sup><i class="footnote">At end</i>' in segment


def test_get_segment_with_tags_non_zero_start():
    """Test that tags at non-zero start positions are also excluded correctly."""
    original_text = "I have a dream to become the world best singer"
    
    durchen_data = [
        {"span": {"start": 5, "end": 10}, "note": "Tag at 10"},
        {"span": {"start": 5, "end": 15}, "note": "Tag at 15"},
        {"span": {"start": 5, "end": 20}, "note": "Tag at 20"},
    ]
    
    tag_position_map = _build_tag_position_map_from_durchen(durchen_data)
    
    # Extract segment [10, 25] - tag at position 10 should be EXCLUDED (start < pos)
    # Tag at position 15 should be INCLUDED
    # Tag at position 20 should be INCLUDED
    segment = get_segment_with_tags(original_text, tag_position_map, 10, 25)
    
    # Tag at exact start (position 10) should NOT be included
    assert '<sup class="footnote-marker"></sup><i class="footnote">Tag at 10</i>' not in segment
    
    # Tags after start should be included
    assert '<sup class="footnote-marker"></sup><i class="footnote">Tag at 15</i>' in segment
    assert '<sup class="footnote-marker"></sup><i class="footnote">Tag at 20</i>' in segment
    
    # Verify original content is present
    content_without_tags = re.sub(r'<sup[^>]*></sup><i[^>]*>.*?</i>', '', segment)
    assert content_without_tags == original_text[10:25]


def test_get_all_segments_with_tags_excludes_tags_at_start():
    """Test that get_all_segments_with_tags excludes tags at segment start positions."""
    original_text = "I have a dream to become the world best singer"
    
    durchen_data = [
        {"span": {"start": 0, "end": 0}, "note": "At seg1 start"},
        {"span": {"start": 0, "end": 5}, "note": "After seg1 start"},
        {"span": {"start": 0, "end": 20}, "note": "At seg2 start"},
        {"span": {"start": 0, "end": 25}, "note": "After seg2 start"},
    ]
    
    segmentation_data = [
        {"id": "seg1", "span": {"start": 0, "end": 20}},
        {"id": "seg2", "span": {"start": 20, "end": 40}},
    ]
    
    segments = get_all_segments_with_tags(
        original_text, segmentation_data, durchen_data=durchen_data
    )
    
    # First segment [0, 20] - tag at position 0 should be EXCLUDED
    assert segments[0]["id"] == "seg1"
    assert '<sup class="footnote-marker"></sup><i class="footnote">At seg1 start</i>' not in segments[0]["content"]
    assert '<sup class="footnote-marker"></sup><i class="footnote">After seg1 start</i>' in segments[0]["content"]
    
    # Second segment [20, 40] - tag at position 20 should be EXCLUDED
    assert segments[1]["id"] == "seg2"
    assert '<sup class="footnote-marker"></sup><i class="footnote">At seg2 start</i>' not in segments[1]["content"]
    assert '<sup class="footnote-marker"></sup><i class="footnote">After seg2 start</i>' in segments[1]["content"]

