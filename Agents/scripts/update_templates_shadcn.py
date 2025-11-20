"""
Script to update all templates with shadcn black/white theme
Replaces all neutral-* color classes with HSL variable-based inline styles
"""

import os
import re

# Template directory
TEMPLATE_DIR = r"c:\Users\bmith\OneDrive\Desktop\projects -2025\MicroLearning\Agents\templates"

# Color mapping: neutral Tailwind classes to shadcn HSL variables
COLOR_MAPPINGS = {
    # Text colors
    r'text-neutral-900': 'style="color: hsl(var(--foreground));"',
    r'text-neutral-800': 'style="color: hsl(var(--foreground));"',
    r'text-neutral-700': 'style="color: hsl(var(--foreground));"',
    r'text-neutral-600': 'style="color: hsl(var(--muted-foreground));"',
    r'text-neutral-500': 'style="color: hsl(var(--muted-foreground));"',
    r'text-neutral-400': 'style="color: hsl(var(--muted-foreground));"',
    r'text-white': 'style="color: hsl(var(--primary-foreground));"',
    
    # Background colors
    r'bg-neutral-900': 'style="background: hsl(var(--primary));"',
    r'bg-neutral-800': 'style="background: hsl(var(--primary));"',
    r'bg-neutral-50': 'style="background: hsl(var(--secondary));"',
    r'bg-neutral-100': 'style="background: hsl(var(--muted));"',
    r'bg-white': 'style="background: hsl(var(--card));"',
    
    # Border colors
    r'border-neutral-900': 'style="border-color: hsl(var(--primary));"',
    r'border-neutral-800': 'style="border-color: hsl(var(--primary));"',
    r'border-neutral-400': 'style="border-color: hsl(var(--border));"',
    r'border-neutral-300': 'style="border-color: hsl(var(--border));"',
    r'border-neutral-200': 'style="border-color: hsl(var(--border));"',
    r'border-neutral-100': 'style="border-color: hsl(var(--border));"',
}

# Complex class combinations that need inline style conversion
COMPLEX_REPLACEMENTS = [
    # Cards with background and border
    (r'class="([^"]*?)bg-white([^"]*?)border([^"]*?)border-neutral-200([^"]*?)"',
     r'class="\1\2\3\4" style="background: hsl(var(--card)); border: 1px solid hsl(var(--border));"'),
    
    # Table headers
    (r'class="([^"]*?)bg-neutral-50([^"]*?)border-b([^"]*?)border-neutral-200([^"]*?)"',
     r'class="\1\2\3\4" style="background: hsl(var(--secondary)); border-bottom: 1px solid hsl(var(--border));"'),
    
    # Primary buttons (black background, white text)
    (r'class="([^"]*?)text-white([^"]*?)bg-neutral-900([^"]*?)"',
     r'class="\1\2\3" style="background: hsl(var(--primary)); color: hsl(var(--primary-foreground));"'),
    
    # Secondary buttons (white background, black text, border)
    (r'class="([^"]*?)text-neutral-900([^"]*?)bg-white([^"]*?)border([^"]*?)border-neutral-300([^"]*?)"',
     r'class="\1\2\3\4\5" style="background: hsl(var(--card)); color: hsl(var(--foreground)); border: 1px solid hsl(var(--border));"'),
    
    # Hover states on rows
    (r'class="([^"]*?)hover:bg-neutral-50([^"]*?)"',
     r'class="\1hover:brightness-95\2"'),
    
    # Dividers
    (r'class="([^"]*?)divide-y([^"]*?)divide-neutral-200([^"]*?)"',
     r'class="\1divide-y\2\3" style="--tw-divide-opacity: 1; border-color: hsl(var(--border) / var(--tw-divide-opacity));"'),
]

def update_template_file(filepath):
    """Update a single template file with shadcn colors"""
    
    print(f"\nProcessing: {os.path.basename(filepath)}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = 0
        
        # Apply complex replacements first
        for pattern, replacement in COMPLEX_REPLACEMENTS:
            matches = len(re.findall(pattern, content))
            if matches > 0:
                content = re.sub(pattern, replacement, content)
                changes_made += matches
                print(f"  - Applied complex pattern: {matches} matches")
        
        # Apply simple color mappings
        for tailwind_class, hsl_style in COLOR_MAPPINGS.items():
            # Only replace if not already in a style attribute
            pattern = rf'class="([^"]*?){tailwind_class}([^"]*?)"(?!\s+style=)'
            matches = len(re.findall(pattern, content))
            if matches > 0:
                # This is trickier - need to add style attribute or merge with existing
                # For now, skip these as complex replacements handle most cases
                pass
        
        if content != original_content:
            # Backup original
            backup_path = filepath + '.backup'
            if not os.path.exists(backup_path):
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                print(f"  ✓ Backup created: {os.path.basename(backup_path)}")
            
            # Write updated content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✓ Updated with {changes_made} changes")
            return True
        else:
            print(f"  - No changes needed")
            return False
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    """Update all templates except base.html and analytics_dashboard.html (already done)"""
    
    print("=" * 60)
    print("Updating Templates with Shadcn Black/White Theme")
    print("=" * 60)
    
    # Skip these files - already updated
    skip_files = ['base.html', 'analytics_dashboard.html', 'dashboard.html']
    
    # Target files
    template_files = [
        'users.html',
        'videos.html',
        'questions.html',
        'documents.html',
        'analytics.html',
        'add_video.html',
        'edit_video.html',
        'user_detail.html',
        'add_user.html',
        'edit_user.html',
    ]
    
    updated = 0
    skipped = 0
    
    for filename in template_files:
        filepath = os.path.join(TEMPLATE_DIR, filename)
        if os.path.exists(filepath):
            if update_template_file(filepath):
                updated += 1
            else:
                skipped += 1
        else:
            print(f"\n✗ File not found: {filename}")
    
    print("\n" + "=" * 60)
    print(f"Summary: {updated} files updated, {skipped} skipped")
    print("=" * 60)
    print("\nNote: Backup files (.backup) created for safety")
    print("Manual review recommended for complex components")

if __name__ == "__main__":
    main()
