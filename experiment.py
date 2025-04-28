from datetime import datetime
import random
import threading
import time
from glob import glob
from os.path import join, exists

from TMSiFileFormats.file_writer import FileWriter, FileFormat


class Experiment:
    def __init__(self, dev, subject, session, feedback_app, session_path, practice, trial_time, break_time, prep_time, pause_time, ntrials, nruns):
        self.subject = subject
        self.session = session
        self.label = "no_label"
        self.trial_time = trial_time
        self.break_time = break_time
        self.prep_time = prep_time
        assert pause_time > 4
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
        self.practice = practice

        self.thread = threading.Thread(target=self.loop)

    def start(self):
        self.feedback_app.update()
        self.thread.start()
        return

    def loop(self):
        print("Input experiment label and start experiment")
        self.label = input()

        if self.feedback_app.helper.traditional and ("feedback" in self.label.lower() or "pope" in self.label.lower()):
            self.countdown("calibration")
            try:
                self.feedback_app.set_task("Break")
                self.feedback_app.helper.calibrate()
            except Exception as e:
                print(e)
                return

        if "pope" in self.label.lower():
            self.feedback_app.perturbation_client.start()

        if self.practice:
            self.text("Start practice", 3)
            practice_tasks = ["MI", "Rest", "MI"]
            print("Start practice")
            self.countdown("practice")
            for j in range(len(practice_tasks)):
                if self.go:
                    self.trial(practice_tasks[j], None, j)
                else:
                    return
            self.annotations = []
            self.text("End of practice", 3)
            self.text("˄ = move or imagine \n˅ = relax \no = break", 0)

            print("\nPress enter to start experiment")
            input()

        self.text("Start experiment", 2)
        for i in range(self.nruns):
            if self.go:
                random.shuffle(self.tasks)

                print("start filewriter: " + datetime.now().strftime('%H:%M:%S'))
                if len(glob(join(self.session_path, f"EEG_{self.label}_R{i}*"))) > 0:
                    self.label = self.label + "1"
                file_writer = FileWriter(FileFormat.poly5, join(self.session_path, f"EEG_{self.label}_R{i}.poly5"))
                file_writer.open(self.dev)

                print("Start Run " + str(i+1))
                self.countdown("run " + str(i+1))

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
                self.text("Break", self.pause_time-4)

        print("End experiment " + self.label)
        self.text("End of experiment", 0)
        return

    def trial(self, task, run, trial):
        try:
            self.feedback_app.set_task(task)
            time.sleep(self.prep_time)

            if "feedback" in self.label.lower() or "pope" in self.label.lower():
                self.feedback_app.give_feedback = True
                if "pope" in self.label.lower():
                    self.feedback_app.perturbation = True
                    self.feedback_app.perturbation_timer = 5
            elif "MM" in self.label.upper() or "MI" in self.label.upper():
                self.feedback_app.dummy_feedback = True
            print("\nStart Trial " + str(trial + 1) + " Task: " + task)
            self.annotations.append([datetime.now().strftime('%H:%M:%S'), task])
            time.sleep(self.trial_time)

            self.feedback_app.set_task("Break")
            self.feedback_app.give_feedback = False
            self.feedback_app.dummy_feedback = False
            self.feedback_app.perturbation = False
            self.feedback_app.helper.reset()
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
        num = ''
        if exists(join(self.session_path, f'annotations_{self.label}_R{run}.txt')):
            num = '1'
            if exists(join(self.session_path, f'annotations_{self.label}{num}_R{run}.txt')):
                num = '2'
        with open(join(self.session_path, f'annotations_{self.label}{num}_R{run}.txt'), 'a') as f:
            for annotation in self.annotations:
                if self.label.upper() == "MM" and annotation[1] == "MI":
                    annotation[1] = "MM"
                f.write(f"{annotation}\n")
        self.annotations = []

    def text(self, text, t):
        self.feedback_app.symbol = text
        time.sleep(t)

    def countdown(self, part):
        self.text(f"Start {part} in 3", 1)
        self.text(f"Start {part} in 2", 1)
        self.text(f"Start {part} in 1", 2)
