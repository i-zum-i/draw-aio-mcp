#!/usr/bin/env python3
"""
簡単なツールテスト
"""

import sys
sys.path.append('.')

from src.server import TOOL_DEFINITIONS

def test_tools():
    print(f"ツール数: {len(TOOL_DEFINITIONS)}")
    
    for i, tool in enumerate(TOOL_DEFINITIONS):
        print(f"\nツール {i+1}:")
        print(f"  名前: {tool.name}")
        print(f"  説明: {tool.description}")
        print(f"  スキーマ: {bool(tool.inputSchema)}")
        
        if tool.inputSchema:
            schema = tool.inputSchema
            print(f"  スキーマタイプ: {schema.get('type')}")
            print(f"  プロパティ: {bool(schema.get('properties'))}")
            if schema.get('properties'):
                print(f"  プロパティ数: {len(schema['properties'])}")

if __name__ == "__main__":
    test_tools()