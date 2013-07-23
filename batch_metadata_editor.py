#!/usr/bin/env python
import sys
import csv

import metadata


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def iter_csv(csv_file, delimiter=",", quotechar='"'):
    with open(csv_file, 'rb') as f:
        csv_reader = csv.reader(f, delimiter=delimiter, quotechar=quotechar)
        for i, row in enumerate(csv_reader):
            metadata = {}
            if i == 0:
                headers = row
                if 'identifier' not in headers:
                    sys.stderr.write('ERROR! Missing "identifier" column.\n')
                    sys.exit(1)
                continue
            for k,v in zip(headers, row):
                if v == '' or v is None:
                    continue
                if metadata.get(k) is None:
                    metadata[k] = v
                else:
                    if type(metadata[k]) == list:
                        metadata[k].append(v)
                    else:
                        metadata[k] = [metadata[k], v]
            if len(metadata.keys()) <= 1:
                continue
            else:
                yield metadata['identifier'], metadata


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
if __name__ == '__main__':
    tab_file = sys.argv[-1]
    errors = []
    for id, md in iter_csv(tab_file):
        result = metadata.modify(id, md)
        if result['content']['success'] is False:
            message = '{identifier}\tERROR! {content[error]}\n'.format(**result)
            sys.stderr.write(message)
            errors.append(result)
        else:
            message = '{identifier}\thttps:{content[log]}\n'.format(**result)
            sys.stdout.write(message)
    if errors == []:
        sys.exit(0)
    else:
        sys.exit(1)
