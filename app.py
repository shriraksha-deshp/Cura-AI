import calendar, hashlib, hmac, html, json, os, secrets, sqlite3, uuid
from datetime import date, datetime

import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
DB = os.getenv("DB_PATH", "records.db")

LANG_OPTIONS = ["ENGLISH", "HINDI", "TELUGU", "KANNADA"]

STRINGS = {
    "ENGLISH": {
        "disclaimer": "This tool explains documents in simple words. It is NOT a doctor and does not diagnose or recommend treatment. Always confirm with a qualified doctor.",
        "brand": "🩺 Cura AI",
        "signin_caption": "Sign in to see your health records.",
        "login": "Log in",
        "create_account": "Create account",
        "username": "Username",
        "password": "Password",
        "choose_username": "Choose a username",
        "choose_password": "Choose a password (6+ characters)",
        "mock_abha": "ABHA ID (mock)",
        "wrong_login": "Wrong username or password.",
        "validation_err": "Username needs 3+ characters and password 6+ characters.",
        "user_taken": "That username is taken. Try another.",
        "menu_dashboard": "🏠 Dashboard",
        "menu_upload": "📄 Upload report",
        "menu_timeline": "🕒 Timeline",
        "menu_details": "👤 My details",
        "menu_export": "📦 Export (FHIR)",
        "summary_lang": "Language",
        "gemini_key": "Gemini API key",
        "logout": "Log out",
        "demo_notice": "Use sample or fake reports for demos, not real records.",
        "hello": "Hello",
        "saved_reports": "report(s) saved",
        "test_trends": "Test trends",
        "trend_empty": "Upload and save a lab report to see your test trends here.",
        "trend_hint": "Save more reports to see a trend over time.",
        "weight": "Weight",
        "height": "Height",
        "age": "Age",
        "bmi": "BMI",
        "add_details_hint": "Fill in age, height and weight under My details to see your BMI.",
        "questions_for_doc": "Questions for your doctor",
        "questions_empty": "After you save a report, suggested questions show up here.",
        "your_treatment": "Your treatment",
        "treatment_empty": "Medicines from your prescriptions will appear here.",
        "from": "From",
        "cal_blue": "Blue days have a saved report.",
        "upload_title": "Upload a report",
        "upload_label": "Prescription or report (photo or PDF)",
        "analyze_btn": "Analyze",
        "api_key_err": "Add your Gemini API key in the sidebar.",
        "reading_doc": "Reading the document...",
        "read_err": "Could not read this document:",
        "save_timeline": "Save to my timeline",
        "saved_success": "Saved. Check your Dashboard and Timeline.",
        "timeline_title": "Timeline",
        "timeline_empty": "Nothing saved yet. Upload a document first.",
        "details_title": "My details",
        "details_saved": "Details saved.",
        "details_caption": "Your details help the app judge normal ranges and fill your health record.",
        "first_name": "First name",
        "last_name": "Last name",
        "age_label": "Age (years)",
        "gender_label": "Gender",
        "height_label": "Height (cm)",
        "weight_label": "Weight (kg)",
        "waist_label": "Waist (cm), optional",
        "save_details_btn": "Save details",
        "required_err": "Please fill in first name, age, height and weight.",
        "export_title": "Export (FHIR)",
        "export_desc": "All saved records as a FHIR-style bundle with your mock ABHA ID.",
        "download_json": "Download JSON",
        "summary": "Summary",
        "no_summary": "No summary available.",
        "diagnoses_mentioned": "Diagnoses mentioned:",
        "medicines": "Medicines",
        "test_results": "Test results",
        "qa_title": "Your questions, answered",
        "qa_caption": "General information based on this report. Your doctor decides what applies to you.",
        "more_questions": "More questions to ask your doctor",
        "re_analyze_hint": "Analyze this report again to get answers to these questions.",
        "no_findings": "No significant findings in this report",
        "bmi_note_intro": "Here is a note based on your height and weight:",
        "female": "Female",
        "male": "Male",
        "other": "Other",
        "prefer_not": "Prefer not to say"
    },
    "HINDI": {
        "disclaimer": "यह टूल केवल सरल शब्दों में समझाता है। यह कोई डॉक्टर नहीं है और न ही दवा या इलाज की सलाह देता है। हमेशा योग्य डॉक्टर से सलाह लें।",
        "brand": "🩺 क्यूरा एआई (Cura AI)",
        "signin_caption": "अपने स्वास्थ्य रिकॉर्ड देखने के लिए लॉग इन करें।",
        "login": "लॉग इन करें",
        "create_account": "खाता बनाएं",
        "username": "उपयोगकर्ता नाम (Username)",
        "password": "पासवर्ड",
        "choose_username": "उपयोगकर्ता नाम चुनें",
        "choose_password": "पासवर्ड चुनें (6+ अक्षर)",
        "mock_abha": "ABHA आईडी (मॉक)",
        "wrong_login": "गलत उपयोगकर्ता नाम या पासवर्ड।",
        "validation_err": "उपयोगकर्ता नाम 3+ और पासवर्ड 6+ अक्षरों का होना चाहिए।",
        "user_taken": "यह नाम पहले से लिया गया है। कोई अन्य चुनें।",
        "menu_dashboard": "🏠 डैशबोर्ड",
        "menu_upload": "📄 रिपोर्ट अपलोड करें",
        "menu_timeline": "🕒 टाइमलाइन",
        "menu_details": "👤 मेरा विवरण",
        "menu_export": "📦 निर्यात (FHIR)",
        "summary_lang": "भाषा",
        "gemini_key": "Gemini API कुंजी",
        "logout": "लॉग आउट",
        "demo_notice": "केवल डेमो के लिए उपयोग करें, असली रिकॉर्ड न डालें।",
        "hello": "नमस्ते",
        "saved_reports": "रिपोर्ट सहेजी गईं",
        "test_trends": "परीक्षण रुझान (Test Trends)",
        "trend_empty": "रुझान देखने के लिए लैब रिपोर्ट अपलोड करके सहेजें।",
        "trend_hint": "समय के साथ रुझान देखने के लिए अधिक रिपोर्ट सहेजें।",
        "weight": "वजन",
        "height": "ऊंचाई",
        "age": "आयु",
        "bmi": "बीएमआई",
        "add_details_hint": "बीएमआई देखने के लिए विवरण में आयु, ऊंचाई और वजन भरें।",
        "questions_for_doc": "डॉक्टर के लिए प्रश्न",
        "questions_empty": "रिपोर्ट सहेजने के बाद यहाँ प्रश्न दिखाई देंगे।",
        "your_treatment": "आपका उपचार / दवाएं",
        "treatment_empty": "आपके नुस्खे की दवाएं यहाँ दिखाई देंगी।",
        "from": "दिनांक",
        "cal_blue": "नीले दिनों में रिपोर्ट सहेजी गई है।",
        "upload_title": "रिपोर्ट अपलोड करें",
        "upload_label": "पर्चा या लैब रिपोर्ट (फोटो या PDF)",
        "analyze_btn": "विश्लेषण करें",
        "api_key_err": "साइडबार में अपनी Gemini API कुंजी दर्ज करें।",
        "reading_doc": "दस्तावेज़ पढ़ा जा रहा है...",
        "read_err": "यह दस्तावेज़ नहीं पढ़ा जा सका:",
        "save_timeline": "टाइमलाइन में सहेजें",
        "saved_success": "सहेज लिया गया। डैशबोर्ड और टाइमलाइन देखें।",
        "timeline_title": "टाइमलाइन",
        "timeline_empty": "अभी कुछ भी सहेजा नहीं गया है। पहले एक दस्तावेज़ अपलोड करें।",
        "details_title": "मेरा विवरण",
        "details_saved": "विवरण सहेजा गया।",
        "details_caption": "यह सामान्य सीमाओं को जांचने में सहायता करता है।",
        "first_name": "पहला नाम",
        "last_name": "उपनाम",
        "age_label": "आयु (वर्ष)",
        "gender_label": "लिंग",
        "height_label": "ऊंचाई (सेमी)",
        "weight_label": "वजन (किलो)",
        "waist_label": "कमर (सेमी), वैकल्पिक",
        "save_details_btn": "विवरण सहेजें",
        "required_err": "कृपया पहला नाम, आयु, ऊंचाई और वजन भरें।",
        "export_title": "निर्यात (FHIR)",
        "export_desc": "आपके मॉक ABHA ID के साथ FHIR-स्टाइल डेटा बंडल।",
        "download_json": "JSON डाउनलोड करें",
        "summary": "सारांश",
        "no_summary": "कोई सारांश उपलब्ध नहीं है।",
        "diagnoses_mentioned": "उल्लिखित निदान:",
        "medicines": "दवाएं",
        "test_results": "परीक्षण परिणाम",
        "qa_title": "आपके प्रश्नों के उत्तर",
        "qa_caption": "रिपोर्ट पर आधारित सामान्य जानकारी। डॉक्टर अंतिम निर्णय लेते हैं।",
        "more_questions": "डॉक्टर से पूछने के लिए अतिरिक्त प्रश्न",
        "re_analyze_hint": "उत्तर पाने के लिए इस रिपोर्ट का पुनः विश्लेषण करें।",
        "no_findings": "इस रिपोर्ट में कोई असामान्य निष्कर्ष नहीं मिला",
        "bmi_note_intro": "आपकी ऊंचाई और वजन के आधार पर सुझाव:",
        "female": "महिला",
        "male": "पुरुष",
        "other": "अन्य",
        "prefer_not": "बताना नहीं चाहते"
    },
    "TELUGU": {
        "disclaimer": "ఈ సాధనం నివేదికలను సరళమైన పదాలలో వివరిస్తుంది. ఇది డాక్టర్ కాదు మరియు ఎలాంటి చికిత్సను సూచించదు. ఎల్లప్పుడూ అర్హత కలిగిన వైద్యుడిని సంప్రదించండి.",
        "brand": "🩺 క్యూరా AI (Cura AI)",
        "signin_caption": "మీ ఆరోగ్య రికార్డులను చూడటానికి లాగిన్ అవ్వండి.",
        "login": "లాగిన్",
        "create_account": "ఖాతాను సృష్టించండి",
        "username": "యూజర్ నేమ్",
        "password": "పాస్‌వర్డ్",
        "choose_username": "యూజర్ నేమ్ ఎంచుకోండి",
        "choose_password": "పాస్‌వర్డ్ ఎంచుకోండి (6+ అక్షరాలు)",
        "mock_abha": "ABHA ID (మాక్)",
        "wrong_login": "తప్పు యూజర్ నేమ్ లేదా పాస్‌వర్డ్.",
        "validation_err": "యూజర్ నేమ్ 3+ మరియు పాస్‌వర్డ్ 6+ అక్షరాలు ఉండాలి.",
        "user_taken": "ఈ యూజర్ నేమ్ ఇప్పటికే ఉంది. మరొకటి ప్రయత్నించండి.",
        "menu_dashboard": "🏠 డ్యాష్‌బోర్డ్",
        "menu_upload": "📄 రిపోర్ట్ అప్‌లోడ్",
        "menu_timeline": "🕒 టైమ్‌లైన్",
        "menu_details": "👤 నా వివరాలు",
        "menu_export": "📦 ఎగుమతి (FHIR)",
        "summary_lang": "భాష",
        "gemini_key": "Gemini API కీ",
        "logout": "లాగ్ అవుట్",
        "demo_notice": "డెమో కోసం నమూనా రికార్డులను మాత్రమే ఉపయోగించండి.",
        "hello": "నమస్కారం",
        "saved_reports": "నివేదికలు భద్రపరచబడ్డాయి",
        "test_trends": "పరీక్షల పోకడలు (Test Trends)",
        "trend_empty": "పోకడలను చూడటానికి ల్యాబ్ నివేదికను అప్‌లోడ్ చేసి భద్రపరచండి.",
        "trend_hint": "పోకడలను ట్రాక్ చేయడానికి మరిన్ని నివేదికలను జోడించండి.",
        "weight": "బరువు",
        "height": "ఎత్తు",
        "age": "వయస్సు",
        "bmi": "BMI",
        "add_details_hint": "BMI చూడటానికి నా వివరాలలో వయస్సు, ఎత్తు, బరువు నమోదు చేయండి.",
        "questions_for_doc": "వైద్యుడిని అడగవలసిన ప్రశ్నలు",
        "questions_empty": "నివేదికను సేవ్ చేసిన తర్వాత ప్రశ్నలు ఇక్కడ కనిపిస్తాయి.",
        "your_treatment": "మీ చికిత్స / మందులు",
        "treatment_empty": "మీ ప్రిస్క్రిప్షన్ నుండి మందులు ఇక్కడ కనిపిస్తాయి.",
        "from": "తేదీ",
        "cal_blue": "నీలిరంగు తేదీలలో నివేదికలు సేవ్ చేయబడ్డాయి.",
        "upload_title": "నివేదికను అప్‌లోడ్ చేయండి",
        "upload_label": "ప్రిస్క్రిప్షన్ లేదా నివేదిక (ఫోటో లేదా PDF)",
        "analyze_btn": "విశ్లేషించండి",
        "api_key_err": "సైడ్‌బార్‌లో మీ Gemini API కీని నమోదు చేయండి.",
        "reading_doc": "పత్రాన్ని చదువుతోంది...",
        "read_err": "పత్రాన్ని చదవడం సాధ్యపడలేదు:",
        "save_timeline": "టైమ్‌లైన్‌కు సేవ్ చేయండి",
        "saved_success": "సేవ్ చేయబడింది. డ్యాష్‌బోర్డ్ మరియు టైమ్‌లైన్ తనిఖీ చేయండి.",
        "timeline_title": "టైమ్‌లైన్",
        "timeline_empty": "ఇంకా ఏమీ సేవ్ కాలేదు. ముందుగా పత్రాన్ని అప్‌లోడ్ చేయండి.",
        "details_title": "నా వివరాలు",
        "details_saved": "వివరాలు సేవ్ చేయబడ్డాయి.",
        "details_caption": "మీ వివరాలు సాధారణ పరిధులను గుర్తించడంలో సహాయపడతాయి.",
        "first_name": "మొదటి పేరు",
        "last_name": "ఇంటి పేరు",
        "age_label": "వయస్సు (సంవత్సరాలు)",
        "gender_label": "లింగం",
        "height_label": "ఎత్తు (సెం.మీ)",
        "weight_label": "బరువు (కిలోలు)",
        "waist_label": "నడుము కొలత (సెం.మీ), ఐచ్ఛికం",
        "save_details_btn": "వివరాలను సేవ్ చేయండి",
        "required_err": "దయచేసి పేరు, వయస్సు, ఎత్తు మరియు బరువును పూరించండి.",
        "export_title": "ఎగుమతి (FHIR)",
        "export_desc": "మీ మాక్ ABHA ID తో FHIR-శైలి బండిల్.",
        "download_json": "JSON డౌన్‌లోడ్ చేయండి",
        "summary": "సారాంశం",
        "no_summary": "సారాంశం అందుబాటులో లేదు.",
        "diagnoses_mentioned": "పేర్కొన్న రోగనిర్ధారణలు:",
        "medicines": "మందులు",
        "test_results": "పరీక్ష ఫలితాలు",
        "qa_title": "మీ ప్రశ్నలకు సమాధానాలు",
        "qa_caption": "ఈ నివేదిక ఆధారంగా సాధారణ సమాచారం. వైద్యుడి నిర్ణయమే తుది నిర్ణయం.",
        "more_questions": "వైద్యుడిని అడగవలసిన మరిన్ని ప్రశ్నలు",
        "re_analyze_hint": "సమాధానాల కోసం ఈ నివేదికను మళ్లీ విశ్లేషించండి.",
        "no_findings": "ఈ నివేదికలో ఎలాంటి తీవ్ర సమస్యలు కనుగొనబడలేదు",
        "bmi_note_intro": "మీ ఎత్తు మరియు బరువు ఆధారంగా సూచనలు:",
        "female": "స్త్రీ",
        "male": "పురుషుడు",
        "other": "ఇతర",
        "prefer_not": "చెప్పడానికి ఇష్టపడలేదు"
    },
    "KANNADA": {
        "disclaimer": "ಈ ಉಪಕರಣವು ವೈದ್ಯಕೀಯ ದಾಖಲೆಗಳನ್ನು ಸರಳ ಪದಗಳಲ್ಲಿ ವಿವರಿಸುತ್ತದೆ. ಇದು ವೈದ್ಯರಲ್ಲ ಮತ್ತು ಯಾವುದೇ ಚಿಕಿತ್ಸೆಯನ್ನು ಶಿಫಾರಸು ಮಾಡುವುದಿಲ್ಲ. ಯಾವಾಗಲೂ ಅರ್ಹ ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ.",
        "brand": "🩺 ಕ್ಯೂರ AI (Cura AI)",
        "signin_caption": "ನಿಮ್ಮ ಆರೋಗ್ಯ ದಾಖಲೆಗಳನ್ನು ವೀಕ್ಷಿಸಲು ಲಾಗಿನ್ ಆಗಿ.",
        "login": "ಲಾಗಿನ್",
        "create_account": "ಖಾತೆ ರಚಿಸಿ",
        "username": "ಬಳಕೆದಾರ ಹೆಸರು",
        "password": "ಪಾಸ್‌ವರ್ಡ್",
        "choose_username": "ಬಳಕೆದಾರ ಹೆಸರನ್ನು ಆಯ್ಕೆಮಾಡಿ",
        "choose_password": "ಪಾಸ್‌ವರ್ಡ್ ಆಯ್ಕೆಮಾಡಿ (6+ ಅಕ್ಷರಗಳು)",
        "mock_abha": "ABHA ID (ಮಾಕ್)",
        "wrong_login": "ತಪ್ಪು ಬಳಕೆದಾರ ಹೆಸರು ಅಥವಾ ಪಾಸ್‌ವರ್ಡ್.",
        "validation_err": "ಬಳಕೆದಾರ ಹೆಸರು ಕನಿಷ್ಠ 3 ಮತ್ತು ಪಾಸ್‌ವರ್ಡ್ ಕನಿಷ್ಠ 6 ಅಕ್ಷರಗಳಾಗಿರಬೇಕು.",
        "user_taken": "ಆ ಹೆಸರು ಈಗಾಗಲೇ ಬಳಕೆಯಲ್ಲಿದೆ. ಬೇರೆ ಹೆಸರನ್ನು ಪ್ರಯತ್ನಿಸಿ.",
        "menu_dashboard": "🏠 ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
        "menu_upload": "📄 ವರದಿ ಅಪ್‌ಲೋಡ್",
        "menu_timeline": "🕒 ಟೈಮ್‌ಲೈನ್",
        "menu_details": "👤 ನನ್ನ ವಿವರಗಳು",
        "menu_export": "📦 ರಫ್ತು (FHIR)",
        "summary_lang": "ಭಾಷೆ",
        "gemini_key": "Gemini API ಕೀ",
        "logout": "ಲಾಗ್ ಔಟ್",
        "demo_notice": "ಡೆಮೊಗಾಗಿ ಮಾದರಿ ದಾಖಲೆಗಳನ್ನು ಮಾತ್ರ ಬಳಸಿ.",
        "hello": "ನಮಸ್ಕಾರ",
        "saved_reports": "ದಾಖಲೆಗಳು ಉಳಿಸಲಾಗಿದೆ",
        "test_trends": "ಪರೀಕ್ಷಾ ಪ್ರವೃತ್ತಿಗಳು (Test Trends)",
        "trend_empty": "ಪ್ರವೃತ್ತಿಗಳನ್ನು ವೀಕ್ಷಿಸಲು ವರದಿಯನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ ಉಳಿಸಿ.",
        "trend_hint": "ಹೆಚ್ಚಿನ ವರದಿಗಳನ್ನು ಉಳಿಸಿದಂತೆ ಕಾಲಕ್ರಮೇಣ ಬದಲಾವಣೆ ತಿಳಿಯುತ್ತದೆ.",
        "weight": "ತೂಕ",
        "height": "ಎತ್ತರ",
        "age": "ವಯಸ್ಸು",
        "bmi": "BMI",
        "add_details_hint": "BMI ತಿಳಿಯಲು ನನ್ನ ವಿವರಗಳಲ್ಲಿ ವಯಸ್ಸು, ಎತ್ತರ ಮತ್ತು ತೂಕವನ್ನು ನಮೂದಿಸಿ.",
        "questions_for_doc": "ವೈದ್ಯರನ್ನು ಕೇಳಬೇಕಾದ ಪ್ರಶ್ನೆಗಳು",
        "questions_empty": "ವರದಿಯನ್ನು ಉಳಿಸಿದ ನಂತರ ಪ್ರಶ್ನೆಗಳು ಇಲ್ಲಿ ಕಾಣಿಸುತ್ತವೆ.",
        "your_treatment": "ನಿಮ್ಮ ಚಿಕಿತ್ಸೆ / ಔಷಧಿಗಳು",
        "treatment_empty": "ನಿಮ್ಮ ಔಷಧ ಚೀಟಿಯ ಔಷಧಿಗಳು ಇಲ್ಲಿ ಕಾಣಿಸುತ್ತವೆ.",
        "from": "ದಿನಾಂಕ",
        "cal_blue": "ನೀಲಿ ದಿನಗಳಲ್ಲಿ ವರದಿಗಳನ್ನು ಉಳಿಸಲಾಗಿದೆ.",
        "upload_title": "ವರದಿ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ",
        "upload_label": "ಔಷಧ ಚೀಟಿ ಅಥವಾ ಲ್ಯಾಬ್ ವರದಿ (ಫೋಟೋ ಅಥವಾ PDF)",
        "analyze_btn": "ವಿಶ್ಲೇಷಿಸಿ",
        "api_key_err": "ಸೈಡ್‌ಬಾರ್‌ನಲ್ಲಿ ನಿಮ್ಮ Gemini API ಕೀಯನ್ನು ನಮೂದಿಸಿ.",
        "reading_doc": "ದಾಖಲೆಯನ್ನು ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ...",
        "read_err": "ದಾಖಲೆಯನ್ನು ಓದಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ:",
        "save_timeline": "ಟೈಮ್‌ಲೈನ್‌ಗೆ ಉಳಿಸಿ",
        "saved_success": "ಉಳಿಸಲಾಗಿದೆ. ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ ಮತ್ತು ಟೈಮ್‌ಲೈನ್ ಪರಿಶೀಲಿಸಿ.",
        "timeline_title": "ಟೈಮ್‌ಲೈನ್",
        "timeline_empty": "ಇನ್ನೂ ಏನೂ ಉಳಿಸಲಾಗಿಲ್ಲ. ಮೊದಲು ದಾಖಲೆಯನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ.",
        "details_title": "ನನ್ನ ವಿವರಗಳು",
        "details_saved": "ವಿವರಗಳನ್ನು ಉಳಿಸಲಾಗಿದೆ.",
        "details_caption": "ನಿಮ್ಮ ವಿವರಗಳು ಸಾಮಾನ್ಯ ಮಿತಿಗಳನ್ನು ನಿರ್ಧರಿಸಲು ಸಹಾಯ ಮಾಡುತ್ತವೆ.",
        "first_name": "ಮೊದಲ ಹೆಸರು",
        "last_name": "ಕೊನೆಯ ಹೆಸರು",
        "age_label": "ವಯಸ್ಸು (ವರ್ಷಗಳು)",
        "gender_label": "ಲಿಂಗ",
        "height_label": "ಎತ್ತರ (ಸೆಂ.ಮೀ)",
        "weight_label": "ತೂಕ (ಕೆ.ಜಿ)",
        "waist_label": "ಸೊಂಟದ ಸುತ್ತಳತೆ (ಸೆಂ.ಮೀ), ಐಚ್ಛಿಕ",
        "save_details_btn": "ವಿವರಗಳನ್ನು ಉಳಿಸಿ",
        "required_err": "ದಯವಿಟ್ಟು ಹೆಸರು, ವಯಸ್ಸು, ಎತ್ತರ ಮತ್ತು ತೂಕವನ್ನು ಭರ್ತಿ ಮಾಡಿ.",
        "export_title": "ರಫ್ತು (FHIR)",
        "export_desc": "ನಿಮ್ಮ ಮಾಕ್ ABHA ID ಯೊಂದಿಗೆ FHIR ಮಾದರಿಯ ದಾಖಲೆ.",
        "download_json": "JSON ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ",
        "summary": "ಸಾರಾಂಶ",
        "no_summary": "ಯಾವುದೇ ಸಾರಾಂಶ ಲಭ್ಯವಿಲ್ಲ.",
        "diagnoses_mentioned": "ಗುರುತಿಸಲಾದ ರೋಗನಿರ್ಣಯ:",
        "medicines": "ಔಷಧಿಗಳು",
        "test_results": "ಪರೀಕ್ಷಾ ಫಲಿತಾಂಶಗಳು",
        "qa_title": "ನಿಮ್ಮ ಪ್ರಶ್ನೆಗಳಿಗೆ ಉತ್ತರಗಳು",
        "qa_caption": "ವರದಿಯ ಆಧಾರದ ಮೇಲೆ ಸಾಮಾನ್ಯ ಮಾಹಿತಿ. ವೈದ್ಯರ ತೀರ್ಮಾನವೇ ಅಂತಿಮ.",
        "more_questions": "ವೈದ್ಯರನ್ನು ಕೇಳಲು ಹೆಚ್ಚಿನ ಪ್ರಶ್ನೆಗಳು",
        "re_analyze_hint": "ಉತ್ತರಗಳನ್ನು ಪಡೆಯಲು ಈ ವರದಿಯನ್ನು ಮತ್ತೊಮ್ಮೆ ವಿಶ್ಲೇಷಿಸಿ.",
        "no_findings": "ಈ ವರದಿಯಲ್ಲಿ ಯಾವುದೇ ಗಂಭೀರ ಅಂಶಗಳು ಕಂಡುಬಂದಿಲ್ಲ",
        "bmi_note_intro": "ನಿಮ್ಮ ಎತ್ತರ ಮತ್ತು ತೂಕದ ಆಧಾರದ ಮೇಲೆ ಟಿಪ್ಪಣಿ:",
        "female": "ಮಹಿಳೆ",
        "male": "ಪುರುಷ",
        "other": "ಇತರ",
        "prefer_not": "ಹೇಳಲು ಇಷ್ಟವಿಲ್ಲ"
    }
}

def t(key):
    lang = st.session_state.get("selected_language", "ENGLISH")
    return STRINGS.get(lang, STRINGS["ENGLISH"]).get(key, STRINGS["ENGLISH"].get(key, key))

PROMPT = """You read medical documents (prescriptions, lab reports, discharge summaries; printed or
handwritten; English or Indian languages). Return ONLY one JSON object, no other text:
{
 "document_type": "prescription|lab_report|discharge_summary|other",
 "document_date": "YYYY-MM-DD or null",
 "doctor_or_lab": "string or null",
 "diagnoses": ["string"],
 "medicines": [{"name":"","dose":"","frequency":"","duration":""}],
 "tests": [{"name":"","value":"","unit":"","reference_range":"","flag":"normal|high|low|unknown"}],
 "summary": "3-5 short sentences in simple language",
 "abnormal_explanations": [{"item":"","meaning":""}],
 "questions_for_doctor": ["string"],
 "question_answers": [{"question":"","answer":""}]
}
Rules: use only what is visible; use null or "" if unreadable, never guess. Do not diagnose,
do not suggest medicines or doses. Explain abnormal values in general terms
("this is above the usual range; your doctor can tell you why").
question_answers: give one entry for EVERY item in questions_for_doctor, with the same question text.
Each answer is 2-4 short sentences of general health information in simple language, tied to the
values in THIS report. You may explain what a result means, common everyday habits that are widely
recommended for that kind of result (balanced meals, regular activity, sleep, staying hydrated), why
and how often such tests are usually repeated, and warning signs to watch for. Never diagnose, never
name or recommend any medicine, dose or supplement, and never say whether the person needs, should
start or should stop a medicine; for those say the doctor decides after a full check-up. If a question
cannot be answered from this report, say so plainly. End answers that depend on the person's own
health with a short reminder that the doctor makes the final call.
Write summary, abnormal_explanations meanings, questions_for_doctor and question_answers in: {lang}.
Keep medicine and test names in their original form."""


# ---------- database ----------
def db():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS records(
        id TEXT PRIMARY KEY, profile TEXT, doc_date TEXT, doc_type TEXT, data TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS users(
        username TEXT PRIMARY KEY, salt TEXT, pw_hash TEXT, abha TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS details(
        username TEXT PRIMARY KEY, first_name TEXT, last_name TEXT, age INTEGER,
        gender TEXT, height_cm INTEGER, weight_kg REAL, waist_cm REAL)""")
    for col in ("weight_kg", "waist_cm"):
        try:
            con.execute(f"ALTER TABLE details ADD COLUMN {col} REAL")
        except sqlite3.OperationalError:
            pass
    return con


# ---------- login ----------
def hash_pw(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 200_000).hex()


def create_user(username, password, abha):
    con = db()
    if con.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone():
        return False
    salt = secrets.token_hex(16)
    con.execute("INSERT INTO users VALUES (?,?,?,?)", (username, salt, hash_pw(password, salt), abha))
    con.commit()
    return True


def check_login(username, password):
    row = db().execute("SELECT salt, pw_hash, abha FROM users WHERE username=?", (username,)).fetchone()
    if row and hmac.compare_digest(hash_pw(password, row[0]), row[1]):
        return row[2]
    return None


def get_genders():
    return [t("female"), t("male"), t("other"), t("prefer_not")]


def get_details(username):
    row = db().execute("SELECT first_name, last_name, age, gender, height_cm, weight_kg, waist_cm FROM details "
                       "WHERE username=?", (username,)).fetchone()
    if not row:
        return {}
    return dict(zip(("first_name", "last_name", "age", "gender", "height_cm", "weight_kg", "waist_cm"), row))


def save_details(username, first, last, age, gender, height, weight, waist=None):
    con = db()
    con.execute("INSERT OR REPLACE INTO details VALUES (?,?,?,?,?,?,?,?)",
                (username, first, last, age, gender, height, weight, waist))
    con.commit()


def save_record(profile, data):
    con = db()
    con.execute("INSERT INTO records VALUES (?,?,?,?,?)",
                (str(uuid.uuid4()), profile, data.get("document_date") or str(date.today()),
                 data.get("document_type", "other"), json.dumps(data)))
    con.commit()


def load_records(profile):
    rows = db().execute("SELECT id, doc_date, doc_type, data FROM records WHERE profile=? "
                        "ORDER BY doc_date", (profile,)).fetchall()
    return [{"id": r[0], "date": r[1], "type": r[2], "data": json.loads(r[3])} for r in rows]


# ---------- AI ----------
def server_key():
    k = os.getenv("GEMINI_API_KEY")
    if k:
        return k
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return ""


def api_key():
    return server_key() or st.session_state.get("key", "")


def context(me):
    if me and me.get("age"):
        g = me.get("gender")
        return f"\nPatient context for reference ranges: age {me['age']}, gender {g}."
    return ""


def analyze(file, lang, me=None):
    client = genai.Client(api_key=api_key())
    part = types.Part.from_bytes(data=file.getvalue(), mime_type=file.type)
    resp = client.models.generate_content(
        model=MODEL,
        contents=[part, PROMPT.replace("{lang}", lang) + context(me)],
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    text = resp.text
    return json.loads(text[text.find("{"): text.rfind("}") + 1])


# ---------- FHIR Export ----------
def to_num(v):
    try:
        return float(str(v).replace(",", "").strip())
    except ValueError:
        return None


def to_fhir(records, profile, abha, me=None):
    me = me or {}
    patient = {"resourceType": "Patient", "name": [{"text": profile}],
               "identifier": [{"system": "https://healthid.abdm.gov.in", "value": abha}]}
    if me.get("first_name"):
        full = f'{me["first_name"]} {me.get("last_name", "")}'.strip()
        patient["name"] = [{"text": full, "family": me.get("last_name", ""), "given": [me["first_name"]]}]
        patient["birthDate"] = str(date.today().year - int(me["age"]))
    entries = [{"resource": patient}]
    if me.get("height_cm"):
        entries.append({"resource": {"resourceType": "Observation", "status": "final",
            "code": {"coding": [{"system": "http://loinc.org", "code": "8302-2"}], "text": "Body height"},
            "effectiveDateTime": str(date.today()),
            "valueQuantity": {"value": me["height_cm"], "unit": "cm"}}})
    if me.get("weight_kg"):
        entries.append({"resource": {"resourceType": "Observation", "status": "final",
            "code": {"coding": [{"system": "http://loinc.org", "code": "29463-7"}], "text": "Body weight"},
            "effectiveDateTime": str(date.today()),
            "valueQuantity": {"value": me["weight_kg"], "unit": "kg"}}})
    if me.get("waist_cm"):
        entries.append({"resource": {"resourceType": "Observation", "status": "final",
            "code": {"coding": [{"system": "http://loinc.org", "code": "8280-0"}], "text": "Waist circumference"},
            "effectiveDateTime": str(date.today()),
            "valueQuantity": {"value": me["waist_cm"], "unit": "cm"}}})
    for r in records:
        d, when = r["data"], r["date"]
        for m in d.get("medicines", []):
            entries.append({"resource": {"resourceType": "MedicationStatement", "status": "recorded",
                "medicationCodeableConcept": {"text": m.get("name", "")},
                "effectiveDateTime": when,
                "dosage": [{"text": f'{m.get("dose","")} {m.get("frequency","")} {m.get("duration","")}'.strip()}]}})
        for t_item in d.get("tests", []):
            num = to_num(t_item.get("value"))
            obs = {"resourceType": "Observation", "status": "final", "code": {"text": t_item.get("name", "")},
                   "effectiveDateTime": when,
                   "referenceRange": [{"text": t_item.get("reference_range", "")}]}
            if num is not None:
                obs["valueQuantity"] = {"value": num, "unit": t_item.get("unit", "")}
            else:
                obs["valueString"] = str(t_item.get("value", ""))
            code = {"high": "H", "low": "L", "normal": "N"}.get(t_item.get("flag"))
            if code:
                obs["interpretation"] = [{"coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                    "code": code}]}]
            entries.append({"resource": obs})
    return {"resourceType": "Bundle", "type": "collection", "entry": entries}


# ---------- UI Elements ----------
def show(d):
    st.subheader(t("summary"))
    st.write(d.get("summary") or t("no_summary"))
    if d.get("diagnoses"):
        st.write(f"**{t('diagnoses_mentioned')}** " + ", ".join(d["diagnoses"]))
    if d.get("medicines"):
        st.write(f"**{t('medicines')}**")
        st.dataframe(d["medicines"], use_container_width=True, hide_index=True)
    if d.get("tests"):
        st.write(f"**{t('test_results')}**")
        st.dataframe(d["tests"], use_container_width=True, hide_index=True)
    for a in d.get("abnormal_explanations", []):
        st.warning(f'**{a.get("item","")}**: {a.get("meaning","")}')
    qa = [x for x in d.get("question_answers", []) if x.get("question") and x.get("answer")]
    if qa:
        st.write(f"**{t('qa_title')}**")
        st.caption(t("qa_caption"))
        for x in qa:
            with st.expander(x["question"], expanded=True):
                st.write(x["answer"])
        answered = {x["question"].strip().lower() for x in qa}
        rest = [q for q in d.get("questions_for_doctor", []) if q.strip().lower() not in answered]
        if rest:
            st.write(f"**{t('more_questions')}**")
            for q in rest:
                st.write("- " + q)
    elif d.get("questions_for_doctor"):
        st.write(f"**{t('questions_for_doc')}**")
        for q in d["questions_for_doctor"]:
            st.write("- " + q)
        st.caption(t("re_analyze_hint"))
    st.caption(t("disclaimer"))


def has_findings(d):
    return any(item.get("flag") in ("high", "low") for item in d.get("tests", [])) or bool(d.get("abnormal_explanations"))


def bmi_info(me):
    h, w, age = me.get("height_cm"), me.get("weight_kg"), me.get("age")
    if not (h and w and age):
        return None
    if age < 18:
        return None, "info", "For under 18, weight is evaluated using age-based growth charts. Please consult a doctor."
    bmi = w / (h / 100) ** 2
    if bmi < 18.5:
        return bmi, "warn", "Weight is lower than typical healthy ranges for this height. Consult a physician."
    if bmi < 23:
        return bmi, "ok", "Weight is in the healthy range for this height. Maintain balanced habits."
    if bmi < 25:
        return bmi, "warn", "Weight is slightly above the healthy range for this height."
    return bmi, "warn", "Weight is above standard healthy limits for this height. Medical guidance is advised."


def show_bmi(me):
    info = bmi_info(me)
    if info is None:
        st.info(t("add_details_hint"))
        return
    bmi, level, text = info
    if bmi:
        st.metric(t("bmi"), f"{bmi:.1f}")
    {"ok": st.success, "warn": st.warning, "info": st.info}[level](text)


CSS = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
.stApp, .stApp p, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp button, .stApp input, .stApp li {
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.stApp { background: #F8FAFC; }
.stApp h1, .stApp h2, .stApp h3 { color: #0F172A; font-weight: 700; }
header[data-testid="stHeader"] { background: transparent; }
footer, #MainMenu { visibility: hidden; }
.block-container { padding-top: 2rem; max-width: 1300px; }
[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #E2E8F0; }
[data-testid="stSidebar"] [role="radiogroup"] { gap: 4px; }
[data-testid="stSidebar"] [role="radiogroup"] label {
    padding: 8px 12px; border-radius: 10px; width: 100%; cursor: pointer;
}
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child { display: none; }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: #F1F5F9; color: #2563EB; font-weight: 600;
}

[class*="st-key-card_"], [data-testid="stForm"] {
    background: #FFFFFF !important;
    border-radius: 16px !important;
    padding: 24px 26px !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
    border: 1px solid #E2E8F0 !important;
}

.stTextInput > div > div,
.stNumberInput > div > div,
.stSelectbox > div > div,
[data-baseweb="input"],
[data-baseweb="base-input"],
div[data-testid="stTextInputRootElement"] > div,
div[data-testid="stNumberInputRootElement"] > div {
    background-color: #F8FAFC !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 8px !important;
    transition: all 0.15s ease-in-out !important;
}

.stTextInput input, 
.stNumberInput input,
input[type="text"], 
input[type="password"], 
input[type="number"] {
    background-color: transparent !important;
    border: none !important;
    padding: 8px 12px !important;
    color: #1E293B !important;
    font-size: 0.95rem !important;
}

div[data-testid="stTextInputRootElement"] > div:focus-within,
div[data-testid="stNumberInputRootElement"] > div:focus-within,
div[data-testid="stSelectbox"] > div > div:focus-within,
[data-baseweb="input"]:focus-within {
    background-color: #FFFFFF !important;
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12) !important;
}

.brand { font-size: 1.25rem; font-weight: 700; color: #2563EB; margin: 4px 0 14px; }
.hello { font-size: 1.75rem; font-weight: 700; margin: 0; color: #0F172A; }
.muted { color: #64748B; font-size: 0.875rem; }
.stat { border-radius: 14px; padding: 16px 18px; min-height: 110px; border: 1px solid #E2E8F0; }
.stat .lbl { font-size: 0.85rem; color: #64748B; font-weight: 500; }
.stat .val { font-size: 1.6rem; font-weight: 700; margin: 4px 0 2px; color: #0F172A; }
.stat .sub { font-size: 0.75rem; color: #94A3B8; }
.stat.blue { background: #F0F7FF; border-color: #BFDBFE; }
.stat.blue .val { color: #1D4ED8; }
.stat.white { background: #FFFFFF; }
.stat.green { background: #F0FDF4; border-color: #BBF7D0; }
.stat.green .val { color: #15803D; }
.stat.sky { background: #F8FAFC; border-color: #E2E8F0; }

.cal { width: 100%; border-collapse: collapse; }
.cal th { color: #94A3B8; font-size: 0.75rem; font-weight: 600; padding: 4px; }
.cal td { text-align: center; padding: 3px; font-size: 0.85rem; }
.cal td span {
    display: inline-block; width: 28px; height: 28px; line-height: 28px; border-radius: 6px; color: #475569;
}
.cal td.rec span { background: #2563EB; color: #FFFFFF; font-weight: 600; }
.cal td.today span { border: 1.5px solid #2563EB; }
.med { display: flex; gap: 12px; align-items: center; padding: 10px 0; border-bottom: 1px solid #F1F5F9; }
.pill {
    width: 36px; height: 36px; border-radius: 8px; background: #F1F5F9; display: flex;
    align-items: center; justify-content: center; flex: none;
}
"""
esc = lambda v: html.escape(str(v or ""))

st.set_page_config(page_title="Cura AI", page_icon="🩺", layout="wide")
st.markdown("<style>" + CSS + "</style>", unsafe_allow_html=True)

if "selected_language" not in st.session_state:
    st.session_state["selected_language"] = "ENGLISH"


def start_session(username, abha):
    st.session_state["user"] = username
    st.session_state["abha"] = abha
    st.rerun()


def login_screen():
    with st.sidebar:
        st.session_state["selected_language"] = st.selectbox(
            t("summary_lang"), LANG_OPTIONS,
            index=LANG_OPTIONS.index(st.session_state.get("selected_language", "ENGLISH"))
        )

    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        with st.container(key="card_login"):
            st.markdown(f'<div class="brand">{t("brand")}</div>', unsafe_allow_html=True)
            st.caption(t("signin_caption"))
            t_in, t_new = st.tabs([t("login"), t("create_account")])
            with t_in:
                u = st.text_input(t("username"), key="li_user")
                p = st.text_input(t("password"), type="password", key="li_pass")
                if st.button(t("login"), type="primary"):
                    abha = check_login(u.strip().lower(), p)
                    if abha is None:
                        st.error(t("wrong_login"))
                    else:
                        start_session(u.strip().lower(), abha)
            with t_new:
                u = st.text_input(t("choose_username"), key="su_user")
                p = st.text_input(t("choose_password"), type="password", key="su_pass")
                abha = st.text_input(t("mock_abha"), "12-3456-7890-1234", key="su_abha")
                if st.button(t("create_account")):
                    u = u.strip().lower()
                    if len(u) < 3 or len(p) < 6:
                        st.error(t("validation_err"))
                    elif not create_user(u, p, abha):
                        st.error(t("user_taken"))
                    else:
                        start_session(u, abha)
            st.caption(t("disclaimer"))


if "user" not in st.session_state:
    login_screen()
    st.stop()

profile = st.session_state["user"]
abha = st.session_state["abha"]
me = get_details(profile)
name = f'{me.get("first_name", "")} {me.get("last_name", "")}'.strip() or profile

menu_map = {
    "dashboard": t("menu_dashboard"),
    "upload": t("menu_upload"),
    "timeline": t("menu_timeline"),
    "details": t("menu_details"),
    "export": t("menu_export"),
}

with st.sidebar:
    st.markdown(f'<div class="brand">{t("brand")}</div>', unsafe_allow_html=True)
    sel_page_label = st.radio("Menu", list(menu_map.values()), label_visibility="collapsed")
    st.divider()
    st.markdown(f"**{esc(name)}**")
    st.caption(f"{t('mock_abha')}: {abha}")
    
    cur_lang = st.selectbox(
        t("summary_lang"),
        LANG_OPTIONS,
        index=LANG_OPTIONS.index(st.session_state.get("selected_language", "ENGLISH"))
    )
    if cur_lang != st.session_state.get("selected_language"):
        st.session_state["selected_language"] = cur_lang
        st.rerun()

    if not server_key():
        st.text_input(t("gemini_key"), type="password", key="key")
    if st.button(t("logout")):
        for k in ("user", "abha", "result"):
            st.session_state.pop(k, None)
        st.rerun()
    st.caption(t("demo_notice"))


def stat(cls, label, value, sub=""):
    return f'<div class="stat {cls}"><div class="lbl">{label}</div><div class="val">{value}</div><div class="sub">{sub}</div></div>'


def bmi_label(b):
    if b < 18.5: return "Low"
    if b < 23: return "Healthy"
    if b < 25: return "Above healthy"
    return "High"


def calendar_card(recs):
    marked = {}
    for r in recs:
        try:
            d = datetime.strptime(r["date"], "%Y-%m-%d").date()
        except ValueError:
            continue
        marked.setdefault((d.year, d.month), set()).add(d.day)
    today = date.today()
    months = sorted({*marked, (today.year, today.month)}, reverse=True)
    with st.container(key="card_cal"):
        ym = st.selectbox("Month", months, label_visibility="collapsed",
                          format_func=lambda m: f"{calendar.month_name[m[1]]} {m[0]}")
        rows = ""
        for week in calendar.monthcalendar(*ym):
            cells = ""
            for d in week:
                if d == 0:
                    cells += "<td></td>"
                else:
                    cls = ("rec " if d in marked.get(ym, ()) else "") + \
                          ("today" if ym == (today.year, today.month) and d == today.day else "")
                    cells += f'<td class="{cls}"><span>{d}</span></td>'
            rows += f"<tr>{cells}</tr>"
        head = "".join(f"<th>{n}</th>" for n in ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"))
        st.markdown(f'<table class="cal"><tr>{head}</tr>{rows}</table>', unsafe_allow_html=True)
        st.caption(t("cal_blue"))


def treatment_card(recs):
    latest = next((r for r in reversed(recs) if r["data"].get("medicines")), None)
    with st.container(key="card_meds"):
        st.markdown(f"**{t('your_treatment')}**")
        if not latest:
            st.caption(t("treatment_empty"))
            return
        st.caption(f'{t("from")} {latest["date"]}')
        for m in latest["data"]["medicines"][:5]:
            detail = " · ".join(x for x in (m.get("dose"), m.get("frequency"), m.get("duration")) if x)
            st.markdown(f'<div class="med"><div class="pill">💊</div><div><b>{esc(m.get("name"))}</b><br>'
                        f'<span class="muted">{esc(detail)}</span></div></div>', unsafe_allow_html=True)


def page_dashboard():
    recs = load_records(profile)
    st.markdown(f'<div class="hello">{t("hello")}, {esc(me.get("first_name") or profile)}</div>'
                f'<p class="muted">{len(recs)} {t("saved_reports")}</p>', unsafe_allow_html=True)
    left, right = st.columns([2.3, 1], gap="medium")
    with left:
        with st.container(key="card_chart"):
            st.markdown(f"**{t('test_trends')}**")
            names = sorted({it["name"] for r in recs for it in r["data"].get("tests", []) if it.get("name")})
            if names:
                pick = st.selectbox("Test", names, label_visibility="collapsed", key="trend_pick")
                pts = {r["date"]: to_num(it.get("value")) for r in recs for it in r["data"].get("tests", [])
                       if it.get("name") == pick and to_num(it.get("value")) is not None}
                if pts:
                    df = pd.DataFrame({pick: list(pts.values())}, index=list(pts.keys()))
                    st.area_chart(df, color="#2563EB", height=250)
                    if len(pts) < 2:
                        st.caption(t("trend_hint"))
            else:
                st.write(t("trend_empty"))
        w, h, a = me.get("weight_kg"), me.get("height_cm"), me.get("age")
        info = bmi_info(me)
        c1, c2, c3, c4 = st.columns(4, gap="small")
        c1.markdown(stat("blue", t("weight"), f"{w:g} kg" if w else "—"), unsafe_allow_html=True)
        c2.markdown(stat("white", t("height"), f"{h:g} cm" if h else "—"), unsafe_allow_html=True)
        c3.markdown(stat("green", t("age"), f"{a} yrs" if a else "—"), unsafe_allow_html=True)
        c4.markdown(stat("sky", t("bmi"), f"{info[0]:.1f}" if info and info[0] else "—",
                         bmi_label(info[0]) if info and info[0] else "—"), unsafe_allow_html=True)
        if not info:
            st.caption(t("add_details_hint"))
        with st.container(key="card_notes"):
            st.markdown(f"**{t('questions_for_doc')}**")
            latest = next((r for r in reversed(recs) if r["data"].get("questions_for_doctor")), None)
            if not latest:
                st.caption(t("questions_empty"))
            else:
                for i, q in enumerate(latest["data"]["questions_for_doctor"][:5]):
                    st.checkbox(q, key=f"q_{latest['id']}_{i}")
    with right:
        calendar_card(recs)
        treatment_card(recs)


def page_upload():
    st.markdown(f'<div class="hello">{t("upload_title")}</div>', unsafe_allow_html=True)
    with st.container(key="card_upload"):
        f = st.file_uploader(t("upload_label"), type=["png", "jpg", "jpeg", "pdf"])
        if f and st.button(t("analyze_btn"), type="primary"):
            if not api_key():
                st.error(t("api_key_err"))
            else:
                with st.spinner(t("reading_doc")):
                    try:
                        st.session_state["result"] = analyze(f, st.session_state["selected_language"].title(), me)
                    except Exception as e:
                        st.error(f"{t('read_err')} {e}")
    if "result" in st.session_state:
        with st.container(key="card_result"):
            show(st.session_state["result"])
            if not has_findings(st.session_state["result"]):
                st.divider()
                st.subheader(t("no_findings"))
                st.write(t("bmi_note_intro"))
                show_bmi(me)
            if st.button(t("save_timeline")):
                save_record(profile, st.session_state.pop("result"))
                st.success(t("saved_success"))


def page_timeline():
    st.markdown(f'<div class="hello">{t("timeline_title")}</div>', unsafe_allow_html=True)
    recs = load_records(profile)
    if not recs:
        st.write(t("timeline_empty"))
    for r in reversed(recs):
        with st.expander(f'{r["date"]} · {r["type"].replace("_", " ")}'):
            show(r["data"])


def page_details():
    st.markdown(f'<div class="hello">{t("details_title")}</div>', unsafe_allow_html=True)
    if st.session_state.pop("saved", False):
        st.success(t("details_saved"))
    with st.container(key="card_form"):
        st.caption(t("details_caption"))
        with st.form("details"):
            c1, c2 = st.columns(2)
            first = c1.text_input(t("first_name"), me.get("first_name", ""))
            last = c2.text_input(t("last_name"), me.get("last_name", ""))
            age = c1.number_input(t("age_label"), min_value=0, max_value=120, value=me.get("age"), step=1)
            genders = get_genders()
            cur_g = me.get("gender")
            g_idx = genders.index(cur_g) if cur_g in genders else 0
            gender = c2.selectbox(t("gender_label"), genders, index=g_idx)
            height = c1.number_input(t("height_label"), min_value=50, max_value=250, value=me.get("height_cm"), step=1)
            weight = c2.number_input(t("weight_label"), min_value=10.0, max_value=300.0, value=me.get("weight_kg"), step=0.5)
            waist = c1.number_input(t("waist_label"), min_value=30.0, max_value=200.0, value=me.get("waist_cm"), step=0.5)
            if st.form_submit_button(t("save_details_btn"), type="primary"):
                if not first.strip() or age is None or height is None or weight is None:
                    st.error(t("required_err"))
                else:
                    save_details(profile, first.strip(), last.strip(), int(age), gender, int(height),
                                 float(weight), float(waist) if waist is not None else None)
                    st.session_state["saved"] = True
                    st.rerun()
    with st.container(key="card_bmi"):
        show_bmi(me)


def page_export():
    st.markdown(f'<div class="hello">{t("export_title")}</div>', unsafe_allow_html=True)
    with st.container(key="card_export"):
        st.write(t("export_desc"))
        st.download_button(t("download_json"), json.dumps(to_fhir(load_records(profile), profile, abha, me), indent=2),
                           file_name="health_records_fhir.json", mime="application/json")


routing = {
    menu_map["dashboard"]: page_dashboard,
    menu_map["upload"]: page_upload,
    menu_map["timeline"]: page_timeline,
    menu_map["details"]: page_details,
    menu_map["export"]: page_export,
}
routing[sel_page_label]()
st.caption(t("disclaimer"))