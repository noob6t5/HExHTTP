#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import argparse
import traceback
import sys, os, re
import time
from urllib.parse import urlparse

from modules.check_localhost import check_localhost
from modules.server_error import get_server_error
from modules.methods import check_methods
from modules.CPDoS import check_CPDoS
from modules.technologies import technology
from modules.cdn import analyze_cdn
from modules.cache_poisoning_files import check_cache_files
from modules.cookie_reflection import check_cookie_reflection
from modules.http_version import check_http_version
from modules.range_check import range_error_check
from modules.vhosts import check_vhost

from tools.autopoisoner.autopoisoner import check_cache_poisoning


requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)


def get_technos(a_tech, req_main, url, s):
    """
    Check what is the reverse proxy/waf/cached server... and test based on the result
    #TODO
    """
    print("\033[36m ├ Techno analyse\033[0m")
    technos = {
    "apache": ["Apache", "apache"],
    "nginx": ["nginx"],
    "envoy": ["envoy"],
    "akamai": ["Akamai", "X-Akamai","X-Akamai-Transformed", "AkamaiGHost"],
    "imperva": ["imperva", "Imperva"],
    "fastly": ["fastly", "Fastly"]
    }

    for t in technos:
        tech_hit = False
        for v in technos[t]:
            for rt in req_main.headers:
                if v in req_main.text or v in req_main.headers[rt] or v in rt:
                    tech_hit = t
        if tech_hit:
            techno_result = getattr(a_tech, tech_hit)(url, s)
            tech_it = False


def bf_hidden_header(url):
    """
    Check if hidden header used by website
    (https://webtechsurvey.com/common-response-headers)
    #TODO
    """
    print("")


def fuzz_x_header(url):
    """
    When fuzzing for custom X-Headers on a target, a setup example as below can be combined with a dictionary/bruteforce attack. This makes it possible to extract hidden headers that the target uses. 
        X-Forwarded-{FUZZ}
        X-Original-{FUZZ}
        X-{COMPANY_NAME}-{FUZZ}
    (https://blog.yeswehack.com/yeswerhackers/http-header-exploitation/)
    #TODO
    """
    print("\033[36m ├ X-FUZZ analyse\033[0m")
    f_header = {"Forwarded":"for=example.com;host=example.com;proto=https, for=example.com"}
    try:
        req_f = requests.get(url, headers=f_header, timeout=10, verify=False)
        if req_f.status_code == 500:
            print(" └──  Header {} return 500 error".format(f_header))
    except:
        pass


def check_cache_header(url, req_main):
    print("\033[36m ├ Header cache\033[0m")
    #basic_header = ["Content-Type", "Content-Length", "Date", "Content-Security-Policy", "Alt-Svc", "Etag", "Referrer-Policy", "X-Dns-Prefetch-Control", "X-Permitted-Cross-Domain-Policies"]

    result = []
    for headi in base_header:
        if "cache" in headi or "Cache" in headi:
            result.append("{}:{}".format(headi.split(":")[0], headi.split(":")[1]))
    for vary in base_header:
        if "Vary" in vary:
            result.append("{}:{}".format(vary.split(":")[0], vary.split(":")[1]))
    for age in base_header:
        if age == "age" or age == "Age":
            result.append("{}:{}".format(age.split(":")[0], age.split(":")[1]))
    for get_custom_header in base_header:
        if "Access" in get_custom_header:
            result.append("{}:{}".format(get_custom_header.split(":")[0], get_custom_header.split(":")[1]))
    for get_custom_host in base_header:
        if "host" in get_custom_header:
            result.append("{}:{}".format(get_custom_host.split(":")[0], get_custom_host.split(":")[1]))
    for r in result:
        print(' └──  {cho:<30}'.format(cho=r))



def main(url, s):
    global base_header
    base_header = []

    a_cdn = analyze_cdn()
    a_tech = technology()

    req_main = s.get(url, verify=False, allow_redirects=False, timeout=10, auth=authent)
    
    print("\033[34m⟙\033[0m")
    print(" URL: {}".format(url))
    print(" URL response: {}".format(req_main.status_code))
    print(" URL response size: {} bytes".format(len(req_main.content)))
    print("\033[34m⟘\033[0m")
    if req_main.status_code not in [200, 302, 301, 403, 401] and not url_file:
        choice = input(" \033[33mThe url does not seem to answer correctly, continue anyway ?\033[0m [y/n]")
        if choice not in ["y", "Y"]:
            sys.exit()
    for k in req_main.headers:
        base_header.append("{}: {}".format(k, req_main.headers[k]))

    #print(base_header)

    get_server_error(url, base_header, full, authent)
    check_vhost(domain, url)
    check_localhost(url, s, domain, authent)
    check_methods(url, custom_header, authent)
    check_http_version(url)
    check_CPDoS(url, s, req_main, domain, custom_header, authent)
    check_cache_poisoning(url, custom_header, behavior, authent)
    check_cache_files(url, custom_header, authent)
    check_cookie_reflection(url, custom_header, authent)
    range_error_check(url)

    cdn = a_cdn.get_cdn(req_main, url, s)
    if cdn:
        cdn_result = getattr(a_cdn, cdn)(url, s)
    techno = get_technos(a_tech, req_main, url, s)

    fuzz_x_header(url)
    check_cache_header(url, req_main)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="HExHTTP is a tool designed to perform tests on HTTP headers.")

    parser.add_argument("-u", "--url", dest='url', help="URL to test \033[31m[required]\033[0m")
    parser.add_argument("-f", "--file", dest='url_file', help="File of URLs", required=False)
    parser.add_argument("-H", "--header", dest='custom_header', help="Add a custom HTTP Header", required=False)
    parser.add_argument("-F", "--full", dest='full', help="Display the full HTTP Header", required=False, action='store_true')
    parser.add_argument("-a", "--auth", dest="auth", help="Add an HTTP authentication. \033[33mEx: --auth admin:admin\033[0m", required=False)
    parser.add_argument("-b", "--behavior", dest='behavior', help="Activates a simplified version of verbose, highlighting interesting cache behaviors", required=False, action='store_true') 

    results = parser.parse_args()
                                     
    url = results.url
    url_file = results.url_file
    full = results.full
    custom_header = results.custom_header
    behavior = results.behavior
    auth = results.auth

    if custom_header:
        custom_header = {
        custom_header.split(":")[0]:custom_header.split(":")[1]
        }


    global authent

    try: 
        if auth:
            r = requests.get(url, allow_redirects=False, verify=False, auth=(auth.split(":")[0], auth.split(":")[1]))
            if r.status_code in [200, 302, 301]:
                print("\n+ Authentification successfull\n")
                authent = (auth.split(":")[0], auth.split(":")[1])
            else:
                print("\n- Authentification error")
                continue_error = input("The authentification seems bad, continue ? [y/N]")
                if continue_error not in ["y", "Y"]:
                    print("Exiting")
                    sys.exit()
        else:
            authent = False

        s = requests.Session()
        s.headers.update({'User-agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; LCJB; rv:11.0) like Gecko'})
        s.max_redirects = 60

        if url_file:
            with open(url_file, "r") as urls:
                urls = urls.read().splitlines()
                for url in urls:
                    domain =  urlparse(url).netloc
                    try:
                        main(url, s)
                    except KeyboardInterrupt:
                        pass
                    except FileNotFoundError:
                        print("Input file not found")
                        sys.exit()
                    except Exception as e:
                        print(f"Error : {e}")
                    print("")
        else:
            domain =  urlparse(url).netloc
            main(url, s)
        # basic errors
    except KeyboardInterrupt:
        sys.exit()
    # requests errors
    except requests.ConnectionError:
        print("Error, cannot connect to target")
    except requests.Timeout:
        print("Error, request timeout (10s)")
    except requests.exceptions.MissingSchema: 
        print("Error, missing http:// or https:// schema")
    print("")
