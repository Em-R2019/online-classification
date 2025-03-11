from datetime import datetime
import random
import threading
import time
from os.path import join

from TMSiFileFormats.file_writer import FileWriter, FileFormat


class Experiment:
    def __init__(self, dev, subject, session, feedback_app, session_path, trial_time, break_time, prep_time, pause_time, ntrials, nruns):
        self.subject = subject
        self.session = session
        self.label = "no_label"
        self.trial_time = trial_time
        self.break_time = break_time
        self.prep_time = prep_time
        self.pause_time = pause_time
        assert ntrials % 2 == 0  # ntrials must be even
        self.ntrials = ntrials
        self.nruns = nruns
        self.feedback_app = feedback_app
        self.session_path = session_path
        self.go = True
        self.annotations = []
        self.tasks = ["MI"]*int(self.ntrials/2) + ["Rest"]*int(self.ntrials/2)
        self.dev = dev

        self.thread = threading.Thread(target=self.loop)

    def start(self):
        self.feedback_app.update()
        self.thread.start()
        return

    def loop(self):
        print("Input experiment label and start experiment")
        self.label = input()

        if self.feedback_app.helper.traditional and (self.label == "feedback" or self.label == "pope"):
            try:
                self.annotations.append([datetime.now().strftime('%H:%M:%S'), "start calibration"])
                self.feedback_app.helper.calibrate()
                self.annotations.append([datetime.now().strftime('%H:%M:%S'), "end calibration"])
                self.save("cal")
            except Exception as e:
                print(e)
                return

        for i in range(self.nruns):
            if self.go:
                random.shuffle(self.tasks)
                print("start filewriter: " + datetime.now().strftime('%H:%M:%S'))
                file_writer = FileWriter(FileFormat.poly5, join(self.session_path, f"S{self.subject}_Session{self.session}.poly5"))
                file_writer.open(self.dev)
                print("Start Run " + str(i))
                for j in range(self.ntrials):
                    if self.go:
                        self.trial(self.tasks[j], i, j)
                    else:
                        self.save(i)
                        return
                file_writer.close()
                self.save(i)
            else:
                return
            if i < self.nruns - 1:
                time.sleep(self.pause_time)

        print("End Experiment" + self.label)
        return

    def trial(self, task, run, trial):
        try:
            self.feedback_app.set_task(task)
            time.sleep(self.prep_time)

            if "feedback" in self.label or self.label == "pope":
                self.feedback_app.give_feedback = True
            print("\nStart Trial " + str(trial) + " Task: " + task)
            self.annotations.append([datetime.now().strftime('H:%M:%S'), task])
            time.sleep(self.trial_time)

            self.feedback_app.set_task("Break")
            self.feedback_app.give_feedback = False
            print("\nBreak")
            self.annotations.append([datetime.now().strftime('%H:%M:%S'), "Break"])
            time.sleep(self.break_time)
        except Exception as e:
            print(e)
            self.save(run)
            return

    def close(self):
        self.go = False
        self.thread.join()

    def save(self, run):
        print("Save annotations")
        with open(join(self.session_path, f'annotations_R{run}_{self.label}.txt'), 'a') as f:
            for annotation in self.annotations:
                if self.label == "MM" and annotation[1] == "MI":
                    annotation[1] = "MM"
                f.write(f"{annotation}\n")
        self.annotations = []