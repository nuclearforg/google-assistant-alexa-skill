# -*- coding: utf-8 -*-
# Copyright 2018 Francesco Circhetta
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
import hashlib
import logging

from ask_sdk_core.handler_input import HandlerInput

from google.oauth2.credentials import Credentials


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


def get_credentials(handler_input: HandlerInput) -> Credentials:
    access_token = handler_input.request_envelope.context.system.user.access_token

    # TODO: a more meaningful exception should be thrown, so that we can return a LinkAccount card to the user
    if not access_token:
        _logger.info('User must link his Google Account')
        raise Exception

        # handler_input.response_builder.set_card(LinkAccountCard()).speak(WARNING_LINK_ACCOUNT)
        # return handler_input.response_builder.response

    # Return credentials
    return Credentials(access_token)


def get_device_id(handler_input: HandlerInput) -> str:
    user_id = handler_input.request_envelope.context.system.user.user_id
    h = hashlib.new('ripemd160')
    h.update(user_id.encode('utf-8'))
    return h.hexdigest()


def get_persistent_attribute(handler_input: HandlerInput, key: str, default: object=None) -> object:
    attr = handler_input.attributes_manager.persistent_attributes
    return attr.get(key, default)


def set_persistent_attribute(handler_input: HandlerInput, key: str, value: object, save: bool = False) -> None:
    _logger.debug('Writing into persistent attribute "%s"...', key)

    attr = handler_input.attributes_manager.persistent_attributes
    attr[key] = value
    handler_input.attributes_manager.persistent_attributes = attr

    if save:
        _logger.info('Saving persistent attributes...')
        handler_input.attributes_manager.save_persistent_attributes()


def get_session_attribute(handler_input: HandlerInput, key: str, default: object=None) -> object:
    attr = handler_input.attributes_manager.session_attributes
    return attr.get(key, default)


def set_session_attribute(handler_input: HandlerInput, key: str, value: object) -> None:
    attr = handler_input.attributes_manager.session_attributes
    attr[key] = value
    handler_input.attributes_manager.session_attributes = attr
