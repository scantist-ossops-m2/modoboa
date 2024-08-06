# Development settings

from __future__ import unicode_literals

import os

BOWER_COMPONENTS_ROOT = os.path.join(
    os.path.dirname(__file__), ".."
)

BOWER_INSTALLED_APPS = (
    "jquery#1.9",
    "jquery-ui#1.11",
    "bootstrap#3.3.5",
    "d3#3.5.0",
    "eonasdan-bootstrap-datetimepicker#3.1.3",
    "font-awesome#4.7.0",
    "c3#0.4.10",
    "selectize#0.12.4",
)
