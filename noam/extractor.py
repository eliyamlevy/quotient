def extract_inventory_items_prompt(text):
    prompt = f"Extract inventory items from this text '{text}' and return as JSON array. Each item should have: name, part number, quantity, and description. The description should be the material specification. Any fields you can't find leave blank. Return only the json response in plain text as if you were an api."
    return prompt

# print(extract_inventory_items_prompt("Hi, could I please get pricing for these items below and how fast you could get them shipped to Huntington Beach location.Alkemix 5-finger Lap Shear Panels in Alclad 2024-T3 quantity 100 Alkemix 5-finger Lap Shear Panels in Bare 7075-T6 quantity 50"))
# print(extract_inventory_items_prompt("HS606B4P5  Qty 100 NAS43DD10-78N   Qty 10 NAS845-3   Qty 10 HS5806AL3S8  Qty  2 MS16562-34  Qty 100 MS28774-228  Qty 100 NAS42HT6-44   Qty 100 D4-16TD1   Qty 1 YC-29204-BN  Qty 5 NAS43DD4-68N   Qty 100 HS4173C10-035   Qty  50 HS5542-04032     Qty 1 M45932/2-114    Qty 100 MS21920-36   Qty 100 HS6043-05R   Qty 3 NAS43DD10-80N   Qty 3 MS27576-4-86    Qty 4 NAS43DD8-10N   Qty 100"))
