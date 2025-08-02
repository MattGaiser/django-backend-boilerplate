#!/usr/bin/env python
"""
Script to generate version.json file with Git metadata and deployment timestamp.

This script reads Git information and creates a version.json file containing:
- commit: Latest commit SHA
- timestamp: Current timestamp (deployment time)  
- branch: Current Git branch

Usage:
    python scripts/write_version_file.py [output_path]
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def get_git_commit():
    """Get the current Git commit SHA."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return 'unknown'


def get_git_branch():
    """Get the current Git branch."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return 'unknown'


def get_timestamp():
    """Get the current timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def create_version_info():
    """Create version information dictionary."""
    return {
        'commit': get_git_commit(),
        'timestamp': get_timestamp(),
        'branch': get_git_branch()
    }


def write_version_file(output_path=None):
    """Write version.json file to the specified path."""
    if output_path is None:
        # Default to version.json in the project root
        base_dir = Path(__file__).parent.parent
        output_path = base_dir / 'version.json'
    else:
        output_path = Path(output_path)
    
    version_info = create_version_info()
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write version file
    with open(output_path, 'w') as f:
        json.dump(version_info, f, indent=2)
    
    print(f"Version file written to: {output_path}")
    print(f"Version info: {json.dumps(version_info, indent=2)}")
    
    return version_info


if __name__ == '__main__':
    output_path = sys.argv[1] if len(sys.argv) > 1 else None
    write_version_file(output_path)