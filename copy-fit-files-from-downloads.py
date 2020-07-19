import os
import re
import zipfile
import logging


def main():
    downloads = os.path.expanduser("~/Downloads")
    dir_path = os.path.dirname(os.path.realpath(__file__))
    data_path = os.path.join(dir_path, "data")

    files = sorted(os.listdir(downloads))
    zipfile_name_pattern = re.compile(r"^(\d{10,}).zip$")
    for filename in files:
        logging.info("Found file %s in downloads", filename)
        m = zipfile_name_pattern.fullmatch(filename)
        if not m:
            logging.info("%s is not a fitfile zip", filename)
            continue
        activity_id = m.group(1)
        fitfile_name = "%s.fit" % activity_id

        dest_path = os.path.join(data_path, fitfile_name)
        if os.path.exists(dest_path):
            logging.info(
                "%s already exists in data, skipping %s", fitfile_name, filename
            )
            continue

        path = os.path.join(downloads, filename)
        with zipfile.ZipFile(path, "r") as zf:
            names = zf.namelist()
            if fitfile_name not in names:
                logging.info("%s does not contain a fitfile", filename)
                continue
            logging.info("Extracting %s from %s", fitfile_name, filename)
            zf.extract(fitfile_name, data_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
