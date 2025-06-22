#!/usr/bin/env python3
"""
Script to extract wildcard domains from ZeroOmega Gist and append to Proxy-Domain.list

This script fetches the ZeroOmega configuration from the specified Gist,
extracts wildcard domain patterns from the "auto switch" profile,
and appends them to the Proxy-Domain.list file as DOMAIN-SUFFIX entries.
"""

import json
import re
import requests
from typing import List, Set
import sys
import os


def fetch_gist_content(gist_url: str) -> dict:
    """
    Fetch and parse JSON content from GitHub Gist
    
    Args:
        gist_url: URL of the GitHub Gist
        
    Returns:
        Parsed JSON content as dictionary
        
    Raises:
        requests.RequestException: If failed to fetch the content
        json.JSONDecodeError: If failed to parse JSON
    """
    # Extract raw URL from gist URL
    if "/raw/" not in gist_url:
        # Convert gist URL to raw URL
        gist_id = gist_url.split('/')[-1]
        raw_url = f"https://gist.githubusercontent.com/cloud-native-yang/{gist_id}/raw/ZeroOmega.json"
    else:
        raw_url = gist_url
    
    print(f"Fetching content from: {raw_url}")
    
    try:
        response = requests.get(raw_url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching gist content: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON content: {e}")
        raise


def extract_wildcard_domains(config: dict) -> Set[str]:
    """
    Extract wildcard domain patterns from auto switch profile
    
    Args:
        config: ZeroOmega configuration dictionary
        
    Returns:
        Set of domain suffixes (without the *. prefix)
    """
    domains = set()
    
    # Look for the "auto switch" profile
    auto_switch_key = "+auto switch"
    if auto_switch_key not in config:
        print("Warning: 'auto switch' profile not found in configuration")
        return domains
    
    auto_switch = config[auto_switch_key]
    
    if "rules" not in auto_switch:
        print("Warning: No rules found in auto switch profile")
        return domains
    
    # Extract wildcard patterns
    for rule in auto_switch["rules"]:
        if "condition" in rule and "pattern" in rule["condition"]:
            pattern = rule["condition"]["pattern"]
            
            # Check if it's a wildcard pattern and has proxy profile
            if (pattern.startswith("*.") and 
                rule.get("profileName") == "proxy"):
                
                # Remove the *. prefix to get the domain suffix
                domain_suffix = pattern[2:]
                domains.add(domain_suffix)
                print(f"Found domain: {domain_suffix}")
    
    return domains


def read_existing_domains(file_path: str) -> Set[str]:
    """
    Read existing domain suffixes from Proxy-Domain.list
    
    Args:
        file_path: Path to the Proxy-Domain.list file
        
    Returns:
        Set of existing domain suffixes
    """
    existing_domains = set()
    
    if not os.path.exists(file_path):
        print(f"Warning: {file_path} does not exist")
        return existing_domains
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith("DOMAIN-SUFFIX,"):
                    domain = line.split(",", 1)[1]
                    existing_domains.add(domain)
    except IOError as e:
        print(f"Error reading {file_path}: {e}")
        raise
    
    return existing_domains


def append_domains_to_file(file_path: str, new_domains: Set[str]) -> None:
    """
    Append new domain suffixes to Proxy-Domain.list file
    
    Args:
        file_path: Path to the Proxy-Domain.list file
        new_domains: Set of new domain suffixes to append
    """
    if not new_domains:
        print("No new domains to append")
        return
    
    try:
        with open(file_path, 'a', encoding='utf-8') as f:
            for domain in sorted(new_domains):
                f.write(f"DOMAIN-SUFFIX,{domain}\n")
                print(f"Added: DOMAIN-SUFFIX,{domain}")
    except IOError as e:
        print(f"Error writing to {file_path}: {e}")
        raise


def main():
    """Main function to orchestrate the domain extraction and appending process"""
    
    # Configuration
    gist_url = "https://gist.github.com/cloud-native-yang/1d4db297fd0146b850f51e33143a4fa5"
    proxy_domain_file = "customize/Proxy-Domain.list"
    
    print("Starting domain extraction process...")
    
    try:
        # Step 1: Fetch gist content
        config = fetch_gist_content(gist_url)
        
        # Step 2: Extract wildcard domains
        new_domains = extract_wildcard_domains(config)
        
        if not new_domains:
            print("No wildcard domains found in the gist")
            return
        
        print(f"Found {len(new_domains)} wildcard domains")
        
        # Step 3: Read existing domains
        existing_domains = read_existing_domains(proxy_domain_file)
        print(f"Found {len(existing_domains)} existing domains in {proxy_domain_file}")
        
        # Step 4: Filter out duplicates
        domains_to_add = new_domains - existing_domains
        
        if not domains_to_add:
            print("All domains already exist in the file")
            return
        
        print(f"Will add {len(domains_to_add)} new domains")
        
        # Step 5: Append new domains
        append_domains_to_file(proxy_domain_file, domains_to_add)
        
        print(f"Successfully added {len(domains_to_add)} new domains to {proxy_domain_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()