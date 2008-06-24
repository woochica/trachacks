#!/bin/bash
rm -rf dest1
rm -rf dest2 
python example.py \
&& trac-admin dest1 permission add anonymous TRAC_ADMIN \
&& trac-admin dest2 permission add anonymous TRAC_ADMIN \
&& trac-admin dest1 version remove 1.0 \
&& trac-admin dest1 version remove 2.0 \
&& trac-admin dest2 version remove 1.0 \
&& trac-admin dest2 version remove 2.0 \
&& trac-admin dest1 priority change blocker "10 blocker"  \
&& trac-admin dest1 priority change critical "9 critical" \
&& trac-admin dest1 priority change major "6 major" \
&& trac-admin dest1 priority change minor "4 minor" \
&& trac-admin dest1 priority change trivial "1 trivial" \
&& trac-admin dest1 priority add "8" \
&& trac-admin dest1 priority add "7" \
&& trac-admin dest1 priority add "5 default" \
&& trac-admin dest1 priority add "3" \
&& trac-admin dest1 priority add "2" \
&& trac-admin dest1 resolution add "complete" \
&& trac-admin dest2 resolution add "complete" \
&& tracd --port 8000 dest1 dest2
