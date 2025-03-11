from os.path import join

from TMSiSDK.device import ChannelType
from TMSiSDK.device.devices.saga.saga_API_enums import SagaBaseSampleRate


def change_config(dev):
    # Set the sample rate of the BIP, UNI and AUX channels to 1000 Hz
    dev.set_device_sampling_config(base_sample_rate = SagaBaseSampleRate.Decimal,  channel_type = ChannelType.BIP, channel_divider = 8)
    dev.set_device_sampling_config(base_sample_rate = SagaBaseSampleRate.Decimal, channel_type = ChannelType.AUX, channel_divider = 8)
    dev.set_device_sampling_config(base_sample_rate = SagaBaseSampleRate.Decimal,  channel_type = ChannelType.UNI, channel_divider = 8)

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
        elif ch.get_channel_name() == 'CREF':
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