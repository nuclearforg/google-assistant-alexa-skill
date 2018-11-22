# -*- coding: utf-8 -*-
import array
import hashlib
import logging
import math

from ask_sdk_core.handler_input import HandlerInput

from google.oauth2.credentials import Credentials


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


def normalize_audio_buffer(buf: bytes, volume_percentage: int, sample_width: int=2) -> bytes:
    """Adjusts the loudness of the audio data in the given buffer.
    Volume normalization is done by scaling the amplitude of the audio
    in the buffer by a scale factor of 2^(volume_percentage/100)-1.
    For example, 50% volume scales the amplitude by a factor of 0.414,
    and 75% volume scales the amplitude by a factor of 0.681.
    For now we only sample_width 2.
    Args:
      buf: byte string containing audio data to normalize.
      volume_percentage: volume setting as an integer percentage (1-100).
      sample_width: size of a single sample in bytes.
    """
    if sample_width != 2:
        raise Exception('unsupported sample width:', sample_width)
    scale = math.pow(2, 1.0*volume_percentage/100)-1
    # Construct array from bytes based on sample_width, multiply by scale
    # and convert it back to bytes
    arr = array.array('h', buf)
    for idx in range(0, len(arr)):
        arr[idx] = int(arr[idx]*scale)
    buf = arr.tostring()
    return buf


def align_buf(buf: bytes, sample_width: bytes):
    """In case of buffer size not aligned to sample_width pad it with 0s"""
    remainder = len(buf) % sample_width
    if remainder != 0:
        buf += b'\0' * (sample_width - remainder)
    return buf


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
    amazon_device_id = handler_input.request_envelope.context.system.device.device_id
    return hashlib.md5(amazon_device_id.encode('utf-8')).hexdigest()


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
    attr = handler_input.attributes_manager.persistent_attributes
    attr[key] = value
    handler_input.attributes_manager.session_attributes = attr
