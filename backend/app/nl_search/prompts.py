"""Prompt for the parser. The LLM only extracts; resolve.py does all lookups and math.

The worked examples are built from RawParse objects, so they always list every field
in exactly the order Ollama must write them (see RawParse.llm_schema).
"""
from .models import RawParse

RULES = """You extract travel search criteria from a traveller's request (English or French) \
and return JSON only. You copy what the traveller wrote into fields. You never compute dates, \
totals or nights, and you never convert city names to airport codes.
Write EVERY field, in the order shown in the examples. Use null (or []) for anything not written.
Never invent budgets, dates, places or star ratings.

language: "fr" if the request is in French, otherwise "en".

trip_type:
  "all_inclusive": all-inclusive, all inclusive, tout inclus, tout-inclus.
  "flight_hotel": flight + hotel, vol + hôtel, package without all-inclusive.
  "flight_only": flight only, vol seulement, or ANY request about a flight/flying that never
                 mentions a hotel, resort or all-inclusive ("direct flight from X to Y").
  "hotel_only": hotel only, hôtel seulement.
  null only when nothing indicates the kind of trip.

adults: "for two", "my wife and I", "ma conjointe et moi", "nous deux" = 2. "just me", "seul" = 1.
  Children are NOT adults: "family of 4 with 2 kids" = 2 adults.
children_ages: ages of the children only. "2 adults and a 12-year-old" -> [12].
adults_only_resort: true only for "adults only", "adultes seulement", "adult resort".

FROM and TO: in "from Montreal to Paris", "Montreal to Paris", "de Québec vers Cancun",
"partir de Boston vers Dallas": the place after from / de / partir de is the ORIGIN;
the place after to / vers / à / au / en / in is the DESTINATION. Fill BOTH when both are written.
origin_airports: departure cities or airports EXACTLY as written ("Plattsburgh", "Montreal").
  Copy the words, never codes. [] if no departure place is written.
destinations: destination places exactly as written ("Paris", "Punta Cana", "Mexique", "Caribbean").
max_drive_hours: the number in any driving statement: "I can drive up to 4 hours",
  "willing to drive 3h", "je peux conduire jusqu'à 5 heures" -> 4 / 3 / 5.

WHEN (copy the parts only):
depart_month / depart_day: departure date or month. depart_year only if a year is written.
  "in February" -> depart_month 2, depart_day null.
window_end_month / window_end_day: only for a range of departure dates:
  "between March 1 and 10", "first two weeks of March" -> depart_day 1, window_end_month 3, window_end_day 14.
flex_days: "give or take 3 days", "plus ou moins 2 jours" -> 3 / 2.
return_month / return_day: ALWAYS fill when a return date is written ("coming back June 9",
  "back on the 19th", "retour le 15 janvier", "aller le 5 et retour le 9"). return_month null if not written.
nights_min / nights_max: only when a duration is written. "7 nights"/"a week"/"une semaine" -> 7 and 7.
  "about a week"/"environ une semaine" -> 6 and 8. "2 weeks"/"2 semaines" -> 14 and 14.
  "10 to 14 nights" -> 10 and 14. null when only a return date is given.

EXTRAS:
min_stars: "4.5 stars" or "4,5 étoiles" -> 4.5.
direct_flight_only: true for "direct", "non-stop", "vol direct", "sans escale"; otherwise null.
budget_amount: the number only. budget_per_person: true for "per person"/"par personne",
  false for a total or "for two".
preferences: short soft wishes in the traveller's words ("quiet", "nice beach", "tranquille").
"""

# Deliberately uses places that are NOT in tests/nl_search/cases.yaml (a test enforces this).
EXAMPLES = [
    ("Non-stop flight from Quebec City to Lisbon, leaving June 2, coming back June 16, just me",
     RawParse(language="en", trip_type="flight_only", adults=1,
              origin_airports=["Quebec City"], destinations=["Lisbon"],
              depart_month=6, depart_day=2, return_month=6, return_day=16,
              direct_flight_only=True)),
    ("All inclusive in Aruba for two, 5 nights in May, 4 stars, leaving from Ottawa or Montreal, "
     "I'm willing to drive 4 hours, max $2,000 per person",
     RawParse(language="en", trip_type="all_inclusive", adults=2,
              origin_airports=["Ottawa", "Montreal"], destinations=["Aruba"], max_drive_hours=4,
              depart_month=5, nights_min=5, nights_max=5, min_stars=4,
              budget_amount=2000, budget_per_person=True)),
    ("Vol seulement de Saint-Hubert vers Miami, aller le 3 avril et retour le 10, pour nous deux",
     RawParse(language="fr", trip_type="flight_only", adults=2,
              origin_airports=["Saint-Hubert"], destinations=["Miami"],
              depart_month=4, depart_day=3, return_day=10)),
]


def _render_examples() -> str:
    blocks = []
    for text, parsed in EXAMPLES:
        blocks.append(f"Request: {text}\n{parsed.model_dump_json()}")
    return "EXAMPLES\n\n" + "\n\n".join(blocks)


SYSTEM_PROMPT = RULES + "\n" + _render_examples() + "\n"

USER_TEMPLATE = "Request: {text}"

RETRY_TEMPLATE = (
    "Your previous JSON was rejected: {error}\n"
    "Return corrected JSON only, with every field, following the same rules.\nRequest: {text}"
)
