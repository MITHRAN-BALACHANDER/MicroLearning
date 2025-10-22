"""
User Management Script - Add and manage users
"""
import sys
import csv
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.operations import (
    get_or_create_user,
    get_user_by_telegram_id,
    get_db,
    init_db
)
from database.models import User
from loguru import logger


def add_single_user(telegram_id: str, username: str = None, 
                   first_name: str = None, last_name: str = None) -> Dict:
    """
    Add a single user to the database
    
    Args:
        telegram_id: Telegram user ID
        username: Telegram username (optional)
        first_name: First name (optional)
        last_name: Last name (optional)
        
    Returns:
        Dict with result
    """
    try:
        user = get_or_create_user(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        
        return {
            "success": True,
            "user_id": user.id,
            "telegram_id": telegram_id,
            "message": f"User {telegram_id} added successfully"
        }
    except Exception as e:
        logger.error(f"Error adding user: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def import_users_from_csv(csv_file: Path) -> Dict:
    """
    Import multiple users from CSV file
    
    CSV Format:
    telegram_id,username,first_name,last_name
    123456789,john_doe,John,Doe
    987654321,jane_smith,Jane,Smith
    
    Args:
        csv_file: Path to CSV file
        
    Returns:
        Dict with import results
    """
    if not csv_file.exists():
        return {
            "success": False,
            "error": f"File not found: {csv_file}"
        }
    
    results = {
        "success": True,
        "total": 0,
        "added": 0,
        "updated": 0,
        "errors": 0,
        "details": []
    }
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Validate headers
            required_headers = ['telegram_id']
            if not all(h in reader.fieldnames for h in required_headers):
                return {
                    "success": False,
                    "error": f"CSV must have at least 'telegram_id' column. Found: {reader.fieldnames}"
                }
            
            for row_num, row in enumerate(reader, start=2):
                results["total"] += 1
                
                telegram_id = row.get('telegram_id', '').strip()
                if not telegram_id:
                    results["errors"] += 1
                    results["details"].append({
                        "row": row_num,
                        "status": "error",
                        "message": "Missing telegram_id"
                    })
                    continue
                
                username = row.get('username', '').strip() or None
                first_name = row.get('first_name', '').strip() or None
                last_name = row.get('last_name', '').strip() or None
                
                # Check if user exists
                existing_user = get_user_by_telegram_id(telegram_id)
                
                result = add_single_user(telegram_id, username, first_name, last_name)
                
                if result["success"]:
                    if existing_user:
                        results["updated"] += 1
                        status = "updated"
                    else:
                        results["added"] += 1
                        status = "added"
                    
                    results["details"].append({
                        "row": row_num,
                        "telegram_id": telegram_id,
                        "status": status,
                        "message": result["message"]
                    })
                else:
                    results["errors"] += 1
                    results["details"].append({
                        "row": row_num,
                        "telegram_id": telegram_id,
                        "status": "error",
                        "message": result["error"]
                    })
        
        return results
        
    except Exception as e:
        logger.error(f"Error importing CSV: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def list_all_users(active_only: bool = False) -> List[Dict]:
    """
    List all users in the database
    
    Args:
        active_only: Only show active users
        
    Returns:
        List of user dictionaries
    """
    try:
        with get_db() as db:
            query = db.query(User)
            if active_only:
                query = query.filter(User.is_active == True)
            
            users = query.all()
            
            return [
                {
                    "id": user.id,
                    "telegram_id": user.telegram_id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "last_active": user.last_active.strftime("%Y-%m-%d %H:%M:%S") if user.last_active else None,
                    "is_active": user.is_active
                }
                for user in users
            ]
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        return []


def deactivate_user(telegram_id: str) -> Dict:
    """
    Deactivate a user
    
    Args:
        telegram_id: Telegram user ID
        
    Returns:
        Dict with result
    """
    try:
        with get_db() as db:
            user = db.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                return {
                    "success": False,
                    "error": "User not found"
                }
            
            user.is_active = False
            db.commit()
            
            return {
                "success": True,
                "message": f"User {telegram_id} deactivated"
            }
    except Exception as e:
        logger.error(f"Error deactivating user: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def activate_user(telegram_id: str) -> Dict:
    """
    Activate a user
    
    Args:
        telegram_id: Telegram user ID
        
    Returns:
        Dict with result
    """
    try:
        with get_db() as db:
            user = db.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                return {
                    "success": False,
                    "error": "User not found"
                }
            
            user.is_active = True
            db.commit()
            
            return {
                "success": True,
                "message": f"User {telegram_id} activated"
            }
    except Exception as e:
        logger.error(f"Error activating user: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def export_users_to_csv(output_file: Path, active_only: bool = False) -> Dict:
    """
    Export users to CSV file
    
    Args:
        output_file: Path to output CSV file
        active_only: Only export active users
        
    Returns:
        Dict with result
    """
    try:
        users = list_all_users(active_only)
        
        if not users:
            return {
                "success": False,
                "error": "No users to export"
            }
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['telegram_id', 'username', 'first_name', 'last_name', 
                         'created_at', 'last_active', 'is_active']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for user in users:
                writer.writerow({
                    'telegram_id': user['telegram_id'],
                    'username': user['username'] or '',
                    'first_name': user['first_name'] or '',
                    'last_name': user['last_name'] or '',
                    'created_at': user['created_at'],
                    'last_active': user['last_active'] or '',
                    'is_active': user['is_active']
                })
        
        return {
            "success": True,
            "count": len(users),
            "file": str(output_file),
            "message": f"Exported {len(users)} users to {output_file}"
        }
        
    except Exception as e:
        logger.error(f"Error exporting users: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='User Management for MicroLearning Bot')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Add user command
    add_parser = subparsers.add_parser('add', help='Add a single user')
    add_parser.add_argument('telegram_id', help='Telegram user ID')
    add_parser.add_argument('--username', help='Telegram username')
    add_parser.add_argument('--first-name', help='First name')
    add_parser.add_argument('--last-name', help='Last name')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import users from CSV')
    import_parser.add_argument('csv_file', help='Path to CSV file')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all users')
    list_parser.add_argument('--active-only', action='store_true', help='Show only active users')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export users to CSV')
    export_parser.add_argument('output_file', help='Output CSV file path')
    export_parser.add_argument('--active-only', action='store_true', help='Export only active users')
    
    # Deactivate command
    deactivate_parser = subparsers.add_parser('deactivate', help='Deactivate a user')
    deactivate_parser.add_argument('telegram_id', help='Telegram user ID')
    
    # Activate command
    activate_parser = subparsers.add_parser('activate', help='Activate a user')
    activate_parser.add_argument('telegram_id', help='Telegram user ID')
    
    args = parser.parse_args()
    
    # Initialize database
    init_db()
    
    if args.command == 'add':
        result = add_single_user(
            args.telegram_id,
            args.username,
            args.first_name,
            args.last_name
        )
        if result["success"]:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ Error: {result['error']}")
    
    elif args.command == 'import':
        csv_file = Path(args.csv_file)
        print(f"Importing users from {csv_file}...")
        result = import_users_from_csv(csv_file)
        
        if result["success"]:
            print(f"\n✅ Import completed!")
            print(f"Total rows: {result['total']}")
            print(f"Added: {result['added']}")
            print(f"Updated: {result['updated']}")
            print(f"Errors: {result['errors']}")
            
            if result['details']:
                print("\nDetails:")
                for detail in result['details']:
                    status_icon = "✅" if detail['status'] in ['added', 'updated'] else "❌"
                    print(f"  {status_icon} Row {detail['row']}: {detail['status']} - {detail.get('message', '')}")
        else:
            print(f"❌ Error: {result['error']}")
    
    elif args.command == 'list':
        users = list_all_users(args.active_only)
        if users:
            print(f"\n{'Active ' if args.active_only else ''}Users ({len(users)}):")
            print("-" * 80)
            print(f"{'ID':<5} {'Telegram ID':<15} {'Username':<20} {'Name':<25} {'Active':<8}")
            print("-" * 80)
            for user in users:
                name = f"{user['first_name'] or ''} {user['last_name'] or ''}".strip() or 'N/A'
                print(f"{user['id']:<5} {user['telegram_id']:<15} {user['username'] or 'N/A':<20} {name:<25} {'Yes' if user['is_active'] else 'No':<8}")
        else:
            print("No users found.")
    
    elif args.command == 'export':
        output_file = Path(args.output_file)
        result = export_users_to_csv(output_file, args.active_only)
        
        if result["success"]:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ Error: {result['error']}")
    
    elif args.command == 'deactivate':
        result = deactivate_user(args.telegram_id)
        if result["success"]:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ Error: {result['error']}")
    
    elif args.command == 'activate':
        result = activate_user(args.telegram_id)
        if result["success"]:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ Error: {result['error']}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
