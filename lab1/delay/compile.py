#! /usr/bin/env python

out_fh = open('out.csv', 'w')
out_fh.write('Utilization,Average,Theory\n')

def theory(utilization_rate):
    service_rate = float(1000000/(1000*8))
    return float(1/(2*float(service_rate))*utilization_rate/(1-utilization_rate))

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
    ut_rate = float(fh_name.strip('.txt'))/100
    out_fh.write(str(ut_rate) + 
            ',%f' % avg + 
            ',%f' % theory(ut_rate) +
            '\n')

out_fh.close()

