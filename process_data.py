from datetime import datetime
from os import walk, makedirs
from os.path import join, exists
import numpy as np

from TMSiFileFormats.file_formats.poly5_to_edf_converter import Poly5_to_EDF_Converter
import mne

if __name__ == '__main__':
    subject = 3
    session = 1
    folder = f"data/raw_files/S{subject}/Session{session}"
    processed_folder = f"data/processed_files/S{subject}/Session{session}"

    if not exists(processed_folder):
        makedirs(processed_folder)

    converter = Poly5_to_EDF_Converter(batch=True, foldername=folder, f_c=[0.1, 249])

    edf_list = []
    annotations_list = []
    for root, dirs, files in walk(folder):
        for file in files:
            if file.endswith('.edf'):
                edf_list.append(file)
            elif file.endswith('.txt'):
                annotations_list.append(file)
    edf_list.sort(reverse=True)

    for annotations_path in annotations_list:
        annotations_file = open(join(folder, annotations_path), 'r')
        annotations = annotations_file.read().split('\n')
        annotations.pop()

        split_annotations = []
        if len(annotations) > 0:
            for annotation in annotations:
                annotation = annotation.split(',')
                for i, item in enumerate(annotation):
                    annotation[i] = item.strip(" ]['")
                print(annotation)
                split_annotations.append(annotation)

            first_annotation = datetime.strptime(split_annotations[0][0], '%H:%M:%S')

            for edf in edf_list:
                edf_time = datetime.strptime(edf.split('-')[1].split('.')[0].split("_")[1], '%H%M%S')
                if edf_time < first_annotation:
                    raw = mne.io.read_raw_edf(join(folder, edf), preload=True)
                    print(raw.info)
                    # edf_start = raw.info['meas_date']
                    label_dict = {'MI': 1, 'MM': 2, 'Rest': 3, 'Break': 4, 'start calibration': 5, 'end calibration': 6}

                    mne_annotations = []
                    for i, annotation in enumerate(split_annotations):
                        annotation_time = datetime.strptime(annotation[0], '%H:%M:%S')
                        if i == len(split_annotations) - 1:
                            annotation_duration = raw.times[-1] - (annotation_time - edf_time).total_seconds()
                        else:
                            annotation_duration = (datetime.strptime(split_annotations[i+1][0], '%H:%M:%S') - annotation_time).total_seconds()
                        mne_annotations.append([(annotation_time - edf_time).total_seconds(), annotation[1], annotation_duration])
                    mne_annotations = np.array(mne_annotations)

                    raw = raw.set_annotations(mne.Annotations(onset=mne_annotations[:, 0], duration=mne_annotations[:, 2], description=mne_annotations[:, 1]))

                    run_label = annotations_path.split('_', 1)[1].split('.')[0]
                    raw.save(join(processed_folder, f"{edf.split('-')[0]}_{run_label}_eeg.fif"), overwrite=True)
                    break
