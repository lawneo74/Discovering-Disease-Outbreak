# %% [markdown]
# ## Step 1: Extract city and country names
# 
# Tasks:
# - Data exploration
# - Some are US state rather than city name
# - Make 'City' an optional search term, as 'City' is sometimes omitted in the headline, e.g., 'Cebu'
# - Different ways to name the city: 'St. Louis' and 'St Louis' (without period)
# - Get US states and their cities
#   
# Output: 
# df -> dataframe with 3 columns (headlines, city, country)

# %%
# Import libraries
import geonamescache
from unidecode import unidecode
import pandas as pd
import re
from pathlib import Path
import pickle

# %%
# Read in headlines as list
with open("./data/headlines.txt", "r") as fh:
    all_headlines = fh.readlines()

# Replace 'Saints' with 'St.' and strip any trailing space
headlines = [headline.replace('Saint', 'St.').strip() for headline in all_headlines]

# %% [markdown]
# ### Load/Create a dictionary of US states and the cities in each US states - 'US_states_get_cities'
# 
# Note that it takes a long time to create the dictionary ('US_states_cities.pkl')

# %%
if Path('US_states_cities.pkl').is_file():
    US_state_get_cities = pickle.load(open('US_states_cities.pkl', 'rb'))
    gen_US_states_cities = False
else:
    gen_US_states_cities = True

if gen_US_states_cities:
    
    # for locating US state based on longitude and latitude
    from geopy.geocoders import Nominatim

    # extract US city names and coordinates
    US_cities = [cities[key]['name'] for key in list(cities.keys())
                if cities[key]['countrycode'] == 'US']
    US_longs = [cities[key]['longitude'] for key in list(cities.keys())
                if cities[key]['countrycode'] == 'US']
    US_latts = [cities[key]['latitude'] for key in list(cities.keys())
                if cities[key]['countrycode'] == 'US']

    def get_states(longs, latts):
        states = []
    
        # use a coordinate tool (Nominatim) from the geopy library
        geolocator = Nominatim(user_agent='anonymous@gmail.com')
        for lon, lat in zip(longs, latts):
            try:\
                # get the name of the state
                location = geolocator.reverse(str(lat)+', '+str(lon))
                state = location.raw['address']['state']
            except:
                # return empty string
                state = ''
            states.append(state)
        return states

    # takes a long time to run the function below.
    US_states = get_states(US_longs, US_latts)

    US_state_get_cities = {}

    for city, state in zip(US_cities, US_states):       
        if state != '': 
            if state in US_state_get_cities.keys():
                US_state_get_cities[state].append(city)
            elif state not in US_state_get_cities.keys():
                US_state_get_cities[state] = [city]

    with open('US_states_cities.pkl', 'wb') as fh:
        pickle.dump(US_state_get_cities, fh)
    
print('US_state_get_cities dictionary has been loaded/created: US_state_get_cities')

# %% [markdown]
# ### Load name of cities and countries from geonamescache

# %%
# Load a dictionary cities -> 'cities'
gc = geonamescache.GeonamesCache()
cities = gc.get_cities()
countries = gc.get_countries()

# %%
# Remove '(' and ')' in city name for regex expession; remove 'Beach' from city name
city_dict = {}
for city in cities.values():
    city_name = city['name'].replace('(', '\(').replace(')','\)') 
    
    if city_name not in list(city_dict.keys()):
        # dictionary key: city name; value: [country name, population size]
        city_dict[city_name] = [countries[city['countrycode']]['name'], city['population']]
    if unidecode(city_name) != city_name:
    # not in list(city_dict.keys()):
        city_dict[unidecode(city_name)] = [countries[city['countrycode']]['name'], city['population']]
    if city['population'] > city_dict[city_name][1]:
        # set 'city' as the one which is most populous
        city_dict[city_name] = [countries[city['countrycode']]['name'], city['population']]

for city_name, city_val in city_dict.items():
    city_dict[city_name] = city_val[0]

# %%
# remove 'Beach', 'Beaches', 'City' from city names 
city_beach_dict = {}
city2_dict = {}

for city_name, city_data in city_dict.items():
    if 'Beach' in city_name:
        new_city_name = city_name.replace('Beaches', '').strip()
        new_city_name = new_city_name.replace('Beach', '').strip()
        city_beach_dict[new_city_name] = city_dict[city_name]
    if 'City' in city_name:
        new_city_name = city_name.replace('City', '').strip()
        city2_dict[new_city_name] = city_dict[city_name]

# %%
# generate list of city names
city_dict.update(city2_dict)
city_dict.update(city_beach_dict)
city_name = list(city_dict.keys())
print('Number of cities in search pattern:', len(city_name))

# %%
# compile search patterns using names of city
city_regex = re.compile(r'\b|\b'.join(city_name))
# compile search patterns using names of US states 
US_states_regex = re.compile(r"\b|\b".join(list(US_state_get_cities.keys())))

# %% [markdown]
# 

# %% [markdown]
# ### Search for name of city and country
# - Name with longest match length is taken as the city name
# - If name of city is not found using city_regex, then proceed to search for name of US states

# %%
city_headline = []
country_headline = []
num_headline_not_found = 0

for idx, hl in enumerate(headlines):
    possible_city = []
    
    if city_regex.search(hl):
        possible_city = city_regex.findall(hl)
    
    if len(possible_city) > 0:
        city_name2 = max(possible_city, key=len)  # return city name with the longest match 
        city_headline.append(city_name2)
        country_headline.append(city_dict[city_name2])
    else:
        # search for matches for name of US states
        if US_states_regex.search(hl):
            # if name of US state is found, then append the list of cities in the US state
            list_cities = US_state_get_cities[US_states_regex.search(hl).group()]
            city_headline.append(list_cities)
            country_headline.append('United States')
        else:
            # no success for the search in the headline
            city_headline.append('')
            country_headline.append('')
            num_headline_not_found += 1
            
if num_headline_not_found > 0:
    print('\n')
    print('Number of headline(s) with issue locating the city & country:', num_headline_not_found)

# %%
# Print a sample of headline, city and country
n1 = 0   # first entry to display
n2 = 5   # last entry to display

print('\n')
print('Sample of headline with city & country')

for headline, city, country in zip(headlines[n1:n2], city_headline[n1:n2], country_headline[n1:n2]):
    print(headline, " -- City/Country:", city,'/', country)

no_city_idx = [idx for idx, city in enumerate(city_headline) if city == '']

print('\n')
print('Sample of headlines (No City and Country)')
for i, idx in enumerate(no_city_idx[n1:n2], 1):
    print('{i} out of {total}:'.format(i=i, total=num_headline_not_found), headlines[idx])


# %%
# export to excel file: headlines_city_country.xlsx
df = pd.DataFrame({'headline':headlines, 'city':city_headline, 'country':country_headline})
df.to_excel('headlines_city_country.xlsx', index=False)


