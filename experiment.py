import random
import threading
import time


class Experiment:
    def __init__(self, subject, session, feedback_app, run_time, break_time, prep_time, nruns):
        self.subject = subject
        self.session = session
        self.run_time = run_time
        self.break_time = break_time
        self.prep_time = prep_time
        assert nruns % 2 == 0  # nruns must be even
        self.nruns = nruns
        self.feedback_app = feedback_app
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

    def run(self, task):
        self.feedback_app.set_task(task)
        time.sleep(self.prep_time)

        self.feedback_app.give_feedback = True
        print("Running...")
        self.annotations.append([time.time(), task])
        time.sleep(self.run_time)

        self.feedback_app.set_task("Break")
        self.feedback_app.give_feedback = False
        print("Break")
        self.annotations.append([time.time(), "Break"])
        time.sleep(self.break_time)

    def close(self):
        self.go = False
        self.thread.join()