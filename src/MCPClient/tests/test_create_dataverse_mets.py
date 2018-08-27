#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from collections import namedtuple
import os
import sys
import xml.etree.ElementTree as et

import pytest
import shutil

from job import Job
import metsrw

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(
    os.path.abspath(os.path.join(THIS_DIR, '../lib/clientScripts')))

import convert_dataverse_structure

# List of dataverse metadata fixtures. We use a namedtuple to provide some
# structure to this index so that we can keep track of information regarding
# dataverse over time, e.g. dataverse version number, the dataset uri and so
# forth.
DataverseMDIndex = namedtuple('DataverseMDIndex',
                              'dv_version url fname')

dv_1 = DataverseMDIndex("4.8.6",
                        "http://dx.doi.org/10.5072/FK2/XSAZXH",
                        "web_ui_demo.dataverse.org.doi.10.5072.1.json")
dv_2 = DataverseMDIndex("4.8.6",
                        "https://doi.org/10.5072/FK2/UNMEZF",
                        "web_ui_demo.dataverse.org.doi.10.5072.2.json")
dv_3 = DataverseMDIndex("4.8.6",
                        "https://doi.org/10.5072/FK2/WZTJWN",
                        "web_ui_demo.dataverse.org.doi.10.5072.3.json")
dv_4 = DataverseMDIndex("4.8.6",
                        "https://doi.org/10.5072/FK2/6PPJ6Y",
                        "api_demo.dataverse.org.doi.10.5072.4.json")
dv_5 = DataverseMDIndex("4.8.6",
                        "https://doi.org/10.5072/FK2/8KDUHM",
                        "api_demo.dataverse.org.doi.10.5072.5.json")
dv_6 = DataverseMDIndex("4.8.6",
                        "https://hdl.handle.net/10864/11651",
                        "api_demo.dataverse.org.doi.10.5072.6.json")
dv_7 = DataverseMDIndex("4.8.6",
                        "https://doi.org/10.5072/FK2/6PPJ6Y",
                        "api_demo.dataverse.org.doi.10.5072.7.json")
dv_8 = DataverseMDIndex("4.8.6",
                        "http://dx.doi.org/10.5072/FK2/NNTESQ",
                        "api_demo.dataverse.org.doi.10.5072.8.json")


class TestDataverseExample(object):

    write_dir = "fixtures/dataverse/dataverse_sources/dataverse_mets/"
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
        shutil.rmtree(cls.WRITE_DIR)

    @pytest.mark.parametrize(
        "fixture_path, fixture_name, mets_output_path, mets_name",
        [(FIXTURES_DIR, dv_1.fname,
          WRITE_DIR, "METS.{}.dataverse.xml".format(dv_1.fname)),
         (FIXTURES_DIR, dv_2.fname,
          WRITE_DIR, "METS.{}.dataverse.xml".format(dv_2.fname)),
         (FIXTURES_DIR, dv_3.fname,
          WRITE_DIR, "METS.{}.dataverse.xml".format(dv_3.fname)),
         (FIXTURES_DIR, dv_4.fname,
          WRITE_DIR, "METS.{}.dataverse.xml".format(dv_4.fname)),
         (FIXTURES_DIR, dv_5.fname,
          WRITE_DIR, "METS.{}.dataverse.xml".format(dv_5.fname)),
         (FIXTURES_DIR, dv_6.fname,
          WRITE_DIR, "METS.{}.dataverse.xml".format(dv_6.fname)),
         (FIXTURES_DIR, dv_7.fname,
          WRITE_DIR, "METS.{}.dataverse.xml".format(dv_7.fname)),
         (FIXTURES_DIR, dv_8.fname,
          WRITE_DIR, "METS.{}.dataverse.xml".format(dv_8.fname)),
         ])
    def test_parse_dataverse(self,
                             fixture_path,
                             fixture_name,
                             mets_output_path,
                             mets_name):
        """Integration tests to determine that the primary conversion function
        does not output a non-zero status.
        """
        job = Job("stub", "stub", ["", ""])
        ret = convert_dataverse_structure.map_(
            job=job, unit_path=fixture_path, unit_uuid="",
            dataset_md_name=fixture_name, output_md_path=mets_output_path,
            output_md_name=mets_name)

        assert ret == 0, ("Creation of Dataverse METS failed with return "
                          "code {}".format(ret))

    @pytest.mark.parametrize(
        "mets_output_path, mets_name, all_file_count, dir_count, item_count",
        [(WRITE_DIR, "METS.{}.dataverse.xml".format(dv_1.fname), 13, 3, 10),
         (WRITE_DIR, "METS.{}.dataverse.xml".format(dv_2.fname), 43, 6, 37),
         (WRITE_DIR, "METS.{}.dataverse.xml".format(dv_3.fname), 5, 2, 3),
         (WRITE_DIR, "METS.{}.dataverse.xml".format(dv_4.fname), 10, 3, 7),
         (WRITE_DIR, "METS.{}.dataverse.xml".format(dv_5.fname), 11, 2, 9),
         (WRITE_DIR, "METS.{}.dataverse.xml".format(dv_6.fname), 18, 3, 15),
         (WRITE_DIR, "METS.{}.dataverse.xml".format(dv_7.fname), 10, 3, 7),
         (WRITE_DIR, "METS.{}.dataverse.xml".format(dv_8.fname), 10, 3, 7),
         ])
    def test_generated_mets(self,
                            mets_output_path,
                            mets_name,
                            all_file_count,
                            dir_count,
                            item_count):
        """Understand whether all the file and directory elements appear in the
        METS as anticipated. A high-level test to quickly understand if
        something has gone wrong while refactoring.
        """
        mets_path = os.path.join(mets_output_path, mets_name)
        if not os.path.isfile(mets_path):
            pytest.fail("Fixtures were not previously setup correctly.")

        try:
            mets = metsrw.METSDocument.fromfile(mets_path)
        except mets.MetsError:
            pytest.fail("Could not parse mets %s", mets_path)

        assert len(mets.all_files()) == all_file_count

        dir_counter = 0
        item_counter = 0
        for file_ in mets.all_files():
            if file_.type == "Directory":
                dir_counter += 1
            if file_.type == "Item":
                item_counter += 1

        assert dir_counter == dir_count, ("Directory count incorrect: '%s', "
                                          "expected: '%s'"
                                          .format(dir_counter, dir_count))
        assert item_counter == item_count, ("Item count incorrect: '%s', "
                                            "expected: '%s'"
                                            .format(item_counter, item_count))

    @pytest.mark.parametrize(
        "dataset_name, mets_output_path, mets_name, ddi_title, pid_type, "
        "pid_value, ddi_count",
        [(dv_1.fname, WRITE_DIR, "METS.{}.dataverse.xml".format(dv_1.fname),
            "Test Dataset", "doi",
            "http://dx.doi.org/10.5072/FK2/XSAZXH", 1),
         (dv_2.fname, WRITE_DIR, "METS.{}.dataverse.xml".format(dv_2.fname),
            "Bala Parental Alienation Study: Canada, United Kingdom, and "
            "Australia 1984-2012 [test]", "doi",
            "https://doi.org/10.5072/FK2/UNMEZF", 5),
         (dv_3.fname, WRITE_DIR, "METS.{}.dataverse.xml".format(dv_3.fname),
            "A study with restricted data", "doi",
            "https://doi.org/10.5072/FK2/WZTJWN", 1),
         (dv_4.fname, WRITE_DIR, "METS.{}.dataverse.xml".format(dv_4.fname),
            "A study of my afternoon drinks", "doi",
            "https://doi.org/10.5072/FK2/6PPJ6Y", 2),
         (dv_5.fname, WRITE_DIR, "METS.{}.dataverse.xml".format(dv_5.fname),
            "Botanical Test", "doi", "https://doi.org/10.5072/FK2/8KDUHM", 1),
         (dv_6.fname, WRITE_DIR, "METS.{}.dataverse.xml".format(dv_6.fname),
            "Research Data Management (RDM) Survey of Queen's University's "
            "Engineering and Science Departments", "hdl",
            "https://hdl.handle.net/10864/11651", 2),
         (dv_7.fname, WRITE_DIR, "METS.{}.dataverse.xml".format(dv_7.fname),
            "A study of my afternoon drinks", "doi",
            "https://doi.org/10.5072/FK2/6PPJ6Y", 2),
         (dv_8.fname, WRITE_DIR, "METS.{}.dataverse.xml".format(dv_8.fname),
            "Depress", "doi",
            "https://doi.org/10.5072/FK2/NNTESQ", 2),
         ])
    def test_mets_content(self,
                          dataset_name,
                          mets_output_path,
                          mets_name,
                          ddi_title,
                          pid_type,
                          pid_value,
                          ddi_count):
        """Cherry-pick certain important elements in the content of the
        dataverse METS that needs to be consistently output by the convert
        dataverse mets script.
        """
        mets_path = os.path.join(mets_output_path, mets_name)
        if not os.path.isfile(mets_path):
            pytest.fail("Fixtures were not previously setup correctly.")

        try:
            mets = metsrw.METSDocument.fromfile(mets_path)
        except mets.MetsError:
            pytest.fail("Could not parse mets %s", mets_path)

        mets_root = et.fromstring(mets.tostring())

        # Setup namespaces to search for in the document.
        ns = {'ddi': 'http://www.icpsr.umich.edu/DDI'}

        # Test for a single instance of the ddi codebook.
        codebook = mets_root.findall('.//ddi:codebook', ns)
        assert len(codebook) == 1, ("Incorrect number of codebook entries "
                                    "discovered: '%s' expected 1."
                                    .format(len(codebook)))

        # Test that we have a single title instance and the title matches what
        # is expected.
        title = mets_root.findall('.//ddi:titl', ns)
        assert len(title) == 1
        assert title[0].text == ddi_title, ("DDI title: %s is not what was "
                                            "expected: %s"
                                            .format(title[0].text, ddi_title))

        # Test that we have a single PID and that it matches what is expected.
        pid = mets_root.findall('.//ddi:IDNo', ns)
        assert len(pid) == 1
        # Agency is synonymous with Type in our use of the PID Agency value.
        # N.B. The agency providing the persistent identifier.
        pid_agency = pid[0].get("agency")
        assert pid_agency == pid_type, ("PID type: %s is not what was "
                                        "expected: %s"
                                        .format(pid_agency, pid_type))
        assert pid[0].text == pid_value, ("PID value: %s is not what was "
                                          "expected: %s"
                                          .format(pid[0].text, pid_value))

        # Title is used in three other locations in the METS. Make sure that
        # they are found as well.
        for map_ in mets_root.findall("{http://www.loc.gov/METS/}structMap"):
            for entry in map_:
                if entry.get("Type") == "Directory" and \
                        entry.get("DMDID") is not None:
                    assert entry.get("LABEL") == ddi_title, \
                        ("Title not found in METS struct maps where expected")

        # Finally, the metadata should contain two mdrefs at this point. Look
        # for them here.
        refs = mets_root.findall('.//{http://www.loc.gov/METS/}mdRef')
        assert len(refs) > 0 and len(refs) <= ddi_count

        # Assert that at least one mdref points to our dataset.json file and
        # that if we find any other mdrefs that they point to ddi files.
        dataset_json = False
        for ref in refs:
            if ref.get("LABEL") == dataset_name:
                dataset_json = True
            elif ref.get("MDTYPE") != "DDI":
                pytest.fail("Unexpected MDREF found in metadata: {}"
                            .format(ref.get("LABEL")))
        assert dataset_json is True
