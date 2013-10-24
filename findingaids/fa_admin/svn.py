# file findingaids/fa_admin/svn.py
#
#   Copyright 2013 Emory University Library
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


# utility code for accessing/updating EAD content in subversion

import subvertpy
from subvertpy import client, ra
from django.conf import settings

def svn_client():
    # note: client only works for local path

    # create an auth with stock svn providers
    auth = ra.Auth([
        ra.get_simple_provider(),
        ra.get_username_provider(),
        ra.get_ssl_client_cert_file_provider(),
        ra.get_ssl_client_cert_pw_file_provider(),
        ra.get_ssl_server_trust_file_provider(),
    ])
    auth.set_parameter(subvertpy.AUTH_PARAM_DEFAULT_USERNAME,
        settings.SVN_USERNAME)
    auth.set_parameter(subvertpy.AUTH_PARAM_DEFAULT_PASSWORD,
        settings.SVN_PASSWORD)

    return client.Client(auth=auth)


def svn_remote(url):
    # note: client only works for local path

    # create an auth with stock svn providers
    auth = ra.Auth([
        ra.get_simple_provider(),
        ra.get_username_provider(),
        ra.get_ssl_client_cert_file_provider(),
        ra.get_ssl_client_cert_pw_file_provider(),
        ra.get_ssl_server_trust_file_provider(),
    ])
    auth.set_parameter(subvertpy.AUTH_PARAM_DEFAULT_USERNAME,
        settings.SVN_USERNAME)
    auth.set_parameter(subvertpy.AUTH_PARAM_DEFAULT_PASSWORD,
        settings.SVN_PASSWORD)

    return ra.RemoteAccess(url, auth=auth)
