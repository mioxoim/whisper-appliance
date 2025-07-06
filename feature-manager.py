#!/usr/bin/env python3
"""
WhisperS2T Feature Management CLI
Automated feature cluster management for structured development

Usage:
    python feature-manager.py create "Feature Name" --priority high --effort 3h
    python feature-manager.py status
    python feature-manager.py complete "Feature Name"
    python feature-manager.py list
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path


class FeatureManager:
    """Professional feature management system"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.features_dir = self.base_path / "features"
        self.readme_path = self.base_path / "README-FEATURES.md"
        
    def create_feature(self, name: str, priority: str = "medium", effort: str = "2h", description: str = ""):
        """Create new feature cluster with standard structure"""
        
        # Create feature directory
        feature_slug = name.lower().replace(" ", "-").replace("_", "-")
        feature_path = self.features_dir / feature_slug
        feature_path.mkdir(parents=True, exist_ok=True)
        
        # Create overview.md
        overview_content = f"""# 🎯 {name}

## 🎯 **Feature Overview**

**Status**: 🟡 **Geplant**  
**Priorität**: {self._priority_emoji(priority)} **{priority.title()}**  
**Aufwand**: 📅 **{effort}**
**Zuständig**: Claude  

### **Problem Statement**
{description or 'Problem statement to be defined...'}

### **Solution Design** 
Solution design to be defined...

### **Key Benefits**
- ✅ Benefit 1
- ✅ Benefit 2  
- ✅ Benefit 3

### **Technical Challenges**
- ⚠️ Challenge 1
- ⚠️ Challenge 2

### **Success Criteria**
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
"""
        
        (feature_path / "00-overview.md").write_text(overview_content)
        
        # Create aufgaben.md
        aufgaben_content = f"""# Aufgaben - {name}

## 🎯 **Offene Aufgaben**

### **Phase 1: Analysis** ⏳
- [ ] Requirements analysis
- [ ] Technical design
- [ ] Impact assessment

### **Phase 2: Implementation** ⏳  
- [ ] Core implementation
- [ ] Testing
- [ ] Documentation

### **Phase 3: Integration** ⏳
- [ ] System integration
- [ ] Validation
- [ ] Deployment

## 🔧 **Technische Validierungen**
- [ ] All tests pass
- [ ] No breaking changes
- [ ] Performance acceptable

## 📋 **Testing Checklist**
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing

## ✅ **Abgeschlossene Aufgaben**
(Tasks will be moved here when completed)
"""
        
        (feature_path / "01-aufgaben.md").write_text(aufgaben_content)
        
        # Create code directory
        code_dir = feature_path / "code"
        code_dir.mkdir(exist_ok=True)
        (code_dir / ".gitkeep").write_text("")
        
        print(f"✅ Feature '{name}' created at: {feature_path}")
        return feature_path
        
    def _priority_emoji(self, priority: str) -> str:
        """Get emoji for priority level"""
        priority_map = {
            "low": "🟢",
            "medium": "🟡", 
            "high": "🔥",
            "critical": "🚨"
        }
        return priority_map.get(priority.lower(), "🟡")
        
    def list_features(self):
        """List all features with their status"""
        if not self.features_dir.exists():
            print("No features directory found")
            return
            
        features = []
        for feature_dir in self.features_dir.iterdir():
            if feature_dir.is_dir():
                overview_file = feature_dir / "00-overview.md"
                if overview_file.exists():
                    content = overview_file.read_text()
                    # Extract status from overview
                    status = "Unknown"
                    for line in content.split('\n'):
                        if "**Status**:" in line:
                            status = line.split("**Status**:")[1].strip()
                            break
                    features.append({
                        'name': feature_dir.name,
                        'status': status,
                        'path': feature_dir
                    })
        
        print("\n📋 **Feature Overview**")
        print("=" * 50)
        for feature in features:
            print(f"• {feature['name']}")
            print(f"  Status: {feature['status']}")
            print(f"  Path: {feature['path']}")
            print()
            
    def update_readme(self):
        """Update main README-FEATURES.md with current status"""
        if not self.features_dir.exists():
            return
            
        # This would scan all features and update the main readme
        # Implementation depends on specific needs
        print("📝 README update functionality to be implemented")


def main():
    parser = argparse.ArgumentParser(description="WhisperS2T Feature Management")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create feature command
    create_parser = subparsers.add_parser('create', help='Create new feature')
    create_parser.add_argument('name', help='Feature name')
    create_parser.add_argument('--priority', choices=['low', 'medium', 'high', 'critical'], 
                              default='medium', help='Feature priority')
    create_parser.add_argument('--effort', default='2h', help='Estimated effort (e.g., 2h, 1d)')
    create_parser.add_argument('--description', default='', help='Feature description')
    
    # List features command  
    list_parser = subparsers.add_parser('list', help='List all features')
    
    # Update readme command
    update_parser = subparsers.add_parser('update-readme', help='Update main README')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
        
    fm = FeatureManager()
    
    if args.command == 'create':
        fm.create_feature(args.name, args.priority, args.effort, args.description)
    elif args.command == 'list':
        fm.list_features()
    elif args.command == 'update-readme':
        fm.update_readme()


if __name__ == "__main__":
    main()
