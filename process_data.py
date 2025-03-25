from datetime import datetime
from os import walk, makedirs
from os.path import join, exists
import numpy as np

from TMSiFileFormats.file_formats.poly5_to_edf_converter import Poly5_to_EDF_Converter
import mne

if __name__ == '__main__':
    subject = 'me'
    session = 1
    folder = f"data/raw_files/S{subject}/Session{session}"
    processed_folder = f"data/processed_files/S{subject}/Session{session}"
    classifier_folder = f"classifiers/S{subject}"

    ## discard : [label, run, trial]
    # discard = [['feedback', 4, 1]]
    discard = []

    if not exists(processed_folder):
        makedirs(processed_folder)
    if not exists(classifier_folder):
        makedirs(classifier_folder)

    converter = Poly5_to_EDF_Converter(batch=True, foldername=folder, f_c=[0.1, 249])

    edf_list = []
    annotation_file_list = []
    for root, dirs, files in walk(folder):
        for file in files:
            if file.endswith('.edf'):
                edf_list.append(file)
            elif file.endswith('.txt'):
                annotation_file_list.append(file)
    edf_list.sort(reverse=True)

    for annotations_path in annotation_file_list:
        annotations_file = open(join(folder, annotations_path), 'r')
        annotations_list = annotations_file.read().split('\n')
        annotations_list.pop()

        if len(annotations_list) > 0:

            split_annotations = []
            for annotation in annotations_list:
                annotation = annotation.split(',')
                for i, item in enumerate(annotation):
                    annotation[i] = item.strip(" ]['")
                print(annotation)
                split_annotations.append(annotation)

            annotations_list = split_annotations

            first_annotation = datetime.strptime(annotations_list[0][0], '%H:%M:%S')

            annotation_label = annotations_path.split('_')[1]
            annotation_run = annotations_path.split('_')[2].split('.')[0]

            for edf in edf_list:
                edf_label = edf.split('_')[1]
                edf_run = edf.split('_')[2].split('-')[0]
                edf_time = datetime.strptime(edf.split('-')[1].split('.')[0].split("_")[1], '%H%M%S')
                if edf_time < first_annotation and edf_label == annotation_label and edf_run == annotation_run:
                    raw = mne.io.read_raw_edf(join(folder, edf), preload=True)
                    print(raw.info)

                    mne_annotations = []
                    for i, annotation in enumerate(annotations_list):
                        annotation_time = datetime.strptime(annotation[0], '%H:%M:%S')
                        if i == len(annotations_list) - 1:
                            annotation_duration = raw.times[-1] - (annotation_time - edf_time).total_seconds()
                        else:
                            annotation_duration = (datetime.strptime(annotations_list[i + 1][0], '%H:%M:%S') - annotation_time).total_seconds()
                        mne_annotations.append([(annotation_time - edf_time).total_seconds(), annotation[1], annotation_duration])
                    mne_annotations = np.array(mne_annotations)

                    if len(discard) > 0:
                        for discard_annotation in discard:
                            if annotation_label == discard_annotation[0] and (int(annotation_run[1:]) + 1) == discard_annotation[1]:
                                mne_annotations[discard_annotation[2] - 1, 1] = 'BAD'


                    raw = raw.set_annotations(mne.Annotations(onset=mne_annotations[:, 0], duration=mne_annotations[:, 2], description=mne_annotations[:, 1]))

                    raw.save(join(processed_folder, f"S{subject}_Session{session}_{annotation_label}_{annotation_run}_eeg.fif"), overwrite=True)
                    break
