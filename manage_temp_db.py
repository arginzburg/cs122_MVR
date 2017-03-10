# Code to take searches from NSF and TAGG and cache them temporarily

# Things that currently don't need to work for the presentation, but obviously
# should at some point:
    # deleting things... if there are more than 20 searches or more than 2000
    #   rows
    # printing warnings if there are too many search results, or blocking
    #   searches too large to store in the temporary database
    # searching specific countries, rather than US or everything

# We can add more options later, but for now it...
# Expects searches as a dictionary with the keys : value data types as follows
    # years : list of strings, empty if nothing selected
    # US_awards : True/False
    # keywords : a string of what the user searched, or the empty string
    # agency : ["NSF", "CDC", "NIH"] zero or more of these strings
# for the search we want to demonstrate, which looks for abstracts with
    # "HIV virus immunology" in the US in the year 2012:
    # search = {"year" : ["2012"],
    #           "US_awards" : True,
    #           "keywords" : "HIV virus immunology",
    #            "agency" : ["NSF", "CDC", "NIH"]}

def split_search_by_source(search):
    if "NSF" in search["agency"]:
        url = generate_nsf_GET(search)

    if "CDC" in search["agency"] or "NIH" in search["agency"]:
        # do TAGG search


def generate_nsf_GET(search):
    base_url = ("https://www.nsf.gov/awardsearch/advancedSearchResult"
        "?PIId="
        "&PIFirstName="
        "&PILastName="
        "&PIOrganization="
        "&PIState="
        "&PIZip="
        "&PICountry={}"
        "&ProgOrganization="
        "&ProgEleCode="
        "&BooleanElement=All"
        "&ProgRefCode="
        "&BooleanRef=All"
        "&Program="
        "&ProgOfficer="
        "&Keyword={}"
        "&AwardNumberOperator="
        "&AwardAmount="
        "&AwardInstrument="
        "&ActiveAwards=true"
        "&ExpiredAwards=true"
        "&OriginalAwardDateOperator=Range"
        "&OriginalAwardDateFrom=01%2F01%2F{}"
        "&OriginalAwardDateTo=12%2F31%2F{}"
        "&StartDateOperator="
        "&ExpDateOperator=")
    
    year_list = search["year"]
    if year_list:
        year_list.sort()
        start_year = "01%2F01%2F" + year_list[0]
        end_year = "12%2F31%2F" + year_list[-1]
    else:
        start_year = {}
        end_year = {}

    if search["US_awards"]:
        country = "US"
    else:
        country = ""

    keywords = search["keywords"]
    if keywords:
        keywords = "+".join(keywords.split())

    return base_url.format(country, keywords, start_year, end_year)


# functions to check if the amount of results returned is totally unreasonable
# def count_nsf_awards(search):
# def count_tagg_awards(search):
