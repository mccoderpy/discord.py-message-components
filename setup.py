import os
import re
from pathlib import Path
from setuptools import setup

# The directory containing this file
HERE = Path(__file__).parent

version = ''
with open(f'{HERE}/discord/__init__.py') as f:
    version += re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE
    )[1]

v = None
if os.path.isfile('version.txt'):
    with open(f'{HERE}/version.txt', 'r') as fp:
        v = fp.read()

if version != v:
    try:
        i = input(f'are you sure to use version {version}>> ')
    except EOFError:
        pass
    else:
        version = i if i else version
        with open('version.txt', 'w') as fp:
            fp.write(i)

if not (version or v):
    try:
        version = input('please set a version>> ')
    except EOFError:
        pass
    if not version:
        raise RuntimeError('version is not set')

if version.endswith(('a', 'b', 'rc', 'dev')):
    # append version identifier based on commit count
    try:
        import subprocess
        p = subprocess.Popen(['git', 'rev-list', '--count', 'HEAD'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out:
            version += out.decode('utf-8').strip()
        p = subprocess.Popen(['git', 'rev-parse', '--short', 'HEAD'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out:
            version += f'+g{out.decode("utf-8").strip()}'
    except Exception:
        __import__('traceback').print_exc()
    else:
        with open(f'{HERE}/version.txt', 'w') as fp:
            fp.write(version)


# The text of the README file
readme = Path('./README.rst').read_text(encoding='utf-8')

#
extras_require = {
    'voice': ['PyNaCl>=1.3.0,<1.5'],
    'docs': [
        'sphinx==3.0.3',
        'sphinxcontrib_trio==1.1.2',
        'sphinxcontrib-websupport',
    ],
    'speedups': [
        'aiohttp[speedups]'
    ]
}

# This call to setup() does all the work
setup(
    name="discord.py-message-components",
    url="https://github.com/mccoderpy/discord.py-message-components",
    project_urls={
        'Documentation': 'https://discordpy-message-components.readthedocs.io/en/latest/',
        'Source': 'https://github.com/mccoderpy/discord.py-message-components/',
        'Support': 'https://discord.gg/sb69muSqsg',
        'Issue Tracker': 'https://github.com/mccoderpy/discord.py-message-components/issues'
    },
    author_email="mccuber04@outlook.de",
    version=str(version),
    author="mccoder.py",
    description="A \"fork\" of discord.py library made by Rapptz with implementation of the Discord-Message-Components & other features by mccoderpy",
    keywords='discord discord4py discord.py discord.py-message-components discord-components discord-interactions  message-components components ',
    long_description=readme,
    long_description_content_type="text/x-rst",
    extras_require=extras_require,
    license="MIT",
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Internet',
        'Framework :: aiohttp',
        'Framework :: asyncio',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities'
    ],
    packages=['discord', 'discord.types', 'discord.bin', 'discord.oauth2', 'discord.ext.commands', 'discord.ext.tasks'],
    include_package_data=True,
    install_requires=[
        "aiohttp",
        "chardet",
        "yarl",
        'aiosignal',
        "async-timeout",
        "typing-extensions",
        "attrs",
        "multidict",
        "idna",
        'importlib-metadata<4;python_version<"3.8.0"',
        'colorama',
        'color-pprint'
    ],
    python_requires=">=3.6"
)
