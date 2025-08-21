import os
import shutil
from datetime import datetime
from os import walk, makedirs
from os.path import join, exists
import numpy as np
import mne

from TMSiFileFormats.file_formats.poly5_to_edf_converter_no_filter import Poly5_to_EDF_Converter_no_filter

if __name__ == '__main__':
    subject = 7
    session = 5
    folder = f"data/raw_files/S{subject}/Session{session}"
    # raw_folder_rds = f"T:\staff-umbrella\RDS Thesis/raw_files/S{subject}/Session{session}"
    # folder = f"T:\staff-umbrella\RDS Thesis\Raw data\S{subject}\Session{session}"
    # filtered_folder = f"data/filtered_files/S{subject}/Session{session}"
    filtered_folder = f"T:\staff-umbrella\RDS Thesis/filtered_files_emg/S{subject}/Session{session}"
    processed_folder = f"data/processed_files_emg/S{subject}/Session{session}"
    processed_folder_rds = f"T:\staff-umbrella\RDS Thesis/processed_files_emg/S{subject}/Session{session}"
    # classifier_folder = f"classifiers/S{subject}"

    ## discard : [label, run, trial]
    # discard = [['feedback', 1, 1]]
    discard = []
    #
    if not exists(filtered_folder):
        makedirs(filtered_folder)
    if not exists(processed_folder):
        makedirs(processed_folder)
    # if not exists(classifier_folder):
    #     makedirs(classifier_folder)
    if not exists(processed_folder_rds):
        makedirs(processed_folder_rds)
    # if not exists(raw_folder_rds):
    #     makedirs(raw_folder_rds)

    converter = Poly5_to_EDF_Converter_no_filter(batch=True, foldername=folder)

    edf_list = []
    annotation_file_list = []
    for root, dirs, files in walk(folder):
        for file in files:
            if file.endswith('.edf') and "pope" in file:
                shutil.move(join(folder, file), join(filtered_folder, file))
                edf_list.append(file)
                # shutil.copy(join(folder, file[:-4] + ".poly5"), join(raw_folder_rds, file[:-4] + ".poly5"))
            elif file.endswith('.edf') and "pope" not in file:
                os.remove(join(folder, file))
            elif file.endswith('.txt') and "pope" in file:
                annotation_file_list.append(file)
            #     shutil.copy(join(folder, file), join(raw_folder_rds, file))
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
                    raw = mne.io.read_raw_edf(join(filtered_folder, edf), preload=True)
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

                    file_name = f"S{subject}_Session{session}_{annotation_label}_{annotation_run}_eeg.fif"
                    raw.save(join(processed_folder, file_name), overwrite=True)
                    shutil.copy(join(processed_folder, file_name), join(processed_folder_rds, file_name))
                    break
