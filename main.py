import tkinter as tk
from change_config import change_config
from experiment import Experiment
from feedback_app import FeedbackApp
from feedback_helper import FeedbackHelper
from os.path import join, exists
from os import makedirs
from TMSiSDK.tmsi_sdk import TMSiSDK, DeviceType, DeviceInterfaceType, DeviceState
from TMSiSDK.tmsi_errors.error import TMSiError
from perturbation_client import PerturbationClient

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
                    print(f"Connected to {dev.get_device_name()}")
                    break

        # change_config(dev)
        dev.import_configuration(join("config", "saga_config.xml"))

        print("Input subject number:")
        subject = input()
        print("Input session number:")
        session = input()
        print("Use traditional classifier? (y/N)")
        traditional = input() == "y"
        print("Start with practice runs? (y/N)")
        practice = input() == "y"

        session_path = join("data", "raw_files", f"S{subject}", f"Session{session}")
        if not exists(session_path):
            makedirs(session_path)

        feedback_helper = FeedbackHelper(subject, session, dev=dev, traditional=traditional)
        perturbation_client = PerturbationClient()
        root = tk.Tk()

        feedback_app = FeedbackApp(root, feedback_helper, perturbation_client)

        experiment = Experiment(dev, subject, session, feedback_app, session_path, practice, trial_time=20, break_time=3,
                                prep_time=2, pause_time=10, ntrials = 6, nruns=5)  ## ntrials = 6, nruns = 5
        experiment.start()

        feedback_app.mainloop()

        print("mainloop ended")

        feedback_helper.close()
        perturbation_client.stop()

        experiment.close()

        dev.close()

    except TMSiError as e:
        print(e)

    finally:
        if 'dev' in locals():
            # Close the connection to the device when the device is opened
            if dev.get_device_state() == DeviceState.connected:
                dev.close()

