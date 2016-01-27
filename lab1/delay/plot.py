#! /usr/bin/env python

import optparse
import sys

import pandas as pd
import matplotlib.pyplot as plt

# Class that parses a file and plots several graphs
class Plotter:
    def __init__(self):
        plt.style.use('ggplot')
        pd.set_option('display.width', 1000)
        pass

    def linePlot(self):
        """ Create a line graph. """
        data = pd.read_csv("out.csv")

        plt.figure()
        fig, axs = plt.subplots(1)
        data.plot(ax=axs,x="Utilization",y="Average")
        data.plot(ax=axs,x="Utilization",y="Theory")
        axs.set_xlabel("Utilization")
        axs.set_ylabel("Queue Delay")
        fig.savefig('line_graph.png')

if __name__ == '__main__':
    p = Plotter()
    p.linePlot()
