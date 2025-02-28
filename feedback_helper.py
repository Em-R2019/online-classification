import numpy as np
import torch
from scipy import signal
from skimage.measure import block_reduce
import classifier
from TMSiBackend.data_consumer.consumer import Consumer
from TMSiBackend.data_consumer.consumer_thread import ConsumerThread
from TMSiSDK.device.tmsi_device_enums import MeasurementType


class FeedbackHelper:
    def __init__(self, model_path, dev):
        self.classifier = classifier.Classifier(model_path)
        self.mirest = 0
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
        dev.start_measurement(MeasurementType.SAGA_SIGNAL)

    def update(self):
        buffer = self.consumer_thread.original_buffer.copy()

        if buffer.dataset is None or buffer.dataset.shape[1] < self.sampling_frequency:
            return

        data = buffer.dataset
        data = signal.sosfilt(self.sos_low, data, axis=1)
        data = signal.sosfilt(self.sos_notch, data, axis=1)

        pointer_data_to_plot = buffer.pointer_buffer

        if pointer_data_to_plot >= self.sampling_frequency:
            segment = data[:18, pointer_data_to_plot-self.sampling_frequency:pointer_data_to_plot]
        else:
            segment = data[:18, :pointer_data_to_plot]
            segment = np.concatenate((data[:18, pointer_data_to_plot- self.sampling_frequency:], segment), axis=1)

        segment = block_reduce(segment, block_size=(1,4), func=np.mean, cval=np.mean(segment))
        segment = segment[:, :160]
        segment = torch.tensor(segment).float().unsqueeze(0).unsqueeze(0)

        self.mirest, self.mimm = self.classifier.predict(segment)

        return self.mirest, self.mimm

    def close(self):
        self.consumer.close()
        self.dev.stop_measurement()