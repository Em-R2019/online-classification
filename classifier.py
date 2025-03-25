from models.EEGNet import EEGNetModel as EEGNet
import torch
from os.path import join

class Classifier:
    def __init__(self, subject, session):
        subject = f"S{subject}"
        session = f"Session{session}"

        self.model_mimm = EEGNet(chans=18, classes=1, time_points=250, temp_kernel=32,
                                 f1=16, f2=32, d=2, pk1=8, pk2=16, dropout_rate=0.5, max_norm1=1, max_norm2=0.25)

        state_dict = torch.load(join("classifiers", subject, f"mimm_{subject}_{session}.pt"), weights_only=False, map_location=torch.device('cpu'))
        self.model_mimm.load_state_dict(state_dict, strict=False)
        self.model_mimm.eval()

        self.model_restmi = EEGNet(chans=18, classes=1, time_points=250, temp_kernel=32,
                                   f1=16, f2=32, d=2, pk1=8, pk2=16, dropout_rate=0.5, max_norm1=1, max_norm2=0.25)
        state_dict = torch.load(join("classifiers", subject, f"restmi_{subject}_{session}.pt"), weights_only=False, map_location=torch.device('cpu'))
        self.model_restmi.load_state_dict(state_dict, strict=False)
        self.model_restmi.eval()

    def predict(self, x):
        return self.model_restmi(x).item(), self.model_mimm(x).item()