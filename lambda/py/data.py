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
from gettext import gettext as _


SKILL_NAME = 'Alexa Assistant'

ERROR_GENERIC = _('Something went wrong, try again later!!')
ERROR_REGISTRATION = _('There was an error registering the Instance with the Google API. The first time that you run '
                       'the skill, make sure that you are logged into the same Google account that created the API')
FIRST_RUN = _('REPEAT AFTER ME Welcome to the unofficial Google Assistant skill for the Amazon Echo. For other '
              'languages and local search results, please open the Google Assistant app on your phone and '
              'complete the language and address settings.')
LINK_ACCOUNT = _('You must link your Google account to use this skill. Please use the link in the Alexa app to '
                 'authorise your Google Account.')
FALLBACK = _('I\'m sorry, I don\'t understand that question!!')

HELLO = _('Hello')

GOOGLE_ASSISTANT_API = {
    'api_endpoint': 'embeddedassistant.googleapis.com',
    'project_id': 'circhioz-alexa-assistant',
    'model_id': 'alexa-assistant-skill'
}

DYNAMODB_TABLE = 'AlexaAssistantSkillSettings'

DEFAULT_GRPC_DEADLINE = 60 * 3 + 5

DEFAULT_AUDIO_SAMPLE_RATE = 16000
DEFAULT_AUDIO_SAMPLE_WIDTH = 2

DEFAULT_AUDIO_VOLUME = 50
RESPONSE_PCM_FILE = '/tmp/response.pcm'
RESPONSE_MP3_FILE = '/tmp/response.mp3'
