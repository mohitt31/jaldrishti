"""Conservative dictionary normalisation. Never invent transliterations of villages."""
import re

HEADERS = {
    "hi": "प्रश्न का उत्तर नीचे अंग्रेज़ी में, स्रोतों सहित दिया गया है।",
    "bn": "প্রশ্নের উত্তর নিচে ইংরেজিতে, উৎসসহ দেওয়া হয়েছে।",
}
# Exact aliases, not a general transliterator: unknown village names remain untouched.
DISTRICTS = {
    "Nadia": ["नदिया", "नादिया", "নদিয়া", "নদিয়া"],
    "North 24 Parganas": ["उत्तर 24 परगना", "উত্তর 24 পরগনা"],
    "South 24 Parganas": ["दक्षिण 24 परगना", "দক্ষিণ 24 পরগনা"],
    "Murshidabad": ["मुर्शिदाबाद", "মুর্শিদাবাদ"],
    "Malda": ["मालदा", "মালদা", "মালদহ"],
    "Birbhum": ["बीरभूम", "বীরভূম"],
    "Bankura": ["बांकुड़ा", "बांकुरा", "বাঁকুড়া", "বাঁকুড়া"],
    "Purulia": ["पुरुलिया", "পুরুলিয়া", "পুরুলিয়া"],
    "Alipurduar": ["अलीपुरद्वार", "আলিপুরদুয়ার"],
    "Cooch Behar": ["कूच बिहार", "কোচবিহার"],
    "Dakshin Dinajpur": ["दक्षिण दिनाजपुर", "দক্ষিণ দিনাজপুর"],
    "Uttar Dinajpur": ["उत्तर दिनाजपुर", "উত্তর দিনাজপুর"],
    "Darjeeling": ["दार्जिलिंग", "দার্জিলিং"],
    "Hooghly": ["हुगली", "হুগলি"], "Howrah": ["हावड़ा", "হাওড়া"],
    "Jalpaiguri": ["जलपाईगुड़ी", "জলপাইগুড়ি"],
    "Jhargram": ["झाड़ग्राम", "ঝাড়গ্রাম"],
    "Kalimpong": ["कालिम्पोंग", "কালিম্পং"], "Kolkata": ["कोलकाता", "কলকাতা"],
    "Paschim Bardhaman": ["पश्चिम बर्धमान", "পশ্চিম বর্ধমান"],
    "Purba Bardhaman": ["पूर्व बर्धमान", "পূর্ব বর্ধমান"],
    "Paschim Medinipur": ["पश्चिम मेदिनीपुर", "পশ্চিম মেদিনীপুর"],
    "Purba Medinipur": ["पूर्व मेदिनीपुर", "পূর্ব মেদিনীপুর"],
}
WORDS = {
    "आर्सेनिक": "arsenic", "আর্সেনিক": "arsenic",
    "फ्लोराइड": "fluoride", "ফ্লোরাইড": "fluoride",
    "भूजल": "groundwater", "ভূগর্ভস্থ জল": "groundwater", "ভূগর্ভস্থ": "groundwater",
    "जिला": "district", "जिले": "district", "জেলা": "district", "জেলায়": "district", "জেলার": "district",
    "अधिकतम": "maximum", "সর্বাধিক": "maximum", "সর্বোচ্চ": "maximum",
    "औसत": "mean", "গড়": "mean", "গড়": "mean",
    "कितना": "what", "কত": "what", "क्या": "what", "কি": "what",
    "कौन": "which", "কোন": "which", "प्रमाण": "evidence", "প্রমাণ": "evidence",
    "में": "in", "का": "of", "की": "of", "के": "of", "है": "", "हैं": "",
    "और": "and", "ও": "and", "এবং": "and", "মাত্রা": "value", "স্তর": "value",
    "मान": "value", "बताओ": "", "बताएं": "", "দেখাও": "", "আছে": "", "ছিল": "",
    "নমুনা": "sample", "नमूना": "sample", "রিপোর্ট": "report", "रिपोर्ट": "report",
}
DIGITS = str.maketrans("०१२३४५६७८९০১২৩৪৫৬৭৮৯", "01234567890123456789")
ALIASES = {alias: name for name, aliases in DISTRICTS.items() for alias in aliases} | WORDS
PATTERN = re.compile(r"(?<![\w\u0900-\u09ff])(?:" + "|".join(re.escape(x) for x in sorted(ALIASES, key=len, reverse=True)) + r")(?![\w\u0900-\u09ff])")

def normalize_question(text):
    language = "bn" if re.search(r"[\u0980-\u09ff]", text) else "hi" if re.search(r"[\u0900-\u097f]", text) else None
    if not language: return text, None
    normalized = PATTERN.sub(lambda m: ALIASES[m.group()], text.translate(DIGITS))
    return " ".join(normalized.replace("।", "?").split()), language
