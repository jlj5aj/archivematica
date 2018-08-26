#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import json
import os
import uuid

from lxml import etree

# databaseFunctions requires Django to be set up
import django
django.setup()

from custom_handlers import get_script_logger
import metsrw


logger = get_script_logger("archivematica.mcp.client.convert_dataverse_struct")


THIS_DIR = os.path.abspath(os.path.dirname(__file__))

# Mapping from originalFormatLabel in dataset.json to file extension. The
# values here are associated with Dataverse Bundles, created when Tabular data
# is ingested, see: http://guides.dataverse.org/en/latest/user/dataset-management.html?highlight=bundle
# The formats supported for tabluar data ingests are here:
# http://guides.dataverse.org/en/latest/user/tabulardataingest/supportedformats.html
EXTENSION_MAPPING = {
    "Comma Separated Values": ".csv",
    "MS Excel (XLSX)": ".xlsx",
    "R Data": ".RData",
    "SPSS Portable": ".por",
    "SPSS SAV": ".sav",
    "Stata Binary": ".dta",
    "Stata 13 Binary": ".dta",
    "UNKNOWN": "UNKNOWN",
}


def concurrent_instances(): return 1


def get_ddi_title_author(dataset_md_latest):
    title_text = author_text = None
    citation = dataset_md_latest.get("metadataBlocks", {}).get("citation")
    if citation:
        for field in citation.get("fields"):
            if field.get("typeName") == "title":
                title_text = field.get("value")
            if field.get("typeName") == "author":
                author_text = field.get("value")[0].get("authorName")\
                    .get("value")
        return title_text.strip(), author_text.strip()


def create_ddi(job, json_metadata):
    """
    Create the DDI dmdSec from JSON information. Returns Element.
    """
    dataset_md_latest = get_latest_version_metadata(json_metadata)
    try:
        title_text, author_text = get_ddi_title_author(dataset_md_latest)
    except TypeError as e:
        logger.error("Unable to gather citation data from dataset.json: %s", e)
        return

    agency = json_metadata.get("protocol")
    idno = json_metadata.get("persistentUrl")
    version_date = dataset_md_latest.get("releaseTime")
    version_type = dataset_md_latest.get("versionState")
    version_num = "{}.{}".format(
        dataset_md_latest.get("versionNumber"),
        dataset_md_latest.get("versionMinorNumber")
    )
    restriction_text = dataset_md_latest.get("termsOfUse")
    distributor_text = json_metadata.get("publisher")

    fields_log = (
        "Fields retrieved from Dataverse:\ntitle: {}\nauthor: {}\n"
        "agency: {}\nidno: {}\nversion_date: {}\nversion_type: {}\n"
        "version_num: {}\nrestriction_text: {}\ndistributor_text: {}\n"
        .format(
            title_text, author_text, agency, idno, version_date, version_type,
            version_num, restriction_text, distributor_text))

    job.pyprint(fields_log)

    # create XML
    nsmap = {"ddi": "http://www.icpsr.umich.edu/DDI"}
    ddins = "{" + nsmap["ddi"] + "}"
    ddi_root = etree.Element(ddins + "codebook", nsmap=nsmap)
    ddi_root.attrib["version"] = "2.5"

    root_ns = "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation"
    dv_ns = (
        "http://www.ddialliance.org/Specification/DDI-Codebook/2.5/"
        "XMLSchema/codebook.xsd"
    )
    ddi_root.attrib[root_ns] = dv_ns

    stdydscr = etree.SubElement(ddi_root, ddins + "stdyDscr", nsmap=nsmap)
    citation = etree.SubElement(stdydscr, ddins + "citation", nsmap=nsmap)

    titlstmt = etree.SubElement(citation, ddins + "titlStmt", nsmap=nsmap)
    etree.SubElement(titlstmt, ddins + "titl", nsmap=nsmap).text = title_text
    etree.SubElement(titlstmt, ddins + "IDNo", agency=agency).text = idno

    rspstmt = etree.SubElement(citation, ddins + "rspStmt")
    etree.SubElement(rspstmt, ddins + "AuthEnty").text = author_text

    diststmt = etree.SubElement(citation, ddins + "distStmt")
    etree.SubElement(diststmt, ddins + "distrbtr").text = distributor_text

    verstmt = etree.SubElement(citation, ddins + "verStmt")
    etree.SubElement(
        verstmt, ddins + "version", date=version_date, type=version_type
    ).text = version_num

    dataaccs = etree.SubElement(stdydscr, ddins + "dataAccs")
    usestmt = etree.SubElement(dataaccs, ddins + "useStmt")
    etree.SubElement(usestmt, ddins + "restrctn").text = restriction_text

    return ddi_root


def create_bundle(job, tabfile_json):
    """
    Creates and returns the metsrw entries for a tabfile's bundle
    """
    # Base name is .tab with suffix stripped
    tabfile_name = tabfile_json.get("label")
    if tabfile_name is not None:
        job.pyprint("Creating entries for tabfile bundle {}"
                    .format(tabfile_name))
        base_name = tabfile_name[:-4]
        bundle = metsrw.FSEntry(path=base_name, type="Directory")
        # Find the original file and add it to the METS FS Entries.
        tabfile_datafile = tabfile_json.get("dataFile")
        fname = None
        ext = EXTENSION_MAPPING.get(
            tabfile_datafile.get("originalFormatLabel", ""), "UNKNOWN")
        logger.info("Retrieved extension mapping value: %s", ext)
        logger.info(
            "Original file format listed as %s", tabfile_datafile.get("originalFileFormat", "None"))
        if ext == "UNKNOWN":
            fname = tabfile_datafile.get("filename")
            logger.info(
                "Original Format Label is UNKNOWN, using filename: %s",
                fname)
        if fname is None:
            fname = "{}{}".format(base_name, ext)
        original_file = metsrw.FSEntry(
            path="{}/{}".format(base_name, fname),
            use="original",
            file_uuid=str(uuid.uuid4()),
            checksumtype="MD5",
            checksum=tabfile_datafile["md5"],
        )
        bundle.add_child(original_file)
        if tabfile_datafile["originalFormatLabel"] != "R Data":
            # RData derivative
            f = metsrw.FSEntry(
                path=base_name + "/" + base_name + ".RData",
                use="derivative",
                derived_from=original_file,
                file_uuid=str(uuid.uuid4()),
            )
            bundle.add_child(f)

        # Add expected bundle contents
        # FIXME what is the actual path for the files?
        # Tabfile
        f = metsrw.FSEntry(
            path=base_name + "/" + tabfile_datafile["filename"],
            use="derivative",
            derived_from=original_file,
            file_uuid=str(uuid.uuid4()),
        )
        f.add_dmdsec(
            md=base_name + "/" + base_name + "-ddi.xml",
            mdtype="DDI",
            mode="mdref",
            label=base_name + "-ddi.xml",
            loctype="OTHER",
            otherloctype="SYSTEM",
        )
        bundle.add_child(f)
        # -ddi.xml
        f = metsrw.FSEntry(
            path=base_name + "/" + base_name + "-ddi.xml",
            use="metadata",
            derived_from=original_file,
            file_uuid=str(uuid.uuid4()),
        )
        bundle.add_child(f)
        # citation - endnote
        f = metsrw.FSEntry(
            path=base_name + "/" + base_name + "citation-endnote.xml",
            use="metadata",
            derived_from=original_file,
            file_uuid=str(uuid.uuid4()),
        )
        bundle.add_child(f)
        # citation - ris
        f = metsrw.FSEntry(
            path=base_name + "/" + base_name + "citation-ris.ris",
            use="metadata",
            derived_from=original_file,
            file_uuid=str(uuid.uuid4()),
        )
        bundle.add_child(f)
        return bundle


def test_if_zip_in_name(fname):
    """Check if a filepath ends in a .zip extension. If so, return true."""
    ext_ = os.path.splitext(fname)[1]
    if ext_.lower() == '.zip':
        return True
    return False


def map_(job, unit_path, unit_uuid, dataset_md_name="dataset.json",
         md_path=None, md_name=None):
    """Docstring..."""
    logger.info(
        "Convert Dataverse structure called with '%s' unit directory and "
        "'%s' unit uuid", unit_path, unit_uuid)

    # Read JSON
    json_path = os.path.join(unit_path, "metadata", dataset_md_name)
    logger.info("Metadata directory exists %s", os.path.exists(json_path))
    with open(json_path, "r") as f:
        json_metadata = json.load(f)

    # Parse DDI into XML
    ddi_root = create_ddi(job, json_metadata)

    latest_version_md = get_latest_version_metadata(json_metadata)

    # Create METS
    sip = metsrw.FSEntry(
        path="None", label=get_ddi_title_author(latest_version_md)[0],
        use=None, type="Directory"
    )
    sip.add_dmdsec(md=ddi_root, mdtype="DDI")
    sip.add_dmdsec(
        md="dataset.json",
        mdtype="OTHER",
        mode="mdref",
        label="dataset.json",
        loctype="OTHER",
        otherloctype="SYSTEM",
    )

    # Add original files to the METS document.
    files = {}
    latest_version = latest_version_md
    files = latest_version_md.get('files')

    if not files:
        return 1

    # If a dataset is restricted we may not have access to all the files. We
    # may also want to flag this dataset to the users of this service. We
    # can do this here and below. Ultimately returning 'Fail' from this
    # microservice.
    restricted_access = False
    contact_information = latest_version.get("termsOfAccess")
    if contact_information == "Please contact owner for access":
        restricted_access = True

    # Signal to users the existence of zip files in this transfer.
    zipped_file = False

    # Signal to users that this transfer might consist of metadata only.
    if len(files) is 0:
        logger.info(
            "Metadata only transfer? There are no file entries in this "
            "transfer's metadata.")

    for file_json in files:
        is_restricted = file_json.get("restricted")
        if is_restricted is True and restricted_access:
            logger.error(
                "Restricted dataset cannot be transferred: %s",
                contact_information)
            return 1
        if file_json["dataFile"]["filename"].endswith(".tab"):
            # A Tabular Data File from Dataverse will consist of an original
            # tabular format submitted by the researcher plus multiple
            # different representations. We need to map that here.
            bundle = create_bundle(job, file_json)
            if bundle:
                sip.add_child(bundle)
            else:
                logger.error(
                    "Create Dataverse transfer METS failed. "
                    "Bundle returned: %s", bundle)
                return 1
        else:
            path_ = None
            datafile = file_json.get("dataFile")
            if datafile:
                path_ = datafile.get("filename")
            if path_:
                if test_if_zip_in_name(path_):
                    # provide some additional logging around the contents of the
                    # dataset we're processing.
                    if not zipped_file:
                        zipped_file = True
                        logger.info(
                            "Non-bundle .zip file found in the dataset.")
                f = metsrw.FSEntry(
                    path=path_,
                    use="original",
                    file_uuid=str(uuid.uuid4()),
                    checksumtype="MD5",
                    checksum=file_json["dataFile"]["md5"],
                )
                sip.add_child(f)
            else:
                logger.error(
                    "Problem retrieving filename from metadata, returned "
                    "datafile: %s, path: %s", datafile, path_)

    # Add metadata directory
    md_dir = metsrw.FSEntry(path="metadata", use=None, type="Directory")
    sip.add_child(md_dir)
    # Add dataset.json
    f = metsrw.FSEntry(
        path="metadata/dataset.json", use="metadata",
        file_uuid=str(uuid.uuid4())
    )
    # Add to metadata dir
    md_dir.add_child(f)

    # Write METS
    metadata_path = md_path
    if metadata_path is None:
        metadata_path = os.path.join(unit_path, "metadata")
    if not os.path.exists(metadata_path):
        os.makedirs(metadata_path)

    metadata_name = md_name
    if metadata_name is None:
        metadata_name = "METS.xml"
    mets_path = os.path.join(metadata_path, metadata_name)
    mets_f = metsrw.METSDocument()
    mets_f.append_file(sip)
    logger.debug(mets_f.tostring(fully_qualified=True).decode('ascii'))
    mets_f.write(mets_path, pretty_print=True, fully_qualified=True)
    return 0


def get_latest_version_metadata(json_metadata):
    """If the datatset has been downloaded from the Dataverse web ui then there
    is a slightly different structure. While the structure is different, the
    majority of fields should remain the same and work with Archivematica. Just
    in case, we log the version here and inform the user of potential
    compatibility issues.

    Ref: https://github.com/IQSS/dataverse/issues/4715
    """
    datasetVersion = json_metadata.get("datasetVersion")
    if datasetVersion:
        logger.info(
            "Dataset seems to have been downloaded from the Dataverse Web UI."
            "Some features of this method may be incompatible with "
            "Archivematica at present.")
        return datasetVersion
    else:
        return json_metadata.get("latestVersion")


def map_dataverse(job):
    """Extract the arguments provided to the script and call the primary
    function concerned with converting the Dataverse metadata JSON.
    """
    try:
        transfer_dir = job.args[1]
        transfer_uuid = job.args[2]
        logger.info("Convert Dataverse Structure with dir args: '%s' "
                    "and transfer uuid: %s", transfer_dir, transfer_uuid)
        return map_(job, unit_path=transfer_dir, unit_uuid=transfer_uuid)
    except IndexError:
        logger.error(
            "Problem with the supplied arguments to the function "
            "len: %s", len(job.args))
        return 1


def call(jobs):
    for job in jobs:
        with job.JobContext(logger=logger):
            job.set_status(map_dataverse(job))