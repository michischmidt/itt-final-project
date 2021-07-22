from pyqtgraph.flowchart import Flowchart, Node
import numpy as np

DATA_LENGTH = 60

# custom FFT node for frequency spectrogram output
class FftNode(Node):
    nodeName = "FftNode"

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

    def calculate_frequency(self, data):
        try:
            #  we only want to get [DATA_LENGTH] frequencies
            #  from the last signals. Since our forier
            #  transformation cuts the data amount throught 2
            #  we use len(data)/2 for this
            while len(data)/2 > DATA_LENGTH:
                data = data[1:]
            n = len(data)
            # fft computing and normalization and
            # use only first half as the function is mirrored
            frequenzy = np.abs(np.fft.fft(data) / n)[0:int(n / 2)]

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
        x_frequency = self.calculate_frequency(self.current_data_x)
        y_frequency = self.calculate_frequency(self.current_data_y)
        z_frequency = self.calculate_frequency(self.current_data_z)

        return {'frequencyX': np.array(x_frequency),
                'frequencyY': np.array(y_frequency),
                'frequencyZ': np.array(z_frequency)}
