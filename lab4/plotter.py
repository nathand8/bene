import matplotlib.pyplot as plt

class Plotter:

    def create_sequence_plot(self, x, y, dropX, dropY, ackX, ackY, chart_name="sequence.png"):
        plt.clf() # Clear current figure
        plt.figure(figsize=(15,5))

        min_time = min(x + dropX + ackX)
        max_time = max(x + dropX + ackX)
        min_time -= max_time / 20
        max_time += max_time / 20
        #print "min time", min_time
        #print "max_time", max_time
        #print x
        #print y
        #print dropX
        #print dropY
        #print ackX
        #print ackY

        plt.scatter(x,y,marker='s',s=10)
        plt.scatter(dropX,dropY,marker="x",s=40)
        plt.scatter(ackX,ackY,marker='s',s=2)
        plt.xlabel('Time (seconds)')
        plt.ylabel('Sequence Number Mod 1000')
        plt.xlim([min_time,max_time])
        if chart_name:
            plt.savefig('charts/' + chart_name)

    def rateTimePlot(self, rrates, current_time, chart_name='rate.png'):
        xplots = []
        yplots = []
        last_timestamp = int(current_time*10) + 11
        for x in range(last_timestamp):

            lower = max(0, x-10)
            upper = min(x+1, last_timestamp)
            t_packets = 0
            for y in range(lower, upper):
                y = str(y)
                y = y[:-1] + '.' + y[-1:]
                rate = rrates.get(y)
                if rate:
                    t_packets += rate
            t_rate = ((t_packets * 1000 * 8) / (upper/10.0 - lower/10.0)) / 1000
            xplots.append(x/10.0)
            yplots.append(t_rate)

        plt.plot(xplots, yplots)
        plt.ylabel("Receive Rate (kbps)")
        plt.xlabel("Time (s)")
        if chart_name:
            plt.savefig('charts/' + chart_name)

    def clear(self):
        plt.clf()

    def queueSizePlot(self, queue_log_x, queue_log_y, dropped_packets_x = [], dropped_packets_y = [], chart_name='queueSize.png'):

        plt.plot(queue_log_x, queue_log_y)
        plt.plot(dropped_packets_x, dropped_packets_y, 'rx', markersize=12, label="dropped packet")
        plt.ylabel("Queue Size (# of packets)")
        plt.xlabel("Time (s)")
        if chart_name:
            plt.savefig('charts/' + chart_name)

    def windowSizePlot(self, window_x, window_y, chart_name='windowSize.png'):

        plt.plot(window_x, window_y)
        plt.ylabel("Widow Size (# of packets)")
        plt.xlabel("Time (s)")
        if chart_name:
            plt.savefig('charts/' + chart_name)
