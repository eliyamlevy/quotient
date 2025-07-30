def extract_inventory_items_prompt(text):
    prompt = f"""\
Extract inventory items from the following email text '{text}' and return as JSON array. \
Each email text represents a single order. \

IMPORTANT: Shipping location, client name, and clauses are ORDER-LEVEL information that applies to ALL items. \
Extract these from the email text and apply them to every item in the response. \

For each item, extract:
    part_number (alphanumeric key could be a material description)
    quantity (quantity of the item)
    description (material description)
    shipping_location (requested shipping location - same for all items)
    client_name (name of the client, from email signature - same for all items)
    clauses (alphanumeric keys that are not part numbers or material descriptions - same for all items)

The part number should be the material specification or an alphanumeric key, \
use context clues to infer if an alphanumeric key is a client id or a part number/material description. \
The description should be extracted from the material description, \
it is a more general description of the item and should only be 1-5 words. \

ORDER-LEVEL INFORMATION (apply to ALL items):
- Shipping location: Look for phrases like "shipping to [location]" in the email body
- Client name: Extract from the email signature at the end of the email. Look for the sender's name in the signature section, typically after "Thank you," or at the bottom of the email. Common patterns include "Name, Title" or "Name\nCompany". Extract just the person's name, not the company name.
- Clauses: Look for phrases like "clauses [list of codes]" in the email body

For images: Read ALL images that contain table data, order details, or relevant text information. \
Only ignore images that are clearly logos, signatures, or decorative elements. \
If an image contains order data (part numbers, quantities, etc.), extract that information. \
If shipping location or clauses are mentioned in the email text, use those values rather than \
trying to extract them from images. \

Clauses are alphanumeric keys related to terms and conditions that are not part numbers or material descriptions. \
They have the format of an upper case character followed by exactly three consecutive digits and sometimes another letter. \
Common clause categories include:
- AXXX: RFP/Bidder Instructions
- CXXX: Transportation/Shipping/Packaging/Marking/Routing  
- DXXX: Material
- EXXX: Property
- FXXX: Financial
- GXXX: Warranty
- HXXX: General Legal/Flowdown
- IXXX: Intellectual Property/Data
- JXXX: Repair/Rework/Overhaul
- MXXX: Miscellaneous
- QXXX: Quality

Make sure to read ALL THE TEXT AND IMAGES attached and compile all details related to the order. \
Every item in the response must include ALL fields (part_number, quantity, description, shipping_location, client_name, clauses). \
If you can't find a value for any field, use an empty string "". \
Return only the json response in plain text as if you were an api. \
Never return non-JSON text.
"""
    return prompt

"""
Below is a chart of the clauses. \

AXXX 	RFP/Bidder Instructions
CXXX 	Transportation/Shipping/Packaging/Marking/Routing
DXXX 	Material
EXXX 	Property
FXXX 	Financial
GXXX 	Warranty
HXXX 	General Legal/Flowdown
IXXX 	Intellectual Property/Data
JXXX 	Repair/Rework/Overhaul
MXXX 	Miscellaneous
QXXX 	Quality
"""

# print(extract_inventory_items_prompt("Hi, could I please get pricing for these items below and how fast you could get them shipped to Huntington Beach location.Alkemix 5-finger Lap Shear Panels in Alclad 2024-T3 quantity 100 Alkemix 5-finger Lap Shear Panels in Bare 7075-T6 quantity 50"))
# print(extract_inventory_items_prompt("HS606B4P5  Qty 100 NAS43DD10-78N   Qty 10 NAS845-3   Qty 10 HS5806AL3S8  Qty  2 MS16562-34  Qty 100 MS28774-228  Qty 100 NAS42HT6-44   Qty 100 D4-16TD1   Qty 1 YC-29204-BN  Qty 5 NAS43DD4-68N   Qty 100 HS4173C10-035   Qty  50 HS5542-04032     Qty 1 M45932/2-114    Qty 100 MS21920-36   Qty 100 HS6043-05R   Qty 3 NAS43DD10-80N   Qty 3 MS27576-4-86    Qty 4 NAS43DD8-10N   Qty 100"))

old = """\
The part number should be the material specification or an alphanumeric key, \
use context clues to infer if an alphanumeric key is a client id or a part number/material description. \
The name of the item should be the extracted from the material description, \
it is a more general description of the item and should only be 1-5 words. \
The client name is the name in the email signature at the end of each email. \
Make sure to ignore any images that look like logos and are not table data or relevant text data. \
Some images may be addresses, be sure to read through the entire email to make sure the address \
is not in the text. \
Clauses are alphanumeric keys that are not part numbers or material descriptions. \
They have the format of an upper case character followed by three digits and then \
is sometimes ended with another letter. Below is a chart of the clauses. \
"""