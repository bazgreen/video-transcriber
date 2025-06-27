#!/usr/bin/env python3
"""
Enhanced Export Dependencies Installer
Interactive script to install optional export format dependencies.
"""

import subprocess
import sys


def run_command(command):
    """Run a command and return success status."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def check_installed(package):
    """Check if a package is already installed."""
    success, _, _ = run_command(f"{sys.executable} -c 'import {package}'")
    return success


def install_package(package, name):
    """Install a specific package."""
    print(f"\n🔄 Installing {name}...")
    success, stdout, stderr = run_command(f"{sys.executable} -m pip install {package}")
    
    if success:
        print(f"✅ {name} installed successfully!")
        return True
    else:
        print(f"❌ Failed to install {name}")
        print(f"Error: {stderr}")
        return False


def main():
    """Main installation function."""
    print("🚀 Enhanced Export Dependencies Installer")
    print("=" * 50)
    print()
    print("This script will help you install optional dependencies for enhanced export formats:")
    print("📄 PDF Reports - Professional analysis documents")
    print("📝 DOCX Documents - Microsoft Word format")
    print()
    
    # Check current status
    reportlab_installed = check_installed("reportlab")
    docx_installed = check_installed("docx")
    
    print("📊 Current Status:")
    print(f"   PDF Support (reportlab):  {'✅ Installed' if reportlab_installed else '❌ Not installed'}")
    print(f"   DOCX Support (python-docx): {'✅ Installed' if docx_installed else '❌ Not installed'}")
    print()
    
    if reportlab_installed and docx_installed:
        print("🎉 All optional dependencies are already installed!")
        print("You have access to all export formats.")
        return
    
    # Installation options
    print("💾 Installation Options:")
    print("1. Install both PDF and DOCX support (recommended)")
    print("2. Install PDF support only")
    print("3. Install DOCX support only")
    print("4. Skip installation")
    print()
    
    try:
        choice = input("Enter your choice (1-4): ").strip()
    except KeyboardInterrupt:
        print("\n\n❌ Installation cancelled by user")
        return
    
    if choice == "1":
        print("\n🔄 Installing full export support...")
        success = True
        if not reportlab_installed:
            success &= install_package("reportlab>=4.0.0", "PDF support (reportlab)")
        if not docx_installed:
            success &= install_package("python-docx>=1.1.0", "DOCX support (python-docx)")
        
        if success:
            print("\n🎉 Full export support installed successfully!")
            print("You now have access to all export formats: SRT, VTT, PDF, DOCX, Enhanced Text, JSON, HTML")
        
    elif choice == "2":
        if not reportlab_installed:
            if install_package("reportlab>=4.0.0", "PDF support (reportlab)"):
                print("\n🎉 PDF export support installed!")
        else:
            print("\n✅ PDF support already installed")
            
    elif choice == "3":
        if not docx_installed:
            if install_package("python-docx>=1.1.0", "DOCX support (python-docx)"):
                print("\n🎉 DOCX export support installed!")
        else:
            print("\n✅ DOCX support already installed")
            
    elif choice == "4":
        print("\n⏭️  Installation skipped")
        print("Core export formats (SRT, VTT, Enhanced Text, JSON, HTML) are still available")
        
    else:
        print("\n❌ Invalid choice. Installation cancelled.")
    
    print("\n💡 You can run this script again anytime to install additional dependencies.")
    print("Or use manual installation:")
    print("   pip install reportlab python-docx")


if __name__ == "__main__":
    main()
