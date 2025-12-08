"""
Setup script for building Marketing Mandy as a Mac app
Usage: python setup.py py2app
"""
from setuptools import setup

APP = ['mandy.py']
DATA_FILES = []

OPTIONS = {
    'argv_emulation': True,
    'iconfile': None,  # Add path to .icns file if you have one
    'plist': {
        'CFBundleName': 'Marketing Mandy',
        'CFBundleDisplayName': 'Marketing Mandy',
        'CFBundleGetInfoString': 'Your AI Posting Homie',
        'CFBundleIdentifier': 'com.marketingmandy.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.13.0',
    },
    'packages': [
        'flask',
        'flask_cors',
        'webview',
        'apscheduler',
        'sqlalchemy',
        'langchain',
        'langchain_anthropic',
        'langchain_openai',
        'pydantic',
    ],
}

setup(
    name='Marketing Mandy',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
