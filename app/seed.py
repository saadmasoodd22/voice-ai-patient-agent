from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Patient, new_uuid


def seed_patients(db: Session) -> int:
    if db.query(Patient).count() > 0:
        return 0

    today = date.today()
    rows = [
        ("Jane", "Doe", date(1988, 4, 12), "Female", "4155550101", "jane.doe@email.com", "18 Oak Street", "Apt 4B", "San Francisco", "CA", "94107", "Blue Cross", "BCX88291", "English", "John Doe", "4155550199", 40),
        ("Marcus", "Nguyen", date(1992, 11, 3), "Male", "2125550188", "marcus.nguyen@email.com", "90 Lexington Ave", None, "New York", "NY", "10016", "UnitedHealthcare", "UHC44120", "English", None, None, 38),
        ("Sofia", "Ramirez", date(1979, 7, 21), "Female", "3055550144", "sofia.ramirez@email.com", "612 Coral Way", None, "Miami", "FL", "33145", "Aetna", "AET90331", "Spanish", "Luis Ramirez", "3055550177", 36),
        ("Daniel", "Okoye", date(1985, 1, 9), "Male", "3125550160", None, "441 W Madison St", "Suite 2", "Chicago", "IL", "60661", "Cigna", "CIG22018", "English", None, None, 33),
        ("Amelia", "Brooks", date(1996, 9, 30), "Female", "6175550133", "amelia.brooks@email.com", "15 Beacon Street", None, "Boston", "MA", "02108", None, None, "English", "Noah Brooks", "6175550111", 30),
        ("Hassan", "Ali", date(1974, 2, 14), "Male", "7135550190", "hassan.ali@email.com", "808 Westheimer Rd", None, "Houston", "TX", "77006", "Humana", "HUM11882", "English", "Amina Ali", "7135550122", 28),
        ("Priya", "Shah", date(1990, 5, 18), "Female", "2065550171", "priya.shah@email.com", "1201 2nd Avenue", "Unit 8", "Seattle", "WA", "98101", "Kaiser", "KSR77210", "English", None, None, 26),
        ("Liam", "O'Connor", date(1983, 12, 2), "Male", "3035550155", "liam.oconnor@email.com", "44 Larimer Street", None, "Denver", "CO", "80202", "Medicare", "MCR44011", "English", "Erin O'Connor", "3035550108", 24),
        ("Mei", "Chen", date(1998, 8, 8), "Female", "4085550129", "mei.chen@email.com", "350 W San Carlos St", None, "San Jose", "CA", "95110", "Blue Cross", "BCX19002", "English", None, None, 22),
        ("Andre", "Williams", date(1969, 3, 27), "Male", "4045550182", None, "230 Peachtree St", None, "Atlanta", "GA", "30303", "Aetna", "AET55190", "English", "Tasha Williams", "4045550104", 20),
        ("Nora", "Ibrahim", date(1994, 6, 11), "Female", "6025550166", "nora.ibrahim@email.com", "701 N Central Ave", "Apt 12", "Phoenix", "AZ", "85004", None, None, "Arabic", None, None, 18),
        ("Ethan", "Baker", date(1981, 10, 5), "Male", "5035550147", "ethan.baker@email.com", "921 SW 6th Ave", None, "Portland", "OR", "97204", "Cigna", "CIG88301", "English", None, None, 16),
        ("Camille", "Dubois", date(1987, 1, 23), "Female", "5045550119", "camille.dubois@email.com", "800 Canal Street", None, "New Orleans", "LA", "70112", "UnitedHealthcare", "UHC99012", "French", "Paul Dubois", "5045550180", 14),
        ("Jonah", "Kim", date(1993, 4, 4), "Male", "2155550136", "jonah.kim@email.com", "1800 Market Street", "Floor 3", "Philadelphia", "PA", "19103", "Independence Blue Cross", "IBC33401", "English", None, None, 12),
        ("Alicia", "Grant", date(1977, 9, 19), "Female", "7025550184", None, "3750 Las Vegas Blvd", None, "Las Vegas", "NV", "89158", "Humana", "HUM22910", "English", "Mark Grant", "7025550112", 11),
        ("Theo", "Patel", date(2000, 7, 7), "Male", "9195550152", "theo.patel@email.com", "301 Fayetteville St", None, "Raleigh", "NC", "27601", None, None, "English", None, None, 10),
        ("Harper", "Singh", date(1986, 11, 16), "Female", "5125550178", "harper.singh@email.com", "98 Congress Avenue", None, "Austin", "TX", "78701", "Blue Cross", "BCX66018", "English", "Aarav Singh", "5125550103", 9),
        ("Owen", "Murphy", date(1972, 8, 25), "Male", "6155550126", None, "414 Broadway", None, "Nashville", "TN", "37203", "Medicare", "MCR88120", "English", None, None, 8),
        ("Isla", "Fernandez", date(1991, 2, 28), "Female", "8585550193", "isla.fernandez@email.com", "225 Broadway", "Unit 6", "San Diego", "CA", "92101", "Kaiser", "KSR44109", "Spanish", None, None, 7),
        ("Caleb", "Wright", date(1984, 5, 1), "Male", "3145550141", "caleb.wright@email.com", "600 Washington Ave", None, "St Louis", "MO", "63101", "Aetna", "AET11028", "English", "Rita Wright", "3145550195", 6),
        ("Ava", "Johnson", date(1999, 12, 12), "Female", "6515550163", "ava.johnson@email.com", "350 Cedar Street", None, "Saint Paul", "MN", "55101", None, None, "English", None, None, 5),
        ("Miles", "Thompson", date(1965, 6, 6), "Male", "2165550117", None, "200 Public Square", None, "Cleveland", "OH", "44114", "Medicare", "MCR22090", "English", "Helen Thompson", "2165550186", 4),
        ("Leah", "Kowalski", date(1989, 3, 15), "Female", "4145550124", "leah.kowalski@email.com", "833 E Michigan St", None, "Milwaukee", "WI", "53202", "UnitedHealthcare", "UHC11880", "English", None, None, 3),
        ("Nolan", "Davis", date(1978, 10, 20), "Male", "8015550189", "nolan.davis@email.com", "15 W South Temple", None, "Salt Lake City", "UT", "84101", "Cigna", "CIG54012", "English", "Amy Davis", "8015550106", 2),
        ("Ruby", "Bennett", date(1995, 1, 31), "Female", "8605550148", "ruby.bennett@email.com", "1 State Street", "Apt 2A", "Hartford", "CT", "06103", "Aetna", "AET77801", "English", None, None, 1),
        ("George", "Adams", date(1959, 4, 17), "Male", "2075550132", None, "45 Exchange Street", None, "Portland", "ME", "04101", "Medicare", "MCR99001", "English", "Martha Adams", "2075550174", 0),
        ("Elena", "Vasquez", date(1982, 8, 9), "Female", "9155550159", "elena.vasquez@email.com", "201 N Mesa St", None, "El Paso", "TX", "79901", "Humana", "HUM33018", "Spanish", None, None, 15),
        ("Felix", "Brown", date(1997, 9, 27), "Male", "8085550110", "felix.brown@email.com", "1001 Bishop Street", None, "Honolulu", "HI", "96813", None, None, "English", None, None, 13),
    ]

    for row in rows:
        created = datetime.combine(today - timedelta(days=row[16]), datetime.min.time())
        db.add(
            Patient(
                patient_id=new_uuid(),
                first_name=row[0],
                last_name=row[1],
                date_of_birth=row[2],
                sex=row[3],
                phone_number=row[4],
                email=row[5],
                address_line_1=row[6],
                address_line_2=row[7],
                city=row[8],
                state=row[9],
                zip_code=row[10],
                insurance_provider=row[11],
                insurance_member_id=row[12],
                preferred_language=row[13],
                emergency_contact_name=row[14],
                emergency_contact_phone=row[15],
                created_at=created,
                updated_at=created,
            )
        )
    db.commit()
    return len(rows)
