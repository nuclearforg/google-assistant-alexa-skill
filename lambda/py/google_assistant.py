# -*- coding: utf-8 -*-
import logging

from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response, Request

import grpc
from google.assistant.embedded.v1alpha2 import embedded_assistant_pb2_grpc, embedded_assistant_pb2
from google.assistant.embedded.v1alpha2.embedded_assistant_pb2 import AssistRequest
from google.auth.transport.grpc import secure_authorized_channel

from tenacity import retry, stop_after_attempt, retry_if_exception

from alexa import data, util


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


_END_OF_UTTERANCE = embedded_assistant_pb2.AssistResponse.END_OF_UTTERANCE
_DIALOG_FOLLOW_ON = embedded_assistant_pb2.DialogStateOut.DIALOG_FOLLOW_ON
_CLOSE_MICROPHONE = embedded_assistant_pb2.DialogStateOut.CLOSE_MICROPHONE


def is_grpc_error_unavailable(e) -> bool:
    is_grpc_error = isinstance(e, grpc.RpcError)
    if is_grpc_error and (e.code() == grpc.StatusCode.UNAVAILABLE):
        _logger.error('gRPC unavailable error: %s', e)
        return True
    return False


# This generator yields AssistResponse proto messages
# received from the gRPC Google Assistant API.
def iter_assist_requests(handler_input: HandlerInput, text_query: str) -> AssistRequest:
    """Yields: AssistRequest messages to send to the API."""

    model_id = data.GOOGLE_ASSISTANT_API['model_id']
    device_id = util.get_device_id(handler_input)

    # TODO: hardcoded locale?
    language_code = 'it-IT'

    # TODO: hardcoded default volume?
    volume = util.get_persistent_attribute(handler_input, 'volume', default=50)

    conversation_state = util.get_session_attribute(handler_input, 'conversation_state')  # type: list
    conversation_state = bytes(conversation_state) if conversation_state is not None else None
    is_new_conversation = conversation_state is None

    config = embedded_assistant_pb2.AssistConfig(
        audio_out_config=embedded_assistant_pb2.AudioOutConfig(
            encoding='LINEAR16',
            sample_rate_hertz=data.DEFAULT_AUDIO_SAMPLE_RATE,
            volume_percentage=volume,
        ),
        dialog_state_in=embedded_assistant_pb2.DialogStateIn(
            language_code=language_code,
            conversation_state=conversation_state,
            is_new_conversation=is_new_conversation,
        ),
        device_config=embedded_assistant_pb2.DeviceConfig(
            device_id=device_id,
            device_model_id=model_id,
        ),
        text_query=text_query
    )
    # Continue current conversation with later requests.
    req = embedded_assistant_pb2.AssistRequest(config=config)
    yield req


@retry(reraise=True, stop=stop_after_attempt(3), retry=retry_if_exception(is_grpc_error_unavailable))
def assist(handler_input: HandlerInput, text_query: str) -> Response:
    _logger.info('Input to be processed is: %s', text_query)

    api_endpoint = data.GOOGLE_ASSISTANT_API['api_endpoint']
    deadline_sec = data.DEFAULT_GRPC_DEADLINE

    # Create an authorized gRPC channel.
    credentials = util.get_credentials(handler_input)
    http_request = Request()
    grpc_channel = secure_authorized_channel(credentials, http_request, api_endpoint)
    _logger.info('Connecting to %s', api_endpoint)

    # Create Assistant stub
    assistant = embedded_assistant_pb2_grpc.EmbeddedAssistantStub(grpc_channel)

    # TODO: record Assistant's response
    # self._fp = open(OUTPUT_AUDIO_FILE, 'wb')
    # self._wave = wave.open(self._fp, 'wb')
    # self._wave.setsampwidth(DEFAULT_AUDIO_SAMPLE_WIDTH)
    # self._wave.setnchannels(1)
    # self._wave.setframerate(DEFAULT_AUDIO_SAMPLE_RATE)

    text_response = None
    mic_open = False

    # TODO: hardcoded default volume?
    volume = util.get_persistent_attribute(handler_input, 'volume', default=50)

    # TODO: should refactor this?
    for resp in assistant.Assist(iter_assist_requests(handler_input, text_query), deadline_sec):
        if len(resp.audio_out.audio_data) > 0:
            _logger.info('Playing assistant response.')
            buf = resp.audio_out.audio_data
            buf = util.align_buf(buf, data.DEFAULT_AUDIO_SAMPLE_WIDTH)
            buf = util.normalize_audio_buffer(buf, volume)
            # TODO: record Assistant's response
            # self._wave.writeframes(buf)
        if resp.dialog_state_out.conversation_state:
            conversation_state = resp.dialog_state_out.conversation_state
            conversation_state = list(conversation_state) if conversation_state is not None else None
            _logger.debug('Updating conversation state.')
            util.set_session_attribute(handler_input, 'conversation_state', conversation_state)
        if resp.dialog_state_out.volume_percentage != 0:
            volume_percentage = resp.dialog_state_out.volume_percentage
            _logger.info('Setting volume to %s%%', volume_percentage)
            util.set_persistent_attribute(handler_input, 'volume', volume_percentage, save=True)
        if resp.dialog_state_out.microphone_mode == _DIALOG_FOLLOW_ON:
            mic_open = True
            _logger.info('Expecting follow-on query from user.')
        elif resp.dialog_state_out.microphone_mode == _CLOSE_MICROPHONE:
            mic_open = False
        if resp.dialog_state_out.supplemental_display_text:
            text_response = resp.dialog_state_out.supplemental_display_text
            _logger.info('Supplemental display text: %s', text_response)

    _logger.info('Finished playing assistant response.')

    # TODO: info on audio file, error if response is empty
    # self._wave.close()
    # self._fp.close()

    return handler_input.response_builder.speak(text_response).set_should_end_session(not mic_open).response
