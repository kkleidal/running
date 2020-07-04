Running
=======

I use this code to perform custom analysis on Garmin .fit files, to get insights about my running.

The code is currently somewhat disorganized and poorly documented, but the basic idea is I put all
my fit files in the `data/` directory (gitignored), then I extract it using the fitfile package,
analyze it using numpy, and generate reports and tables using matplotlib and render them into PDF
reports, like [this one](./examples/5k-report.pdf) for a 5K time trial I did recently.

Over time, I'll try to improve documentation and add tests.

I generated the report using the command:

```sh
python report.py -o ~/Documents/5k-report.pdf race_pace \
  --critical-power 292 --weight-lbs 147 \
  --race-powers-from-stryd 306 320 332 --race-distance-meters 5000
```

Feel free to leverage any of this code for your own use cases
(very permissive "Unlicense" terms provided in [LICENSE.txt](./LICENSE.txt)).

Happy running and coding!
