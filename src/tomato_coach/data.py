"""Module 1 — data (knowledge base), bilingual (English / Bulgarian).

Built-in, offline content for growing organic tomatoes:
  * regions (stable key + localized name/note) and their average frost dates,
  * the ordered growth stages (measured in days from sowing),
  * a watering rule per stage,
  * organic care tips per stage (including hilling / earthing-up),
  * the two climate watering notes (warm / cool).

Every human-readable string is stored as ``{"en": ..., "bg": ...}`` and the
lookup helpers take a ``lang`` argument. Logic-only fields (keys, frost dates,
``start_day``, watering frequency) are language-independent. Unknown languages
fall back to English; unknown regions/stages raise a clear error.
"""
from __future__ import annotations

from dataclasses import dataclass

LANGUAGES = ("en", "bg")
DEFAULT_LANG = "en"


def normalize_lang(lang: str | None) -> str:
    """Return a supported language code, falling back to English."""
    return "bg" if lang == "bg" else "en"


def _t(field: dict, lang: str) -> str:
    """Pick the localized string for ``lang`` from a bilingual field."""
    return field.get(lang) or field[DEFAULT_LANG]


class UnknownRegionError(ValueError):
    """Raised when a region name/key is not in the built-in dataset."""


class UnknownStageError(ValueError):
    """Raised when a growth-stage key is not recognised."""


@dataclass(frozen=True)
class Region:
    """A growing region (localized) and its average frost dates (month, day)."""

    key: str
    name: str
    last_frost: tuple[int, int]   # average last spring frost
    first_frost: tuple[int, int]  # average first autumn frost
    note: str


@dataclass(frozen=True)
class Stage:
    """A growth stage (localized), beginning ``start_day`` days after sowing."""

    key: str
    label: str
    start_day: int
    description: str


@dataclass(frozen=True)
class WateringRule:
    """How often (and how) to water during a given stage (note localized)."""

    times_per_week: int
    note: str


# --- Regions -----------------------------------------------------------------
# Frost dates are typical averages and are meant as a guide.
_REGIONS_RAW: tuple[dict, ...] = (
    {
        "key": "northern-europe",
        "name": {"en": "Northern Europe", "bg": "Северна Европа"},
        "last_frost": (5, 15), "first_frost": (9, 25),
        "note": {
            "en": "Cool, short season — start indoors early and choose a fast variety.",
            "bg": "Хладен, кратък сезон — започнете разсада рано на закрито и изберете бързозреещ сорт.",
        },
    },
    {
        "key": "central-europe",
        "name": {"en": "Central Europe", "bg": "Централна Европа"},
        "last_frost": (4, 25), "first_frost": (10, 15),
        "note": {
            "en": "Moderate season with warm summers — a reliable all-round tomato climate.",
            "bg": "Умерен сезон с топло лято — надежден климат за домати.",
        },
    },
    {
        "key": "uk-ireland",
        "name": {"en": "UK & Ireland", "bg": "Великобритания и Ирландия"},
        "last_frost": (5, 1), "first_frost": (10, 31),
        "note": {
            "en": "Mild, damp maritime climate — watch for blight; a greenhouse helps.",
            "bg": "Мек, влажен морски климат — внимавайте за картофена мана; оранжерия помага.",
        },
    },
    {
        "key": "mediterranean",
        "name": {"en": "Mediterranean", "bg": "Средиземноморие"},
        "last_frost": (3, 15), "first_frost": (11, 30),
        "note": {
            "en": "Long, hot, dry season — easy tomato growing; mulch to hold moisture.",
            "bg": "Дълъг, горещ и сух сезон — лесно отглеждане; мулчирайте, за да задържите влагата.",
        },
    },
    {
        "key": "us-northeast",
        "name": {"en": "US Northeast", "bg": "Североизток на САЩ"},
        "last_frost": (5, 10), "first_frost": (10, 5),
        "note": {
            "en": "Cold winters, warm summers — transplant out after mid-May.",
            "bg": "Студени зими, топло лято — разсаждайте навън след средата на май.",
        },
    },
    {
        "key": "us-south",
        "name": {"en": "US South", "bg": "Юг на САЩ"},
        "last_frost": (3, 15), "first_frost": (11, 15),
        "note": {
            "en": "Long, hot season — plant early and again in late summer for a fall crop.",
            "bg": "Дълъг, горещ сезон — садете рано и отново в края на лятото за есенна реколта.",
        },
    },
)

# Lookup by key or by either language's name (case-insensitive).
_REGION_LOOKUP: dict[str, dict] = {}
for _raw in _REGIONS_RAW:
    _REGION_LOOKUP[_raw["key"].lower()] = _raw
    for _lang in LANGUAGES:
        _REGION_LOOKUP[_raw["name"][_lang].lower()] = _raw


# --- Growth stages -----------------------------------------------------------
# start_day = number of days after sowing when the stage begins.
_STAGES_RAW: tuple[dict, ...] = (
    {"key": "germination", "start_day": 0,
     "label": {"en": "Sowing & germination", "bg": "Сеитба и покълване"},
     "description": {"en": "Seeds sprout indoors in a warm, bright spot.",
                     "bg": "Семената покълват на закрито на топло и светло място."}},
    {"key": "seedling", "start_day": 14,
     "label": {"en": "Seedling", "bg": "Разсад"},
     "description": {"en": "Young plants grow their first true leaves indoors.",
                     "bg": "Младите растения развиват първите си истински листа на закрито."}},
    {"key": "transplant", "start_day": 42,
     "label": {"en": "Transplanting", "bg": "Разсаждане"},
     "description": {"en": "Harden off and move plants outdoors after the last frost.",
                     "bg": "Закалете и преместете растенията навън след последния слан."}},
    {"key": "vegetative", "start_day": 56,
     "label": {"en": "Vegetative growth", "bg": "Вегетативен растеж"},
     "description": {"en": "Rapid leaf and stem growth — time to support and prune.",
                     "bg": "Бърз растеж на листа и стъбла — време е за подпори и резитба."}},
    {"key": "flowering", "start_day": 84,
     "label": {"en": "Flowering", "bg": "Цъфтеж"},
     "description": {"en": "Yellow flowers appear and need pollinating.",
                     "bg": "Появяват се жълти цветове, които се нуждаят от опрашване."}},
    {"key": "fruiting", "start_day": 105,
     "label": {"en": "Fruiting", "bg": "Плодоносене"},
     "description": {"en": "Fruits set and swell — keep feeding and watering evenly.",
                     "bg": "Плодовете завързват и наедряват — продължавайте да подхранвате и поливате равномерно."}},
    {"key": "harvest", "start_day": 135,
     "label": {"en": "Harvest", "bg": "Прибиране на реколтата"},
     "description": {"en": "Ripe tomatoes are ready to pick.",
                     "bg": "Зрелите домати са готови за бране."}},
)

_STAGE_RAW_BY_KEY = {raw["key"]: raw for raw in _STAGES_RAW}


# --- Watering rules per stage ------------------------------------------------
_WATERING_RAW: dict[str, dict] = {
    "germination": {"times_per_week": 7, "note": {
        "en": "Keep the seed mix consistently moist; mist gently and never let it dry out.",
        "bg": "Поддържайте субстрата постоянно влажен; пръскайте леко и не допускайте да изсъхне."}},
    "seedling": {"times_per_week": 4, "note": {
        "en": "Water when the soil surface feels dry; avoid soggy roots.",
        "bg": "Поливайте, когато повърхността на почвата е суха; избягвайте преовлажняване на корените."}},
    "transplant": {"times_per_week": 4, "note": {
        "en": "Water in deeply at planting and keep evenly moist while roots establish.",
        "bg": "Полейте обилно при засаждане и поддържайте равномерна влажност, докато корените се захванат."}},
    "vegetative": {"times_per_week": 3, "note": {
        "en": "Water deeply at the base; keep the leaves dry to avoid disease.",
        "bg": "Поливайте обилно в основата; пазете листата сухи, за да избегнете болести."}},
    "flowering": {"times_per_week": 3, "note": {
        "en": "Keep moisture steady — uneven watering now causes blossom-end rot.",
        "bg": "Поддържайте равномерна влажност — неравномерното поливане сега причинява връхно гниене."}},
    "fruiting": {"times_per_week": 3, "note": {
        "en": "Deep, regular watering; ease off slightly as fruit ripens for better flavour.",
        "bg": "Дълбоко, редовно поливане; намалете леко при зреене на плодовете за по-добър вкус."}},
    "harvest": {"times_per_week": 2, "note": {
        "en": "Water only to stop plants wilting; drier soil concentrates flavour.",
        "bg": "Поливайте само колкото да не увяхват растенията; по-сухата почва концентрира вкуса."}},
}


# --- Climate watering notes (warm / cool) ------------------------------------
_CLIMATE_NOTES: dict[str, dict] = {
    "warm": {
        "en": "Your long, warm season dries soil fast — water in the early morning "
              "and check the soil daily in hot spells.",
        "bg": "Дългият, топъл сезон изсушава почвата бързо — поливайте рано сутрин "
              "и проверявайте почвата всеки ден в горещини.",
    },
    "cool": {
        "en": "In your cooler, damper climate, let the surface dry a little between "
              "waterings to limit disease.",
        "bg": "В по-хладния, влажен климат оставяйте повърхността да поизсъхне между "
              "поливанията, за да ограничите болестите.",
    },
}


# --- Organic care tips per stage ---------------------------------------------
_TIPS_RAW: dict[str, dict[str, tuple[str, ...]]] = {
    "germination": {
        "en": (
            "Use a fine seed-starting mix — no fertiliser needed yet.",
            "Keep at 20–25 °C near a bright window or under a grow light.",
            "Label each variety so you can tell them apart later.",
        ),
        "bg": (
            "Използвайте фин субстрат за разсад — все още не е нужен тор.",
            "Поддържайте 20–25 °C до светъл прозорец или под лампа за растеж.",
            "Етикетирайте всеки сорт, за да ги различавате по-късно.",
        ),
    },
    "seedling": {
        "en": (
            "Pot on into larger pots once the first true leaves appear.",
            "Brush the seedlings daily or run a fan to build sturdy stems.",
            "Feed weekly with a weak, diluted compost tea.",
        ),
        "bg": (
            "Прехвърлете в по-големи саксии, щом се появят първите истински листа.",
            "Докосвайте разсада всеки ден или пуснете вентилатор за здрави стъбла.",
            "Подхранвайте седмично със слаб разреден компостен чай.",
        ),
    },
    "transplant": {
        "en": (
            "Harden off over about a week before planting out — only after the last frost.",
            "Bury the stem deep, up to the lowest leaves, to grow extra roots (earthing-up / hilling).",
            "Mix compost into the hole and add crushed eggshells for calcium.",
        ),
        "bg": (
            "Закалявайте около седмица преди засаждане навън — само след последния слан.",
            "Заровете стъблото дълбоко, до най-долните листа, за повече корени (загърляне / насипване).",
            "Смесете компост в дупката и добавете натрошени черупки от яйца за калций.",
        ),
    },
    "vegetative": {
        "en": (
            "Hill / earth up soil around the base to support the new stem roots.",
            "Pinch out the side-shoots (suckers) on cordon types to focus energy.",
            "Mulch with straw to hold moisture in and keep weeds down.",
            "Stake or cage the plants now, before they get top-heavy.",
        ),
        "bg": (
            "Загърлете почвата около основата, за да подпомогнете новите корени по стъблото.",
            "Премахвайте колтуците (страничните разклонения) при високите сортове, за да насочите силата.",
            "Мулчирайте със слама, за да задържите влагата и да ограничите плевелите.",
            "Поставете подпори или клетки сега, преди растенията да натежат.",
        ),
    },
    "flowering": {
        "en": (
            "Gently shake the flowers or tap the supports to help pollination.",
            "Feed with an organic high-potassium feed such as comfrey tea.",
            "Remove the lowest leaves touching the soil to slow disease.",
        ),
        "bg": (
            "Леко разклащайте цветовете или потупвайте подпорите, за да подпомогнете опрашването.",
            "Подхранвайте с органичен тор, богат на калий, например чай от зарасличе (комфри).",
            "Премахнете най-долните листа, които докосват почвата, за да забавите болестите.",
        ),
    },
    "fruiting": {
        "en": (
            "Keep feeding every 1–2 weeks with a potassium-rich organic feed.",
            "Pick off any yellowing lower leaves.",
            "Once enough trusses have set, pinch out the growing tip to ripen the fruit.",
        ),
        "bg": (
            "Продължавайте да подхранвате на всеки 1–2 седмици с органичен тор, богат на калий.",
            "Откъсвайте пожълтелите долни листа.",
            "След като завържат достатъчно китки, отрежете връхчето, за да узреят плодовете.",
        ),
    },
    "harvest": {
        "en": (
            "Pick tomatoes as they colour up — they finish ripening off the vine.",
            "Harvest before the first frost; ripen green tomatoes indoors.",
            "Save seeds from your best fruits for next year.",
        ),
        "bg": (
            "Берете доматите, щом започнат да се оцветяват — доузряват и откъснати.",
            "Приберете реколтата преди първия слан; оставете зелените домати да узреят на закрито.",
            "Запазете семена от най-добрите плодове за следващата година.",
        ),
    },
}


def _build_region(raw: dict, lang: str) -> Region:
    return Region(
        key=raw["key"],
        name=_t(raw["name"], lang),
        last_frost=raw["last_frost"],
        first_frost=raw["first_frost"],
        note=_t(raw["note"], lang),
    )


def _build_stage(raw: dict, lang: str) -> Stage:
    return Stage(
        key=raw["key"],
        label=_t(raw["label"], lang),
        start_day=raw["start_day"],
        description=_t(raw["description"], lang),
    )


# Canonical ordered stages (in the default language) — used for logic/iteration.
STAGES: tuple[Stage, ...] = tuple(_build_stage(raw, DEFAULT_LANG) for raw in _STAGES_RAW)


def list_regions(lang: str = DEFAULT_LANG) -> list[Region]:
    """Return all supported regions in display order, localized to ``lang``."""
    lang = normalize_lang(lang)
    return [_build_region(raw, lang) for raw in _REGIONS_RAW]


def get_region(name_or_key: str, lang: str = DEFAULT_LANG) -> Region:
    """Look up a region by key or by either language's name (case-insensitive)."""
    if not name_or_key:
        raise UnknownRegionError("No region given.")
    raw = _REGION_LOOKUP.get(name_or_key.strip().lower())
    if raw is None:
        known = ", ".join(r["key"] for r in _REGIONS_RAW)
        raise UnknownRegionError(f"Unknown region: {name_or_key!r}. Known keys: {known}.")
    return _build_region(raw, normalize_lang(lang))


def get_stage(key: str, lang: str = DEFAULT_LANG) -> Stage:
    """Look up a growth stage by its key, localized to ``lang``."""
    raw = _STAGE_RAW_BY_KEY.get(key)
    if raw is None:
        known = ", ".join(s.key for s in STAGES)
        raise UnknownStageError(f"Unknown stage: {key!r}. Known stages: {known}.")
    return _build_stage(raw, normalize_lang(lang))


def get_tips(stage_key: str, lang: str = DEFAULT_LANG) -> list[str]:
    """Return the organic care tips for a stage key, localized to ``lang``."""
    if stage_key not in _TIPS_RAW:
        known = ", ".join(s.key for s in STAGES)
        raise UnknownStageError(f"Unknown stage: {stage_key!r}. Known stages: {known}.")
    return list(_TIPS_RAW[stage_key][normalize_lang(lang)])


def watering_rule(stage_key: str, lang: str = DEFAULT_LANG) -> WateringRule:
    """Return the watering rule for a stage key, with a localized note."""
    if stage_key not in _WATERING_RAW:
        known = ", ".join(s.key for s in STAGES)
        raise UnknownStageError(f"Unknown stage: {stage_key!r}. Known stages: {known}.")
    rec = _WATERING_RAW[stage_key]
    return WateringRule(rec["times_per_week"], _t(rec["note"], normalize_lang(lang)))


def climate_note(climate_key: str, lang: str = DEFAULT_LANG) -> str:
    """Return the localized watering note for a climate key ('warm' or 'cool')."""
    if climate_key not in _CLIMATE_NOTES:
        raise ValueError(f"Unknown climate key: {climate_key!r}.")
    return _t(_CLIMATE_NOTES[climate_key], normalize_lang(lang))
