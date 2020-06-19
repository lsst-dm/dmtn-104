# LSST Data Management System
# Copyright 2018 AURA/LSST.
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <http://www.lsstcorp.org/LegalNotices/>.

import os
import re
import pandoc


class Config:
    MD_COMP_URL = f"https://twcloud.lsst.org:8111/osmc/resources/{{res}}/elements/{{comp}}"
    PANDOC_TYPE = None
    DOC = pandoc.Document()
    OUTPUT_FORMAT = None
    CACHED_GIT_REPOS = {}
    # to store here git trees when MD Section is ongoing to avoid rate limit problem?
    CACHED_GIT_TREES = []
    MODE_PREFIX = None
    TIMEZONE = "US/Pacific"
    TEMPLATE_LANGUAGE = "latex"
    TEMPLATE_DIRECTORY = os.curdir

    # Regexes for LSST things
    DOC_NAMES = ['LDM', 'LSE', 'DMTN', 'DMTR', 'TSS', 'LPM']
    doc_pattern_text = r"\b(" + "|".join(DOC_NAMES) + r")(-\d+)([\s\.])"
    DOCUSHARE_DOC_PATTERN = re.compile(doc_pattern_text)
    milestone_pattern_text = r"\b(" + "|".join(DOC_NAMES) + r")(-\d+-\d+)([\s\.])"
    SUBSYSTEM_YML_FILE = "subsystem.yaml"
