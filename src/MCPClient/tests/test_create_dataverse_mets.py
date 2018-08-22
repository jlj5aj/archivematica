#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from collections import namedtuple
import os
import sys
# import shutil

import pytest

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(
    os.path.abspath(os.path.join(THIS_DIR, '../lib/clientScripts')))

import convert_dataverse_structure

# List of dataverse metadata fixtures. We use a namedtuple to provide some
# structure to this index so that we can keep track of information regarding
# dataverse over time, e.g. dataverse version number, the date the dataset was
# created, and so forth.
DataverseMDIndex = namedtuple('DataverseMDIndex',
                              'dv_version created_date title url fname')

dv_1 = DataverseMDIndex("4.8.6",
                        "2016-03-10T14:55:44Z",
                        "Test Dataset",
                        "http://dx.doi.org/10.5072/FK2/XSAZXH",
                        "web_ui_demo.dataverse.org.doi.10.5072.1.json")

dv_2 = DataverseMDIndex("4.8.6",
                        "2018-05-16T17:54:01Z",
                        "Bala Parental Alienation Study: Canada, United "
                        "Kingdom, and Australia 1984-2012 [test]",
                        "https://doi.org/10.5072/FK2/UNMEZF",
                        "web_ui_demo.dataverse.org.doi.10.5072.2.json")

dv_3 = DataverseMDIndex("4.8.6",
                        "2018-05-09T21:26:07Z",
                        "A study with restricted data",
                        "https://doi.org/10.5072/FK2/WZTJWN",
                        "web_ui_demo.dataverse.org.doi.10.5072.3.json")

dv_4 = DataverseMDIndex("4.8.6",
                        "2018-05-09T20:33:36Z",
                        "A study of my afternoon drinks ",
                        "https://doi.org/10.5072/FK2/6PPJ6Y",
                        "api_demo.dataverse.org.doi.10.5072.4.json")


dv_5 = DataverseMDIndex("4.8.6",
                        "2018-08-24T14:15:00Z",
                        "Botanical Test",
                        "https://doi.org/10.5072/FK2/8KDUHM",
                        "api_demo.dataverse.org.doi.10.5072.5.json")

dv_6 = DataverseMDIndex("4.8.6",
                        "2018-08-24T14:15:00Z",
                        "Botanical Test",
                        "https://hdl.handle.net/10864/11651",
                        "api_demo.dataverse.org.doi.10.5072.6.json")


class TestDataverseExample(object):

    write_dir = "fixtures/dataverse/dataverse_sources/mets/"
    fixture_path = "fixtures/dataverse/dataverse_sources"

    THIS_DIR = os.path.dirname(os.path.abspath(__file__))
    FIXTURES_DIR = os.path.join(THIS_DIR, fixture_path)
    WRITE_DIR = os.path.join(THIS_DIR, write_dir)

    def setup_class(cls):
        try:
            os.makedirs(cls.WRITE_DIR)
        except OSError as e:
            print(
                "Creating fixture directory failed: {}".format(e),
                file=sys.stderr)

    def teardown_class(cls):
        # shutil.rmtree(cls.WRITE_DIR)
        return

    @pytest.mark.parametrize(
        "fixture_path, fixture_name, mets_output_path, mets_name",
        [(FIXTURES_DIR, dv_1.fname,
          WRITE_DIR, "METS.{}.xml".format(dv_1.fname)),
         (FIXTURES_DIR, dv_2.fname,
          WRITE_DIR, "METS.{}.xml".format(dv_2.fname)),
         (FIXTURES_DIR, dv_3.fname,
          WRITE_DIR, "METS.{}.xml".format(dv_3.fname)),
         (FIXTURES_DIR, dv_4.fname,
          WRITE_DIR, "METS.{}.xml".format(dv_4.fname)),
         (FIXTURES_DIR, dv_5.fname,
          WRITE_DIR, "METS.{}.xml".format(dv_5.fname)),
         (FIXTURES_DIR, dv_6.fname,
          WRITE_DIR, "METS.{}.xml".format(dv_6.fname)),
         ])
    def test_parse_dataverse(self,
                             fixture_path,
                             fixture_name,
                             mets_output_path,
                             mets_name):
        ret = convert_dataverse_structure.map_(
            unit_path=fixture_path, unit_uuid="", dataset_md_name=fixture_name,
            md_path=mets_output_path, md_name=mets_name)

        assert ret == 0, ("Creation of Dataverse METS failed with return "
                          "code {}".format(ret))
