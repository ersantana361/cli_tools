#!/bin/bash

# Check if a date argument is provided
if [ -z "$1" ]; then
  echo "Usage: bash send_request.sh <date>"
  exit 1
fi

# Assign the first argument to the DATE variable
DATE="$1"

# Use the date in the XML payload
curl -X POST \
     -H "Content-Type: text/xml; charset=utf-8" \
     -d "<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\">
    <s:Header>
        <h:HTNGHeader xmlns:h=\"http://pms.tca-ss.com\" xmlns=\"http://pms.tca-ss.com\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">
            <From>
                <SystemId>ZATLAS</SystemId>
                <Credential>
                    <UserName>ZATLAS</UserName>
                    <Password>Z47L1S!</Password>
                </Credential>
            </From>
            <To>
                <SystemId>SUA</SystemId>
            </To>
        </h:HTNGHeader>
    </s:Header>
    <s:Body>
        <OTA_ReadRQ EchoToken=\"f206f483-0d49-421e-a53f-79abe7e6bfb3\" Version=\"1.0\" xmlns=\"http://www.opentravel.org/OTA/2003/05\">
            <ReadRequests>
                <HotelReadRequest>
                    <Verification>
                        <ReservationTimeSpan Start=\"$DATE\"/>
                    </Verification>
                </HotelReadRequest>
            </ReadRequests>
        </OTA_ReadRQ>
    </s:Body>
</s:Envelope>" \
     https://interfaces-v10-2.innsist.tca-ss.com:8501/TCAOTAServer

