#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import uuid

# databaseFunctions requires Django to be set up
import django
django.setup()
from django.utils import timezone

# archivematicaCommon
from archivematicaFunctions import get_file_checksum
from custom_handlers import get_script_logger
import databaseFunctions
from main.models import Agent, File
import metsrw

logger = get_script_logger("archivematica.mcp.client.parse_dataverse_mets")
transfer_objects_directory = "%transferDirectory%objects"


def concurrent_instances(): return 1


def get_db_objects(job, mets, transfer_uuid):
    """
    Get DB objects for files in METS.

    This also validates that files exist for each file asserted in the
    structMap

    :param mets: Parse METS file
    :return: Dict where key is the FSEntry and value is the DB object
    """
    mapping = {}
    for entry in mets.all_files():
        if entry.type == 'Directory' or entry.label == 'dataset.json':
            continue
        # TODO remove this once RData files are returned
        if entry.path.endswith('.RData'):
            continue
        # Retrieve the item name from the database. The proof-of-concept for
        # Dataverse extracts objects from a bundle (zip) which can then be
        # found on the root path of the transfer (the objects folder), but
        # that means the initial lookup of the file might not resolve as
        # anticipated as the directory structure of the bundle is reflected in
        # the original path. We try the base name for the item below.
        f = None
        try:
            item_path = os.path.join(transfer_objects_directory, entry.path)
            job.pyprint(
                "Looking for for file type: '{}' using relative path: {}"
                .format(entry.type, item_path))
            f = File.objects.get(originallocation=item_path,
                                 transfer_id=transfer_uuid)
        except File.DoesNotExist:
            logger.info(
                "Could not find file type: '{}' in the database: {}"
                .format(entry.type, entry.path))
        except File.MultipleObjectsReturned as e:
            logger.info("Multiple entries for `%s` found. Exception: %s",
                        entry.path, e)

        try:
            # Attempt to find the original location through just its filename
            # as it may be sitting in the root item/objects directory of the
            # transfer.
            if f is None:
                base_name = os.path.basename(entry.path)
                item_path = os.path.join(transfer_objects_directory, base_name)
                job.pyprint("Looking for for file type: '{}' using "
                            "base name: {}".format(entry.type, item_path))
                f = File.objects.get(
                    originallocation=item_path,
                    transfer_id=transfer_uuid)
        except File.DoesNotExist:
            logger.error(
                "Could not find file type: '{}' in the database: {}. "
                "Checksum: '{}'"
                .format(entry.type, base_name, entry.checksum))
            return None
        except File.MultipleObjectsReturned as e:
            logger.info("Multiple entries for `%s` found. Exception: %s",
                        base_name, e)
            return None

        job.pyprint("Adding mapping dict [{}] entry: {}".format(entry, f))
        mapping[entry] = f

    return mapping


def update_file_use(job, mapping):
    """
    Update the file's USE for files in mets.

    :param mets: Parse METS file
    :return: None
    """
    for entry, f in mapping.items():
        f.filegrpuse = entry.use
        job.pyprint(entry.label, 'file group use set to', entry.use)
        f.save()


def add_external_agents(job, unit_path):
    """
    Add external agent(s).

    :return: ID of the first agent, assuming that's the Dataverse agent.
    """
    agents_jsonfile = os.path.join(unit_path, 'metadata', 'agents.json')
    try:
        with open(agents_jsonfile, 'r') as f:
            agents_json = json.load(f)
    except (OSError, IOError):
        return None

    agent_id = None
    for agent in agents_json:
        a, created = Agent.objects.get_or_create(
            identifiertype=agent['agentIdentifierType'],
            identifiervalue=agent['agentIdentifierValue'],
            name=agent['agentName'],
            agenttype=agent['agentType'],
        )
        if created:
            job.pyprint('Added agent', agent)
        else:
            job.pyprint('Agent already exists', agent)
        agent_id = agent_id or a.id

    return agent_id


def create_derivatives(job, mapping, dataverse_agent_id):
    """
    Create derivatives for derived tabular data.
    """
    for entry, f in mapping.items():
        if entry.derived_from and entry.use == 'derivative':
            original_uuid = mapping[entry.derived_from].uuid
            event_uuid = uuid.uuid4()
            # Add event
            databaseFunctions.insertIntoEvents(
                original_uuid,
                eventIdentifierUUID=event_uuid,
                eventType="derivation",
                eventDateTime=None,  # From Dataverse?
                eventDetail="",  # From Dataverse?
                eventOutcome="",  # From Dataverse?
                eventOutcomeDetailNote=f.currentlocation,
                agents=[dataverse_agent_id],
            )
            # Add derivation
            databaseFunctions.insertIntoDerivations(
                sourceFileUUID=original_uuid,
                derivedFileUUID=f.uuid,
                relatedEventUUID=event_uuid,
            )
            job.pyprint('Added derivation from', original_uuid, 'to', f.uuid)


def validate_checksums(job, mapping, unit_path):
    date = timezone.now().isoformat(' ')
    for entry, f in mapping.items():
        if entry.checksum and entry.checksumtype:
            job.pyprint('Checking checksum', entry.checksum, 'for', entry.label)
            if f.currentlocation is None and f.removedtime is not None:
                logger.info("File: %s removed by extract packages?", entry.label)
                continue
            path_ = f.currentlocation.replace('%transferDirectory%', unit_path)
            if os.path.isdir(path_):
                continue
            verify_checksum(
                job=job,
                file_uuid=f.uuid,
                path=path_,
                checksum=entry.checksum,
                checksumtype=entry.checksumtype,
                date=date,
            )


def verify_checksum(job, file_uuid, path, checksum, checksumtype,
                    event_id=None, date=None):
    """
    Verify the checksum of a given file, and create a fixity event.

    :param str file_uuid: UUID of the file to verify
    :param str path: Path of the file to verify
    :param str checksum: Checksum to compare against
    :param str checksumtype: Type of the provided checksum (md5, sha256, etc)
    :param str event_id: Event ID
    :param str date: Date of the event
    """
    if event_id is None:
        event_id = str(uuid.uuid4())
    if date is None:
        date = timezone.now().isoformat(' ')

    checksumtype = checksumtype.lower()
    generated_checksum = get_file_checksum(path, checksumtype)
    event_detail = ('program="python"; '
                    'module="hashlib.{}()"'.format(checksumtype))
    if checksum != generated_checksum:
        job.pyprint('Checksum failed')
        event_outcome = "Fail"
        detail_note = 'Dataverse checksum %s verification failed' % checksum
    else:
        job.pyprint('Checksum passed')
        event_outcome = "Pass"
        detail_note = 'Dataverse checksum %s verified' % checksum

    databaseFunctions.insertIntoEvents(
        fileUUID=file_uuid,
        eventIdentifierUUID=event_id,
        eventType='fixity check',
        eventDateTime=date,
        eventDetail=event_detail,
        eventOutcome=event_outcome,
        eventOutcomeDetailNote=detail_note,
    )


def parse_(job, unit_path, unit_uuid):
    """Access the existing METS file and extract and validate its components.
    """
    dataverse_mets_path = os.path.join(unit_path, 'metadata', 'METS.xml')
    mets = metsrw.METSDocument.fromfile(dataverse_mets_path)
    mapping = get_db_objects(job, mets, unit_uuid)
    if mapping is None:
        logger.error(
            "Exiting. Returning the database objects for our Dataverse "
            "files has failed.")
        return 1
    update_file_use(job, mapping)
    agent = add_external_agents(job, unit_path)
    create_derivatives(job, mapping, agent)
    validate_checksums(job, mapping, unit_path)
    return 0


def parse_dataverse_mets(job):
    """Extract the arguments provided to the script and call the primary
    function concerned with parsing Dataverse METS.
    """
    try:
        transfer_dir = job.args[1]
        transfer_uuid = job.args[2]
        logger.info("Parse Dataverse METS with dir args: '%s' and transfer "
                    "uuid: %s", transfer_dir, transfer_uuid)
        return parse_(job, transfer_dir, transfer_uuid)
    except IndexError:
        logger.error(
            "Problem with the supplied arguments to the function "
            "len: %s", len(job.args))
        return 1


def call(jobs):
    for job in jobs:
        with job.JobContext(logger=logger):
            job.set_status(parse_dataverse_mets(job))