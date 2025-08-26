# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
"""Sphinx configuration."""

import datetime
import os
import shutil
import sys
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, ClassVar

# Mock kubernetes.config before adding source path to prevent import errors
from unittest.mock import MagicMock
import types
kubernetes_config = types.ModuleType('kubernetes.config')
kubernetes_config.KUBE_CONFIG_DEFAULT_LOCATION = "~/.kube/config"
sys.modules['kubernetes.config'] = kubernetes_config

# Add the source directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


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
    "sphinx_copybutton",
    "sphinx.ext.autosummary",
    "sphinx.ext.autosectionlabel",
    "sphinx_design",
    "sphinx_click"
]


autodoc_mock_imports = ["pyspark", "feature_store_pyspark", "py4j", "boto3", "botocore", "kubernetes", "yaml", "sagemaker_core"]

source_suffix = {
    '.rst': 'restructuredtext',
    '.ipynb': 'myst-nb',
    '.md': 'myst-nb',
}

autoclass_content = "class"
autodoc_class_signature = "mixed"
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "private-members": False,
    "special-members": False,
    "show-inheritance": False,
}

# Don't document class attributes automatically
autodoc_typehints_format = "short"
autodoc_preserve_defaults = True
autodoc_member_order = "bysource"
default_role = "py:obj"

html_theme = "sphinx_book_theme"
html_theme_options = {
    "logo": {
        "text": "SageMaker HyperPod<br>CLI and SDK",
        "image_light": "_static/image.png",
        "image_dark": "_static/image.png",
    },
    "repository_url": "https://github.com/aws/sagemaker-hyperpod-cli",
    "use_repository_button": True,
    "use_issues_button": True,
    "use_edit_page_button": True,
    "path_to_docs": "doc",
    "show_navbar_depth": 2,
    "use_fullscreen_button": False,
    "use_download_button": False,
    "home_page_in_toc": True,
    "secondary_sidebar_items": ["edit-this-page", "page-toc"],
    "toc_title": "Table of contents",
    "show_toc_level": 3,   
}

author = "Amazon Web Services"
copyright = f"{datetime.datetime.now().year}, Amazon Web Services"

htmlhelp_basename = "{}doc".format(project)
html_static_path = ["_static"]
html_css_files = ["custom.css",
                  "search_accessories.css",
                  ]
napoleon_use_rtype = False
napoleon_use_param = False
napoleon_include_init_with_doc = False
napoleon_use_ivar = True
napoleon_parameter_style = "table"
napoleon_type_aliases = None
napoleon_custom_sections = [('Parameters', 'params_style')]

viewcode_line_numbers = True

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
    "attrs_inline",
]
myst_heading_anchors = 3
nb_execution_mode = "off"

# Make version available to MyST templates
myst_substitutions = {
    "version": version,
}

# Automatically extract typehints when specified and place them in
# descriptions of the relevant function/method.
autodoc_typehints = "signature"

# Clean documentation without Pydantic boilerplate
# Hide constructor signature and parameters
autodoc_class_signature = "separated"
autodoc_member_order = "bysource"

def setup(app):
    pass


# autosummary
autosummary_generate = True
autosummary_ignore_module_all = False

# autosectionlabel
autosectionlabel_prefix_document = True