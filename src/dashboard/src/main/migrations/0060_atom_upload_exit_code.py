# -*- coding: utf-8 -*-
"""Migration to ensure that a job associated to the ``Choose config for AtoM
DIP upload`` link is marked as completed successfully when the exit code is
``0``.
"""
from __future__ import unicode_literals

from django.db import migrations

# Can't use apps.get_model for this model as we need to access class attributes.
from main.models import Job


ATOM_DIP_UPLOAD_CONFIG_EXIT_CODE_ZERO = 'c9e90d83-533f-44c3-8220-083a6eb91751'


def data_migration_up(apps, schema_editor):
    """Fix ``MicroServiceChainLinkExitCode.exitmessage``.

    In ``Choose config for AtoM DIP upload`` the value in ``exitmessage`` is
    a string (``Completed successfully``) instead of its corresponding Job
    status ID (``Job.STATUS_COMPLETED_SUCCESSFULLY``).
    """
    MicroServiceChainLinkExitCode = apps.get_model(
        'main', 'MicroServiceChainLinkExitCode')

    MicroServiceChainLinkExitCode.objects.filter(
        id=ATOM_DIP_UPLOAD_CONFIG_EXIT_CODE_ZERO).update(
            exitmessage=Job.STATUS_COMPLETED_SUCCESSFULLY)


def data_migration_down(apps, schema_editor):
    MicroServiceChainLinkExitCode = apps.get_model(
        'main', 'MicroServiceChainLinkExitCode')

    MicroServiceChainLinkExitCode.objects.filter(
        id=ATOM_DIP_UPLOAD_CONFIG_EXIT_CODE_ZERO).update(
            exitmessage='Completed successfully')


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0059_siparrange_longblob'),
    ]

    operations = [
        migrations.RunPython(data_migration_up, data_migration_down),
    ]
