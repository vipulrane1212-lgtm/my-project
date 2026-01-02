#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup script to configure Git credentials for Railway.
This script helps set up GitHub Personal Access Token for automatic Git pushes.
"""
import os
import subprocess
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def check_git_repo():
    """Check if we're in a Git repository."""
    if not Path('.git').exists():
        print("❌ Not in a Git repository!")
        return False
    return True

def get_remote_url():
    """Get current Git remote URL."""
    try:
        result = subprocess.run(
            ['git', 'config', '--get', 'remote.origin.url'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception:
        return None

def setup_git_credentials():
    """Setup Git credentials using environment variable."""
    print("="*80)
    print("SETUP GIT CREDENTIALS FOR RAILWAY")
    print("="*80)
    
    if not check_git_repo():
        return False
    
    # Check for GitHub token
    github_token = os.getenv('GITHUB_TOKEN') or os.getenv('GIT_TOKEN')
    
    if not github_token:
        print("\nWARNING: GITHUB_TOKEN not found in environment variables")
        print("\nTo set up:")
        print("1. Create GitHub PAT: https://github.com/settings/tokens")
        print("2. Add to Railway Variables: GITHUB_TOKEN=ghp_xxxxx")
        print("3. Or set locally: export GITHUB_TOKEN=ghp_xxxxx")
        return False
    
    print(f"\n✅ Found GITHUB_TOKEN (length: {len(github_token)})")
    
    # Get remote URL
    remote_url = get_remote_url()
    if not remote_url:
        print("❌ Could not get Git remote URL")
        return False
    
    print(f"📡 Current remote: {remote_url}")
    
    # Check if URL already has token
    if '@' in remote_url and 'github.com' in remote_url:
        print("✅ Remote URL already configured with credentials")
        return True
    
    # Update remote URL to include token
    if 'github.com' in remote_url:
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(remote_url)
        
        # Extract username from URL or use token
        if parsed.netloc.startswith('github.com'):
            new_netloc = f"{github_token}@{parsed.netloc}"
        else:
            new_netloc = parsed.netloc
        
        new_url = f"{parsed.scheme}://{new_netloc}{parsed.path}"
        
        try:
            subprocess.run(
                ['git', 'remote', 'set-url', 'origin', new_url],
                capture_output=True,
                timeout=5,
                check=True
            )
            print(f"✅ Updated remote URL with credentials")
            print(f"   New remote: {parsed.scheme}://{github_token[:10]}...@{parsed.netloc}{parsed.path}")
            return True
        except Exception as e:
            print(f"❌ Failed to update remote URL: {e}")
            return False
    
    return False

def test_git_push():
    """Test if Git push works."""
    print("\n🧪 Testing Git push...")
    try:
        # Try to push (dry-run or check remote)
        result = subprocess.run(
            ['git', 'ls-remote', '--heads', 'origin', 'main'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print("✅ Git authentication working - can access remote")
            return True
        else:
            print(f"⚠️  Git authentication test failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"⚠️  Could not test Git push: {e}")
        return False

if __name__ == "__main__":
    success = setup_git_credentials()
    if success:
        test_git_push()
        print("\n✅ Git credentials configured!")
        print("\nNext steps:")
        print("1. Add GITHUB_TOKEN to Railway Variables")
        print("2. Redeploy Railway service")
        print("3. Check logs for 'Synced to Git' messages")
    else:
        print("\n❌ Git credentials setup incomplete")
        print("See SETUP_GIT_CREDENTIALS.md for detailed instructions")
        sys.exit(1)

