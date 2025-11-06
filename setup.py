"""
AICode 安装脚本
"""
from setuptools import setup, find_packages
from aicode.config.constants import VERSION, PROJECT_NAME

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

with open('requirements.txt', 'r', encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name=PROJECT_NAME,
    version=VERSION,
    description='AI-powered coding assistant CLI',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='AICode Team',
    author_email='',
    url='https://github.com/yourusername/aicode',
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'aicode=aicode.cli.main:cli_entry',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    python_requires='>=3.9',
)
