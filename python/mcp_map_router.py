#!/usr/bin/env python3
"""
MCP Map-First Router (Standalone Universal Engine)
Author: Open Source Community
License: MIT

Implements the "Asset Map First, Just-In-Time Mount Next" paradigm:
1. Keeps global mcp_config.json minimal to eliminate Tool Context Tax.
2. Scans user intent against a local structured Asset Map (mcp_registry.json).
3. Mounts matching servers into the active slot only when needed, and detaches when done.
"""

import sys
import os
import json
import re
import argparse

DEFAULT_REGISTRY_FILE = "mcp_registry.json"
DEFAULT_CONFIG_FILE = "mcp_config.json"

def find_file_upwards(filename, max_depth=4):
    curr = os.getcwd()
    for _ in range(max_depth):
        candidate = os.path.join(curr, filename)
        if os.path.exists(candidate):
            return candidate
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent
    return None

def resolve_paths(custom_registry=None, custom_config=None):
    reg_path = custom_registry or find_file_upwards(DEFAULT_REGISTRY_FILE) or DEFAULT_REGISTRY_FILE
    cfg_path = custom_config or find_file_upwards(DEFAULT_CONFIG_FILE) or DEFAULT_CONFIG_FILE
    return reg_path, cfg_path

def load_json(filepath):
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filepath, data):
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

class McpMapRouter:
    def __init__(self, registry_path, config_path):
        self.registry_path = registry_path
        self.config_path = config_path
        self.registry = load_json(registry_path) or {"servers": {}, "profiles": {}}
        self.config = load_json(config_path) or {"mcpServers": {}}

    def status(self):
        active = self.config.get("mcpServers", {})
        all_servers = self.registry.get("servers", {})
        print(f"=== MCP Map Router Status ===")
        print(f"Registry: {self.registry_path} ({len(all_servers)} registered assets)")
        print(f"Config:   {self.config_path} ({len(active)} active mounted)")
        print("\nActive (Mounted in Context):")
        if not active:
            print("  (Empty slot - Zero context overhead)")
        for name in active:
            meta = all_servers.get(name, {})
            desc = meta.get("description", "No description")
            count = meta.get("toolsCount", "?")
            print(f"  ● {name:20s} [{count} tools] - {desc}")
        print("\nAvailable in Asset Map (Dormant):")
        for name, meta in all_servers.items():
            if name not in active:
                desc = meta.get("description", "No description")
                count = meta.get("toolsCount", "?")
                print(f"  ○ {name:20s} [{count} tools] - {desc}")

    def list_profiles(self):
        profiles = self.registry.get("profiles", {})
        print("=== Configured Profiles ===")
        for p, servers in profiles.items():
            print(f"  - {p:12s} -> {', '.join(servers)}")

    def use_profile(self, profile_name):
        profiles = self.registry.get("profiles", {})
        if profile_name not in profiles:
            print(f"Error: Profile '{profile_name}' not found. Available: {list(profiles.keys())}", file=sys.stderr)
            return False
        target_servers = profiles[profile_name]
        new_active = {}
        for s in target_servers:
            if s in self.registry.get("servers", {}):
                new_active[s] = self.registry["servers"][s]["serverConfig"]
        self.config["mcpServers"] = new_active
        save_json(self.config_path, self.config)
        print(f"Successfully switched to profile '{profile_name}'. Mounted: {', '.join(new_active.keys())}")
        return True

    def scan_intent(self, text, threshold=3):
        text_lower = text.lower()
        matches = []
        for name, meta in self.registry.get("servers", {}).items():
            score = 0
            matched_terms = []
            for tag in meta.get("tags", []):
                if tag.lower() in text_lower:
                    score += 2
                    matched_terms.append(tag)
            for pattern in meta.get("intentPatterns", []):
                if pattern.lower() in text_lower or re.search(re.escape(pattern), text_lower):
                    score += 3
                    matched_terms.append(f"regex:{pattern}")
            if score >= threshold:
                matches.append((score, name, meta, list(set(matched_terms))))
        matches.sort(key=lambda x: x[0], reverse=True)
        return matches

    def jit_mount(self, server_name):
        if server_name not in self.registry.get("servers", {}):
            print(f"Server '{server_name}' not registered in asset map.", file=sys.stderr)
            return False
        active = self.config.get("mcpServers", {})
        if server_name in active:
            print(f"'{server_name}' already mounted.")
            return True
        active[server_name] = self.registry["servers"][server_name]["serverConfig"]
        self.config["mcpServers"] = active
        save_json(self.config_path, self.config)
        print(f"Just-In-Time Mounted '{server_name}' into {self.config_path}.")
        return True

def main():
    parser = argparse.ArgumentParser(description="MCP Map-First Router CLI")
    parser.add_argument("-r", "--registry", help="Path to mcp_registry.json")
    parser.add_argument("-c", "--config", help="Path to mcp_config.json")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("status", help="Show active vs dormant servers")
    subparsers.add_parser("list", help="List available profiles")
    
    use_parser = subparsers.add_parser("use", help="Switch to named profile")
    use_parser.add_argument("profile", help="Profile name")

    scan_parser = subparsers.add_parser("scan", help="Scan intent against asset map")
    scan_parser.add_argument("prompt", help="User input text")
    scan_parser.add_argument("--mount", action="store_true", help="Auto-mount top match")

    args = parser.parse_args()
    reg_path, cfg_path = resolve_paths(args.registry, args.config)
    router = McpMapRouter(reg_path, cfg_path)

    if args.command == "status":
        router.status()
    elif args.command == "list":
        router.list_profiles()
    elif args.command == "use":
        router.use_profile(args.profile)
    elif args.command == "scan":
        results = router.scan_intent(args.prompt)
        if not results:
            print(f"No matching server found for: '{args.prompt}'")
        else:
            print(f"Matches for: '{args.prompt}'")
            for score, name, meta, terms in results:
                print(f"  ★ [{score} pts] {name} ({meta.get('displayName')}) - Matched: {', '.join(terms)}")
            if args.mount:
                top = results[0][1]
                router.jit_mount(top)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
