# -*- coding: utf-8 -*-

"""Migration to create a Dataverse Transfer Type.


New UUIDs that are created (should all be removed in the down function):

    # Tasks:

    * task_uuid="2b2042d4-548f-4c63-a394-bf14b5faa5d1",
    * task_uuid="7d1872fc-d90e-4354-a5c9-97d24bbdf629",
    * task_uuid="a6b1efde-ddf1-492a-8eb4-0c556657bd38",
    * task_uuid="ab6c6e52-10c5-449e-ae92-89cf7903e6bc",
    * task_uuid="7eade269-0bc3-4a6a-9801-e8e4d8babb55",
    * task_uuid="477bc37e-b6a7-440a-9088-85672b3b38a7",
    * task_uuid="4d36c35a-0829-4b2d-ba3d-0a30a3e837f9",

    # MicroService Chains

    * chain_uuid="35a26b59-dcf3-45ec-b963-ba7bfaa8304f",
    * chain_uuid="10c00bc8-8fc2-419f-b593-cf5518695186",

    # MicroServiceChainLinks

    * ms_uuid="9ec31d55-f053-4695-b86d-8c2a8abdb0fc",
    * ms_uuid="213fe743-f170-4695-8b3e-77886a31a89d",
    * ms_uuid="364ac694-6440-4e45-8b2a-d3715c524970",
    * ms_uuid="e942d973-9db1-46bf-afdd-2827c22223d0",
    * ms_uuid="246943e4-d203-48e1-ac84-4865520e7c30",
    * ms_uuid="fdb12ea6-22aa-46c8-a591-a2bcf5d42e5e",
    * ms_uuid="0af6b163-5455-4a76-978b-e35cc9ee445f",

    # Standard Task Configs (MCP Client Scripts)

    * task_uuid="286b4b17-d382-48eb-bdbe-ca3b2a32568b",
    * task_uuid="ed3cda67-94b6-457e-9d00-c58f413dbfce",

    # Set Unit Variables

    * var_uuid="f5908626-38be-4c2b-9c09-a389585e9f6c",
    * var_uuid="3fcc6e42-0117-4786-9cd4-e773f6f71296",

    # Variable Link Pulls

    * link_uuid="5b11c0a9-6f62-4d7e-ad48-2905e75ff419",

    # MicroServiceExitCodes

    * exit_code_uuid="da46e870-290b-4fd4-8f84-194b9177d8c0",
    * exit_code_uuid="4ce6a3bd-026b-4ce7-beae-809844bae289",
    * exit_code_uuid="84647820-e56a-45cc-94a1-9f74de375ba8",
    * exit_code_uuid="d515821d-b1f6-4ce9-b4e4-0503fa99c8cf",
    * exit_code_uuid="f7e3753c-4df9-43fe-9c32-0d11c511308c",

    # Microservice Choices

    * choice_uuid="dc9b59b3-dd5f-4cd6-8e97-ee1d83734c4c",
    * choice_uuid="77bb4993-9f5b-4e60-bbe9-0039a6f5934e",

    # WatchedDirectories

    * watched_uuid="3901db52-dd1d-4b44-9d86-4285ddc5c022",

UUIDs that are updated (should be updated in the down function):

    # MicroServiceExitCodes

    * exit_code_uuid="9cb81a5c-a7a1-43a8-8eb6-3e999923e03c",

"""


from __future__ import unicode_literals

import logging

from django.db import migrations

# Can't use apps.get_model for this model as we need to access class attributes.
from main.models import Job

# Get an instance of a logger
logger = logging.getLogger(__name__)
logger.setLevel("INFO")

DEFAULT_NEXT_MS = "61c316a6-0a50-4f65-8767-1f44b1eeb6dd"


def create_variable_link_pull(
        apps, link_uuid, variable, default_ms_uuid=None):
    """Create a new variable link pull in the database."""
    apps.get_model("main", "TaskConfigUnitVariableLinkPull").objects.create(
        id=link_uuid,
        variable=variable,
        defaultmicroservicechainlink_id=default_ms_uuid,
    )


def create_set_unit_variable(
        apps, var_uuid, variable_name, variable_value=None, ms_uuid=None):
    """Create a new unit variable in the database."""
    apps.get_model("main", "TaskConfigSetUnitVariable").objects.create(
        id=var_uuid,
        variable=variable_name,
        variablevalue=variable_value,
        microservicechainlink_id=ms_uuid,
    )


def create_standard_task_config(apps, task_uuid, execute_string, args):
    """Create a task configuration, inc. the command and args and write to the
    database.
    """
    get_model(apps, "StandardTaskConfig").objects.create(
        id=task_uuid, execute=execute_string, arguments=args,
    )


def create_task(
        apps, task_type_uuid, task_uuid, task_desc, task_config=None):
    """Create a new task configuration entry in the database."""
    get_model(apps, 'TaskConfig').objects.create(
        id=task_uuid, description=task_desc, tasktype_id=task_type_uuid,
        tasktypepkreference=task_config,
    )


def create_ms_chain_link(
        apps, ms_uuid, group, task_uuid, ms_exit_message=Job.STATUS_FAILED,
        default_next_link=DEFAULT_NEXT_MS):
    """Create a microservice chainlink in the database."""
    apps.get_model("main", "MicroServiceChainLink").objects.create(
        id=ms_uuid,
        microservicegroup=group,
        defaultexitmessage=ms_exit_message,
        currenttask_id=task_uuid,
        defaultnextchainlink_id=default_next_link,
    )


def create_ms_chain(apps, chain_uuid, ms_uuid, chain_description):
    """Create a new chain in the database."""
    apps.get_model("main", "MicroServiceChain").objects.create(
        id=chain_uuid,
        startinglink_id=ms_uuid,
        description=chain_description,
    )


def create_ms_choice(apps, choice_uuid, chain_uuid, link_uuid):
    """Create a choice in the database."""
    apps.get_model('main', 'MicroServiceChainChoice').objects.create(
        id=choice_uuid,
        chainavailable_id=chain_uuid,
        choiceavailableatlink_id=link_uuid,
    )


def create_watched_dir(
        apps, watched_uuid, dir_path, expected_type, chain_uuid):
    """Create a new watched directory in the database."""
    get_model(apps, "WatchedDirectory").objects.create(
        id=watched_uuid, watched_directory_path=dir_path,
        expected_type_id=expected_type, chain_id=chain_uuid,
    )


def create_ms_exit_codes(
        apps, exit_code_uuid, ms_in, ms_out,
        ms_exit_message=Job.STATUS_COMPLETED_SUCCESSFULLY, update=False):
    """Create an exit code entry in the database."""
    if not update:
        apps.get_model("main", "MicroServiceChainLinkExitCode").objects.create(
            id=exit_code_uuid,
            microservicechainlink_id=ms_in,
            nextmicroservicechainlink_id=ms_out,
            exitmessage=ms_exit_message,
        )
        return
    apps.get_model("main", "MicroServiceChainLinkExitCode").objects\
        .filter(id=exit_code_uuid)\
        .update(nextmicroservicechainlink_id=ms_out)


##############################################################################
# Add to migration down...
##############################################################################


def create_skip_user_choice_on_extract_link_pull(apps):
    """Docstring..."""

    create_task(
        apps=apps, task_type_uuid="c42184a3-1a7f-4c4d-b380-15d8d97fdd11",
        task_uuid="8f785c2e-aa48-48f4-a0ef-b08e208a9d95",
        task_desc="Skip user choice to extract Dataverse?",
        task_config="a0483e03-f2c6-40a0-aa71-0e39f22f0aeb",
    )

    # ...
    create_ms_chain_link(
        apps=apps, ms_uuid="f0ff25d8-528b-426c-9229-689196b5d312",
        group="Extract packages",
        task_uuid="8f785c2e-aa48-48f4-a0ef-b08e208a9d95",
        ms_exit_message=Job.STATUS_COMPLETED_SUCCESSFULLY,)

    # If linkToConvertDataverseStructure is set then goto the configured
    # microservice, else, goto the default microservice.
    # Default MS: 'Extract packages?'
    create_variable_link_pull(
        apps=apps, link_uuid="a0483e03-f2c6-40a0-aa71-0e39f22f0aeb",
        variable="overrideUserExtractChoice",
        default_ms_uuid="dec97e3c-5598-4b99-b26e-f87a435a6b7f")

    # Break and Update the existing link to connect to our new link.
    # Original: 4ba2d89a-d741-4868-98a7-6202d0c57163
    # ms_1: b944ec7f-7f99-491f-986d-58914c9bb4fa
    #  (Determine if transfer contains packages)
    # ms_2: dec97e3c-5598-4b99-b26e-f87a435a6b7f
    #  (Extract packages?)
    # New:
    # b944ec7f (Determine if transfer contains packages)
    # f0ff25d8 (Override user extract choice for Dataverse?)
    create_ms_exit_codes(
        apps=apps, exit_code_uuid="4ba2d89a-d741-4868-98a7-6202d0c57163",
        ms_in="b944ec7f-7f99-491f-986d-58914c9bb4fa",
        ms_out="f0ff25d8-528b-426c-9229-689196b5d312",
        update=True)


def create_extract_dataverse_link_pull(apps):
    """Docstring..."""

    create_task(
        apps=apps, task_type_uuid="c42184a3-1a7f-4c4d-b380-15d8d97fdd11",
        task_uuid="3180b1eb-f9a3-4667-bc92-639bd51b75ae",
        task_desc="Determine if Dataverse Bundle Needs Extracting",
        task_config="6a141385-ac1e-40d5-9923-d776b2d8b997",
    )

    # ...
    create_ms_chain_link(
        apps=apps, ms_uuid="527bff64-7b96-4285-8715-9e36285f9380",
        group="Extract packages",
        task_uuid="3180b1eb-f9a3-4667-bc92-639bd51b75ae",
        ms_exit_message=Job.STATUS_COMPLETED_SUCCESSFULLY,)

    # If linkToConvertDataverseStructure is set then goto the configured
    # microservice, else, goto the default microservice.
    # Default MS: 'Add processed structMap to METS.xml document'
    create_variable_link_pull(
        apps=apps, link_uuid="6a141385-ac1e-40d5-9923-d776b2d8b997",
        variable="extractFromDataverse",
        default_ms_uuid="307edcde-ad10-401c-92c4-652917c993ed")

    # Break and Update the existing link to connect to our new link.
    # Original: 1f877d65-66c5-49da-bf51-2f1757b59c90
    # ms_1: 2522d680-c7d9-4d06-8b11-a28d8bd8a71f
    #       (Identify File Format)
    # ms_2: cc16178b-b632-4624-9091-822dd802a2c6
    #       (Move to Extract Packages)
    # New: 1f877d65-66c5-49da-bf51-2f1757b59c90
    # 2522d680 (Identify File Format)
    # 527bff64 (Determine if DB Bundle needs extracting)
    create_ms_exit_codes(
        apps=apps, exit_code_uuid="1f877d65-66c5-49da-bf51-2f1757b59c90",
        ms_in="2522d680-c7d9-4d06-8b11-a28d8bd8a71f",
        ms_out="527bff64-7b96-4285-8715-9e36285f9380",
        update=True)


##############################################################################
# Add to migration down...
##############################################################################


def create_parse_dataverse_mets_link_pull(apps):
    """Create the variable link pull set of database rows."""

    #  (Determine Dataverse Conversion) task to associate with
    # a MicroServiceChainLink.
    create_task(
        apps=apps, task_type_uuid="c42184a3-1a7f-4c4d-b380-15d8d97fdd11",
        task_uuid="355c22ae-ba5b-408b-a9b6-a01372d158b5",
        task_desc="Determine Parse Dataverse METS XML",
        task_config="6f7a2ebd-bd88-44b7-b146-c552ac4e40cb"
    )

    #  (Determine Dataverse Conversion).
    create_ms_chain_link(
        apps=apps, ms_uuid="ec3c965c-c056-47e3-a551-ad1966e00824",
        group="Parse External Files",
        task_uuid="355c22ae-ba5b-408b-a9b6-a01372d158b5",
        ms_exit_message=Job.STATUS_COMPLETED_SUCCESSFULLY,)

    # If linkToConvertDataverseStructure is set then goto the configured
    # microservice, else, goto the default microservice.
    create_variable_link_pull(
        apps=apps, link_uuid="6f7a2ebd-bd88-44b7-b146-c552ac4e40cb",
        variable="linkToParseDataverseMETS",
        default_ms_uuid="dae3c416-a8c2-4515-9081-6dbd7b265388")

    # Break and Update the existing link to connect to our new link.
    # Original: 434066e6-8205-4832-a71f-cc9cd8b539d2
    # ms_1: a536828c-be65-4088-80bd-eb511a0a063d
    #       (Validate Formats)
    # ms_2: 70fc7040-d4fb-4d19-a0e6-792387ca1006
    #       (Perform policy checks on originals?)
    # New: 434066e6-8205-4832-a71f-cc9cd8b539d2
    # a536828c (Validate Formats)
    # ec3c965c (Determine Parse Dataverse METS XML)
    create_ms_exit_codes(
        apps=apps, exit_code_uuid="434066e6-8205-4832-a71f-cc9cd8b539d2",
        ms_in="a536828c-be65-4088-80bd-eb511a0a063d",
        ms_out="ec3c965c-c056-47e3-a551-ad1966e00824",
        update=True)

    # Create a new link now we have broken the original.
    #  (Convert Dataverse Structure) connects to:
    #  (Attempt Restructure For Compliance)
    create_ms_exit_codes(
        apps=apps, exit_code_uuid="6f7a2ebd-bd88-44b7-b146-c552ac4e40cb",
        ms_in="ec3c965c-c056-47e3-a551-ad1966e00824",
        ms_out="db99ab43-04d7-44ab-89ec-e09d7bbdc39d",)


def create_convert_dataverse_link_pull(apps):
    """Create the variable link pull set of database rows."""

    # 7eade269 (Determine Dataverse Conversion) task to associate with
    # a MicroServiceChainLink.
    create_task(
        apps=apps, task_type_uuid="c42184a3-1a7f-4c4d-b380-15d8d97fdd11",
        task_uuid="7eade269-0bc3-4a6a-9801-e8e4d8babb55",
        task_desc="Determine Dataverse conversion",
        task_config="5b11c0a9-6f62-4d7e-ad48-2905e75ff419"
    )

    # 7eade269 (Determine Dataverse Conversion).
    create_ms_chain_link(
        apps=apps, ms_uuid="2a0a7afb-d09b-414b-a7ae-625f162103c1",
        group="Verify transfer compliance",
        task_uuid="7eade269-0bc3-4a6a-9801-e8e4d8babb55",
        ms_exit_message=Job.STATUS_COMPLETED_SUCCESSFULLY,)

    # If linkToConvertDataverseStructure is set then goto the configured
    # microservice, else, goto the default microservice.
    create_variable_link_pull(
        apps=apps, link_uuid="5b11c0a9-6f62-4d7e-ad48-2905e75ff419",
        variable="linkToConvertDataverseStructure",
        default_ms_uuid="ea0e8838-ad3a-4bdd-be14-e5dba5a4ae0c")

    # Break and Update the existing link to connect to our new link.
    # Original: 9cb81a5c-a7a1-43a8-8eb6-3e999923e03c
    # ms_1: 5d780c7d-39d0-4f4a-922b-9d1b0d217bca
    #       (Remove hidden files and directories)
    # ms_2: ea0e8838-ad3a-4bdd-be14-e5dba5a4ae0c
    #       (Attempt restructure for compliance)
    # New: 9cb81a5c-a7a1-43a8-8eb6-3e999923e03c
    # 5d780c7d (Remove Unneeded Files) connects to:
    # 2a0a7afb (Determine Dataverse Conversion)
    create_ms_exit_codes(
        apps=apps, exit_code_uuid="9cb81a5c-a7a1-43a8-8eb6-3e999923e03c",
        ms_in="5d780c7d-39d0-4f4a-922b-9d1b0d217bca",
        ms_out="2a0a7afb-d09b-414b-a7ae-625f162103c1",
        update=True)

    # Create a new link now we have broken the original.
    # 9ec31d55 (Convert Dataverse Structure) connects to:
    # ea0e8838 (Attempt Restructure For Compliance)
    create_ms_exit_codes(
        apps=apps, exit_code_uuid="d515821d-b1f6-4ce9-b4e4-0503fa99c8cf",
        ms_in="9ec31d55-f053-4695-b86d-8c2a8abdb0fc",
        ms_out="ea0e8838-ad3a-4bdd-be14-e5dba5a4ae0c",)


def create_units(apps):
    """Docstring..."""

    # Create a Task that creates a unit variable to instruct Archivematica to
    # convert a Dataverse metadata structure to METS.
    create_task(
        apps=apps, task_type_uuid="6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
        task_uuid="2b2042d4-548f-4c63-a394-bf14b5faa5d1",
        task_desc="Set Convert Dataverse Structure",
        task_config="f5908626-38be-4c2b-9c09-a389585e9f6c")

    # Create a Task that creates a unit variable to instruct Archivematica to
    # process an external Dataverse METS.
    create_task(
        apps=apps, task_type_uuid="6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
        task_uuid="7d1872fc-d90e-4354-a5c9-97d24bbdf629",
        task_desc="Set Parse Dataverse Mets",
        task_config="3fcc6e42-0117-4786-9cd4-e773f6f71296")

    # Create a MicroServiceChainLink to point to the Set Dataverse Transfer
    # Create Unit Variable Task.
    create_ms_chain_link(
        apps=apps, ms_uuid="213fe743-f170-4695-8b3e-77886a31a89d",
        group="Verify transfer compliance",
        task_uuid="2b2042d4-548f-4c63-a394-bf14b5faa5d1")

    # Create a MicroServiceChainLink to point to the Set Parse Dataverse METS
    # Create Unit Variable Task.
    create_ms_chain_link(
        apps=apps, ms_uuid="364ac694-6440-4e45-8b2a-d3715c524970",
        group="Verify transfer compliance",
        task_uuid="7d1872fc-d90e-4354-a5c9-97d24bbdf629")

    # Create a task for setting the unit variable telling a transfer to parse
    # an external Dataverse METS file.
    create_task(
        apps=apps, task_type_uuid="6f0b612c-867f-4dfd-8e43-5b35b7f882d7",
        task_uuid="a6b1efde-ddf1-492a-8eb4-0c556657bd38",
        task_desc="Set Parse Dataverse Mets",
        task_config="3fcc6e42-0117-4786-9cd4-e773f6f71296")

    # Set unit: linkToConvertDataverseStructure
    create_ms_chain_link(
        apps=apps, ms_uuid="e942d973-9db1-46bf-afdd-2827c22223d0",
        group="Verify transfer compliance",
        task_uuid="a6b1efde-ddf1-492a-8eb4-0c556657bd38")

    # Create the MicroServiceChainLinks required to ask Archivematica to
    # process a transfer as a Dataverse one.

    # Pointer to the convert Dataverse structure MCP Client script.
    create_standard_task_config(
        apps=apps, task_uuid="286b4b17-d382-48eb-bdbe-ca3b2a32568b",
        execute_string="convertDataverseStructure_v0.0",
        args="%SIPDirectory% %SIPUUID%")

    # ab6c6e52 (Convert Dataverse Structure) task to be associated with a
    # MicroServiceChainLink.
    create_task(
        apps=apps, task_type_uuid="36b2e239-4a57-4aa5-8ebc-7a29139baca6",
        task_uuid="ab6c6e52-10c5-449e-ae92-89cf7903e6bc",
        task_desc="Convert Dataverse Structure",
        task_config="286b4b17-d382-48eb-bdbe-ca3b2a32568b"
    )

    # =======================================================================

    # Move this:

    # Pointer to the convert Dataverse structure MCP Client script.
    create_standard_task_config(
        apps=apps, task_uuid="58988b82-7b65-40f3-94a7-f2f3e13b8700",
        execute_string="parseDataverse",
        args="%SIPDirectory% %SIPUUID%")

    #  (Convert Dataverse Structure) task to be associated with a
    # MicroServiceChainLink.
    create_task(
        apps=apps, task_type_uuid="36b2e239-4a57-4aa5-8ebc-7a29139baca6",
        task_uuid="e593507e-f4bf-4346-8652-32a832524782",
        task_desc="Parse Dataverse METS XML",
        task_config="58988b82-7b65-40f3-94a7-f2f3e13b8700"
    )

    #  (Convert Dataverse Structure) Chainlink.
    create_ms_chain_link(
        apps=apps, ms_uuid="fba1fd92-150a-4969-84fb-f2c6097855cf",
        group="Parse External Files",
        task_uuid="e593507e-f4bf-4346-8652-32a832524782")

    # Create a new link now we have broken the original.
    # 364ac694 (Set Parse Dataverse (Unit Variable)) connects to:
    # 50b67418 (Remove hidden files and directories).
    create_ms_exit_codes(
        apps=apps, exit_code_uuid="d10e1118-4d6c-4d3c-a9a8-1307a2931a32",
        ms_in="fba1fd92-150a-4969-84fb-f2c6097855cf",
        ms_out="db99ab43-04d7-44ab-89ec-e09d7bbdc39d")

    # =======================================================================

    # ab6c6e52 (Convert Dataverse Structure) Chainlink.
    create_ms_chain_link(
        apps=apps, ms_uuid="9ec31d55-f053-4695-b86d-8c2a8abdb0fc",
        group="Verify transfer compliance",
        task_uuid="ab6c6e52-10c5-449e-ae92-89cf7903e6bc")

    # Create a unit variable to enable Archivematica to see this as a Dataverse
    # transfer and process the contents downloaded via the Storage Service
    # appropriately.
    create_set_unit_variable(
        apps=apps, var_uuid="f5908626-38be-4c2b-9c09-a389585e9f6c",
        variable_name="linkToConvertDataverseStructure",
        ms_uuid="9ec31d55-f053-4695-b86d-8c2a8abdb0fc")

    # Create a unit variable to determine that the external METS file created
    # for Dataverse will be parsed later on in the process by Archivematica.
    create_set_unit_variable(
        apps=apps, var_uuid="3fcc6e42-0117-4786-9cd4-e773f6f71296",
        variable_name="linkToParseDataverseMETS",
        ms_uuid="fba1fd92-150a-4969-84fb-f2c6097855cf")

    # Break and Update the existing link to connect to our new link.
    # 0af6b163 (Set Transfer Type: Dataverse) connects to:
    # 213fe743 (Set Parse Dataverse METS)
    create_ms_exit_codes(
        apps=apps, exit_code_uuid="da46e870-290b-4fd4-8f84-194b9177d8c0",
        ms_in="0af6b163-5455-4a76-978b-e35cc9ee445f",
        ms_out="213fe743-f170-4695-8b3e-77886a31a89d",
        update=True)

    # Create a new link now we have broken the original.
    # 213fe743 (Set Dataverse Transfer)
    # 364ac694 (Set Parse Dataverse METS)
    create_ms_exit_codes(
        apps=apps, exit_code_uuid="4ce6a3bd-026b-4ce7-beae-809844bae289",
        ms_in="213fe743-f170-4695-8b3e-77886a31a89d",
        ms_out="364ac694-6440-4e45-8b2a-d3715c524970",)

    # Create a new link now we have broken the original.
    # 364ac694 (Set Parse Dataverse (Unit Variable)) connects to:
    # 50b67418 (Remove hidden files and directories).
    create_ms_exit_codes(
        apps=apps, exit_code_uuid="84647820-e56a-45cc-94a1-9f74de375ba8",
        ms_in="364ac694-6440-4e45-8b2a-d3715c524970",
        ms_out="50b67418-cb8d-434d-acc9-4a8324e7fdd2")


def data_migration_up(apps, schema_editor):

    create_standard_task_config(
        apps=apps, task_uuid="ed3cda67-94b6-457e-9d00-c58f413dbfce",
        execute_string="archivematicaSetTransferType_v0.0",
        args="\"%SIPUUID%\" \"Dataverse\"")

    create_task(
        apps=apps, task_type_uuid="61fb3874-8ef6-49d3-8a2d-3cb66e86a30c",
        task_uuid="477bc37e-b6a7-440a-9088-85672b3b38a7",
        task_desc="Approve Dataverse Transfer")

    create_task(
        apps=apps, task_type_uuid="36b2e239-4a57-4aa5-8ebc-7a29139baca6",
        task_uuid="4d36c35a-0829-4b2d-ba3d-0a30a3e837f9",
        task_desc="Set transfer type: Dataverse",
        task_config="ed3cda67-94b6-457e-9d00-c58f413dbfce"
    )

    # create ms
    create_ms_chain_link(
        apps=apps, ms_uuid="246943e4-d203-48e1-ac84-4865520e7c30",
        group="Approve Dataverse transfer",
        task_uuid="477bc37e-b6a7-440a-9088-85672b3b38a7")

    # move to processing dir
    create_ms_chain_link(
        apps=apps, ms_uuid="fdb12ea6-22aa-46c8-a591-a2bcf5d42e5e",
        group="Verify transfer compliance",
        task_uuid="7c02a87b-7113-4851-97cd-2cf9d3fc0010")

    # set transfer type: dataverse
    create_ms_chain_link(
        apps=apps, ms_uuid="0af6b163-5455-4a76-978b-e35cc9ee445f",
        group="Verify transfer compliance",
        task_uuid="4d36c35a-0829-4b2d-ba3d-0a30a3e837f9")

    # create chain
    create_ms_chain(
        apps=apps, chain_uuid="35a26b59-dcf3-45ec-b963-ba7bfaa8304f",
        ms_uuid="246943e4-d203-48e1-ac84-4865520e7c30",
        chain_description="Dataverse Transfers in Progress")

    create_ms_chain(
        apps=apps, chain_uuid="10c00bc8-8fc2-419f-b593-cf5518695186",
        ms_uuid="fdb12ea6-22aa-46c8-a591-a2bcf5d42e5e",
        chain_description="Approve Dataverse transfer")

    # Approve
    create_ms_choice(
        apps=apps, choice_uuid="dc9b59b3-dd5f-4cd6-8e97-ee1d83734c4c",
        chain_uuid="10c00bc8-8fc2-419f-b593-cf5518695186",
        link_uuid="246943e4-d203-48e1-ac84-4865520e7c30")

    # Reject
    create_ms_choice(
        apps=apps, choice_uuid="77bb4993-9f5b-4e60-bbe9-0039a6f5934e",
        chain_uuid="1b04ec43-055c-43b7-9543-bd03c6a778ba",
        link_uuid="246943e4-d203-48e1-ac84-4865520e7c30")

    create_watched_dir(
        apps=apps, watched_uuid="3901db52-dd1d-4b44-9d86-4285ddc5c022",
        dir_path="%watchDirectoryPath%activeTransfers/dataverseTransfer",
        expected_type="f9a3a93b-f184-4048-8072-115ffac06b5d",
        chain_uuid="35a26b59-dcf3-45ec-b963-ba7bfaa8304f")

    # TODO look up these tasks and then annotate what they are...
    create_ms_exit_codes(
        apps=apps, exit_code_uuid="f7e3753c-4df9-43fe-9c32-0d11c511308c",
        ms_in="fdb12ea6-22aa-46c8-a591-a2bcf5d42e5e",
        ms_out="0af6b163-5455-4a76-978b-e35cc9ee445f")

    create_ms_exit_codes(
        apps=apps, exit_code_uuid="da46e870-290b-4fd4-8f84-194b9177d8c0",
        ms_in="0af6b163-5455-4a76-978b-e35cc9ee445f",
        ms_out="50b67418-cb8d-434d-acc9-4a8324e7fdd2")

    # TODO start to split these things up ...
    create_units(apps)
    create_convert_dataverse_link_pull(apps)
    create_parse_dataverse_mets_link_pull(apps)
    create_extract_dataverse_link_pull(apps)
    create_skip_user_choice_on_extract_link_pull(apps)


def get_model(apps, model_name):
    return apps.get_model("main", model_name)


def data_migration_down(apps, schema_editor):

    # Fix broken chain links:
    # Original: 9cb81a5c-a7a1-43a8-8eb6-3e999923e03c
    # ms_1: 5d780c7d-39d0-4f4a-922b-9d1b0d217bca
    #       (Remove hidden files and directories)
    # ms_2: ea0e8838-ad3a-4bdd-be14-e5dba5a4ae0c
    #       (Attempt restructure for compliance)
    create_ms_exit_codes(
        apps=apps, exit_code_uuid="9cb81a5c-a7a1-43a8-8eb6-3e999923e03c",
        ms_in="5d780c7d-39d0-4f4a-922b-9d1b0d217bca",
        ms_out="ea0e8838-ad3a-4bdd-be14-e5dba5a4ae0c",
        update=True)

    # Original: 434066e6-8205-4832-a71f-cc9cd8b539d2
    # ms_1: a536828c-be65-4088-80bd-eb511a0a063d
    #       (Validate Formats)
    # ms_2: 70fc7040-d4fb-4d19-a0e6-792387ca1006
    #       (Perform policy checks on originals?)
    create_ms_exit_codes(
        apps=apps, exit_code_uuid="434066e6-8205-4832-a71f-cc9cd8b539d2",
        ms_in="a536828c-be65-4088-80bd-eb511a0a063d",
        ms_out="70fc7040-d4fb-4d19-a0e6-792387ca1006",
        update=True)

    # Fix broken chain links:
    # Original: 1f877d65-66c5-49da-bf51-2f1757b59c90
    # ms_1: 2522d680-c7d9-4d06-8b11-a28d8bd8a71f
    #       (Identify File Format)
    # ms_2: cc16178b-b632-4624-9091-822dd802a2c6
    #       (Move to Extract Packages)
    create_ms_exit_codes(
        apps=apps, exit_code_uuid="1f877d65-66c5-49da-bf51-2f1757b59c90",
        ms_in="2522d680-c7d9-4d06-8b11-a28d8bd8a71f",
        ms_out="cc16178b-b632-4624-9091-822dd802a2c6",
        update=True)

    # Fix broken chain links:
    # Original: 4ba2d89a-d741-4868-98a7-6202d0c57163
    # ms_1: b944ec7f-7f99-491f-986d-58914c9bb4fa
    #  (Determine if transfer contains packages)
    # ms_2: dec97e3c-5598-4b99-b26e-f87a435a6b7f
    #  (Extract packages?)
    create_ms_exit_codes(
        apps=apps, exit_code_uuid="4ba2d89a-d741-4868-98a7-6202d0c57163",
        ms_in="b944ec7f-7f99-491f-986d-58914c9bb4fa",
        ms_out="dec97e3c-5598-4b99-b26e-f87a435a6b7f",
        update=True)

    # Once we've fixed the previous chains, we can delete the extraneous pieces
    # introduced by the attempt to create the transfer type here.

    # Remove WatchedDirectories
    get_model(apps=apps, model_name="WatchedDirectory").objects.filter(
        id="3901db52-dd1d-4b44-9d86-4285ddc5c022").delete()

    # Remove MicroServiceChains
    for uuid_ in ['10c00bc8-8fc2-419f-b593-cf5518695186',
                  '35a26b59-dcf3-45ec-b963-ba7bfaa8304f']:
        get_model(apps, 'MicroServiceChain').objects.filter(
            id=uuid_).delete()

    # Remove MicroServiceExitCodes
    for uuid_ in ["da46e870-290b-4fd4-8f84-194b9177d8c0",
                  "4ce6a3bd-026b-4ce7-beae-809844bae289",
                  "84647820-e56a-45cc-94a1-9f74de375ba8",
                  "d515821d-b1f6-4ce9-b4e4-0503fa99c8cf",
                  "f7e3753c-4df9-43fe-9c32-0d11c511308c",
                  "d10e1118-4d6c-4d3c-a9a8-1307a2931a32",
                  "6f7a2ebd-bd88-44b7-b146-c552ac4e40cb"]:
        get_model(apps=apps, model_name="MicroServiceChainLinkExitCode")\
            .objects.filter(id=uuid_).delete()

    # Remove MicroServiceChainLinks
    for uuid_ in ["9ec31d55-f053-4695-b86d-8c2a8abdb0fc",
                  "213fe743-f170-4695-8b3e-77886a31a89d",
                  "364ac694-6440-4e45-8b2a-d3715c524970",
                  "e942d973-9db1-46bf-afdd-2827c22223d0",
                  "246943e4-d203-48e1-ac84-4865520e7c30",
                  "fdb12ea6-22aa-46c8-a591-a2bcf5d42e5e",
                  "0af6b163-5455-4a76-978b-e35cc9ee445f",
                  "fba1fd92-150a-4969-84fb-f2c6097855cf",
                  "ec3c965c-c056-47e3-a551-ad1966e00824",
                  "f0ff25d8-528b-426c-9229-689196b5d312",
                  "527bff64-7b96-4285-8715-9e36285f9380"]:
        get_model(apps, 'MicroServiceChainLink').objects.filter(
            id=uuid_).delete()

    # Remove MicroServiceChain Choices
    for uuid_ in ["dc9b59b3-dd5f-4cd6-8e97-ee1d83734c4c",
                  "77bb4993-9f5b-4e60-bbe9-0039a6f5934e"]:
        get_model(apps, 'MicroServiceChainChoice').objects.filter(
            id=uuid_).delete()

    # Remove Standard Task Configurations
    for uuid_ in ["286b4b17-d382-48eb-bdbe-ca3b2a32568b",
                  "ed3cda67-94b6-457e-9d00-c58f413dbfce",
                  "58988b82-7b65-40f3-94a7-f2f3e13b8700"]:
        get_model(apps=apps, model_name="StandardTaskConfig").objects.filter(
            id=uuid_).delete()

    # Remove Task Configurations
    for uuid_ in ["2b2042d4-548f-4c63-a394-bf14b5faa5d1",
                  "7d1872fc-d90e-4354-a5c9-97d24bbdf629",
                  "a6b1efde-ddf1-492a-8eb4-0c556657bd38",
                  "ab6c6e52-10c5-449e-ae92-89cf7903e6bc",
                  "7eade269-0bc3-4a6a-9801-e8e4d8babb55",
                  "477bc37e-b6a7-440a-9088-85672b3b38a7",
                  "4d36c35a-0829-4b2d-ba3d-0a30a3e837f9",
                  "e593507e-f4bf-4346-8652-32a832524782",
                  "355c22ae-ba5b-408b-a9b6-a01372d158b5",
                  "3180b1eb-f9a3-4667-bc92-639bd51b75ae",
                  "8f785c2e-aa48-48f4-a0ef-b08e208a9d95"]:
        get_model(apps, 'TaskConfig').objects.filter(
            id=uuid_).delete()

    # Remove Set Unit Variables
    for uuid_ in ['3fcc6e42-0117-4786-9cd4-e773f6f71296',
                  'f5908626-38be-4c2b-9c09-a389585e9f6c']:
        get_model(apps, 'TaskConfigSetUnitVariable').objects.filter(
            id=uuid_).delete()

    # Remove Variable Link Pulls
    for uuid_ in ['5b11c0a9-6f62-4d7e-ad48-2905e75ff419',
                  '6f7a2ebd-bd88-44b7-b146-c552ac4e40cb',
                  "a0483e03-f2c6-40a0-aa71-0e39f22f0aeb",
                  "6a141385-ac1e-40d5-9923-d776b2d8b997"]:
        get_model(apps, 'TaskConfigUnitVariableLinkPull').objects.filter(
            id=uuid_).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0059_siparrange_longblob'),
    ]

    operations = [
        migrations.RunPython(data_migration_up, data_migration_down),
    ]
