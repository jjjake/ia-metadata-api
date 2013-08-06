#!/usr/bin/env python
import sys
import os
import httplib
import urllib
import json

import jsonpatch


# HTTP Requests ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~>
def _request(identifier, method='POST', data={}, debug=False):
    """function for making HTTP requests to the IA Metadata Write API.

    :param identifier: String. Unique Internet Archive identifier used to locate item.
    :param method: (optional) String. HTTP method to use for the request.
    :param data: (optional) Dictionary. POST data to urlencode, and sent to the Metadata Write API. Only used when :param:`method` is ``'POST'``.
    :param debug: (optional) Boolean. Print HTTP headers returned from the Metadata API to stdout for debugging.
    
    """
    host = 'archive.org'
    path = '/metadata/{0}'.format(identifier)
    http = httplib.HTTP(host)
    if debug is True:
        http.set_debuglevel('info')
    http.putrequest("POST", path)
    http.putheader("Host", host)
    if method == 'POST':
        data = urllib.urlencode(data)
        http.putheader("Content-Type", 'application/x-www-form-urlencoded')
        http.putheader("Content-Length", str(len(data)))
    http.endheaders()

    if method == 'POST':
        http.send(data)

    status_code, error_message, headers = http.getreply()
    resp_file = http.getfile()
    return dict(
        status_code = status_code,
        error_message = error_message,
        headers = headers,
        content = json.loads(resp_file.read()),
        identifier = identifier,
    )

# METADATA ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~>
def modify(identifier=None, metadata={}, target='metadata', debug=False):
    """function for modifying the metadata of an existing item on archive.org.
    Note: The Metadata Write API does not yet comply with the latest Json-Patch
    standard. It currently complies with version 02:

        https://tools.ietf.org/html/draft-ietf-appsawg-json-patch-02

    :param identifier: String. Unique Internet Archive identifier used to locate item.
    :param metadata: (optional) Dictionary. Metadata used to update the item.
    :param target: (optional) String. Metadata target to update.
    :param debug: (optional) Boolean. Print the JSON Patch to stdout and exit.

    Usage:

        >>> md = dict(new_key='new_value', foo=['bar', 'bar2'])
        >>> metadata('mapi_test_item1', md)

    """
    access_key, secret_key = os.environ['IAS3KEYS'].split(':')
    src = _request(identifier, method='GET')['content'].get(target, {})
    dest = dict((src.items() + metadata.items()))

    # Prepare patch to remove metadata elements with the value: "REMOVE_TAG"
    for k,v in metadata.items():
        if v == 'REMOVE_TAG' or not v:
            del dest[k]

    json_patch = jsonpatch.make_patch(src, dest).patch
    # Reformat patch to be compliant with version 02 of the Json-Patch standard
    patch = []
    for p in json_patch:
        pd = {p['op']: p['path']}
        if p['op'] != 'remove':
            pd['value'] = p['value']
        patch.append(dict((k,v) for k,v in pd.items() if v))

    data = {
        '-patch': json.dumps(patch), 
        '-target': target,
        'access': access_key,
        'secret': secret_key,
    }

    if debug:
        sys.stdout.write("Target:\t{-patch}\nPatch:\t{-target}\n".format(**data))
        sys.exit(0)

    return _request(
                identifier, 
                method='POST', 
                data=data, 
    )
