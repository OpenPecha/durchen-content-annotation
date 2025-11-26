#!/usr/bin/env python3
"""Script to run durchen annotation functions with data files."""

import json
from pathlib import Path

from durchen_content_annotation.annotation import (
    get_all_segments_with_tags,
)



def main():
    """Run annotation functions with data files."""
    # Paths to data files
    data_dir = "./data"
    text_path = "./data/text.txt"
    durchen_path = "./data/durchen.json"
    segmentation_path = "./data/segmentation.json"


    # Load data
    print("Loading data files...")
    with open(text_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    with open(durchen_path, 'r', encoding='utf-8') as f:
        durchen_data = json.load(f)["data"]
    
    with open(segmentation_path, 'r', encoding='utf-8') as f:
        segmentation_data = json.load(f)["data"]
 
    
    
    segments_with_tags = get_all_segments_with_tags(
        text, segmentation_data, durchen_data=durchen_data
    )
 
    # Save results to file (optional)
    output_path = "./data/segments_with_tags.json"
    print(f"\nSaving results to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(segments_with_tags, f, ensure_ascii=False, indent=2)
    print(f"  ✓ Saved {len(segments_with_tags)} segments to {output_path}")
    
if __name__ == "__main__":
    main()

