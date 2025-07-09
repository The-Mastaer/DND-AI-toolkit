D&D AI Toolkit - Bug Fix Log
This document tracks significant bugs encountered and resolved during the development of the D&D AI Toolkit.

1. Configuration & Execution Errors
1.1. Relative Import Error on Launch
Error: ImportError: attempted relative import with no known parent package

Cause: The application was being launched by directly executing python src/main.py. This method does not treat the src directory as a package, causing relative imports (from .state import ...) to fail.

Solution:

Execution Command: The application must be run as a module from the project's root directory using the command: python -m src.main.

IDE Configuration: A PyCharm "Run Configuration" was set up to use the "Module name" src.main instead of "Script path", automating the correct execution method.

1.2. Supabase Key Not Found
Error: WARNING: SUPABASE_KEY not found in .env file. followed by SupabaseException: supabase_key is required.

Cause: The .env file containing the API keys was located in the wrong directory. The python-dotenv library was looking for it in the project root, where execution was initiated.

Solution: The .env file was moved to the project's root directory (DND-AI-toolkit/), parallel to the src/ folder.

2. Flet Framework Syntax Errors
A series of AttributeError exceptions were encountered due to subtle inconsistencies in Flet's syntax.

2.1. Incorrect ft.Icons and ft.Colors Usage
Error: AttributeError: module 'flet' has no attribute 'icons' and AttributeError: module 'flet' has no attribute 'colors'.

Cause: The initial code used lowercase ft.Icons and ft.Colors. The Flet library requires PascalCase for these modules.

Solution: All references were updated to use the correct, case-sensitive syntax: ft.Icons and ft.Colors.

2.2. Invalid Color Constant
Error: AttributeError: SURFACE_VARIANT

Cause: The code attempted to use ft.Colors.SURFACE_VARIANT. While SURFACE_VARIANT is a color concept in the Material Design 3 theme system, it is not a direct color constant available under ft.Colors.

Solution: The invalid color was replaced with a valid, appropriate constant from the ft.Colors enum. The AppBar background color was changed to ft.Colors.SURFACE_CONTAINER_HIGHEST.