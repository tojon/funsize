#!/usr/bin/env python

import os
import logging
import argparse
import json
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                "/home/worker/tools/lib/python/vendor/requests-0.10.8"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                "/home/worker/tools/lib/python"))

from balrog.submitter.cli import NightlySubmitterV4
from util.retry import retry


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts-url-prefix", required=True,
                        help="URL prefix for MAR")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("-a", "--api-root", required=True,
                        help="Balrog API root")
    parser.add_argument("-d", "--dummy", action="store_true",
                        help="Add '-dummy' suffix to branch name")
    parser.add_argument("-v", "--verbose", action="store_const",
                        dest="loglevel", const=logging.DEBUG,
                        default=logging.INFO)
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format="%(message)s")

    balrog_username = os.environ.get("BALROG_USERNAME")
    balrog_password = os.environ.get("BALROG_PASSWORD")
    if not balrog_username and not balrog_password:
        raise RuntimeError("BALROG_USERNAME and BALROG_PASSWORD environment "
                           "variables should be set")

    manifest = json.load(open(args.manifest))
    auth = (balrog_username, balrog_password)
    submitter = NightlySubmitterV4(args.api_root, auth, args.dummy)
    for entry in manifest:
        mar_url = "{}/{}".format(args.artifacts_url_prefix, entry["mar"])
        partialInfo = [
            {
                "url": mar_url,
                "hash": entry["hash"],
                "from_buildid": entry["from_buildid"],
                "size": entry["size"],
            }
        ]
        completeInfo = [
            {
                "url": entry["to_mar"],
                "hash": entry["to_hash"],
                "size": entry["to_size"],
            }
        ]
        retry(lambda: submitter.run(
            platform=entry["platform"], buildID=entry["to_buildid"],
            productName=entry["appName"], branch=entry["branch"],
            appVersion=entry["version"], locale=entry["locale"],
            hashFunction='sha512', extVersion=entry["version"],
            partialInfo=partialInfo, completeInfo=completeInfo)
        )
