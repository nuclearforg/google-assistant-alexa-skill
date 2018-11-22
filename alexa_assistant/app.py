# -*- coding: utf-8 -*-
"""Unofficial Google Assistant skill for the Amazon Echo."""
import logging
from functools import wraps
from typing import Callable

from ask_sdk_core.handler_input import HandlerInput
from ask_sdk.standard import StandardSkillBuilder
from ask_sdk_core.utils import is_intent_name, is_request_type
from ask_sdk_model import Response

import google_assistant
from alexa import data, util
from alexa.device_helpers import register_device, RegistrationError


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)

_sb = StandardSkillBuilder(table_name=data.DYNAMODB_TABLE, auto_create_table=True)


def preflight_check(f: Callable) -> Callable:
    @wraps(f)
    def decorated_function(handler_input: HandlerInput) -> Response:
        _logger.info('Pre-flight check')

        # Obtain credentials
        credentials = util.get_credentials(handler_input)

        # Obtain the deviceId
        device_id = util.get_device_id(handler_input)
        last_device_id = util.get_persistent_attribute(handler_input, 'device_id')

        project_id = data.GOOGLE_ASSISTANT_API['project_id']
        model_id = data.GOOGLE_ASSISTANT_API['model_id']

        # Re-register if "device_id" is different from the last "device_id":
        if device_id != last_device_id:
            _logger.info('Trying to register device...')
            try:
                register_device(project_id, credentials, model_id, device_id)
            except RegistrationError as e:
                _logger.error('Error in device registration: %s', e)
                handler_input.response_builder.speak(data.ERROR_REGISTRATION)
                return handler_input.response_builder.response

            _logger.info('Device was registered successfully')

            util.set_persistent_attribute(handler_input, 'device_id', device_id, save=True)
            _logger.info('New device_id was saved into persistent storage')

        return f(handler_input)

    return decorated_function


@_sb.request_handler(can_handle_func=is_request_type("LaunchRequest"))
@preflight_check
def launch_request_handler(handler_input: HandlerInput) -> Response:
    """Handler for Skill Launch."""
    _logger.info('LaunchRequest')

    return google_assistant.assist(handler_input, data.HELLO)


@_sb.request_handler(can_handle_func=is_intent_name("SearchIntent"))
@preflight_check
def search_intent_handler(handler_input: HandlerInput) -> Response:
    """Handler for Search Intent."""
    _logger.info('SearchIntent')

    alexa_utterance = handler_input.request_envelope.request.intent.slots['search'].value
    return google_assistant.assist(handler_input, alexa_utterance)


@_sb.request_handler(can_handle_func=is_request_type("SessionEndedRequest"))
def session_ended_request_handler(handler_input: HandlerInput) -> Response:
    """Handler for Session End."""
    _logger.info('Session ended with reason: %s', handler_input.request_envelope.request.reason)
    return handler_input.response_builder.response


@_sb.request_handler(can_handle_func=lambda i: True)
def unhandled_intent_handler(handler_input: HandlerInput) -> Response:
    """Handler for all other unhandled requests."""
    _logger.debug(handler_input.request_envelope.request)
    handler_input.response_builder.speak(data.FALLBACK)
    return handler_input.response_builder.response


@_sb.exception_handler(can_handle_func=lambda i, e: True)
def all_exception_handler(handler_input: HandlerInput, exception: Exception) -> Response:
    """Catch all exception handler, log exception and
    respond with custom message.
    """
    _logger.error(exception, exc_info=True)
    handler_input.response_builder.speak(data.ERROR_GENERIC)
    return handler_input.response_builder.response


@_sb.global_response_interceptor()
def log_response(_: HandlerInput, response: Response) -> None:
    """Response logger."""
    _logger.info("Response: {}".format(response))


_logger.info('Loading Alexa Assistant...')

# Handler name that is used on AWS lambda
lambda_handler = _sb.lambda_handler()
