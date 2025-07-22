"""Sphinx configuration."""

import datetime
import os
import shutil
import sys
import re
from pathlib import Path

def run_apidoc(app):
    """Generate doc stubs using sphinx-apidoc."""
    module_dir = os.path.join(app.srcdir, "../src/")
    output_dir = os.path.join(app.srcdir, "_apidoc")
    excludes = []

    # Ensure that any stale apidoc files are cleaned up first.
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    cmd = [
        "--separate",
        "--module-first",
        "--doc-project=API Reference",
        "-o",
        output_dir,
        module_dir,
    ]
    cmd.extend(excludes)

    try:
        from sphinx.ext import apidoc  # Sphinx >= 1.7

        apidoc.main(cmd)
    except ImportError:
        from sphinx import apidoc  # Sphinx < 1.7

        cmd.insert(0, apidoc.__file__)
        apidoc.main(cmd)


def setup(app):
    """Register our sphinx-apidoc hook."""
    app.connect("builder-inited", run_apidoc)


# Get version from setup.py
def get_version():
    try:
        # Find the project root directory (where setup.py is located)
        project_root = Path(__file__).parent.parent
        setup_py_path = project_root / "setup.py"
        
        # Read setup.py content
        with open(setup_py_path, "r") as f:
            setup_py_content = f.read()
        
        # Extract version using regex
        version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', setup_py_content)
        if version_match:
            return version_match.group(1)
        else:
            print("Warning: Could not find version in setup.py")
            return "unknown"
    except Exception as e:
        print(f"Warning: Could not extract version from setup.py: {e}")
        return "unknown"


# Sphinx configuration below.
project = "SageMaker HyperPod CLI"
version = get_version()
release = version

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {"python": ("http://docs.python.org/", None)}

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "nbsphinx",
    "myst_nb",
    "sphinx_design",
    "sphinx_tabs.tabs",
    "sphinx_copybutton"
]

# Mock modules that might not be available during documentation build
autodoc_mock_imports = [
    'sagemaker.hyperpod.training.config.hyperpod_pytorch_job_config',
    'hyperpod_pytorch_job_template.registry'
]

source_suffix = {
    '.rst': 'restructuredtext',
    '.ipynb': 'myst-nb',
    '.md': 'myst-nb',
}
master_doc = "index"

autoclass_content = "class"
autodoc_member_order = "bysource"
default_role = "py:obj"

html_theme = "sphinx_book_theme"
html_theme_options = {
    "logo": {
        "image_light": "_static/image.png",
        "image_dark": "_static/image.png",
    },
    "repository_url": "https://github.com/aws/sagemaker-hyperpod-cli",
    "use_repository_button": True,
    "use_issues_button": True,
    "use_edit_page_button": True,
    "path_to_docs": "doc",
    "show_navbar_depth": 2,
}
htmlhelp_basename = "{}doc".format(project)

napoleon_use_rtype = False

# nbsphinx configuration
nbsphinx_allow_errors = True
nbsphinx_kernel_name = 'python3'

# MyST-NB configuration
myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_image",
    "html_admonition",
    # "linkify",  # Commented out until linkify-it-py is installed
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]
myst_heading_anchors = 3
nb_execution_mode = "off"

# Make version available to MyST templates
myst_substitutions = {
    "version": version,
}
