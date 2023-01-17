# this file stores reference constants


# map component type integers to logical names
COMPONENT_TYPE_MAP = {
    0: 'other',
    1: 'boiler',
    2: 'tank shell',
    3: 'cone',
    4: 'floor',
    5: 'piping',
    6: 'panel'
}


# Gecko customers identified as power companies
POWER_CUST_LIST = [
    'AEP',
    'AES',
    'ALCOA',
    'Dominion',
    'Duke Energy',
    'East Kentucky Power Coop (EKPC)',
    'Hallador Power Company',
    'NRG',
    'Southern Co'
]

# some assumed conversions
DOLLARS_PER_MWH = 40
MWH_LOST_PER_OUTAGE = 120
CAP_FACTOR = 0.6
OUTAGES_PER_CRIT = 3
HOUSEHOLDS_PER_MW = 750