# Danish day and month names
danish_months = (
    "Januar", "Februar", "Marts", "April", "Maj", "Juni",
    "Juli", "August", "September", "Oktober", "November", "December"
)
danish_days = ("Man", "Tir", "Ons", "Tor", "Fre", "Lør", "Søn")

# Default user settings
def get_default_settings():
    return {
        "UseNormalHoursAsDefault": False,
        "UseAvgWeekHoursAsDefault": False,
        "WorkHours": {
            "Mandag": {"From": "08:00", "To": "15:45", "Total": "7:45"},
            "Tirsdag": {"From": "08:00", "To": "15:45", "Total": "7:45"},
            "Onsdag": {"From": "08:00", "To": "15:45", "Total": "7:45"},
            "Torsdag": {"From": "08:00", "To": "15:45", "Total": "7:45"},
            "Fredag": {"From": "08:00", "To": "14:00", "Total": "6:00"}
        },
        "Children": [],
        "UserDetails": {
            "EmploymentDate": "31-12-1999",
            "BirthDate": "31-12-1999"
        },
        "HoursPerWeek": 37.0,
        "HoursPerDay": 7.4,
        "Bias": {
            "Flex": "0:00",
            "Ferie": "0:00",
            "Six_ferie": "0:00",
            "Careday": "0",
            "Seniorday": "0"
        }
    }
