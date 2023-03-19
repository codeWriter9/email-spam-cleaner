#!/bin/bash
cp cached-mesages.txt cache-messages.txt
diff cached-mesages.txt cache-messages.txt
python quickStarter.py spam.txt
