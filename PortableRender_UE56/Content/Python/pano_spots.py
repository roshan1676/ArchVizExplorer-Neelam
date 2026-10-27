"""Panorama spots (x, y in cm; eye height comes from pano.EYE_Z = 163 cm). Names become file names."""
SPOTS = {
    "3BHK": {
        "01_Living":    (20, 520),
        "02_Balcony":   (-400, 560),
        "03_Dining":    (660, 340),
        "04_Kitchen":   (150, 0),
        "05_Corridor":  (380, -150),
        "06_Bedroom1":  (-90, -720),
        "07_Bedroom2":  (-150, -1150),
    },
    "2BHK": {
        "01_Living":    (60, -900),
        "02_Dining":    (-260, -720),
        "03_Balcony":   (365, -780),
        "04_Kitchen":   (100, -330),
        "05_Bedroom1":  (310, 200),
        "06_Bedroom2":  (300, 700),
        "07_Bathroom":  (-470, 780),
        "08_Toilet2":   (-470, -150),
    },
}
