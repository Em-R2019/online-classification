Run using ```python main.py``` the program will only run when the computer is connected to a TMSi SAGA EEG amplifier.

At initialization you will asked for subject and session number, whether you want to use the traditional classifier (default is DL) and whether you want to start with 3 practice runs (default is not).

At the start of the experiment you will be asked for the experiment label, this can be anything, but the program uses the keywords [MM, MI, feedback, pope](capitalization is irrelevant) in the label for certain settings:
- MM: feedback will be generated dummy feedback, regardless of classifier choice; active trials will be annotated with 'MM' (default is MI)
- MI: feedback will be generated dummy feedback, regardless of classifier choice
- feedback: feedback will be determined by the classifier output
- pope: same as feedback, with perturbations, requires an ethernet connection with the wrist perturbator('pope') computer and for the trial on the pope to have been started using the 'Emmy_server' files.

If none of these keywords appear there will be no feedback during the trials. If you use the same label two or three times during 1 session, the files of the latter segments will be appended with 1 or 2.

When using the DL classifiers, network structure and weights are loaded from .pt files with names ```restmi_{subject}_{session-1}.pt``` and ```mimm_{subject}_{session-1}.pt``` in ```classifiers\{subject}``` directory.

After the experiment is finished you will have .poly5 EEG data files and .txt annotation files, run ```process_data.py``` to obtain filtered and annotated .fif EEG files.
