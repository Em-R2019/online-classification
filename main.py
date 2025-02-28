import sys
import time
import tkinter as tk

from TMSiFileFormats.file_writer import FileFormat, FileWriter
from TMSiGui.gui import Gui
from experiment import Experiment
from feedback_app import FeedbackApp
from feedback_helper import FeedbackHelper
from TMSiSDK.device import ChannelType
from TMSiSDK.device.devices.saga.saga_API_enums import SagaBaseSampleRate
from os.path import join
from TMSiSDK.tmsi_sdk import TMSiSDK, DeviceType, DeviceInterfaceType, DeviceState
from TMSiSDK.tmsi_errors.error import TMSiError
from TMSiBackend.plotter.impedance_plotter_helper import ImpedancePlotterHelper
from PySide6.QtWidgets import *

if __name__ == "__main__":
    subject = 1
    session = 1

    try:
        # Execute a device discovery. This returns a list of device-objects for every discovered device.
        TMSiSDK().discover(dev_type = DeviceType.saga, dr_interface = DeviceInterfaceType.docked, ds_interface = DeviceInterfaceType.usb)
        discoveryList = TMSiSDK().get_device_list(DeviceType.saga)

        if len(discoveryList) > 0:
            # Get the handle to the first discovered device and open the connection.
            for i,_ in enumerate(discoveryList):
                dev = discoveryList[i]
                if dev.get_dr_interface() == DeviceInterfaceType.docked:
                    # Open the connection to SAGA
                    dev.open()
                    print(f"Connected to {dev.get_device_name()}")
                    break

        # Set the sample rate of the BIP, UNI and AUX channels to 1000 Hz
        dev.set_device_sampling_config(base_sample_rate = SagaBaseSampleRate.Decimal,  channel_type = ChannelType.BIP, channel_divider = 4)
        dev.set_device_sampling_config(base_sample_rate = SagaBaseSampleRate.Decimal, channel_type = ChannelType.AUX, channel_divider = 4)
        dev.set_device_sampling_config(base_sample_rate = SagaBaseSampleRate.Decimal,  channel_type = ChannelType.UNI, channel_divider = 4)

        # Enable BIP 01, BIP 02, AUX 1-1, 1-2 and 1-3, and 18 UNI channels
        AUX_list = [0,1,2]
        BIP_list = [0,1]
        UNI_list = ['FC5', 'FC1', 'C3', 'Cz', 'CP5', 'CP1', 'Fp1', 'AF3', 'F7', 'F3', 'Fz', 'T7', 'P7', 'P3', 'Pz',
                    'PO3', 'O1', 'Oz']

        # Retrieve all channels from the device and update which should be enabled
        ch_list = dev.get_device_channels()

        # The counters are used to keep track of the number of AUX and BIP channels
        # that have been encountered while looping over the channel list
        AUX_count = 0
        BIP_count = 0

        enable_channels = []
        disable_channels = []
        for idx, ch in enumerate(ch_list):
            if ch.get_channel_type() == ChannelType.UNI:
                if ch.get_channel_name() in UNI_list:
                    enable_channels.append(idx)
                else:
                    disable_channels.append(idx)
            elif ch.get_channel_type() == ChannelType.AUX:
                if AUX_count in AUX_list:
                    enable_channels.append(idx)
                else:
                    disable_channels.append(idx)
                AUX_count += 1
            elif ch.get_channel_type()== ChannelType.BIP:
                if BIP_count in BIP_list:
                    enable_channels.append(idx)
                else:
                    disable_channels.append(idx)
                BIP_count += 1
            elif ch.get_channel_name() == 'PGND':
                enable_channels.append(idx)
            else :
                disable_channels.append(idx)

        dev.set_device_active_channels(enable_channels, True)
        dev.set_device_active_channels(disable_channels, False)

        for idx, ch in enumerate(dev.get_device_channels()):
            if ch.get_channel_name() == 'BIP 01':
                dev.set_device_channel_names(['Flex_EMG'], [idx])
            elif ch.get_channel_name() == 'BIP 02':
                dev.set_device_channel_names(['Ext_EMG'], [idx])

        fs_info= dev.get_device_sampling_frequency(detailed=True)
        sampling_frequency = dev.get_device_sampling_frequency()
        print('The current base-sample-rate is {0} Hz.'.format(fs_info['base_sampling_rate']))
        print('\nThe current sample-rates per channel-type-group are :')

        for fs in fs_info:
            if fs != 'base_sampling_rate':
                print('{0} = {1} Hz'.format(fs, fs_info[fs]))

        dev.export_configuration(join("config", "saga_config_first_session.xml"))

        # Check if there is already a plotter application in existence
        app = QApplication.instance()

        # Initialise the plotter application if there is no other plotter application
        if not app:
            app = QApplication(sys.argv)

        # Initialise the helper
        plotter_helper = ImpedancePlotterHelper(device=dev,
                                                is_head_layout=True,
                                                file_storage = join(f"measurements","impedance measurement"))
        # Define the GUI object and show it
        gui = Gui(plotter_helper = plotter_helper)
        # Enter the event loop
        app.exec()

        # Pause for a while to properly close the GUI after completion
        print('\n Wait to close the plot... \n')
        time.sleep(1)

        # Initialise the desired file-writer class and state its file path
        file_writer = FileWriter(FileFormat.poly5, join("measurements",f"subject_{subject}_session{session}.poly5"))

        # Define the handle to the device
        file_writer.open(dev)

        feedback_helper = FeedbackHelper(model_path=join("classifiers", str(subject)), dev=dev)
        root = tk.Tk()
        feedback_app = FeedbackApp(root, feedback_helper)

        print("Start Experiment")
        experiment = Experiment(subject, session, feedback_app, file_writer, run_time=5, break_time=3, prep_time=2, nruns=2)
        experiment.start()

        feedback_app.mainloop()

        experiment.close()
        feedback_helper.close()

        # Close the file writer after GUI termination
        file_writer.close()

        # Close the connection to the SAGA device
        dev.close()

    except TMSiError as e:
        print(e)

    finally:
        if 'dev' in locals():
            # Close the connection to the device when the device is opened
            if dev.get_device_state() == DeviceState.connected:
                dev.close()

