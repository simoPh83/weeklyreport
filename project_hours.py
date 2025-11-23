"""
Project Hours Calculator
Analyzes git commits to estimate total hours worked on the project
"""
import subprocess
import json
from datetime import datetime, timedelta
from collections import defaultdict
import sys


def run_git_command(command_args):
    """Run a git command and return the output"""
    try:
        # Don't use shell=True to avoid PowerShell interpretation issues
        result = subprocess.run(
            command_args,
            capture_output=True,
            text=True,
            cwd=".",
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e}")
        print(f"stderr: {e.stderr}")
        return None


def get_all_commits():
    """Get all commits with timestamp and author info"""
    # Get commits - use list format to avoid shell interpretation
    git_log = run_git_command([
        'git', 'log', '--all', 
        '--format=%H|%aI|%an|%ae|%s'
    ])
    
    if not git_log:
        print("No commits found or git repository not initialized")
        return []
    
    commits = []
    for line in git_log.split('\n'):
        if not line:
            continue
        
        parts = line.split('|')
        if len(parts) >= 5:
            commit_hash = parts[0]
            timestamp_str = parts[1]
            author_name = parts[2]
            author_email = parts[3]
            message = '|'.join(parts[4:])  # In case message contains |
            
            try:
                # Parse ISO 8601 format: 2025-11-21T14:44:46Z
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                commits.append({
                    'hash': commit_hash,
                    'timestamp': timestamp,
                    'author_name': author_name,
                    'author_email': author_email,
                    'message': message
                })
            except (ValueError, AttributeError) as e:
                print(f"Warning: Could not parse timestamp '{timestamp_str}': {e}")
                continue
    
    return sorted(commits, key=lambda x: x['timestamp'])


def calculate_work_sessions(commits, max_gap_hours=3):
    """
    Calculate work sessions based on commit timestamps
    Assumes a new session starts if gap between commits > max_gap_hours
    """
    if not commits:
        return []
    
    sessions = []
    current_session_start = commits[0]['timestamp']
    current_session_end = commits[0]['timestamp']
    current_session_commits = [commits[0]]
    
    for i in range(1, len(commits)):
        commit = commits[i]
        time_gap = (commit['timestamp'] - current_session_end).total_seconds() / 3600
        
        if time_gap <= max_gap_hours:
            # Same session
            current_session_end = commit['timestamp']
            current_session_commits.append(commit)
        else:
            # New session - save previous session
            # Estimate session duration: add 1 hour after last commit
            session_duration = (current_session_end - current_session_start).total_seconds() / 3600 + 1.0
            sessions.append({
                'start': current_session_start,
                'end': current_session_end,
                'duration_hours': session_duration,
                'commits': len(current_session_commits),
                'commit_list': current_session_commits
            })
            
            # Start new session
            current_session_start = commit['timestamp']
            current_session_end = commit['timestamp']
            current_session_commits = [commit]
    
    # Add final session
    session_duration = (current_session_end - current_session_start).total_seconds() / 3600 + 1.0
    sessions.append({
        'start': current_session_start,
        'end': current_session_end,
        'duration_hours': session_duration,
        'commits': len(current_session_commits),
        'commit_list': current_session_commits
    })
    
    return sessions


def main():
    """Main function to calculate and display project hours"""
    print("=" * 70)
    print("PROJECT HOURS CALCULATOR")
    print("=" * 70)
    print()
    
    # Get repository info
    repo_name = run_git_command(['git', 'config', '--get', 'remote.origin.url'])
    if repo_name:
        print(f"Repository: {repo_name}")
    
    current_branch = run_git_command(['git', 'branch', '--show-current'])
    if current_branch:
        print(f"Current Branch: {current_branch}")
    print()
    
    # Get all commits
    print("Fetching all commits from all branches...")
    commits = get_all_commits()
    
    if not commits:
        print("\nNo commits found. Make sure you're in a git repository.")
        return
    
    print(f"Found {len(commits)} commits")
    print()
    
    # Calculate sessions
    print("Calculating work sessions (commits within 3 hours = same session)...")
    sessions = calculate_work_sessions(commits, max_gap_hours=3)
    
    print(f"Identified {len(sessions)} work sessions")
    print()
    
    # Calculate totals
    total_hours = sum(session['duration_hours'] for session in sessions)
    total_commits = len(commits)
    
    # Get unique authors
    authors = defaultdict(lambda: {'commits': 0, 'hours': 0})
    for session in sessions:
        for commit in session['commit_list']:
            author = commit['author_name']
            authors[author]['commits'] += 1
    
    # Distribute session hours among authors proportionally
    for session in sessions:
        session_commits_by_author = defaultdict(int)
        for commit in session['commit_list']:
            session_commits_by_author[commit['author_name']] += 1
        
        total_session_commits = len(session['commit_list'])
        for author, commit_count in session_commits_by_author.items():
            proportion = commit_count / total_session_commits
            authors[author]['hours'] += session['duration_hours'] * proportion
    
    # Display summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total Work Hours (estimated): {total_hours:.1f} hours ({total_hours/8:.1f} days)")
    print(f"Total Commits: {total_commits}")
    print(f"Total Sessions: {len(sessions)}")
    print(f"Average Session Length: {total_hours/len(sessions):.1f} hours")
    print()
    
    # First commit date
    first_commit = commits[0]
    last_commit = commits[-1]
    project_duration = (last_commit['timestamp'] - first_commit['timestamp']).days
    
    print(f"First Commit: {first_commit['timestamp'].strftime('%Y-%m-%d %H:%M')}")
    print(f"Last Commit: {last_commit['timestamp'].strftime('%Y-%m-%d %H:%M')}")
    print(f"Project Duration: {project_duration} days")
    print()
    
    # Authors breakdown
    if len(authors) > 1:
        print("=" * 70)
        print("BREAKDOWN BY AUTHOR")
        print("=" * 70)
        for author, stats in sorted(authors.items(), key=lambda x: x[1]['hours'], reverse=True):
            print(f"{author}:")
            print(f"  - Hours: {stats['hours']:.1f} ({stats['hours']/8:.1f} days)")
            print(f"  - Commits: {stats['commits']}")
            print()
    
    # Recent sessions
    print("=" * 70)
    print("LAST 10 WORK SESSIONS")
    print("=" * 70)
    for session in sessions[-10:]:
        start_str = session['start'].strftime('%Y-%m-%d %H:%M')
        end_str = session['end'].strftime('%H:%M')
        authors_in_session = set(c['author_name'] for c in session['commit_list'])
        author_str = ', '.join(authors_in_session)
        
        print(f"{start_str} - {end_str} ({session['duration_hours']:.1f}h) - {session['commits']} commits - {author_str}")
    
    print()
    print("=" * 70)
    print("Note: Hours are estimated based on commit patterns.")
    print("Sessions are assumed to last 1 hour after the last commit.")
    print("Commits within 3 hours are considered part of the same session.")
    print("=" * 70)


if __name__ == '__main__':
    main()
