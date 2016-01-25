#! /usr/bin/env python

import os
folder = 'results'
for fh_name in os.listdir(folder):
    fh = open(os.path.join(folder, fh_name), 'r')
    lines = fh.readlines()
    total = 0
    count = 0
    for line in lines:
        total += float(line)
        count += 1
    avg = total/count
    print int(fh_name.strip('.txt')), avg

