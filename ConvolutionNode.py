from pyqtgraph.flowchart import Flowchart, Node
import numpy as np

DATA_LENGTH = 60

# custom FFT node for frequency spectrogram output
class ConvolveNode(Node):
    nodeName = "ConvolveNode"

    def __init__(self, name):
        Node.__init__(self, name, terminals={
            "accelX": dict(io="in"),
            "accelY": dict(io="in"),
            "accelZ": dict(io="in"),
            "setActive": dict(io="in"),
            "frequencyX": dict(io="out"),
            "frequencyY": dict(io="out"),
            "frequencyZ": dict(io="out"),
        })
        self.had_input_yet = False
        self.current_data_x = []
        self.current_data_y = []
        self.current_data_z = []

    def convolve_signal(self, data):
        try:
            # kernel_avg = np.zeros(101)
            # for i in range(47,53):
            #     kernel_avg[i] = 1.0 / 6
            kernel_size = 20
            kernel_avg = np.ones(kernel_size) / kernel_size
            
            frequenzy = np.convolve(data, kernel_avg, mode="same")

            # tolist() to convert from np.ndarray
            return frequenzy.tolist()
        except Exception as e:
            print(e)

    def get_had_input_yet(self):
        return self.had_input_yet

    def process(self, **kwds):
        self.had_input_yet = True
        self.current_data_x.append(kwds["accelX"][-1])
        self.current_data_y.append(kwds["accelY"][-1])
        self.current_data_z.append(kwds["accelZ"][-1])
        x_frequency = self.convolve_signal(self.current_data_x)
        y_frequency = self.convolve_signal(self.current_data_y)
        z_frequency = self.convolve_signal(self.current_data_z)

        return {'frequencyX': np.array(x_frequency),
                'frequencyY': np.array(y_frequency),
                'frequencyZ': np.array(z_frequency)}
