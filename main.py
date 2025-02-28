import sys
import time
import tkinter as tk
from TMSiGui.gui import Gui
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
                    break

        # Set the sample rate of the BIP and AUX channels to 2000 Hz
        dev.set_device_sampling_config(base_sample_rate = SagaBaseSampleRate.Binary,  channel_type = ChannelType.BIP, channel_divider =2)
        dev.set_device_sampling_config(base_sample_rate = SagaBaseSampleRate.Binary, channel_type = ChannelType.AUX, channel_divider = 2)
        dev.set_device_sampling_config(base_sample_rate = SagaBaseSampleRate.Binary,  channel_type = ChannelType.UNI, channel_divider =4)

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
        print(enable_channels)

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


        # Check if there is already a plotter application in existence
        app = QApplication.instance()

        # Initialise the plotter application if there is no other plotter application
        if not app:
            app = QApplication(sys.argv)

        # Initialise the helper
        plotter_helper = ImpedancePlotterHelper(device=dev,
                                                is_head_layout=True,
                                                file_storage = join("measurements","example_EEG_workflow"))
        # Define the GUI object and show it
        gui = Gui(plotter_helper = plotter_helper)
        # Enter the event loop
        app.exec()

        # Pause for a while to properly close the GUI after completion
        print('\n Wait for a bit while we close the plot... \n')
        time.sleep(1)

        subject = 1

        feedback_helper = FeedbackHelper(model_path=join("classifiers", str(subject)), dev=dev)
        root = tk.Tk()
        myapp = FeedbackApp(root, feedback_helper)
        myapp.mainloop()

        feedback_helper.close()
        # root.destroy()

        # Close the file writer after GUI termination
        # file_writer.close()

        # Close the connection to the SAGA device
        dev.close()

    except TMSiError as e:
        print(e)

    finally:
        if 'dev' in locals():
            # Close the connection to the device when the device is opened
            if dev.get_device_state() == DeviceState.connected:
                dev.close()

