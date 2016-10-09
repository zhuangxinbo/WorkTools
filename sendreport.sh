#!/bin/bash
starttime=$(date -d "-1day 15:00:00" +"%Y%m%d%H%M%S")
jobpath=$(cd `dirname $0`; pwd)
if [ -n "$jobpath" ]; then
	cd ${jobpath}
	rm -fr ${jobpath}/tmp/*
	python ${jobpath}/gate.py --team astro,mocha --start-time ${starttime} --format html --output-dir=tmp >/dev/null
	declare htmlname="$(ls -t $jobpath/tmp/ |head -n 1)"
	python ${jobpath}/sendreport.py ${jobpath}/tmp/${htmlname} email.conf>/dev/null
else
	echo "can't find your source code."
fi
