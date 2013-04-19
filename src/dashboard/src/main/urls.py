# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.

from django.conf.urls.defaults import *
from django.conf import settings
from django.views.generic.simple import direct_to_template, redirect_to

urlpatterns = patterns('main.views',

    # Index
    (r'^$', 'home'),

    # Forbidden
    (r'forbidden/$', 'forbidden'),

    # Jobs and tasks (is part of ingest)
    (r'jobs/(?P<uuid>' + settings.UUID_REGEX + ')/explore/$', 'jobs_explore'),
    (r'jobs/(?P<uuid>' + settings.UUID_REGEX + ')/list-objects/$', 'jobs_list_objects'),
    (r'tasks/(?P<uuid>' + settings.UUID_REGEX + ')/$', 'tasks'),
    (r'task/(?P<uuid>' + settings.UUID_REGEX + ')/$', 'task'),

    # Access
    (r'access/$', 'access_list'),
    (r'access/(?P<id>\d+)/delete/$', 'access_delete'),

    # Lookup
#    (r'lookup/rightsholder/(?P<id>\d+)/$', 'rights_holders_lookup'),

    # Autocomplete
#    (r'autocomplete/rightsholders$', 'rights_holders_autocomplete'),

    # Disabled until further development can be done
    #(r'administration/search/$', 'administration_search'),
    #(r'administration/search/flush/aips/$', 'administration_search_flush_aips'),

    # JSON feeds
    (r'status/$', 'status'),
    (r'formdata/(?P<type>\w+)/(?P<parent_id>\d+)/(?P<delete_id>\d+)/$', 'formdata_delete'),
    (r'formdata/(?P<type>\w+)/(?P<parent_id>\d+)/$', 'formdata'),
)
