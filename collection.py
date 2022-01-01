#!/bin/env/python
"""
This script fetches a collection and tries to semi-automatically generate the ModID + WorkshopItems + Map parameters for your config.ini

With the default collection_id: 2703232204



"""
import asyncio
import re

import aiohttp
from bs4 import BeautifulSoup


mod_id_regex = re.compile(r'Mod ID:.*')
map_folder_regex = re.compile(r'Map Folder:.*')

collection_id = 2703232204

# If this is given, it will no longer ask the user about what to exclude. (Mod ID on the steam page, WorkshopItems in the config)
exclude_workshop_items = [
    "LitSortOGSN_gold",
    "LitSortOGSN_diamond",
    "LitSortOGSN_chocolate",
    "LitSortOGSN_rice",
    "Authentic Z - Fashion Montage",
    "ATA_Jeep_x10",
    "ATA_Jeep_x4",
    "PLLootF",
    "PLLootG",
    "PLLootF_Patch",
    "PLLootG_Patch",
    ""
]


async def do_mod_request(session, mod_id, mod_link):
    # Now time to guess the Workshop Item Name
    print(f"Fetch Workshop data for {mod_id}")
    async with session.get(mod_link) as req:
        mod_soup = BeautifulSoup(await req.text(), 'html.parser')

    # We want to just look inside the Description and look for "Workshop ID: ".
    workshop_names = mod_soup.find("div", class_="workshopItemDescription").find_all(string=mod_id_regex)
    map_folder = mod_soup.find("div", class_="workshopItemDescription").find_all(string=map_folder_regex)
    # TODO: Detect dependencies and make sure we have all of them at the end.
    dependencies = []
    return mod_id, mod_link, workshop_names, map_folder, dependencies


async def main():

    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://steamcommunity.com/sharedfiles/filedetails/?id={collection_id}") as req:
            soup = BeautifulSoup(await req.text(), 'html.parser')
        list_of_items = soup.find_all('div', class_='collectionItem')

        mod_links = []

        for value in list_of_items:
            mod_id = value['id'].lstrip('sharedfile_')
            mod_link = value.div.a['href']
            mod_links.append((mod_id, mod_link))
        print("Starting to fetch all Workshop Item Descriptions")
        return await asyncio.gather(*(do_mod_request(session, mod_id, mod_link) for mod_id, mod_link in mod_links))


workshop_items = asyncio.run(main())

# Sets to avoid duplicates.
mod_ids = set()
mod_names = set()
map_folders = set()

for mod_id, mod_link, workshop_names, map_folder, dependencies in workshop_items:
    if not workshop_names:
        print(f"Could not find a MOD ID for {mod_link}")

    # If there's only 1 workshop name or all items are the same name
    if len(workshop_names) == 1 or all(x == workshop_names[0] for x in workshop_names):
        mod_ids.add(mod_id.replace("Workshop ID:", "").strip())
        mod_names.add(workshop_names[0].replace("Mod ID:", "").strip())
    else:
        print(f"Found multiple Workshop items/Mod IDS for {mod_link}")

        if exclude_workshop_items:
            for i, it in enumerate(workshop_names):
                mod_name = it.replace("Mod ID:", "").strip()
                if mod_name in exclude_workshop_items:
                    print(f"{i+1}. {mod_name} SKIPPED")
                    continue
                print(f"{i+1}. {mod_name}")
                mod_ids.add(mod_id.replace("Workshop ID:", "").strip())
                mod_names.add(mod_name)


        else:
            # Print out and ask the user about it.
            for i, it in enumerate(workshop_names):
                print(f"{i+1}. {it}")

            while True:
                wanted = input(f"Please select which workshop names to add separated by commas (i.e. 1 or 1,2,3)")

                try:
                    if not wanted:
                        raise IndexError
                    for i in wanted.split(','):
                        mod_names.add(workshop_names[int(i)-1].replace("Mod ID:", "").strip())
                    break
                except IndexError:
                    print("Invalid number given.")

    if map_folder:
        map_folders.extend(map_folder)


breakpoint()

map_folders.add("Muldraugh, KY")
print("Mods=" + ";".join(mod_names))
print("WorkshopItems=" + ";".join(mod_ids))
print("Map=:" + ";".join(map_folders))
breakpoint()
