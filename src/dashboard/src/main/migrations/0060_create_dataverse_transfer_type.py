# -*- coding: utf-8 -*-
"""Migration to create a Dataverse Transfer Type.

This migration introduces a new transfer type for Dataverse,
https://dataverse.org/ datasets.

The migration also introduces two new microservices:

* Convert Dataverse Structure
* Parse Dataverse METS

In order to do that, the transfer workflow requires two signals in the form
of unit variables to read from when the new microservice tasks need to be
performed.

Once the tasks have completed, the workflow is picked up from where it would
normally for a standard transfer type.
"""

from __future__ import unicode_literals

from django.db import migrations

# We can't use apps.get_model for this model as we need to access class
# attributes.
from main.models import Job

DEFAULT_NEXT_MS = "61c316a6-0a50-4f65-8767-1f44b1eeb6dd"


def create_variable_link_pull(
        apps, link_uuid, variable, default_ms_uuid=None):
    """Create a new variable link pull in the database."""
    apps.get_model("main", model_name="TaskConfigUnitVariableLinkPull") \
        .objects.create(
        id=link_uuid,
        variable=variable,
        defaultmicroservicechainlink_id=default_ms_uuid,
    )


def create_set_unit_variable(
        apps, var_uuid, variable_name, variable_value=None, ms_uuid=None):
    """Create a new unit variable in the database."""
    apps.get_model("main", model_name="TaskConfigSetUnitVariable") \
        .objects.create(
        id=var_uuid,
        variable=variable_name,
        variablevalue=variable_value,
        microservicechainlink_id=ms_uuid,
    )


def create_standard_task_config(apps, task_uuid, execute_string, args):
    """Create a task configuration, inc. the command and args and write to the
    database.
    """
    apps.get_model("main", model_name="StandardTaskConfig").objects.create(
        id=task_uuid, execute=execute_string, arguments=args,
    )


def create_task(
        apps, task_type_uuid, task_uuid, task_desc, task_config=None):
    """Create a new task configuration entry in the database."""
    apps.get_model("main", model_name='TaskConfig').objects.create(
        id=task_uuid, description=task_desc, tasktype_id=task_type_uuid,
        tasktypepkreference=task_config,
    )


def create_ms_chain_link(
        apps, ms_uuid, group, task_uuid, ms_exit_message=Job.STATUS_FAILED,
        default_next_link=DEFAULT_NEXT_MS):
    """Create a microservice chainlink in the database."""
    apps.get_model("main", model_name="MicroServiceChainLink").objects.create(
        id=ms_uuid,
        microservicegroup=group,
        defaultexitmessage=ms_exit_message,
        currenttask_id=task_uuid,
        defaultnextchainlink_id=default_next_link,
    )


def create_ms_chain(apps, chain_uuid, ms_uuid, chain_description):
    """Create a new chain in the database."""
    apps.get_model("main", model_name="MicroServiceChain").objects.create(
        id=chain_uuid,
        startinglink_id=ms_uuid,
        description=chain_description,
    )


def create_ms_choice(apps, choice_uuid, chain_uuid, link_uuid):
    """Create a choice in the database."""
    apps.get_model('main', model_name='MicroServiceChainChoice').objects.create(
        id=choice_uuid,
        chainavailable_id=chain_uuid,
        choiceavailableatlink_id=link_uuid,
    )


def create_watched_dir(
        apps, watched_uuid, dir_path, expected_type, chain_uuid):
    """Create a new watched directory in the database."""
    apps.get_model('main', model_name="WatchedDirectory").objects.create(
        id=watched_uuid, watched_directory_path=dir_path,
        expected_type_id=expected_type, chain_id=chain_uuid,
    )


def create_ms_exit_codes(
        apps, exit_code_uuid, ms_in, ms_out,
        ms_exit_message=Job.STATUS_COMPLETED_SUCCESSFULLY, update=False):
    """Create an exit code entry in the database."""
    if not update:
        apps.get_model("main", model_name="MicroServiceChainLinkExitCode") \
            .objects.create(
            id=exit_code_uuid,
            microservicechainlink_id=ms_in,
            nextmicroservicechainlink_id=ms_out,
            exitmessage=ms_exit_message,
        )
        return
    apps.get_model("main", "MicroServiceChainLinkExitCode").objects\
        .filter(id=exit_code_uuid)\
        .update(nextmicroservicechainlink_id=ms_out)


def create_parse_dataverse_mets_link_pull(apps):
    """Enable Archivematica to detect that it needs to run the 'Parse Dataverse
    METS' microservice given a Dataverse transfer type.
    """

    # 355c22ae (Determine Parse Dataverse METS XML) task to associate with
    # a MicroServiceChainLink.
    create_task(
        apps=apps, task_type_uuid="c42184a3-1a7f-4c4d-b380-15d8d97fdd11",
        task_uuid="355c22ae-ba5b-408b-a9b6-a01372d158b5",
        task_desc="Determine Parse Dataverse METS XML",
        task_config="6f7a2ebd-bd88-44b7-b146-c552ac4e40cb"
    )

    # ec3c965c (Determine Parse Dataverse METS XML).
    create_ms_chain_link(
        apps=apps, ms_uuid="ec3c965c-c056-47e3-a551-ad1966e00824",
        group="Parse External Files",
        task_uuid="355c22ae-ba5b-408b-a9b6-a01372d158b5",
        ms_exit_message=Job.STATUS_COMPLETED_SUCCESSFULLY,)

    # If linkToParseDataverseMETS is set then goto the configured microservice,
    # else, goto the default microservice.
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
    # ec3c965c (Determine Parse Dataverse METS XML)
    # db99ab43 (Create transfer metadata XML)
    create_ms_exit_codes(
        apps=apps, exit_code_uuid="6f7a2ebd-bd88-44b7-b146-c552ac4e40cb",
        ms_in="ec3c965c-c056-47e3-a551-ad1966e00824",
        ms_out="db99ab43-04d7-44ab-89ec-e09d7bbdc39d",)


def create_convert_dataverse_link_pull(apps):
    """Enable Archivematica to detect that it needs to run the 'Convert
    Dataverse Structure' microservice given a Dataverse transfer type.
    """

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


def create_parse_dataverse_mets_microservice(apps):
    """Create the database rows specific to the parse Dataverse METS
    microservice.
    """

    # Pointer to the parse Dataverse client script.
    create_standard_task_config(
        apps=apps, task_uuid="58988b82-7b65-40f3-94a7-f2f3e13b8700",
        execute_string="parseDataverse_v0.0",
        args="%SIPDirectory% %SIPUUID%")

    # e593507e (Parse Dataverse METS XML) task to be associated with a
    # MicroServiceChainLink.
    create_task(
        apps=apps, task_type_uuid="36b2e239-4a57-4aa5-8ebc-7a29139baca6",
        task_uuid="e593507e-f4bf-4346-8652-32a832524782",
        task_desc="Parse Dataverse METS XML",
        task_config="58988b82-7b65-40f3-94a7-f2f3e13b8700"
    )

    # fba1fd92 (Parse Dataverse METS XML) Chainlink.
    create_ms_chain_link(
        apps=apps, ms_uuid="fba1fd92-150a-4969-84fb-f2c6097855cf",
        group="Parse External Files",
        task_uuid="e593507e-f4bf-4346-8652-32a832524782")

    # Create a new link now we have broken the original.
    # fba1fd92 (Parse Dataverse METS XML) connects to:
    # db99ab43 (Create transfer metadata XML)
    create_ms_exit_codes(
        apps=apps, exit_code_uuid="d10e1118-4d6c-4d3c-a9a8-1307a2931a32",
        ms_in="fba1fd92-150a-4969-84fb-f2c6097855cf",
        ms_out="db99ab43-04d7-44ab-89ec-e09d7bbdc39d")


def create_dataverse_unit_variables_and_initial_tasks(apps):
    """Once the Dataverse transfer has started then the Archivematica
    workflow needs to know how to route itself. We set two unit variables
    here which are used later in the workflow, and we set the first Dataverse
    specific microservice to run, 'Convert Dataverse Structure'
    """

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

    # Create a MicroServiceChainLink to point to the 'Set Dataverse Transfer'
    # Create Unit Variable Task.
    create_ms_chain_link(
        apps=apps, ms_uuid="213fe743-f170-4695-8b3e-77886a31a89d",
        group="Verify transfer compliance",
        task_uuid="2b2042d4-548f-4c63-a394-bf14b5faa5d1")

    # Create a MicroServiceChainLink to point to the 'Set Parse Dataverse METS'
    # Create Unit Variable Task.
    create_ms_chain_link(
        apps=apps, ms_uuid="364ac694-6440-4e45-8b2a-d3715c524970",
        group="Verify transfer compliance",
        task_uuid="7d1872fc-d90e-4354-a5c9-97d24bbdf629")

    # Create the MicroServiceChainLinks required to ask Archivematica to
    # process a transfer as a Dataverse one.

    # Pointer to the convert Dataverse structure MCP Client script.
    create_standard_task_config(
        apps=apps, task_uuid="286b4b17-d382-48eb-bdbe-ca3b2a32568b",
        execute_string="convertDataverseStructure_v0.0",
        args="%SIPDirectory%")

    # ab6c6e52 (Convert Dataverse Structure) task to be associated with a
    # MicroServiceChainLink.
    create_task(
        apps=apps, task_type_uuid="36b2e239-4a57-4aa5-8ebc-7a29139baca6",
        task_uuid="ab6c6e52-10c5-449e-ae92-89cf7903e6bc",
        task_desc="Convert Dataverse Structure",
        task_config="286b4b17-d382-48eb-bdbe-ca3b2a32568b"
    )

    # ab6c6e52 (Convert Dataverse Structure) Chainlink.
    create_ms_chain_link(
        apps=apps, ms_uuid="9ec31d55-f053-4695-b86d-8c2a8abdb0fc",
        group="Verify transfer compliance",
        task_uuid="ab6c6e52-10c5-449e-ae92-89cf7903e6bc")

    # Create a set of unit variables to enable Archivematica to see this as a
    # Dataverse transfer and process the contents downloaded via the Storage
    # Service appropriately.
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
    # 213fe743 (Set Convert Dataverse Structure (Unit Variable))
    create_ms_exit_codes(
        apps=apps, exit_code_uuid="da46e870-290b-4fd4-8f84-194b9177d8c0",
        ms_in="0af6b163-5455-4a76-978b-e35cc9ee445f",
        ms_out="213fe743-f170-4695-8b3e-77886a31a89d",
        update=True)

    # Create a new link now we have broken the original.
    # 213fe743 (Set Convert Dataverse Structure) connects to:
    # 364ac694 (Set Parse Dataverse METS (Unit Variable))
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


def create_dataverse_transfer_type(apps):
    """Create the database rows required to create a new transfer type in
    Archivematica.
    """

    # Configuration of transfer initiation tasks.
    create_standard_task_config(
        apps=apps, task_uuid="ed3cda67-94b6-457e-9d00-c58f413dbfce",
        execute_string="archivematicaSetTransferType_v0.0",
        args="\"%SIPUUID%\" \"Dataverse\"")

    # Create tasks related to the initiation of a new Dataverse transfer.
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

    # 246943e4 (Approve Dataverse transfer)
    create_ms_chain_link(
        apps=apps, ms_uuid="246943e4-d203-48e1-ac84-4865520e7c30",
        group="Approve Dataverse transfer",
        task_uuid="477bc37e-b6a7-440a-9088-85672b3b38a7")

    # fdb12ea6 (Move to processing directory)
    create_ms_chain_link(
        apps=apps, ms_uuid="fdb12ea6-22aa-46c8-a591-a2bcf5d42e5e",
        group="Verify transfer compliance",
        task_uuid="7c02a87b-7113-4851-97cd-2cf9d3fc0010")

    # 0af6b163 (Set transfer type: Dataverse)
    create_ms_chain_link(
        apps=apps, ms_uuid="0af6b163-5455-4a76-978b-e35cc9ee445f",
        group="Verify transfer compliance",
        task_uuid="4d36c35a-0829-4b2d-ba3d-0a30a3e837f9")

    # Create chains for the initiation of Dataverse transfers.
    create_ms_chain(
        apps=apps, chain_uuid="35a26b59-dcf3-45ec-b963-ba7bfaa8304f",
        ms_uuid="246943e4-d203-48e1-ac84-4865520e7c30",
        chain_description="Dataverse Transfers in Progress")
    create_ms_chain(
        apps=apps, chain_uuid="10c00bc8-8fc2-419f-b593-cf5518695186",
        ms_uuid="fdb12ea6-22aa-46c8-a591-a2bcf5d42e5e",
        chain_description="Approve Dataverse transfer")

    # Approve Dataverse transfer
    create_ms_choice(
        apps=apps, choice_uuid="dc9b59b3-dd5f-4cd6-8e97-ee1d83734c4c",
        chain_uuid="10c00bc8-8fc2-419f-b593-cf5518695186",
        link_uuid="246943e4-d203-48e1-ac84-4865520e7c30")

    # Reject Dataverse transfer
    create_ms_choice(
        apps=apps, choice_uuid="77bb4993-9f5b-4e60-bbe9-0039a6f5934e",
        chain_uuid="1b04ec43-055c-43b7-9543-bd03c6a778ba",
        link_uuid="246943e4-d203-48e1-ac84-4865520e7c30")

    # Create a watched directory which will be where transfers can be
    # initiated.
    create_watched_dir(
        apps=apps, watched_uuid="3901db52-dd1d-4b44-9d86-4285ddc5c022",
        dir_path="%watchDirectoryPath%activeTransfers/dataverseTransfer",
        expected_type="f9a3a93b-f184-4048-8072-115ffac06b5d",
        chain_uuid="35a26b59-dcf3-45ec-b963-ba7bfaa8304f")

    # Create a new link now we have broken the original.
    # fdb12ea6 (Move to processing directory) connects to:
    # 0af6b163 (Set transfer type: Dataverse)
    create_ms_exit_codes(
        apps=apps, exit_code_uuid="f7e3753c-4df9-43fe-9c32-0d11c511308c",
        ms_in="fdb12ea6-22aa-46c8-a591-a2bcf5d42e5e",
        ms_out="0af6b163-5455-4a76-978b-e35cc9ee445f")

    # Create a new link now we have broken the original.
    # 0af6b163 (Set transfer type: Dataverse) connects to:
    # 50b67418 (Remove hidden files and directories)
    create_ms_exit_codes(
        apps=apps, exit_code_uuid="da46e870-290b-4fd4-8f84-194b9177d8c0",
        ms_in="0af6b163-5455-4a76-978b-e35cc9ee445f",
        ms_out="50b67418-cb8d-434d-acc9-4a8324e7fdd2")


def data_migration_up(apps, schema_editor):
    """Run the various groupings of migration functions for the Dataverse
    specific transfer type.
    """
    create_dataverse_transfer_type(apps)
    create_parse_dataverse_mets_microservice(apps)
    create_dataverse_unit_variables_and_initial_tasks(apps)
    create_convert_dataverse_link_pull(apps)
    create_parse_dataverse_mets_link_pull(apps)


def data_migration_down(apps, schema_editor):
    """Reverse the changes made to the database in order to create a Dataverse
    transfer type.
    """

    # Fix the originally broken chain links:
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

    # Once we've fixed the previous chains, we can delete the extraneous pieces
    # introduced by the attempt to create the transfer type here.

    # Remove WatchedDirectories
    apps.get_model("main", model_name="WatchedDirectory").objects.filter(
        id="3901db52-dd1d-4b44-9d86-4285ddc5c022").delete()

    # Remove MicroServiceChains
    for uuid_ in ['10c00bc8-8fc2-419f-b593-cf5518695186',
                  '35a26b59-dcf3-45ec-b963-ba7bfaa8304f']:
        apps.get_model("main", model_name='MicroServiceChain') \
            .objects.filter(
            id=uuid_).delete()

    # Remove MicroServiceExitCodes
    for uuid_ in ["da46e870-290b-4fd4-8f84-194b9177d8c0",
                  "4ce6a3bd-026b-4ce7-beae-809844bae289",
                  "84647820-e56a-45cc-94a1-9f74de375ba8",
                  "d515821d-b1f6-4ce9-b4e4-0503fa99c8cf",
                  "f7e3753c-4df9-43fe-9c32-0d11c511308c",
                  "d10e1118-4d6c-4d3c-a9a8-1307a2931a32",
                  "6f7a2ebd-bd88-44b7-b146-c552ac4e40cb"]:
        apps.get_model("main", model_name="MicroServiceChainLinkExitCode") \
            .objects.filter(id=uuid_).delete()

    # Remove MicroServiceChainLinks
    for uuid_ in ["9ec31d55-f053-4695-b86d-8c2a8abdb0fc",
                  "213fe743-f170-4695-8b3e-77886a31a89d",
                  "364ac694-6440-4e45-8b2a-d3715c524970",
                  "246943e4-d203-48e1-ac84-4865520e7c30",
                  "fdb12ea6-22aa-46c8-a591-a2bcf5d42e5e",
                  "0af6b163-5455-4a76-978b-e35cc9ee445f",
                  "fba1fd92-150a-4969-84fb-f2c6097855cf",
                  "ec3c965c-c056-47e3-a551-ad1966e00824"]:
        apps.get_model("main", model_name='MicroServiceChainLink').objects.filter(
            id=uuid_).delete()

    # Remove MicroServiceChain Choices
    for uuid_ in ["dc9b59b3-dd5f-4cd6-8e97-ee1d83734c4c",
                  "77bb4993-9f5b-4e60-bbe9-0039a6f5934e"]:
        apps.get_model("main", model_name='MicroServiceChainChoice').objects.filter(
            id=uuid_).delete()

    # Remove Standard Task Configurations
    for uuid_ in ["286b4b17-d382-48eb-bdbe-ca3b2a32568b",
                  "ed3cda67-94b6-457e-9d00-c58f413dbfce",
                  "58988b82-7b65-40f3-94a7-f2f3e13b8700"]:
        apps.get_model("main", model_name="StandardTaskConfig") \
            .objects.filter(id=uuid_).delete()

    # Remove Task Configurations
    for uuid_ in ["2b2042d4-548f-4c63-a394-bf14b5faa5d1",
                  "7d1872fc-d90e-4354-a5c9-97d24bbdf629",
                  "a6b1efde-ddf1-492a-8eb4-0c556657bd38",
                  "ab6c6e52-10c5-449e-ae92-89cf7903e6bc",
                  "7eade269-0bc3-4a6a-9801-e8e4d8babb55",
                  "477bc37e-b6a7-440a-9088-85672b3b38a7",
                  "4d36c35a-0829-4b2d-ba3d-0a30a3e837f9",
                  "e593507e-f4bf-4346-8652-32a832524782",
                  "355c22ae-ba5b-408b-a9b6-a01372d158b5"]:
        apps.get_model("main", model_name='TaskConfig').objects.filter(
            id=uuid_).delete()

    # Remove Set Unit Variables
    for uuid_ in ['3fcc6e42-0117-4786-9cd4-e773f6f71296',
                  'f5908626-38be-4c2b-9c09-a389585e9f6c']:
        apps.get_model("main", model_name='TaskConfigSetUnitVariable') \
            .objects.filter(id=uuid_).delete()

    # Remove Variable Link Pulls
    for uuid_ in ['5b11c0a9-6f62-4d7e-ad48-2905e75ff419',
                  '6f7a2ebd-bd88-44b7-b146-c552ac4e40cb']:
        apps.get_model("main", model_name='TaskConfigUnitVariableLinkPull') \
            .objects.filter(id=uuid_).delete()


class Migration(migrations.Migration):
    """Run the migration to create a Dataverse Transfer Type."""
    dependencies = [
        ('main', '0059_siparrange_longblob'),
    ]

    operations = [
        migrations.RunPython(data_migration_up, data_migration_down),
    ]
