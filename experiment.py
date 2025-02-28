from datetime import datetime
import random
import threading
import time


class Experiment:
    def __init__(self, subject, session, feedback_app, filewriter, run_time, break_time, prep_time, nruns):
        self.subject = subject
        self.session = session
        self.run_time = run_time
        self.break_time = break_time
        self.prep_time = prep_time
        assert nruns % 2 == 0  # nruns must be even
        self.nruns = nruns
        self.feedback_app = feedback_app
        self.filewriter = filewriter
        self.go = True
        self.annotations = []
        self.tasks = ["MI"]*int(self.nruns/2) + ["Rest"]*int(self.nruns/2)

        self.thread = threading.Thread(target=self.loop)

    def start(self):
        self.thread.start()

    def loop(self):
        random.shuffle(self.tasks)
        for i in range(self.nruns):
            if self.go:
                self.run(self.tasks[i])
            else:
                self.save()
                return
        self.save()
        return

    def run(self, task):
        self.feedback_app.set_task(task)
        time.sleep(self.prep_time)

        self.feedback_app.give_feedback = True
        print("Running...")
        self.annotations.append([datetime.now().strftime('%H:%M:%S'), task])
        time.sleep(self.run_time)

        self.feedback_app.set_task("Break")
        self.feedback_app.give_feedback = False
        print("Break")
        self.annotations.append([datetime.now().strftime('%H:%M:%S'), "Break"])
        time.sleep(self.break_time)

    def close(self):
        self.go = False
        self.thread.join()

    def save(self):
        with open(f'measurements\\annotations_subject_{self.subject}_session_{self.session}.txt', 'w') as f:
            for annotation in self.annotations:
                f.write(f"{annotation}\n")