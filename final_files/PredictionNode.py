from pyqtgraph.flowchart import Node
from sklearn import svm
import fluidsynth

DATA_LENGTH = 30

class PredictNode(Node):
    nodeName = "PredictNode"
    fs = fluidsynth.Synth(1)
    fs.start(driver='alsa')
    sfid = fs.sfload('./pns_drum.sf2')
    # select MIDI track, sound font, MIDI bank and preset
    fs.program_select(0, sfid, 0, 0)

    def __init__(self, name):
        Node.__init__(self, name, terminals={
            "accelerator_x": dict(io="in"),
            "accelerator_y": dict(io="in"),
            "accelerator_z": dict(io="in")
        })

        self.current_gesture_x_frequencies = []
        self.current_gesture_y_frequencies = []
        self.current_gesture_z_frequencies = []
        self.current_prediction = "None"
        self.training_data_dict = {}

    def init_svm_with_data(self, data):
        print("initsvm with data")
        # print(data)
        self.training_data_dict = data
        self.classifier = svm.SVC()
        categories = []
        training_data = []
        if len(data) > 1:
            current_index = 0
            for key, value in data.items():
                categories += [current_index]
                current_values_array = []
                current_values_array.append(value.get("x"))
                current_values_array.append(value.get("y"))
                current_values_array.append(value.get("z"))

                training_data += self.get_svm_data_array(current_values_array)

                current_index += 1
            self.classifier.fit(training_data, categories)

    def get_svm_data_array(self, x_y_z_array):
        svm_data_array = []
        for value in x_y_z_array:
            x_cut = []
            for index, x_value in enumerate(x_y_z_array[0]):
                if index < DATA_LENGTH:
                    x_cut.append(x_value)
            y_cut = []
            for index, y_value in enumerate(x_y_z_array[1]):
                if index < DATA_LENGTH:
                    y_cut.append(y_value)
            z_cut = []
            for index, z_value in enumerate(x_y_z_array[2]):
                if index < DATA_LENGTH:
                    z_cut.append(z_value)

            svm_data_array += x_cut + y_cut + z_cut
        return [svm_data_array]

    # testing sound accuracy
    def make_sound(self, result, drumNumber):
        if (result > 0):
            self.fs.noteon(0, drumNumber, 100)
            self.fs.noteoff(0, drumNumber)

    def get_prediction(self, drumNumber):
        input_data = []
        input_data.append(self.current_gesture_x_frequencies)
        input_data.append(self.current_gesture_y_frequencies)
        input_data.append(self.current_gesture_z_frequencies)
        predicition_data = self.get_svm_data_array(input_data)
        result = self.classifier.predict(predicition_data)[0]
        self.make_sound(result, drumNumber)
        return list(self.training_data_dict.keys())[result]

    def process(self, **kwds):
        # Get the last values from our accelerator data
        self.current_gesture_x_frequencies = kwds["accelerator_x"]
        self.current_gesture_y_frequencies = kwds["accelerator_y"]
        self.current_gesture_z_frequencies = kwds["accelerator_z"]
