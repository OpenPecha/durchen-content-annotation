"""Functions for inserting durchen annotations into text content."""

import re
from typing import List, Dict, Any


def insert_durchen_tags(text: str, durchen_data: List[Dict[str, Any]]) -> str:
    """
    Insert durchen note tags into text at segment end positions.
    
    All tags are inserted simultaneously using original indices to avoid
    index shifting issues. Tags are inserted in descending order of end
    positions to maintain correct indices.
    
    Args:
        text: Original text content
        durchen_data: List of durchen annotation objects, each containing:
            - span: dict with 'start' and 'end' keys
            - note: string containing the note content
    
    Returns: 
        Text with durchen tags inserted at appropriate positions.
        Tags are formatted as <note_content>.
    
    Example:
        >>> text = "I have a dream"
        >>> durchen_data = [{"span": {"start": 0, "end": 10}, "note": "A is good"}]
        >>> insert_durchen_tags(text, durchen_data)
        'I have a d<A is good>ream'
    """
    # Build tag position map using helper function
    tag_position_map = _build_tag_position_map_from_durchen(durchen_data)
    
    # Insert tags starting from the end (descending order) to avoid index shifting
    # Reverse the list since tag_position_map is sorted in ascending order
    annotated_text = text
    for tag_info in reversed(tag_position_map):
        end_index = tag_info['original_pos']
        tag = tag_info['tag']
        annotated_text = annotated_text[:end_index] + tag + annotated_text[end_index:]
    
    return annotated_text


def _build_tag_position_map_from_durchen(durchen_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Build tag position map directly from durchen_data.
    
    This is more efficient than parsing annotated text since we already have
    the exact positions and notes from durchen_data. No regex parsing needed.
    
    Args:
        durchen_data: List of durchen annotation objects, each containing:
            - span: dict with 'start' and 'end' keys
            - note: string containing the note content
    
    Returns:
        List of dictionaries with 'tag' and 'original_pos' keys, sorted by original_pos.
    """
    tag_position_map = []
    for item in durchen_data:
        end_index = item["span"]["end"]
        note = item["note"]
        marker = f'<sup class="footnote-marker"></sup><i class="footnote">{note}</i>'

        tag_position_map.append({
            'tag': marker,
            'original_pos': end_index,
        })
    
    # Sort by original_pos
    tag_position_map.sort(key=lambda x: x['original_pos'])
    return tag_position_map


def get_segment_with_tags(
    original_text: str,
    tag_position_map: List[Dict[str, Any]],
    start: int,
    end: int
) -> str:
    """
    Extract a segment using pre-computed tag position map (optimized for multiple segments).
    
    This function is used internally by get_all_segments_with_tags() to avoid
    recomputing tag positions for each segment.
    
    Args:
        original_text: Original text without tags
        tag_position_map: Pre-computed list of tag positions from _build_tag_position_map()
        start: Start index of the segment (in original text)
        end: End index of the segment (in original text)
    
    Returns:
        Segment content with durchen tags included at their relative positions.
    """
    original_segment = original_text[start:end]
    
    # Filter tags that fall within (start, end] range
    # Note: start is exclusive, end is inclusive
    relevant_tags = [
        tag_info for tag_info in tag_position_map
        if start < tag_info['original_pos'] <= end
    ]
    
    if not relevant_tags:
        return original_segment
    
    # Build result using list
    result_parts = []
    current_pos = 0
    
    for tag_info in relevant_tags:
        relative_pos = tag_info['original_pos'] - start
        
        if relative_pos > current_pos:
            result_parts.append(original_segment[current_pos:relative_pos])
        
        result_parts.append(tag_info['tag'])
        current_pos = relative_pos
    
    if current_pos < len(original_segment):
        result_parts.append(original_segment[current_pos:])
    
    return ''.join(result_parts)


def get_all_segments_with_tags(
    original_text: str,
    segmentation_data: List[Dict[str, Any]],
    durchen_data: List[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Extract all segments from segmentation data with durchen tags included.
    
    Optimized version that builds tag position map once and reuses it for all segments.
    If durchen_data is provided, uses direct data access instead of parsing annotated_text.
    
    Args:
        original_text: Original text without tags
        segmentation_data: List of segmentation objects, each containing:
            - id: segment identifier
            - span: dict with 'start' and 'end' keys
        durchen_data: Optional list of durchen annotation objects. If provided, uses
            this instead of parsing annotated_text for better performance.
    
    Returns:
        List of segment dictionaries with added 'content' field containing
        the segment text with durchen tags included.
    """
    # Build tag position map once (cached for reuse)
    # Use durchen_data if provided for better performance
    if durchen_data is not None:
        tag_position_map = _build_tag_position_map_from_durchen(durchen_data)
   
    
    segments_with_tags = []
    
    for segment in segmentation_data:
        span = segment["span"]
        start = span["start"]
        end = span["end"]
        
        # Extract segment content with tags using cached tag map
        content = get_segment_with_tags(
            original_text, tag_position_map, start, end
        )
        
        # Create new segment dict with content
        segment_with_content = {
            "id": segment["id"],
            "content": content
        }
        
        segments_with_tags.append(segment_with_content)
    
    return segments_with_tags

