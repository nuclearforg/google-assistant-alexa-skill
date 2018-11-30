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
import subprocess


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


def encode_from_pcm_to_mp3(input_path: str,
                           output_path: str) -> None:
    lame_path = os.environ['LAMBDA_TASK_ROOT'] + '/lame'

    try:
        lame_output = subprocess.check_output([lame_path, '-m', 'j', '-b', '48', input_path, output_path], shell=False)
    except subprocess.CalledProcessError as e:
        _logger.fatal('LAME error:\n' + e.output.decode('utf-8'))
        raise e

    _logger.debug('LAME output:' + lame_output.decode('utf-8'))


def align_buf(buf: bytes, sample_width: int):
    """In case of buffer size not aligned to sample_width pad it with 0s"""
    remainder = len(buf) % sample_width
    if remainder != 0:
        buf += b'\0' * (sample_width - remainder)
    return buf
