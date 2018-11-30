# -*- coding: utf-8 -*-
# Copyright (C) 2018 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json

from google.auth.transport.requests import AuthorizedSession
from google.auth.transport import Response
from google.oauth2.credentials import Credentials


_DEVICE_API_URL = 'https://embeddedassistant.googleapis.com/v1alpha2'

_ERROR_MESSAGE_TEMPLATE = """Failed to register device {status} ({status_code}): {error_text}"""


class RegistrationError(Exception):
    def __init__(self, response: Response, device_model_id: str) -> None:
        super(RegistrationError, self).__init__(
              self._format_error(response, device_model_id))

    @staticmethod
    def _format_error(response: Response, device_model_id: str) -> str:
        """Prints a pretty error message for registration failures."""
        status_code = response.status_code
        error_text = response.text
        status = "ERROR"

        try:
            error_text = response.json()['error']['message']
            status = response.json()['error']['status']
        except ValueError:
            pass

        return _ERROR_MESSAGE_TEMPLATE.format(
                    status=status,
                    status_code=status_code,
                    error_text=error_text,
                    device_model_id=device_model_id)


def register_device(project_id: str,
                    credentials: Credentials,
                    device_model_id: str,
                    device_id: str,
                    device_api_url: str = _DEVICE_API_URL) -> None:
    """Register a new assistant device instance.

    Args:
       project_id(str): The project ID used to register device instance.
       credentials(google.oauth2.credentials.Credentials): The Google
                OAuth2 credentials of the user to associate the device
                instance with.
       device_model_id(str): The registered device model ID.
       device_id(str): The device ID of the new instance.
       device_api_url(str): URL of the Device API.
    """
    base_url = '/'.join([device_api_url, 'projects', project_id, 'devices'])
    device_url = '/'.join([base_url, device_id])
    session = AuthorizedSession(credentials)
    r = session.get(device_url)
    # Check if the device already is registered and if not then we try to
    # register. If any HTTP connection fails raise a RegistrationError.
    if r.status_code == 404:
        print('Registering...', end='')
        r = session.post(base_url, data=json.dumps({
            'id': device_id,
            'model_id': device_model_id,
            'client_type': 'SDK_SERVICE',
            'nickname': 'Alexa Assistant'
        }))
        if r.status_code != 200:
            raise RegistrationError(r, device_model_id)
        print('Done.\n')
    elif r.status_code != 200:
        raise RegistrationError(r, device_model_id)
