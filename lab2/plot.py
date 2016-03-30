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

    def transmissionTimePlot(self):
        data = pd.read_csv("experiment.csv")

        plt.figure()
        fig, axs = plt.subplots(1)
        data.plot(ax=axs,x="window",y="time")
        axs.set_xlabel("Window Size")
        axs.set_ylabel("Transmission Time (Seconds)")
        fig.savefig('graphs/time-graph.png')

    def avgQueueDelayPlot(self):
        data = pd.read_csv("experiment.csv")

        plt.figure()
        fig, axs = plt.subplots(1)
        data.plot(ax=axs,x="window",y="avg_queue_delay")
        axs.set_xlabel("Window Size")
        axs.set_ylabel("Average Queueing Delay (Seconds)")
        fig.savefig('graphs/avg-queue-graph.png')

    def maxQueueDelayPlot(self):
        data = pd.read_csv("experiment.csv")

        plt.figure()
        fig, axs = plt.subplots(1)
        data.plot(ax=axs,x="window",y="max_queue_delay")
        axs.set_xlabel("Window Size")
        axs.set_ylabel("Max Queueing Delay (Seconds)")
        fig.savefig('graphs/max-queue-graph.png')

    def throughputPlot(self):
        data = pd.read_csv("experiment.csv")

        plt.figure()
        fig, axs = plt.subplots(1)
        data.plot(ax=axs,x="window",y="throughput")
        axs.set_xlabel("Window Size")
        axs.set_ylabel("Throughput (Bytes/Second)")
        fig.savefig('graphs/throughput.png')

if __name__ == '__main__':
    p = Plotter()
    p.transmissionTimePlot()
    p.avgQueueDelayPlot()
    p.maxQueueDelayPlot()
    p.throughputPlot()
