import os
import re
from pathlib import Path
from setuptools import setup

# The directory containing this file
HERE = Path(__file__).parent

version = ''
with open(f'{HERE}/discord/__init__.py') as f:
    version += re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

v = None
if os.path.isfile('version.txt'):
    with open('version.txt', 'r') as fp:
        v = fp.read()

if version and not v:
    version = i if (i := input(f'are you sure to use version {version}>> ')) else version
    with open('version.txt', 'w') as fp:
        fp.write(i)

if not (version or v):
    if not (version := input('please set an version>> ')):
        raise RuntimeError('version is not set')

if version.endswith(('a', 'b', 'rc')):
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
            version += '+g' + out.decode('utf-8').strip()
    except Exception as exc:
        pass


# The text of the README file

readme = Path('./README.rst').read_text(encoding='utf-8')

#
extras_require = {
    'voice': ['PyNaCl>=1.3.0,<1.5'],
    'docs': [
        'sphinx==3.0.3',
        'sphinxcontrib_trio==1.1.2',
        'sphinxcontrib-websupport',
    ]
}

# This call to setup() does all the work
setup(
    name="discord.py-message-components",
    url="https://github.com/mccoderpy/discord.py-message-components",
    project_urls={'Documentation': 'https://discordpy-message-components.readthedocs.io/en/latest/', 'Source': 'https://github.com/mccoderpy/discord.py-message-components/', 'Support': 'https://discord.gg/sb69muSqsg', 'Issue Tracker': 'https://github.com/mccoderpy/discord.py-message-components/issues'},
    author_email="mccuber04@outlook.de",
    version=str(v if v else version),
    author="mccoder.py",
    description="The discord.py Library with implementation of the Discord-Message-Components",
    keywords='discord.py discord.py-message-components discord-components discord-interactions discord message-components',
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
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities'
    ],
    packages=['discord', 'discord.ext.commands', 'discord.ext.tasks'],
    include_package_data=True,
    install_requires=["aiohttp", "chardet", "yarl", "async-timeout", "typing-extensions", "attrs", "multidict", "idna"],
    python_requires=">=3.6"
)
