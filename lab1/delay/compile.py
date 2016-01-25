#! /usr/bin/env python

out_fh = open('out.csv', 'w')
out_fh.write('Utilization,Queueing Delay\n')

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
    out_fh.write(fh_name.strip('.txt') + ',' + '%f' % avg + "\n")

out_fh.close()

