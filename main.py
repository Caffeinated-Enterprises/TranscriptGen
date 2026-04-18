import os
import sys

from download import run_grouped

# group_1 = [
#     "https://www.youtube.com/playlist?list=PLkil-jsseebxNZKrETEEHEcXHCFB8ppk0",
#     "https://www.youtube.com/playlist?list=PLkil-jsseebyFyRcRotztGpm3i1SkJcO8",
# ]

# group_2 = [
#     "https://www.youtube.com/playlist?list=PLwL0Myd7Dk1HTts6LRSSGwt_YfSHVEP76",
#     "https://www.youtube.com/playlist?list=PLwL0Myd7Dk1HxSDd1lczdBdH8orrrDhB1",
#     "https://www.youtube.com/playlist?list=PLwL0Myd7Dk1FBwkPKHM1qbM9k7XotQWfZ",
#     "https://www.youtube.com/playlist?list=PLwL0Myd7Dk1GpKJNXqKAyEl__S0W4Vnom",
#     "https://www.youtube.com/playlist?list=PLwL0Myd7Dk1E-onkQYbutYRGOyU-mdsV3",
#     "https://www.youtube.com/playlist?list=PLwL0Myd7Dk1F0iQPGrjehze3eDpco1eVz",
# ]

# group_3 = [
#     "https://www.youtube.com/playlist?list=PL0o_zxa4K1BWYThyV4T2Allw6zY0jEumv",
#     "https://www.youtube.com/playlist?list=PL0o_zxa4K1BVsziIRdfv4Hl4UIqDZhXWV",
#     "https://www.youtube.com/playlist?list=PL0o_zxa4K1BWLRgHW2i8diQ359U5FbKnI",
#     "https://www.youtube.com/playlist?list=PL0o_zxa4K1BXb1arH6tkSV8xTI99OR2XD",
#     "https://www.youtube.com/playlist?list=PL0o_zxa4K1BXXDYmpXlwz3umLs_VGaTe8",
# ]

group_4 = [
    "https://www.youtube.com/playlist?list=PLDesaqWTN6ESsmwELdrzhcGiRhk5DjwLP",
    "https://www.youtube.com/playlist?list=PLDesaqWTN6ETc1ZwHWijCBcZ2gOvS2tTN",
    "https://www.youtube.com/playlist?list=PLF797E961509B4EB5",
    "https://www.youtube.com/playlist?list=PLDesaqWTN6EQ2J4vgsN1HyBeRADEh4Cw-",
    "https://www.youtube.com/playlist?list=PLDesaqWTN6ESk16YRmzuJ8f6-rnuy0Ry7",
    "https://www.youtube.com/playlist?list=PLC292123722B1B450",
    "https://www.youtube.com/playlist?list=PL5102DFDC6790F3D0",
]

# Add playlist URLs for the fifth group (or leave empty to skip)
group_5 = [
    # "https://www.youtube.com/playlist?list=...",
]

PLAYLIST_GROUPS = [
    # ("group_1", group_1),
    # ("group_2", group_2),
    # ("group_3", group_3),
    ("group_4", group_4),
    ("group_5", group_5),
]

if __name__ == "__main__":
    _out = os.environ.get("OUTPUT_DIR", "").strip()
    OUTPUT_BASE = os.path.abspath(_out) if _out else os.path.join(os.getcwd(), "downloads")

    run_grouped(PLAYLIST_GROUPS, OUTPUT_BASE)
