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

        comments = reservation.get("ota:ResGlobalInfo", {}) \
                                  .get("ota:Comments", {}) \
                                  .get("ota:Comment", {}) \

        res_guest = reservation.get("ota:ResGuests", {}).get("ota:ResGuest")

        if isinstance(res_guest, dict):
            given_name = guest_name(res_guest)
        elif isinstance(res_guest, list):
            given_name = guest_name(res_guest[0])
        else:
            given_name = "null"


        rows.append({
            #"Checkin Date": checkin_date,
            #"Status": status,
            #"Given Name": given_name,
            "Comment 4": get_item_safe(comments, 3, {}).get("ota:Text", ""),
            "Comment 5": get_item_safe(comments, 4, {}).get("ota:Text", ""),
            "Comment 6": get_item_safe(comments, 5, {}).get("ota:Text", ""),
            "Comment 7": get_item_safe(comments, 6, {}).get("ota:Text", ""),
            "Comment 8": get_item_safe(comments, 7, {}).get("ota:Text", "")
        })
    
    return rows

def guest_name(res_guest):
    return res_guest.get("ota:Profiles", {}) \
                           .get("ota:ProfileInfo", {}) \
                           .get("ota:Profile", {}) \
                           .get("ota:Customer", {}) \
                           .get("ota:PersonName", {}) \
                           .get("ota:GivenName", "null")

def get_item_safe(lst, index, default=None):
    return lst[index] if index < len(lst) else default


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

