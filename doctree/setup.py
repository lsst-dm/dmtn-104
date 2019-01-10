from setuptools import setup

requires = [
    'requests',
    'pyandoc',
    'arrow',
    'jinja2',
    'click',
    'BeautifulSoup4',
    'marshmallow<3',
    'setuptools_scm'
]

doc_requires = [
    "sphinx",
    "sphinx_click",
    "sphinx_rtd_theme"
]

setup(
    name='doctree',
    use_scm_version={'version_scheme': 'post-release'},
    setup_requires=['setuptools_scm'],
    packages=['doctree'],
    url='https://github.com/lsst-dm/DMTN-104/doctree',
    license='GPL',
    author='Gabriele Comoretto',
    author_email='gcomoretto@lsst.org',
    description='DocTree generation from different sources (MagicDraw, GitHub)',
    install_requires=requires,
    package_data={'doctree': ['templates/*.jinja2']},
    entry_points={
        'console_scripts': [
            'doctree = doctree:cli',
        ],
    },
    extras_require={'docs': doc_requires}
)
