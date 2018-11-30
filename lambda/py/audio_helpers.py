# -*- coding: utf-8 -*-
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
