#!/bin/bash
# render.sh <dir> <workers>
set -e
d=$1; W=${2:-4}
python3 make.py $d >/dev/null
N=$(python3 -c "import json,math;print(math.ceil(json.load(open('$d/timeline.json'))['total']*30))")
P=(); : > $d/l.txt
for ((i=0;i<W;i++)); do a=$((N*i/W)); b=$((N*(i+1)/W)); python3 rend.py $d $a $b $d/p$i.mp4 & P+=($!); echo "file 'p$i.mp4'" >> $d/l.txt; done
for p in ${P[@]}; do wait $p; done
ffmpeg -y -v error -f concat -safe 0 -i $d/l.txt -i $d/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 160k -shortest -movflags +faststart $d/final.mp4
