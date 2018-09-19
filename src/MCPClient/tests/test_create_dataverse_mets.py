#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from collections import namedtuple
import os
import sys

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
                              'dv_version, ddi_title, pid_value, pid_type, '
                              'fname, all_file_count, dir_count, item_count, '
                              'ddi_count')

dv_1 = DataverseMDIndex("4.8.6",
                        "Test Dataset",
                        "http://dx.doi.org/10.5072/FK2/XSAZXH",
                        "doi",
                        "web_ui_demo.dataverse.org.doi.10.5072.1.json",
                        13, 3, 10, 1)
dv_2 = DataverseMDIndex("4.8.6",
                        "Bala Parental Alienation Study: Canada, United "
                        "Kingdom, and Australia 1984-2012 [test]",
                        "https://doi.org/10.5072/FK2/UNMEZF",
                        "doi",
                        "web_ui_demo.dataverse.org.doi.10.5072.2.json",
                        43, 6, 37, 5)
dv_3 = DataverseMDIndex("4.8.6",
                        "A study with restricted data",
                        "https://doi.org/10.5072/FK2/WZTJWN",
                        "doi",
                        "web_ui_demo.dataverse.org.doi.10.5072.3.json",
                        5, 2, 3, 1)
dv_4 = DataverseMDIndex("4.8.6",
                        "A study of my afternoon drinks",
                        "https://doi.org/10.5072/FK2/6PPJ6Y",
                        "doi",
                        "api_demo.dataverse.org.doi.10.5072.4.json",
                        10, 3, 7, 2)
dv_5 = DataverseMDIndex("4.8.6",
                        "Botanical Test",
                        "https://doi.org/10.5072/FK2/8KDUHM",
                        "doi",
                        "api_demo.dataverse.org.doi.10.5072.5.json",
                        11, 2, 9, 1)
dv_6 = DataverseMDIndex("4.8.6",
                        "Research Data Management (RDM) Survey of Queen's "
                        "University's Engineering and Science Departments",
                        "https://hdl.handle.net/10864/11651",
                        "hdl",
                        "api_demo.dataverse.org.doi.10.5072.6.json",
                        18, 3, 15, 2)
dv_7 = DataverseMDIndex("4.8.6",
                        "A study of my afternoon drinks",
                        "https://doi.org/10.5072/FK2/6PPJ6Y",
                        "doi",
                        "api_demo.dataverse.org.doi.10.5072.7.json",
                        10, 3, 7, 2)
dv_8 = DataverseMDIndex("4.8.6",
                        "Depress",
                        "https://doi.org/10.5072/FK2/NNTESQ",
                        "doi",
                        "api_demo.dataverse.org.doi.10.5072.8.json",
                        10, 3, 7, 2)


class TestDataverseExample(object):

    write_dir = "fixtures/dataverse/dataverse_sources/dataverse_mets/"
    fixture_path = "fixtures/dataverse/dataverse_sources"

    THIS_DIR = os.path.dirname(os.path.abspath(__file__))
    FIXTURES_DIR = os.path.join(THIS_DIR, fixture_path)
    WRITE_DIR = os.path.join(THIS_DIR, write_dir)

    mets_file_name = "METS.{}.dataverse.xml"

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
        "fixture", [dv_1, dv_2, dv_3, dv_4, dv_5, dv_6, dv_7, dv_8])
    def test_generated_mets_(self, fixture):
        """Understand whether all the file and directory elements appear in the
        METS as anticipated. A high-level test to quickly understand if
        something has gone wrong while refactoring.
        """
        job = Job("stub", "stub", ["", ""])
        ret = convert_dataverse_structure.convert_dataverse_to_mets(
            job=job, unit_path=self.FIXTURES_DIR,
            dataset_md_name=fixture.fname, output_md_path=self.WRITE_DIR,
            output_md_name=self.mets_file_name.format(fixture.fname))
        assert ret is None, ("Creation of Dataverse METS failed with return "
                             "code {}".format(ret))

        mets_path = os.path.join(
            self.WRITE_DIR, self.mets_file_name.format(fixture.fname))
        if not os.path.isfile(mets_path):
            pytest.fail("Fixtures were not previously setup correctly.")

        try:
            mets = metsrw.METSDocument.fromfile(mets_path)
        except mets.MetsError:
            pytest.fail("Could not parse mets %s", mets_path)

        assert len(mets.all_files()) == \
            fixture.all_file_count, (
                "File count incorrect: '{}', expected '{}'"
                .format(len(mets.all_files()), fixture.all_file_count))

        dir_counter = 0
        item_counter = 0
        for file_ in mets.all_files():
            if file_.type == "Directory":
                dir_counter += 1
            if file_.type == "Item":
                item_counter += 1

        assert dir_counter == \
            fixture.dir_count, (
                "Directory count incorrect: '{}', expected: '{}'"
                .format(dir_counter, fixture.dir_count))
        assert item_counter == \
            fixture.item_count, (
                "Item count incorrect: '{}', expected: '{}'"
                .format(item_counter, fixture.item_count))

    @pytest.mark.parametrize(
        "fixture", [dv_1, dv_2, dv_3, dv_4, dv_5, dv_6, dv_7, dv_8])
    def test_mets_content(self, fixture):
        """Cherry-pick certain important elements in the content of the
        Dataverse METS that needs to be consistently output by the convert
        Dataverse METS script.
        """
        mets_path = os.path.join(
            self.WRITE_DIR, self.mets_file_name.format(fixture.fname))
        if not os.path.isfile(mets_path):
            pytest.fail("Fixtures were not previously setup correctly.")

        try:
            mets = metsrw.METSDocument.fromfile(mets_path)
        except mets.MetsError:
            pytest.fail("Could not parse mets %s", mets_path)

        mets_root = mets.serialize()

        # Setup namespaces to search for in the document.
        ns = {'ddi': 'http://www.icpsr.umich.edu/DDI'}

        # Test for a single instance of the ddi codebook.
        codebook = mets_root.findall('.//ddi:codebook', ns)
        assert len(codebook) == 1, ("Incorrect number of codebook entries "
                                    "discovered: '{}' expected 1."
                                    .format(len(codebook)))

        # Test that we have a single title instance and the title matches what
        # is expected.
        title = mets_root.findall('.//ddi:titl', ns)
        assert len(title) == 1
        assert title[0].text == \
            fixture.ddi_title, (
                "DDI title: '{}' is not what was expected: '{}'"
                .format(title[0].text, fixture.ddi_title))

        # Test that we have a single PID and that it matches what is expected.
        pid = mets_root.findall('.//ddi:IDNo', ns)
        assert len(pid) == 1
        # Agency is synonymous with Type in our use of the PID Agency value.
        # N.B. The agency providing the persistent identifier.
        pid_agency = pid[0].get("agency")
        assert pid_agency == \
            fixture.pid_type, ("PID type: '{}'' is not what was expected: '{}'"
                               .format(pid_agency, fixture.pid_type))
        assert pid[0].text == \
            fixture.pid_value, ("PID value: '{}' is not what was expected: '{}"
                                .format(pid[0].text, fixture.pid_value))

        # Title is used in three other locations in the METS. Make sure that
        # they are found as well.
        for map_ in mets_root.findall("{http://www.loc.gov/METS/}structMap"):
            for entry in map_:
                if entry.get("Type") == "Directory" and \
                        entry.get("DMDID") is not None:
                    assert entry.get("LABEL") == fixture.ddi_title, \
                        ("Title not found in METS struct maps where expected")

        # Test that the MDRef count is what is expected.
        refs = mets_root.findall('.//{http://www.loc.gov/METS/}mdRef')
        assert fixture.ddi_count >= len(refs) > 0

        # Assert that at least one mdref points to our dataset.json file and
        # that if we find any other mdrefs that they point to ddi files.
        dataset_json = False
        for ref in refs:
            if ref.get("LABEL") == fixture.fname:
                dataset_json = True
            elif ref.get("MDTYPE") != "DDI":
                pytest.fail("Unexpected MDREF found in metadata: {}"
                            .format(ref.get("LABEL")))
        assert dataset_json is True
