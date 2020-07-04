import datetime
import pandas as pd

from krunning import FitFile, load_pandas_from_fitfile


def test_fitfile_fields():
    with FitFile("test/resources/2020-05-14.fit") as fit_file:
        assert fit_file.fields == {
            "Air Power": "Watts",
            "Cadence": "RPM",
            "Form Power": "Watts",
            "Ground Time": "Milliseconds",
            "Leg Spring Stiffness": "kN/m",
            "Power": "Watts",
            "Vertical Oscillation": "Centimeters",
            "cadence": "rpm",
            "distance": "m",
            "enhanced_altitude": "m",
            "enhanced_speed": "m/s",
            "fractional_cadence": "rpm",
            "heart_rate": "bpm",
            "position_lat": "semicircles",
            "position_long": "semicircles",
            "temperature": "C",
            "timestamp": None,
            "unknown_108": None,
            "unknown_87": None,
            "unknown_88": None,
            "unknown_90": None,
        }


def test_fitfile_length():
    with FitFile("test/resources/2020-05-14.fit") as fit_file:
        assert len(fit_file) == 1757


def test_fitfile_get_fields_none():
    with FitFile("test/resources/2020-05-14.fit") as fit_file:
        count = 0
        for record in fit_file.get_fields([]):
            assert record == []
            count += 1
        assert count == len(fit_file)


def test_fitfile_get_fields_bad_key():
    with FitFile("test/resources/2020-05-14.fit") as fit_file:
        try:
            for record in fit_file.get_fields(["missing_key"]):
                pass
        except KeyError as exc:
            assert "missing_key" in str(exc)
        else:
            assert False, "Expected key error for missing column"


def test_fitfile_get_all_fields():
    with FitFile("test/resources/2020-05-14.fit") as fit_file:
        fields = sorted(fit_file.fields)
        count = 0
        for i, record in enumerate(fit_file.get_fields(fields)):
            if i == 1000:
                assert record == [
                    4,
                    72,
                    78,
                    288,
                    9.375,
                    201,
                    10.625,
                    72,
                    3415.34,
                    15.0,
                    2.781,
                    0.0,
                    151,
                    506449918,
                    -847887398,
                    16,
                    datetime.datetime(2020, 5, 14, 11, 33, 27),
                    None,
                    0,
                    100,
                    3,
                ]
            count += 1
        assert count == len(fit_file)


def test_load_pandas_from_fitfile():
    with FitFile("test/resources/2020-05-14.fit") as fit_file:
        df = load_pandas_from_fitfile(fit_file, ["timestamp", "distance"])
        assert len(df) == 1757
        assert df["distance"].to_numpy()[-1] == 5904.69
        assert df["timestamp"].to_list()[-1] == pd.Timestamp("2020-05-14 11:46:38")
        assert list(df.keys()) == ["timestamp", "distance"]


def test_load_pandas_from_fitfile_all():
    with FitFile("test/resources/2020-05-14.fit") as fit_file:
        df = load_pandas_from_fitfile(fit_file)
        assert len(df) == 1757
        assert df["distance"].to_numpy()[-1] == 5904.69
        assert df["timestamp"].to_list()[-1] == pd.Timestamp("2020-05-14 11:46:38")
        assert list(df.keys()) == sorted(fit_file.fields)
