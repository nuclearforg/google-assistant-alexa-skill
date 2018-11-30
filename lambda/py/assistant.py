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
import logging
import os
import wave
from xml.sax.saxutils import escape

from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response, Request

import boto3

import grpc
from ask_sdk_model.ui import SimpleCard
from google.assistant.embedded.v1alpha2 import embedded_assistant_pb2_grpc, embedded_assistant_pb2
from google.assistant.embedded.v1alpha2.embedded_assistant_pb2 import AssistRequest
from google.auth.transport.grpc import secure_authorized_channel

from tenacity import retry, stop_after_attempt, retry_if_exception

import audio_helpers
import skill_helpers
import data

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


_END_OF_UTTERANCE = embedded_assistant_pb2.AssistResponse.END_OF_UTTERANCE
_DIALOG_FOLLOW_ON = embedded_assistant_pb2.DialogStateOut.DIALOG_FOLLOW_ON
_CLOSE_MICROPHONE = embedded_assistant_pb2.DialogStateOut.CLOSE_MICROPHONE

# Get the service client.
_s3 = boto3.client('s3')


def _is_grpc_error_unavailable(e) -> bool:
    is_grpc_error = isinstance(e, grpc.RpcError)
    if is_grpc_error and (e.code() == grpc.StatusCode.UNAVAILABLE):
        _logger.error('gRPC unavailable error: %s', e)
        return True
    return False


# This generator yields AssistResponse proto messages
# received from the gRPC Google Assistant API.
def _iter_assist_requests(handler_input: HandlerInput, text_query: str) -> AssistRequest:
    """Yields: AssistRequest messages to send to the API."""

    model_id = data.GOOGLE_ASSISTANT_API['model_id']
    device_id = skill_helpers.get_device_id(handler_input)

    locale = getattr(handler_input.request_envelope.request, 'locale', 'en-US')

    conversation_state = skill_helpers.get_session_attribute(handler_input, 'conversation_state')  # type: list
    is_new_conversation = conversation_state is None
    blob = bytes(conversation_state) if not is_new_conversation else None

    config = embedded_assistant_pb2.AssistConfig(
        audio_out_config=embedded_assistant_pb2.AudioOutConfig(
            encoding='LINEAR16',
            sample_rate_hertz=data.DEFAULT_AUDIO_SAMPLE_RATE,
            volume_percentage=100,
        ),
        dialog_state_in=embedded_assistant_pb2.DialogStateIn(
            language_code=locale,
            conversation_state=blob,
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


@retry(reraise=True, stop=stop_after_attempt(3), retry=retry_if_exception(_is_grpc_error_unavailable))
def assist(handler_input: HandlerInput, text_query: str) -> Response:
    _logger.info('Input to be processed is: %s', text_query)

    # Get constants
    api_endpoint = data.GOOGLE_ASSISTANT_API['api_endpoint']
    deadline_sec = data.DEFAULT_GRPC_DEADLINE

    # Create an authorized gRPC channel.
    credentials = skill_helpers.get_credentials(handler_input)
    http_request = Request()
    grpc_channel = secure_authorized_channel(credentials, http_request, api_endpoint)
    _logger.info('Connecting to %s', api_endpoint)

    # Create Assistant stub
    assistant = embedded_assistant_pb2_grpc.EmbeddedAssistantStub(grpc_channel)

    # Initial state
    text_response = None
    mic_open = False

    # Open the response PCM file in which we are going to stream Assistant's response
    fp = open(data.RESPONSE_PCM_FILE, 'wb')

    # Init WAVE file parser
    wavep = wave.open(fp, 'wb')
    wavep.setsampwidth(data.DEFAULT_AUDIO_SAMPLE_WIDTH)
    wavep.setnchannels(1)
    wavep.setframerate(data.DEFAULT_AUDIO_SAMPLE_RATE)

    # The magic happens
    for resp in assistant.Assist(_iter_assist_requests(handler_input, text_query), deadline_sec):
        if len(resp.audio_out.audio_data) > 0:
            _logger.info('Playing assistant response.')
            buf = resp.audio_out.audio_data
            buf = audio_helpers.align_buf(buf, data.DEFAULT_AUDIO_SAMPLE_WIDTH)
            wavep.writeframes(buf)
        if resp.dialog_state_out.conversation_state:
            conversation_state = resp.dialog_state_out.conversation_state
            conversation_state = list(conversation_state) if conversation_state is not None else None
            _logger.debug('Updating conversation state.')
            skill_helpers.set_session_attribute(handler_input, 'conversation_state', conversation_state)
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
    wavep.close()
    fp.close()

    # Encode Assistant's response in an MP3 we can stream to Alexa
    audio_helpers.encode_from_pcm_to_mp3(data.RESPONSE_PCM_FILE, data.RESPONSE_MP3_FILE)

    # S3 bucket
    bucket = os.environ['S3_BUCKET']
    key = skill_helpers.get_device_id(handler_input)

    # Upload the response MP3 to the bucket
    _s3.upload_file(data.RESPONSE_MP3_FILE, Bucket=bucket, Key=key)

    # Generate a short-lived signed url to the MP3
    params = {
            'Bucket': bucket,
            'Key': key
    }
    url = _s3.generate_presigned_url(ClientMethod='get_object', Params=params, ExpiresIn=10)
    url = escape(url)

    # Create Alexa response
    response_builder = handler_input.response_builder
    response_builder.speak(f'<audio src="{url}"/>')
    if text_response:
        response_builder.set_card(SimpleCard(title='Google Assistant', content=text_response))
    response_builder.set_should_end_session(not mic_open)

    return response_builder.response
