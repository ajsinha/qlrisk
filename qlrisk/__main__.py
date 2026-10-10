"""
QLRisk v2.2.1 - Package Entry Point
==================================================

Allows the package to be run with: python -m qlrisk

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is 
strictly prohibited without explicit written permission from the copyright holder.
"""

import sys

def main():
    """Main entry point for the package."""
    from qlrisk.main import main as run_main
    return run_main()

if __name__ == "__main__":
    sys.exit(main())
