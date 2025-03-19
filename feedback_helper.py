import time
from os.path import join

import numpy as np
import torch
from scipy import signal
from skimage.measure import block_reduce
import classifier
from traditional_classifier import TraditionalClassifier
from TMSiBackend.data_consumer.consumer import Consumer
from TMSiBackend.data_consumer.consumer_thread import ConsumerThread
from TMSiSDK.device.tmsi_device_enums import MeasurementType


class FeedbackHelper:
    def __init__(self, subject, session, dev, traditional=False):
        self.traditional = traditional
        if traditional:
            self.mean = None
            self.variance = None

            self.classifier = TraditionalClassifier()
            ch_list = dev.get_device_active_channels()
            surrounding_channels = []
            for idx, ch in enumerate(ch_list):
                if ch.get_channel_name() == "C3":
                    self.c3 = idx
                if ch.get_channel_name() in ["CP5", "CP1", "FC5", "FC1"]:
                    surrounding_channels.append(idx)
            self.surrounding_channels = surrounding_channels
        else:
            self.classifier = classifier.Classifier(subject, int(session)-1)
        self.restmi = 0
        self.mimm = 0

        self.sampling_frequency = dev.get_device_sampling_frequency()

        self.sos_low = signal.butter(10, 80, 'lowpass', fs=self.sampling_frequency, output='sos')
        self.sos_notch = signal.butter(10, [59.5, 60,5], 'bandstop', fs=self.sampling_frequency, output='sos')

        self.consumer = Consumer()
        # Initialize thread
        self.consumer_thread = ConsumerThread(
            consumer_reading_queue= self.consumer.reading_queue,
            sample_rate= self.sampling_frequency
        )
        # Register device to sample data server and start reading samples
        self.consumer.open(
            server =  dev,
            reading_queue_id =  dev.get_id(),
            consumer_thread= self.consumer_thread)

        self.dev = dev
        self.dev.start_measurement(MeasurementType.SAGA_SIGNAL)
        self.measuring = True
        self.calibrating = False


    def update(self):
        if self.traditional and self.mean is None:
            return

        if not self.measuring:
            raise IOError("Not measuring")

        buffer = self.consumer_thread.original_buffer.copy()

        if buffer.dataset is None or buffer.dataset.shape[1] < self.sampling_frequency:
            return

        data = self.filter_buffer(buffer)

        pointer_data_to_plot = buffer.pointer_buffer

        if pointer_data_to_plot >= self.sampling_frequency:
            segment = data[:18, pointer_data_to_plot-self.sampling_frequency:pointer_data_to_plot]
        else:
            segment = data[:18, pointer_data_to_plot- self.sampling_frequency:]
            segment = np.concatenate((data[:18, :pointer_data_to_plot], segment), axis=1)

        self.restmi, self.mimm = self.prediction(segment)

        return self.restmi, self.mimm

    def close(self):
        self.consumer.close()
        print("Feedback helper closed")
        self.dev.stop_measurement()

    def calibrate(self):
        print("Calibrating")
        self.calibrating = True
        time.sleep(10)

        buffer = self.consumer_thread.original_buffer.copy()

        if buffer.dataset is None or buffer.dataset.shape[1] < self.sampling_frequency * 10:
            time.sleep(1)
            buffer = self.consumer_thread.original_buffer.copy()
            if buffer.dataset is None or buffer.dataset.shape[1] < self.sampling_frequency * 10:
                time.sleep(1)
                buffer = self.consumer_thread.original_buffer.copy()
                if buffer.dataset is None or buffer.dataset.shape[1] < self.sampling_frequency * 10:
                    IOError("Not enough data to calibrate")

        data = self.filter_buffer(buffer)

        pointer_data_to_plot = buffer.pointer_buffer

        segment = data[:18, pointer_data_to_plot:]
        segment = np.concatenate((data[:18, :pointer_data_to_plot], segment), axis=1)

        result = []
        for i in range(20):
            restmi, _ = self.prediction(segment[:, i*self.sampling_frequency//2: i*self.sampling_frequency//2 +
                                                                                 self.sampling_frequency])
            result.append(restmi)

        time.sleep(10)

        buffer = self.consumer_thread.original_buffer.copy()

        if buffer.dataset is None or buffer.dataset.shape[1] < self.sampling_frequency * 10:
            IOError("A problem occured while accessing the buffer")

        data = self.filter_buffer(buffer)

        pointer_data_to_plot = buffer.pointer_buffer

        segment = data[:18, pointer_data_to_plot:]
        segment = np.concatenate((data[:18, :pointer_data_to_plot], segment), axis=1)

        for i in range(20):
            restmi, _ = self.prediction(segment[:, i*self.sampling_frequency//2: i*self.sampling_frequency//2 +
                                                                                 self.sampling_frequency])
            result.append(restmi)

        time.sleep(10)

        buffer = self.consumer_thread.original_buffer.copy()

        if buffer.dataset is None or buffer.dataset.shape[1] < self.sampling_frequency * 10:
            IOError("A problem occured while accessing the buffer")

        data = self.filter_buffer(buffer)

        pointer_data_to_plot = buffer.pointer_buffer

        segment = data[:18, pointer_data_to_plot:]
        segment = np.concatenate((data[:18, :pointer_data_to_plot], segment), axis=1)

        for i in range(20):
            restmi, _ = self.prediction(segment[:, i*self.sampling_frequency//2: i*self.sampling_frequency//2 +
                                                                                 self.sampling_frequency])
            result.append(restmi)

        self.mean = np.mean(result)
        self.variance = np.var(result)

        print("Calibration done")
        print("Mean: " + str(self.mean))
        print("Variance: " + str(self.variance))

        self.variance += 1e-12 # Prevent division by zero

        self.calibrating = False


    def prediction(self, segment):
        segment = block_reduce(segment, block_size=(1,2), func=np.mean, cval=np.mean(segment))

        if self.traditional:
            x = segment[self.c3, :]

            arrays = [x]
            arrays.append([segment[i, :] for i in self.surrounding_channels])
            x = np.vstack(arrays)

            restmi = self.classifier.predict(x, x.shape[1])

            if self.mean is not None:
                # Normalize
                restmi = 1 - ((restmi - self.mean) / self.variance / 4 + 0.5)
                if restmi < 0:
                    restmi = 0
                elif restmi > 1:
                    restmi = 1
            mimm = restmi
        else:
            segment = torch.tensor(segment).float().unsqueeze(0).unsqueeze(0)
            restmi, mimm = self.classifier.predict(segment)

        return restmi, mimm

    def filter_buffer(self, buffer):
        data = buffer.dataset
        data = signal.sosfilt(self.sos_low, data, axis=1)
        data = signal.sosfilt(self.sos_notch, data, axis=1)
        return data

