# -*- coding: utf-8 -*-
# Resolving gettext as _ for module loading.
# TODO: from gettext import gettext as _


SKILL_NAME = 'Alexa Assistant'

ERROR_GENERIC = ('Qualcosa è andato storto, riprova più tardi!!')
ERROR_REGISTRATION = ('Si è verificato un errore con la registrazione del dispositivo. Riprova più tardi!!')
FIRST_RUN = ('RIPETI DOPO DI ME Benvenuto nella skill non ufficiale di Assistente Google per Amazon Echo. Per '
              'modificare le impostazioni, apri l\'app di Assistente Google sul tuo smartphone.')
LINK_ACCOUNT = ('Per usare questa skill devi collegare il tuo account Google. Usa l\'app Alexa per collegare '
                 'il tuo account Amazon con il tuo account Google.')
FALLBACK = ('Scusa, non ho capito!!')

HELLO = ('Hello')

GOOGLE_ASSISTANT_API = {
    'api_endpoint': 'embeddedassistant.googleapis.com',
    'project_id': 'circhioz-alexa-assistant',
    'model_id': 'alexa-assistant-skill'
}

DYNAMODB_TABLE = 'AlexaAssistantSkillSettings'

DEFAULT_GRPC_DEADLINE = 60 * 3 + 5

DEFAULT_AUDIO_SAMPLE_RATE = 16000
DEFAULT_AUDIO_SAMPLE_WIDTH = 2
DEFAULT_AUDIO_ITER_SIZE = 3200
