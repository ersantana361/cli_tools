import sys
import json

def extract_reservation_data(json_data):
    """
    Extracts reservation data from the JSON object and formats it into a list of rows.
    """
    reservations = json_data.get("SOAP-ENV:Envelope", {}) \
                            .get("SOAP-ENV:Body", {}) \
                            .get("ota:OTA_ReadRS", {}) \
                            .get("ota:OTA_ResRetrieveRS", {}) \
                            .get("ota:ReservationsList", {}) \
                            .get("ota:HotelReservation", [])
    
    rows = []
    for reservation in reservations:
        checkin_date = reservation.get("ota:RoomStays", {}) \
                                  .get("ota:RoomStay", {}) \
                                  .get("ota:RoomRates", {}) \
                                  .get("ota:RoomRate", {}) \
                                  .get("@EffectiveDate", {})

        status = reservation.get("@ResStatus", "null")

        hotel_code = reservation.get("ota:ResGlobalInfo", {}) \
                                .get("ota:BasicPropertyInfo", {}) \
                                .get("@HotelCode", "null")

        amount_after_tax = reservation.get("ota:ResGlobalInfo", {}) \
                                      .get("ota:Total", {}) \
                                      .get("@AmountAfterTax", "null")
        
        res_guest = reservation.get("ota:ResGuests", {}).get("ota:ResGuest")

        if isinstance(res_guest, dict):
            given_name, surname = guest_name(res_guest)
        elif isinstance(res_guest, list):
            given_name, surname = guest_name(res_guest[0])
        else:
            given_name, surname = "null", "null"

        rows.append({
            "Checkin Date": checkin_date,
            "Status": status,
            "Hotel Code": hotel_code,
            "Amount After Tax": amount_after_tax,
            "Given Name": given_name,
            "Surname": surname
        })
    
    return rows

def guest_name(res_guest):
    person_name = res_guest.get("ota:Profiles", {}) \
                           .get("ota:ProfileInfo", {}) \
                           .get("ota:Profile", {}) \
                           .get("ota:Customer", {}) \
                           .get("ota:PersonName", {})

    given_name = person_name.get("ota:GivenName", "null")
    surname = person_name.get("ota:Surname", "null")

    return given_name, surname


def main():
    response_data = sys.stdin.read().strip()
    try:
        json_data = json.loads(response_data)
    except json.JSONDecodeError:
        print("Invalid JSON data.")
        return

    rows = extract_reservation_data(json_data)
    print(json.dumps(rows, indent=2))

if __name__ == "__main__":
    main()

