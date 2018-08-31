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


def get_ddi_title_author(dataset_md_latest):
    """Retrieve the title and the author of the dataset for the DDI XML
    snippet to be included in the METS file.
    """
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
    """Create the DDI dmdSec from the JSON metadata."""
    dataset_md_latest = get_latest_version_metadata(json_metadata)

    ddi_elems = {
        "Title": "",
        "Author": "",
        "PID Type": "",
        "IDNO": "",
        "Version Date": "",
        "Version Type": "",
        "Version Number": "",
        "Restriction Text": "",
        "Distributor Text": ""}

    try:
        ddi_elems["Title"], \
            ddi_elems["Author"] = get_ddi_title_author(dataset_md_latest)
    except TypeError as e:
        logger.error("Unable to gather citation data from dataset.json: %s", e)
        return None

    ddi_elems["PID Type"] = json_metadata.get("protocol", "")
    ddi_elems["IDNO"] = json_metadata.get("persistentUrl", "")
    ddi_elems["Version Date"] = dataset_md_latest.get("releaseTime", "")
    ddi_elems["Version Type"] = dataset_md_latest.get("versionState", "")
    ddi_elems["Version Number"] = "{}.{}".format(
        dataset_md_latest.get("versionNumber", ""),
        dataset_md_latest.get("versionMinorNumber", "")
    )
    ddi_elems["Restriction Text"] = dataset_md_latest.get("termsOfUse", "")
    ddi_elems["Distributor Text"] = json_metadata.get("publisher", "")

    draft = False
    job.pyprint("Fields retrieved from Dataverse:")
    for ddi_k, ddi_v in ddi_elems.iteritems():
        if ddi_k == "Version Type" and ddi_v == "DRAFT":
            draft = True
        job.pyprint("{}: {}".format(ddi_k, ddi_v))

    if draft:
        job.pyprint(
            "Dataset is in a DRAFT state and may not transfer correctly")
        logger.error(
            "Dataset is in a DRAFT state and may not transfer correctly")

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
    etree.SubElement(titlstmt, ddins + "titl", nsmap=nsmap).text \
        = ddi_elems["Title"]

    etree.SubElement(
        titlstmt, ddins + "IDNo", agency=ddi_elems["PID Type"]).text \
        = ddi_elems["IDNO"]

    rspstmt = etree.SubElement(citation, ddins + "rspStmt")
    etree.SubElement(rspstmt, ddins + "AuthEnty").text \
        = ddi_elems["Author"]

    diststmt = etree.SubElement(citation, ddins + "distStmt")
    etree.SubElement(diststmt, ddins + "distrbtr").text \
        = ddi_elems["Distributor Text"]

    verstmt = etree.SubElement(citation, ddins + "verStmt")
    etree.SubElement(
        verstmt, ddins + "version", date=ddi_elems["Version Date"],
        type=ddi_elems["Version Type"]
    ).text = ddi_elems["Version Number"]

    dataaccs = etree.SubElement(stdydscr, ddins + "dataAccs")
    usestmt = etree.SubElement(dataaccs, ddins + "useStmt")
    etree.SubElement(usestmt, ddins + "restrctn").text \
        = ddi_elems["Restriction Text"]

    return ddi_root


def display_checksum_for_user(job, checksum_value, checksum_type="MD5"):
    """Provide some feedback to the user that enables them to understand what
    this script is doing in the Dataverse workflow.
    """
    job.pyprint(
        "Checksum retrieved from dataset.json: {} ({})"
        .format(checksum_value, checksum_type))


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
        checksum_value = tabfile_datafile.get("md5")
        if checksum_value is None:
            return None
        display_checksum_for_user(job, checksum_value)
        original_file = metsrw.FSEntry(
            path="{}/{}".format(base_name, fname),
            use="original",
            file_uuid=str(uuid.uuid4()),
            checksumtype="MD5",
            checksum=checksum_value,
        )
        bundle.add_child(original_file)
        if tabfile_datafile.get("originalFormatLabel") != "R Data":
            # RData derivative
            f = metsrw.FSEntry(
                path="{}/{}.RData".format(base_name, base_name),
                use="derivative",
                derived_from=original_file,
                file_uuid=str(uuid.uuid4()),
            )
            bundle.add_child(f)

        # Add expected bundle contents
        # FIXME what is the actual path for the files?
        # Tabfile
        f = metsrw.FSEntry(
            path="{}/{}".format(base_name, tabfile_datafile.get("filename")),
            use="derivative",
            derived_from=original_file,
            file_uuid=str(uuid.uuid4()),
        )
        f.add_dmdsec(
            md="{}/{}-ddi.xml".format(base_name, base_name),
            mdtype="DDI",
            mode="mdref",
            label="{}-ddi.xml".format(base_name),
            loctype="OTHER",
            otherloctype="SYSTEM",
        )
        bundle.add_child(f)
        # -ddi.xml
        f = metsrw.FSEntry(
            path="{}/{}-ddi.xml".format(base_name, base_name),
            use="metadata",
            derived_from=original_file,
            file_uuid=str(uuid.uuid4()),
        )
        bundle.add_child(f)
        # citation - endnote
        f = metsrw.FSEntry(
            path="{}/{}citation-endnote.xml".format(base_name, base_name),
            use="metadata",
            derived_from=original_file,
            file_uuid=str(uuid.uuid4()),
        )
        bundle.add_child(f)
        # citation - ris
        f = metsrw.FSEntry(
            path="{}/{}citation-ris.ris".format(base_name, base_name),
            use="metadata",
            derived_from=original_file,
            file_uuid=str(uuid.uuid4()),
        )
        bundle.add_child(f)
        return bundle


def test_access(latest_version_md):
    """Return a tuple that can be used to direct users to information about a
    dataset if it is restricted.
    """
    restricted_access = False
    contact_information = latest_version_md.get("termsOfAccess")
    if contact_information == "Please contact owner for access":
        restricted_access = True
    return restricted_access, contact_information


def test_if_zip_in_name(fname):
    """Check if a file-path ends in a .zip extension. If so, return true. This
    helps us to log some information about the characteristics of the package
    as we go.
    """
    ext_ = os.path.splitext(fname)[1]
    if ext_.lower() == '.zip':
        return True
    return False


def add_ddi_xml(job, sip, json_metadata):
    """Create a DDI XML data block and add this to the METS."""
    ddi_root = create_ddi(job, json_metadata)
    if create_ddi is None:
        return None
    sip.add_dmdsec(md=ddi_root, mdtype="DDI")
    return sip


def add_metadata_ref(sip, md_name, md_loc):
    """Add a single mdref to the METS file."""
    sip.add_dmdsec(
        md=md_loc,
        mdtype="OTHER",
        mode="mdref",
        label=md_name,
        loctype="OTHER",
        otherloctype="SYSTEM",
    )
    return sip


def add_md_dir_to_structmap(sip):
    """Add the metadata directory to the structmap."""
    md_dir = metsrw.FSEntry(path="metadata", use=None, type="Directory")
    sip.add_child(md_dir)
    # Add dataset.json to the fileSec output.
    f = metsrw.FSEntry(
        path="metadata/dataset.json", use="metadata",
        file_uuid=str(uuid.uuid4())
    )
    # Add dataset.json to the metadata fileSec group.
    md_dir.add_child(f)
    return sip


def add_dataset_files_to_md(job, sip, latest_version_md, contact_information):
    # Add original files to the METS document.
    files = {}
    files = latest_version_md.get('files')
    if not files:
        return None

    # Signal to users the existence of zip files in this transfer.
    zipped_file = False

    # Signal to users that this transfer might consist of metadata only.
    if len(files) is 0:
        logger.info(
            "Metadata only transfer? There are no file entries in this "
            "transfer's metadata.")

    for file_json in files:
        is_restricted = file_json.get("restricted")
        if is_restricted is True and contact_information:
            logger.error(
                "Restricted dataset files may not have transferred "
                "correctly: %s", contact_information)
        if file_json.get("dataFile").get("filename").endswith(".tab"):
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
                return None
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
                checksum_value = file_json.get("dataFile").get("md5")
                if checksum_value is None:
                    return None
                display_checksum_for_user(job, checksum_value)
                f = metsrw.FSEntry(
                    path=path_,
                    use="original",
                    file_uuid=str(uuid.uuid4()),
                    checksumtype="MD5",
                    checksum=checksum_value,
                )
                sip.add_child(f)
            else:
                logger.error(
                    "Problem retrieving filename from metadata, returned "
                    "datafile: %s, path: %s", datafile, path_)
                return None
    return sip


def write_mets_to_file(sip, unit_path, output_md_path, output_md_name):
    # Write METS
    metadata_path = output_md_path
    if metadata_path is None:
        metadata_path = os.path.join(unit_path, "metadata")
    if not os.path.exists(metadata_path):
        os.makedirs(metadata_path)

    metadata_name = output_md_name
    if metadata_name is None:
        metadata_name = "METS.xml"
    mets_path = os.path.join(metadata_path, metadata_name)

    # Write the data structure out to a file and ensure that the encoding is
    # purposely set to UTF-8. This pattern is used in ```create_mets_v2.py```.
    # Given the opportunity we should add an encoding feature to the metsrw
    # package.
    mets_f = metsrw.METSDocument()
    mets_f.append_file(sip)
    tree = etree.fromstring(mets_f.tostring())
    with open(mets_path, 'w') as xml_file:
        xml_file.write(etree.tostring(
            tree, pretty_print=True, encoding="utf-8", xml_declaration=True))


def load_md_and_return_json(unit_path, dataset_md_name):
    # Read JSON
    json_path = os.path.join(unit_path, "metadata", dataset_md_name)
    logger.info("Metadata directory exists %s", os.path.exists(json_path))
    try:
        with open(json_path, "r") as f:
            return json.load(f)
    except IOError as e:
        logger.error("Error opening dataset metadata: %s", e)
        return None


def map_(job, unit_path, unit_uuid, dataset_md_name="dataset.json",
         output_md_path=None, output_md_name=None):
    """Docstring..."""
    logger.info(
        "Convert Dataverse structure called with '%s' unit directory and "
        "'%s' unit uuid", unit_path, unit_uuid)

    json_metadata = load_md_and_return_json(unit_path, dataset_md_name)
    if json_metadata is None:
        return 1
    latest_version_md = get_latest_version_metadata(json_metadata)
    if latest_version_md is None:
        return 1

    # If a dataset is restricted we may not have access to all the files. We
    # may also want to flag this dataset to the users of this service. We
    # can do this here and below. We do not yet know whether this microservice
    # should fail because we don't know how all datasets behave when some
    # restrictions are placed on them.
    restricted_access, contact_information = test_access(latest_version_md)

    # Create METS
    sip = metsrw.FSEntry(
        path="None", label=get_ddi_title_author(latest_version_md)[0],
        use=None, type="Directory"
    )

    sip = add_ddi_xml(job, sip, json_metadata)
    if sip is None:
        return 1

    sip = add_metadata_ref(
        sip, dataset_md_name, "metadata/{}".format(dataset_md_name))

    sip = add_dataset_files_to_md(
        job, sip, latest_version_md, contact_information)
    if sip is None:
        return 1

    sip = add_md_dir_to_structmap(sip)
    write_mets_to_file(sip, unit_path, output_md_path, output_md_name)

    # Success code to pass back to Job.
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
