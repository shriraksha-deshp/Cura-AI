import calendar
import hashlib
import hmac
import html
import json
import os
import secrets
import sqlite3
import time
import uuid
from datetime import date, datetime

import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# ============================================================
# Cura AI — educational medical-document organizer
# Run: python -m streamlit run app.py
# ============================================================

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
DB = os.getenv("DB_PATH", "records.db")
LANG_OPTIONS = ["ENGLISH", "HINDI", "TELUGU", "TAMIL", "KANNADA"]

STRINGS = {
    "ENGLISH": {
        "disclaimer": "Cura AI explains documents in simple language. It is not a doctor, does not diagnose, and does not recommend treatment. Confirm medical decisions with a qualified clinician.",
        "brand": "🩺 Cura AI", "tagline": "✨ Your Gentle, Multilingual Health Companion",
        "signin_caption": "Sign in to organize and understand your health reports.",
        "login": "Log in", "create_account": "Create account", "username": "Username",
        "password": "Password", "choose_username": "Choose a username",
        "choose_password": "Choose a password (6+ characters)", "mock_abha": "ABHA ID (demo)",
        "wrong_login": "Invalid username or password.",
        "validation_err": "Username must be at least 3 characters and password at least 6 characters.",
        "user_taken": "That username is already taken.", "menu_dashboard": "🏠 Dashboard",
        "menu_upload": "📄 Upload report", "menu_timeline": "🕒 Timeline",
        "menu_details": "👤 My details", "summary_lang": "Language", "gemini_key": "Gemini API key",
        "logout": "Log out", "demo_notice": "🌱 Demonstration mode: use synthetic records for testing.",
        "hello": "Hello & welcome back", "saved_reports": "health reports saved",
        "test_trends": "📊 Biometric & lab trends",
        "trend_empty": "Upload and save a lab report to generate trends.",
        "trend_hint": "Save more reports to compare results across dates.",
        "weight": "Weight", "height": "Height", "age": "Age", "bmi": "BMI",
        "add_details_hint": "Add your age, height and weight under My Details to calculate BMI.",
        "questions_for_doc": "💬 Questions to discuss with your doctor",
        "questions_empty": "Save a report to see suggested discussion questions.",
        "your_treatment": "💊 Medicines in latest saved report",
        "treatment_empty": "Medicines parsed from saved prescriptions appear here.",
        "from": "Document date:", "cal_blue": "Highlighted dates have saved documents.",
        "upload_title": "Scan & analyze report",
        "upload_label": "Upload prescription or lab report (JPG, PNG, PDF)",
        "analyze_btn": "✨ Analyze document", "api_key_err": "The AI service is not configured. Please contact the Cura AI team.",
        "reading_doc": "Reading and analyzing the document…", "read_err": "Unable to analyze document:",
        "save_timeline": "💾 Save to my health timeline",
        "saved_success": "Report analyzed and saved to your timeline.",
        "timeline_title": "🕒 Clinical timeline",
        "timeline_empty": "No clinical history yet. Upload your first document.",
        "details_title": "👤 Personal health profile", "details_saved": "Profile updated.",
        "details_caption": "These details help provide context; they do not replace a clinician's assessment.",
        "first_name": "First name", "last_name": "Last name", "age_label": "Age (years)",
        "gender_label": "Gender", "height_label": "Height (cm)", "weight_label": "Weight (kg)",
        "waist_label": "Waist (cm), optional", "save_details_btn": "Save details",
        "required_err": "Please enter a first name and valid age, height and weight.",
        "summary": "Clinical overview", "no_summary": "No summary available.",
        "diagnoses_mentioned": "Diagnoses / observations mentioned:",
        "medicines": "Medicines listed in document", "test_results": "Biometric & lab parameters",
        "qa_title": "🌱 Plain-language answers", "qa_caption": "General educational information; confirm with your clinician.",
        "more_questions": "Questions for your next consultation",
        "no_findings": "No high/low flags were returned by the document parser",
        "bmi_note_intro": "BMI screening note based on your saved measurements:",
        "female": "Female", "male": "Male", "other": "Other", "prefer_not": "Prefer not to say",
        "open_modal": "🔍 Open full report", "quick_edit": "✏️ Quick edit measurements",
        "inspect": "🔍 Inspect details", "delete": "Delete saved report",
    },
    "HINDI": {
        "disclaimer": "Cura AI दस्तावेज़ों को सरल भाषा में समझाता है। यह डॉक्टर नहीं है, निदान नहीं करता और इलाज की सलाह नहीं देता। चिकित्सा निर्णयों के लिए योग्य डॉक्टर से सलाह लें।",
        "brand": "🩺 क्यूरा एआई", "tagline": "✨ आपका बहुभाषी स्वास्थ्य साथी",
        "signin_caption": "स्वास्थ्य रिपोर्ट देखने और व्यवस्थित करने के लिए लॉग इन करें।",
        "login": "लॉग इन", "create_account": "खाता बनाएं", "username": "उपयोगकर्ता नाम",
        "password": "पासवर्ड", "choose_username": "उपयोगकर्ता नाम चुनें",
        "choose_password": "पासवर्ड चुनें (कम से कम 6 अक्षर)", "mock_abha": "ABHA ID (डेमो)",
        "wrong_login": "उपयोगकर्ता नाम या पासवर्ड गलत है।",
        "validation_err": "उपयोगकर्ता नाम कम से कम 3 और पासवर्ड 6 अक्षरों का होना चाहिए।",
        "user_taken": "यह उपयोगकर्ता नाम पहले से मौजूद है।", "menu_dashboard": "🏠 डैशबोर्ड",
        "menu_upload": "📄 रिपोर्ट अपलोड", "menu_timeline": "🕒 टाइमलाइन",
        "menu_details": "👤 मेरा विवरण", "summary_lang": "भाषा", "gemini_key": "Gemini API कुंजी",
        "logout": "लॉग आउट", "demo_notice": "🌱 डेमो: परीक्षण के लिए नकली रिकॉर्ड उपयोग करें।",
        "hello": "नमस्ते, स्वागत है", "saved_reports": "स्वास्थ्य रिपोर्ट सहेजी गईं",
        "test_trends": "📊 परीक्षण रुझान", "trend_empty": "रुझान देखने के लिए लैब रिपोर्ट अपलोड करके सहेजें।",
        "trend_hint": "तुलना के लिए और रिपोर्ट सहेजें।", "weight": "वजन", "height": "ऊंचाई",
        "age": "आयु", "bmi": "BMI", "add_details_hint": "BMI के लिए मेरा विवरण में आयु, ऊंचाई और वजन भरें।",
        "questions_for_doc": "💬 डॉक्टर से पूछने के प्रश्न", "questions_empty": "रिपोर्ट सहेजने पर प्रश्न दिखेंगे।",
        "your_treatment": "💊 नवीनतम रिपोर्ट की दवाएं", "treatment_empty": "सहेजे गए पर्चे की दवाएं यहां दिखेंगी।",
        "from": "दस्तावेज़ दिनांक:", "cal_blue": "चिह्नित तारीखों पर दस्तावेज़ सहेजे गए हैं।",
        "upload_title": "रिपोर्ट स्कैन और विश्लेषण करें", "upload_label": "पर्चा या लैब रिपोर्ट (JPG, PNG, PDF)",
        "analyze_btn": "✨ दस्तावेज़ का विश्लेषण करें", "api_key_err": "AI सेवा कॉन्फ़िगर नहीं है। कृपया Cura AI टीम से संपर्क करें।",
        "reading_doc": "दस्तावेज़ का विश्लेषण हो रहा है…", "read_err": "दस्तावेज़ का विश्लेषण नहीं हो सका:",
        "save_timeline": "💾 टाइमलाइन में सहेजें", "saved_success": "रिपोर्ट टाइमलाइन में सहेजी गई।",
        "timeline_title": "🕒 स्वास्थ्य टाइमलाइन", "timeline_empty": "अभी कोई इतिहास नहीं है। पहले दस्तावेज़ अपलोड करें।",
        "details_title": "👤 स्वास्थ्य प्रोफ़ाइल", "details_saved": "प्रोफ़ाइल अपडेट हुई।",
        "details_caption": "ये विवरण संदर्भ देते हैं, डॉक्टर के मूल्यांकन का विकल्प नहीं हैं।",
        "first_name": "पहला नाम", "last_name": "उपनाम", "age_label": "आयु (वर्ष)",
        "gender_label": "लिंग", "height_label": "ऊंचाई (सेमी)", "weight_label": "वजन (किलो)",
        "waist_label": "कमर (सेमी), वैकल्पिक", "save_details_btn": "विवरण सहेजें",
        "required_err": "पहला नाम, आयु, ऊंचाई और वजन दर्ज करें।", "summary": "चिकित्सीय सारांश",
        "no_summary": "सारांश उपलब्ध नहीं है।", "diagnoses_mentioned": "उल्लिखित निदान / टिप्पणियां:",
        "medicines": "दवाएं", "test_results": "परीक्षण परिणाम", "qa_title": "🌱 सरल भाषा में उत्तर",
        "qa_caption": "सामान्य जानकारी; डॉक्टर से पुष्टि करें।", "more_questions": "डॉक्टर से पूछने के प्रश्न",
        "no_findings": "विश्लेषण में उच्च/निम्न संकेत नहीं मिले", "bmi_note_intro": "आपके माप पर आधारित BMI नोट:",
        "female": "महिला", "male": "पुरुष", "other": "अन्य", "prefer_not": "बताना नहीं चाहते",
        "open_modal": "🔍 पूरी रिपोर्ट देखें", "quick_edit": "✏️ माप संपादित करें",
        "inspect": "🔍 विवरण देखें", "delete": "सहेजी गई रिपोर्ट हटाएं",
    },
    "TELUGU": {
        "disclaimer": "Cura AI పత్రాలను సరళంగా వివరిస్తుంది. ఇది డాక్టర్ కాదు; రోగ నిర్ధారణ లేదా చికిత్స సూచనలు ఇవ్వదు. వైద్య నిర్ణయాల కోసం అర్హత కలిగిన వైద్యుడిని సంప్రదించండి.",
        "brand": "🩺 Cura AI", "tagline": "✨ మీ బహుభాషా ఆరోగ్య సహచరుడు",
        "signin_caption": "మీ ఆరోగ్య నివేదికలను చూడటానికి, నిర్వహించడానికి లాగిన్ అవ్వండి.",
        "login": "లాగిన్", "create_account": "ఖాతా సృష్టించండి", "username": "యూజర్ నేమ్",
        "password": "పాస్‌వర్డ్", "choose_username": "యూజర్ నేమ్ ఎంచుకోండి",
        "choose_password": "పాస్‌వర్డ్ (కనీసం 6 అక్షరాలు)", "mock_abha": "ABHA ID (డెమో)",
        "wrong_login": "యూజర్ నేమ్ లేదా పాస్‌వర్డ్ తప్పు.", "validation_err": "యూజర్ నేమ్ కనీసం 3, పాస్‌వర్డ్ 6 అక్షరాలు ఉండాలి.",
        "user_taken": "ఈ యూజర్ నేమ్ ఇప్పటికే ఉంది.", "menu_dashboard": "🏠 డ్యాష్‌బోర్డ్",
        "menu_upload": "📄 నివేదిక అప్‌లోడ్", "menu_timeline": "🕒 టైమ్‌లైన్",
        "menu_details": "👤 నా వివరాలు", "summary_lang": "భాష", "gemini_key": "Gemini API కీ",
        "logout": "లాగ్ అవుట్", "demo_notice": "🌱 డెమో కోసం నమూనా రికార్డులు ఉపయోగించండి.",
        "hello": "నమస్కారం", "saved_reports": "ఆరోగ్య నివేదికలు సేవ్ అయ్యాయి",
        "test_trends": "📊 పరీక్షల ట్రెండ్స్", "trend_empty": "ట్రెండ్స్ కోసం ల్యాబ్ నివేదికను అప్‌లోడ్ చేసి సేవ్ చేయండి.",
        "trend_hint": "పోల్చడానికి మరిన్ని నివేదికలు సేవ్ చేయండి.", "weight": "బరువు", "height": "ఎత్తు",
        "age": "వయస్సు", "bmi": "BMI", "add_details_hint": "BMI కోసం నా వివరాల్లో వయస్సు, ఎత్తు, బరువు నమోదు చేయండి.",
        "questions_for_doc": "💬 వైద్యుడిని అడగాల్సిన ప్రశ్నలు", "questions_empty": "నివేదిక సేవ్ చేసిన తర్వాత ప్రశ్నలు కనిపిస్తాయి.",
        "your_treatment": "💊 తాజా నివేదికలోని మందులు", "treatment_empty": "సేవ్ చేసిన ప్రిస్క్రిప్షన్ మందులు ఇక్కడ కనిపిస్తాయి.",
        "from": "పత్రం తేదీ:", "cal_blue": "గుర్తించిన తేదీల్లో పత్రాలు సేవ్ అయ్యాయి.",
        "upload_title": "నివేదికను విశ్లేషించండి", "upload_label": "ప్రిస్క్రిప్షన్ లేదా ల్యాబ్ నివేదిక (JPG, PNG, PDF)",
        "analyze_btn": "✨ పత్రాన్ని విశ్లేషించండి", "api_key_err": "AI సేవ కాన్ఫిగర్ చేయబడలేదు. దయచేసి Cura AI బృందాన్ని సంప్రదించండి.",
        "reading_doc": "పత్రాన్ని విశ్లేషిస్తోంది…", "read_err": "పత్రాన్ని విశ్లేషించలేకపోయాం:",
        "save_timeline": "💾 టైమ్‌లైన్‌కు సేవ్ చేయండి", "saved_success": "నివేదిక టైమ్‌లైన్‌లో సేవ్ అయింది.",
        "timeline_title": "🕒 ఆరోగ్య టైమ్‌లైన్", "timeline_empty": "ఇంకా చరిత్ర లేదు. మొదటి పత్రాన్ని అప్‌లోడ్ చేయండి.",
        "details_title": "👤 ఆరోగ్య ప్రొఫైల్", "details_saved": "ప్రొఫైల్ నవీకరించబడింది.",
        "details_caption": "ఈ వివరాలు సందర్భాన్ని అందిస్తాయి; వైద్యుడి అంచనాకు ప్రత్యామ్నాయం కావు.",
        "first_name": "మొదటి పేరు", "last_name": "ఇంటి పేరు", "age_label": "వయస్సు (సంవత్సరాలు)",
        "gender_label": "లింగం", "height_label": "ఎత్తు (సెం.మీ)", "weight_label": "బరువు (కిలోలు)",
        "waist_label": "నడుము (సెం.మీ), ఐచ్ఛికం", "save_details_btn": "వివరాలు సేవ్ చేయండి",
        "required_err": "మొదటి పేరు, వయస్సు, ఎత్తు, బరువు నమోదు చేయండి.", "summary": "వైద్య సారాంశం",
        "no_summary": "సారాంశం లేదు.", "diagnoses_mentioned": "పేర్కొన్న అంశాలు:",
        "medicines": "మందులు", "test_results": "పరీక్ష ఫలితాలు", "qa_title": "🌱 సరళమైన సమాధానాలు",
        "qa_caption": "సాధారణ సమాచారం; వైద్యుడిని సంప్రదించండి.", "more_questions": "వైద్యుడిని అడగాల్సిన ప్రశ్నలు",
        "no_findings": "విశ్లేషణలో అధిక/తక్కువ సూచనలు లేవు", "bmi_note_intro": "మీ కొలతల ఆధారంగా BMI గమనిక:",
        "female": "స్త్రీ", "male": "పురుషుడు", "other": "ఇతర", "prefer_not": "చెప్పదలచుకోలేదు",
        "open_modal": "🔍 పూర్తి నివేదిక చూడండి", "quick_edit": "✏️ కొలతలు మార్చండి",
        "inspect": "🔍 వివరాలు చూడండి", "delete": "సేవ్ చేసిన నివేదికను తొలగించండి",
    },
    "KANNADA": {
        "disclaimer": "Cura AI ವೈದ್ಯಕೀಯ ದಾಖಲೆಗಳನ್ನು ಸರಳವಾಗಿ ವಿವರಿಸುತ್ತದೆ. ಇದು ವೈದ್ಯರಲ್ಲ; ರೋಗನಿರ್ಣಯ ಅಥವಾ ಚಿಕಿತ್ಸೆಯನ್ನು ಶಿಫಾರಸು ಮಾಡುವುದಿಲ್ಲ. ವೈದ್ಯಕೀಯ ನಿರ್ಧಾರಗಳಿಗಾಗಿ ಅರ್ಹ ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ.",
        "brand": "🩺 Cura AI", "tagline": "✨ ನಿಮ್ಮ ಬಹುಭಾಷಾ ಆರೋಗ್ಯ ಸಹಾಯಕ",
        "signin_caption": "ನಿಮ್ಮ ಆರೋಗ್ಯ ವರದಿಗಳನ್ನು ವೀಕ್ಷಿಸಲು ಮತ್ತು ವ್ಯವಸ್ಥೆಗೊಳಿಸಲು ಲಾಗಿನ್ ಆಗಿ.",
        "login": "ಲಾಗಿನ್", "create_account": "ಖಾತೆ ರಚಿಸಿ", "username": "ಬಳಕೆದಾರ ಹೆಸರು",
        "password": "ಪಾಸ್‌ವರ್ಡ್", "choose_username": "ಬಳಕೆದಾರ ಹೆಸರನ್ನು ಆಯ್ಕೆಮಾಡಿ",
        "choose_password": "ಪಾಸ್‌ವರ್ಡ್ (ಕನಿಷ್ಠ 6 ಅಕ್ಷರಗಳು)", "mock_abha": "ABHA ID (ಡೆಮೊ)",
        "wrong_login": "ತಪ್ಪಾದ ಬಳಕೆದಾರ ಹೆಸರು ಅಥವಾ ಪಾಸ್‌ವರ್ಡ್.", "validation_err": "ಬಳಕೆದಾರ ಹೆಸರು ಕನಿಷ್ಠ 3 ಮತ್ತು ಪಾಸ್‌ವರ್ಡ್ 6 ಅಕ್ಷರಗಳಿರಬೇಕು.",
        "user_taken": "ಈ ಬಳಕೆದಾರ ಹೆಸರು ಈಗಾಗಲೇ ಇದೆ.", "menu_dashboard": "🏠 ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
        "menu_upload": "📄 ವರದಿ ಅಪ್‌ಲೋಡ್", "menu_timeline": "🕒 ಟೈಮ್‌ಲೈನ್",
        "menu_details": "👤 ನನ್ನ ವಿವರಗಳು", "summary_lang": "ಭಾಷೆ", "gemini_key": "Gemini API ಕೀ",
        "logout": "ಲಾಗ್ ಔಟ್", "demo_notice": "🌱 ಡೆಮೊ ಪರೀಕ್ಷೆಗೆ ಮಾದರಿ ದಾಖಲೆಗಳನ್ನು ಬಳಸಿ.",
        "hello": "ನಮಸ್ಕಾರ, ಸ್ವಾಗತ", "saved_reports": "ಆರೋಗ್ಯ ವರದಿಗಳು ಉಳಿಸಲಾಗಿದೆ",
        "test_trends": "📊 ಪರೀಕ್ಷಾ ಪ್ರವೃತ್ತಿಗಳು", "trend_empty": "ಪ್ರವೃತ್ತಿಗಳಿಗಾಗಿ ಲ್ಯಾಬ್ ವರದಿಯನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ ಉಳಿಸಿ.",
        "trend_hint": "ಹೋಲಿಕೆಗಾಗಿ ಇನ್ನಷ್ಟು ವರದಿಗಳನ್ನು ಉಳಿಸಿ.", "weight": "ತೂಕ", "height": "ಎತ್ತರ",
        "age": "ವಯಸ್ಸು", "bmi": "BMI", "add_details_hint": "BMI ಗಾಗಿ ನನ್ನ ವಿವರಗಳಲ್ಲಿ ವಯಸ್ಸು, ಎತ್ತರ ಮತ್ತು ತೂಕ ನಮೂದಿಸಿ.",
        "questions_for_doc": "💬 ವೈದ್ಯರನ್ನು ಕೇಳಬೇಕಾದ ಪ್ರಶ್ನೆಗಳು", "questions_empty": "ವರದಿ ಉಳಿಸಿದ ನಂತರ ಪ್ರಶ್ನೆಗಳು ಕಾಣಿಸುತ್ತವೆ.",
        "your_treatment": "💊 ಇತ್ತೀಚಿನ ವರದಿಯ ಔಷಧಿಗಳು", "treatment_empty": "ಉಳಿಸಿದ ಔಷಧ ಚೀಟಿಯ ಔಷಧಿಗಳು ಇಲ್ಲಿ ಕಾಣಿಸುತ್ತವೆ.",
        "from": "ದಾಖಲೆಯ ದಿನಾಂಕ:", "cal_blue": "ಗುರುತಿಸಿದ ದಿನಾಂಕಗಳಲ್ಲಿ ದಾಖಲೆಗಳಿವೆ.",
        "upload_title": "ವರದಿಯನ್ನು ವಿಶ್ಲೇಷಿಸಿ", "upload_label": "ಔಷಧ ಚೀಟಿ ಅಥವಾ ಲ್ಯಾಬ್ ವರದಿ (JPG, PNG, PDF)",
        "analyze_btn": "✨ ದಾಖಲೆಯನ್ನು ವಿಶ್ಲೇಷಿಸಿ", "api_key_err": "AI ಸೇವೆಯನ್ನು ಕಾನ್ಫಿಗರ್ ಮಾಡಲಾಗಿಲ್ಲ. ದಯವಿಟ್ಟು Cura AI ತಂಡವನ್ನು ಸಂಪರ್ಕಿಸಿ.",
        "reading_doc": "ದಾಖಲೆಯನ್ನು ವಿಶ್ಲೇಷಿಸಲಾಗುತ್ತಿದೆ…", "read_err": "ದಾಖಲೆಯನ್ನು ವಿಶ್ಲೇಷಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ:",
        "save_timeline": "💾 ಟೈಮ್‌ಲೈನ್‌ಗೆ ಉಳಿಸಿ", "saved_success": "ವರದಿಯನ್ನು ಟೈಮ್‌ಲೈನ್‌ಗೆ ಉಳಿಸಲಾಗಿದೆ.",
        "timeline_title": "🕒 ಆರೋಗ್ಯ ಟೈಮ್‌ಲೈನ್", "timeline_empty": "ಇನ್ನೂ ಇತಿಹಾಸವಿಲ್ಲ. ಮೊದಲು ದಾಖಲೆಯನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ.",
        "details_title": "👤 ಆರೋಗ್ಯ ಪ್ರೊಫೈಲ್", "details_saved": "ಪ್ರೊಫೈಲ್ ನವೀಕರಿಸಲಾಗಿದೆ.",
        "details_caption": "ಈ ವಿವರಗಳು ಸಂದರ್ಭಕ್ಕಾಗಿ ಮಾತ್ರ; ವೈದ್ಯರ ಮೌಲ್ಯಮಾಪನಕ್ಕೆ ಪರ್ಯಾಯವಲ್ಲ.",
        "first_name": "ಮೊದಲ ಹೆಸರು", "last_name": "ಕೊನೆಯ ಹೆಸರು", "age_label": "ವಯಸ್ಸು (ವರ್ಷಗಳು)",
        "gender_label": "ಲಿಂಗ", "height_label": "ಎತ್ತರ (ಸೆಂ.ಮೀ)", "weight_label": "ತೂಕ (ಕೆ.ಜಿ)",
        "waist_label": "ಸೊಂಟ (ಸೆಂ.ಮೀ), ಐಚ್ಛಿಕ", "save_details_btn": "ವಿವರಗಳನ್ನು ಉಳಿಸಿ",
        "required_err": "ಮೊದಲ ಹೆಸರು, ವಯಸ್ಸು, ಎತ್ತರ ಮತ್ತು ತೂಕ ನಮೂದಿಸಿ.", "summary": "ವೈದ್ಯಕೀಯ ಸಾರಾಂಶ",
        "no_summary": "ಸಾರಾಂಶ ಲಭ್ಯವಿಲ್ಲ.", "diagnoses_mentioned": "ಉಲ್ಲೇಖಿತ ಅಂಶಗಳು:",
        "medicines": "ಔಷಧಿಗಳು", "test_results": "ಪರೀಕ್ಷಾ ಫಲಿತಾಂಶಗಳು", "qa_title": "🌱 ಸರಳ ಉತ್ತರಗಳು",
        "qa_caption": "ಸಾಮಾನ್ಯ ಮಾಹಿತಿ; ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ.", "more_questions": "ವೈದ್ಯರನ್ನು ಕೇಳಬೇಕಾದ ಪ್ರಶ್ನೆಗಳು",
        "no_findings": "ವಿಶ್ಲೇಷಣೆಯಲ್ಲಿ ಹೆಚ್ಚು/ಕಡಿಮೆ ಸೂಚನೆಗಳು ಬಂದಿಲ್ಲ", "bmi_note_intro": "ನಿಮ್ಮ ಅಳತೆಗಳ ಆಧಾರದ BMI ಟಿಪ್ಪಣಿ:",
        "female": "ಮಹಿಳೆ", "male": "ಪುರುಷ", "other": "ಇತರೆ", "prefer_not": "ಹೇಳಲು ಇಷ್ಟವಿಲ್ಲ",
        "open_modal": "🔍 ಪೂರ್ಣ ವರದಿ ತೆರೆಯಿರಿ", "quick_edit": "✏️ ಅಳತೆಗಳನ್ನು ತ್ವರಿತವಾಗಿ ಬದಲಾಯಿಸಿ",
        "inspect": "🔍 ವಿವರಗಳನ್ನು ವೀಕ್ಷಿಸಿ", "delete": "ಉಳಿಸಿದ ವರದಿಯನ್ನು ಅಳಿಸಿ",
    },
}

STRINGS["TAMIL"] = {
    "disclaimer": "Cura AI மருத்துவ ஆவணங்களை எளிய மொழியில் விளக்குகிறது. இது மருத்துவர் அல்ல; நோயைக் கண்டறியாது, சிகிச்சையையும் பரிந்துரைக்காது. மருத்துவ முடிவுகளுக்கு தகுதியான மருத்துவரை அணுகவும்.",
    "brand": "🩺 Cura AI", "tagline": "✨ உங்கள் பன்மொழி ஆரோக்கிய துணை",
    "signin_caption": "உங்கள் சுகாதார அறிக்கைகளைப் பார்க்கவும் ஒழுங்கமைக்கவும் உள்நுழைக.",
    "login": "உள்நுழை", "create_account": "கணக்கை உருவாக்கு", "username": "பயனர் பெயர்",
    "password": "கடவுச்சொல்", "choose_username": "பயனர் பெயரைத் தேர்ந்தெடுக்கவும்",
    "choose_password": "கடவுச்சொல் (குறைந்தது 6 எழுத்துகள்)", "mock_abha": "ABHA ID (டெமோ)",
    "wrong_login": "பயனர் பெயர் அல்லது கடவுச்சொல் தவறானது.",
    "validation_err": "பயனர் பெயர் குறைந்தது 3 எழுத்துகளும், கடவுச்சொல் குறைந்தது 6 எழுத்துகளும் இருக்க வேண்டும்.",
    "user_taken": "இந்த பயனர் பெயர் ஏற்கனவே உள்ளது.", "menu_dashboard": "🏠 டாஷ்போர்டு",
    "menu_upload": "📄 அறிக்கையைப் பதிவேற்று", "menu_timeline": "🕒 காலவரிசை",
    "menu_details": "👤 என் விவரங்கள்", "summary_lang": "மொழி", "gemini_key": "Gemini API விசை",
    "logout": "வெளியேறு", "demo_notice": "🌱 டெமோ பயன்முறை: சோதனைக்கு மாதிரி பதிவுகளைப் பயன்படுத்தவும்.",
    "hello": "வணக்கம், வருக", "saved_reports": "சுகாதார அறிக்கைகள் சேமிக்கப்பட்டன",
    "test_trends": "📊 பரிசோதனை போக்குகள்",
    "trend_empty": "போக்குகளைப் பார்க்க ஆய்வக அறிக்கையைப் பதிவேற்றி சேமிக்கவும்.",
    "trend_hint": "ஒப்பிட மேலும் அறிக்கைகளைச் சேமிக்கவும்.",
    "weight": "எடை", "height": "உயரம்", "age": "வயது", "bmi": "BMI",
    "add_details_hint": "BMI கணக்கிட, என் விவரங்களில் வயது, உயரம், எடையை உள்ளிடவும்.",
    "questions_for_doc": "💬 மருத்துவரிடம் கேட்க வேண்டிய கேள்விகள்",
    "questions_empty": "அறிக்கையைச் சேமித்தவுடன் கேள்விகள் தோன்றும்.",
    "your_treatment": "💊 சமீபத்திய அறிக்கையில் உள்ள மருந்துகள்",
    "treatment_empty": "சேமித்த மருந்துச் சீட்டுகளின் மருந்துகள் இங்கே தோன்றும்.",
    "from": "ஆவண தேதி:", "cal_blue": "குறிக்கப்பட்ட தேதிகளில் ஆவணங்கள் சேமிக்கப்பட்டுள்ளன.",
    "upload_title": "அறிக்கையை ஸ்கேன் செய்து பகுப்பாய்வு செய்",
    "upload_label": "மருந்துச் சீட்டு அல்லது ஆய்வக அறிக்கை (JPG, PNG, PDF)",
    "analyze_btn": "✨ ஆவணத்தைப் பகுப்பாய்வு செய்",
    "api_key_err": "AI சேவை கட்டமைக்கப்படவில்லை. தயவுசெய்து Cura AI குழுவைத் தொடர்பு கொள்ளவும்.",
    "reading_doc": "ஆவணம் பகுப்பாய்வு செய்யப்படுகிறது…", "read_err": "ஆவணத்தைப் பகுப்பாய்வு செய்ய முடியவில்லை:",
    "save_timeline": "💾 காலவரிசையில் சேமி", "saved_success": "அறிக்கை காலவரிசையில் சேமிக்கப்பட்டது.",
    "timeline_title": "🕒 சுகாதார காலவரிசை", "timeline_empty": "இன்னும் வரலாறு இல்லை. முதல் ஆவணத்தைப் பதிவேற்றவும்.",
    "details_title": "👤 சுகாதார சுயவிவரம்", "details_saved": "சுயவிவரம் புதுப்பிக்கப்பட்டது.",
    "details_caption": "இந்த விவரங்கள் சூழலுக்காக மட்டுமே; மருத்துவரின் மதிப்பீட்டுக்கு மாற்றல்ல.",
    "first_name": "முதல் பெயர்", "last_name": "குடும்பப் பெயர்", "age_label": "வயது (ஆண்டுகள்)",
    "gender_label": "பாலினம்", "height_label": "உயரம் (செ.மீ)", "weight_label": "எடை (கிலோ)",
    "waist_label": "இடுப்பு (செ.மீ), விருப்பத்திற்குரியது", "save_details_btn": "விவரங்களைச் சேமி",
    "required_err": "முதல் பெயர், வயது, உயரம், எடையை உள்ளிடவும்.", "summary": "மருத்துவ சுருக்கம்",
    "no_summary": "சுருக்கம் இல்லை.", "diagnoses_mentioned": "குறிப்பிடப்பட்டவை:",
    "medicines": "மருந்துகள்", "test_results": "பரிசோதனை முடிவுகள்", "qa_title": "🌱 எளிய மொழியில் பதில்கள்",
    "qa_caption": "பொதுவான தகவல்; மருத்துவரிடம் உறுதிப்படுத்தவும்.",
    "more_questions": "மருத்துவரிடம் கேட்க வேண்டிய கேள்விகள்",
    "no_findings": "பகுப்பாய்வில் அதிக/குறைந்த குறிப்புகள் இல்லை",
    "bmi_note_intro": "உங்கள் அளவீடுகளின் அடிப்படையிலான BMI குறிப்பு:",
    "female": "பெண்", "male": "ஆண்", "other": "மற்றவை", "prefer_not": "சொல்ல விரும்பவில்லை",
    "open_modal": "🔍 முழு அறிக்கையைத் திற", "quick_edit": "✏️ அளவீடுகளைத் திருத்து",
    "inspect": "🔍 விவரங்களைப் பார்", "delete": "சேமித்த அறிக்கையை நீக்கு",
}

# Strings for the FHIR export feature (all languages)
_EXPORT_STRINGS = {
    "ENGLISH": {"export_fhir": "⬇️ Export FHIR (JSON)", "export_all": "⬇️ Export all records (FHIR bundle)"},
    "HINDI": {"export_fhir": "⬇️ FHIR निर्यात (JSON)", "export_all": "⬇️ सभी रिकॉर्ड निर्यात करें (FHIR)"},
    "TELUGU": {"export_fhir": "⬇️ FHIR ఎగుమతి (JSON)", "export_all": "⬇️ అన్ని రికార్డులను ఎగుమతి చేయండి (FHIR)"},
    "TAMIL": {"export_fhir": "⬇️ FHIR ஏற்றுமதி (JSON)", "export_all": "⬇️ அனைத்து பதிவுகளையும் ஏற்றுமதி செய் (FHIR)"},
    "KANNADA": {"export_fhir": "⬇️ FHIR ರಫ್ತು (JSON)", "export_all": "⬇️ ಎಲ್ಲಾ ದಾಖಲೆಗಳನ್ನು ರಫ್ತು ಮಾಡಿ (FHIR)"},
}
for _lang, _vals in _EXPORT_STRINGS.items():
    STRINGS[_lang].update(_vals)


def t(key):
    lang = st.session_state.get("selected_language", "ENGLISH")
    return STRINGS.get(lang, STRINGS["ENGLISH"]).get(key, STRINGS["ENGLISH"].get(key, key))

PROMPT = """
You extract information from medical documents (prescriptions, lab reports, discharge summaries),
printed or handwritten, in English or Indian languages. Return ONLY valid JSON with this schema:
{
 "document_type":"prescription|lab_report|discharge_summary|other",
 "document_date":"YYYY-MM-DD or null",
 "doctor_or_lab":"string or null",
 "diagnoses":["string"],
 "medicines":[{"name":"","dose":"","frequency":"","duration":""}],
 "tests":[{"name":"","value":"","unit":"","reference_range":"","flag":"normal|high|low|unknown"}],
 "summary":"3-5 short sentences in simple language",
 "abnormal_explanations":[{"item":"","meaning":""}],
 "questions_for_doctor":["string"],
 "question_answers":[{"question":"","answer":""}]
}
Rules:
- Use only visible information. Never guess; use null or empty strings when unreadable.
- Do not diagnose, recommend medicines, doses, supplements, or treatment changes.
- Explain abnormal results cautiously and generally.
- Provide one question_answers entry for each questions_for_doctor item, preserving exact question text.
- Answers should be 2-4 short sentences, educational, and tied to this report when possible.
- If the report does not contain enough information, say so. A clinician must make personal medical decisions.
- Write summary, abnormal_explanations meanings, questions_for_doctor and question_answers in {lang}.
- Keep medicine and test names in their original form.
"""

# -------------------- Database --------------------
def db():
    con = sqlite3.connect(DB, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id TEXT PRIMARY KEY,
            profile TEXT NOT NULL,
            doc_date TEXT,
            doc_type TEXT,
            data TEXT NOT NULL
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            salt TEXT NOT NULL,
            pw_hash TEXT NOT NULL,
            abha TEXT
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS details (
            username TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            age INTEGER,
            gender TEXT,
            height_cm INTEGER,
            weight_kg REAL,
            waist_cm REAL
        )
    """)
    # Migrate databases created by older versions.
    cols = {row["name"] for row in con.execute("PRAGMA table_info(details)").fetchall()}
    for col in ("weight_kg", "waist_cm"):
        if col not in cols:
            con.execute(f"ALTER TABLE details ADD COLUMN {col} REAL")
    con.commit()
    return con

def hash_pw(password, salt):
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), 200_000
    ).hex()

def create_user(username, password, abha):
    with db() as con:
        exists = con.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone()
        if exists:
            return False
        salt = secrets.token_hex(16)
        con.execute(
            "INSERT INTO users(username,salt,pw_hash,abha) VALUES (?,?,?,?)",
            (username, salt, hash_pw(password, salt), abha.strip())
        )
    return True

def check_login(username, password):
    with db() as con:
        row = con.execute(
            "SELECT salt,pw_hash,abha FROM users WHERE username=?", (username,)
        ).fetchone()
    if row and hmac.compare_digest(hash_pw(password, row["salt"]), row["pw_hash"]):
        return row["abha"] or ""
    return None

def get_details(username):
    with db() as con:
        row = con.execute(
            """SELECT first_name,last_name,age,gender,height_cm,weight_kg,waist_cm
               FROM details WHERE username=?""", (username,)
        ).fetchone()
    return dict(row) if row else {}

def save_details(username, first, last, age, gender, height, weight, waist=None):
    with db() as con:
        con.execute("""
            INSERT OR REPLACE INTO details
            (username,first_name,last_name,age,gender,height_cm,weight_kg,waist_cm)
            VALUES (?,?,?,?,?,?,?,?)
        """, (username, first, last, age, gender, height, weight, waist))

def save_record(profile, data):
    doc_date = data.get("document_date")
    try:
        if not doc_date:
            doc_date = str(date.today())
        else:
            datetime.strptime(str(doc_date), "%Y-%m-%d")
    except (ValueError, TypeError):
        doc_date = str(date.today())

    doc_type = data.get("document_type") or "other"
    with db() as con:
        con.execute(
            "INSERT INTO records(id,profile,doc_date,doc_type,data) VALUES (?,?,?,?,?)",
            (str(uuid.uuid4()), profile, doc_date, doc_type, json.dumps(data, ensure_ascii=False))
        )

def load_records(profile):
    with db() as con:
        rows = con.execute(
            """SELECT id,doc_date,doc_type,data FROM records
               WHERE profile=? ORDER BY doc_date ASC, rowid ASC""", (profile,)
        ).fetchall()
    results = []
    for row in rows:
        try:
            data = json.loads(row["data"])
        except (json.JSONDecodeError, TypeError):
            data = {}
        results.append({
            "id": row["id"], "date": row["doc_date"] or "",
            "type": row["doc_type"] or "other", "data": data
        })
    return results

def delete_record(profile, record_id):
    with db() as con:
        con.execute("DELETE FROM records WHERE id=? AND profile=?", (record_id, profile))

# -------------------- FHIR-style export --------------------
ABHA_SYSTEM = "https://healthid.ndhm.gov.in"
INTERPRETATION = {"high": ("H", "High"), "low": ("L", "Low"), "normal": ("N", "Normal")}

def fhir_gender(value):
    """Map the (possibly translated) gender label saved in the profile to a FHIR code."""
    text = (value or "").strip().lower()
    for lang in STRINGS.values():
        for key in ("female", "male", "other"):
            if text and text == lang.get(key, "").strip().lower():
                return key
    return "unknown"

def _fhir_patient(username, abha, details):
    patient = {
        "resourceType": "Patient",
        "id": f"patient-{username}",
        "identifier": [{
            "system": ABHA_SYSTEM,
            "value": abha or "not-provided",
            "type": {"text": "ABHA ID (mock, for demonstration)"},
        }],
        "gender": fhir_gender(details.get("gender")),
    }
    name = {"use": "official"}
    if details.get("first_name"):
        name["given"] = [details["first_name"]]
    if details.get("last_name"):
        name["family"] = details["last_name"]
    patient["name"] = [name if len(name) > 1 else {"text": username}]
    return patient

def _fhir_record_resources(patient_ref, record):
    """Convert one saved report into FHIR-style resources."""
    data = record.get("data") or {}
    rid = str(record.get("id") or uuid.uuid4())
    day = record.get("date") or str(date.today())
    resources, observation_refs = [], []

    for i, test in enumerate(data.get("tests") or []):
        if not isinstance(test, dict) or not test.get("name"):
            continue
        obs_id = f"{rid}-obs-{i}"
        obs = {
            "resourceType": "Observation", "id": obs_id, "status": "final",
            "category": [{"coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "laboratory"}]}],
            "code": {"text": str(test["name"])},
            "subject": {"reference": patient_ref},
            "effectiveDateTime": day,
        }
        number = to_num(test.get("value"))
        if number is not None:
            quantity = {"value": number}
            if test.get("unit"):
                quantity["unit"] = str(test["unit"])
            obs["valueQuantity"] = quantity
        elif test.get("value"):
            obs["valueString"] = str(test["value"])
        if test.get("reference_range"):
            obs["referenceRange"] = [{"text": str(test["reference_range"])}]
        flag = INTERPRETATION.get(str(test.get("flag", "")).lower())
        if flag:
            obs["interpretation"] = [{"coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                "code": flag[0], "display": flag[1]}]}]
        resources.append(obs)
        observation_refs.append({"reference": f"Observation/{obs_id}"})

    for i, med in enumerate(data.get("medicines") or []):
        if not isinstance(med, dict) or not med.get("name"):
            continue
        instruction = " ".join(str(med.get(k)) for k in ("dose", "frequency", "duration") if med.get(k))
        request = {
            "resourceType": "MedicationRequest", "id": f"{rid}-med-{i}",
            "status": "active", "intent": "order",
            "medicationCodeableConcept": {"text": str(med["name"])},
            "subject": {"reference": patient_ref}, "authoredOn": day,
        }
        if instruction:
            request["dosageInstruction"] = [{"text": instruction}]
        resources.append(request)

    for i, diagnosis in enumerate(data.get("diagnoses") or []):
        resources.append({
            "resourceType": "Condition", "id": f"{rid}-cond-{i}",
            "code": {"text": str(diagnosis)},
            "subject": {"reference": patient_ref}, "recordedDate": day,
        })

    report = {
        "resourceType": "DiagnosticReport", "id": f"{rid}-report", "status": "final",
        "code": {"text": str(record.get("type") or data.get("document_type") or "other").replace("_", " ")},
        "subject": {"reference": patient_ref}, "effectiveDateTime": day,
        "conclusion": str(data.get("summary") or ""),
    }
    if data.get("doctor_or_lab"):
        report["performer"] = [{"display": str(data["doctor_or_lab"])}]
    if observation_refs:
        report["result"] = observation_refs
    resources.append(report)
    return resources

def to_fhir_bundle(username, abha, details, records):
    """Build a FHIR-style Bundle (JSON string) for one or more saved reports.
    Demonstration export: structured like FHIR R4 but not validated against a FHIR server."""
    patient = _fhir_patient(username, abha, details or {})
    patient_ref = f"Patient/{patient['id']}"
    entries = [{"resource": patient}]
    for record in records:
        entries.extend({"resource": r} for r in _fhir_record_resources(patient_ref, record))
    bundle = {
        "resourceType": "Bundle", "type": "collection",
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "meta": {"tag": [{"display": "FHIR-style demo export generated by Cura AI; mock ABHA ID"}]},
        "entry": entries,
    }
    return json.dumps(bundle, ensure_ascii=False, indent=2)

# -------------------- Gemini AI --------------------
def server_key():
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if key:
        return key
    try:
        return str(st.secrets.get("GEMINI_API_KEY", "")).strip()
    except Exception:
        return ""

def api_key():
    # The key is configured on the server (environment variable or Streamlit secrets).
    # Users are never asked to enter one.
    return server_key()

def context(me):
    if me and me.get("age"):
        return (
            f"\nOptional patient context supplied by user: age {me['age']}, "
            f"gender {me.get('gender') or 'not specified'}. Do not infer diagnoses."
        )
    return ""

def analyze(uploaded_file, lang, me=None):
    key = api_key()
    if not key:
        raise RuntimeError("Gemini API key is missing.")
    client = genai.Client(api_key=key)
    file_part = types.Part.from_bytes(
        data=uploaded_file.getvalue(),
        mime_type=uploaded_file.type or "application/octet-stream"
    )
    response = client.models.generate_content(
        model=MODEL,
        contents=[file_part, PROMPT.replace("{lang}", lang) + context(me)],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1
        )
    )
    raw = response.text or ""
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end < start:
        raise ValueError("Gemini did not return a valid JSON object.")
    data = json.loads(raw[start:end + 1])
    # Normalize expected keys so UI rendering is resilient to incomplete responses.
    data.setdefault("document_type", "other")
    data.setdefault("document_date", None)
    data.setdefault("doctor_or_lab", None)
    for key_name in ("diagnoses", "medicines", "tests", "abnormal_explanations",
                     "questions_for_doctor", "question_answers"):
        if not isinstance(data.get(key_name), list):
            data[key_name] = []
    data.setdefault("summary", "")
    return data

def to_num(value):
    if value is None:
        return None
    try:
        cleaned = str(value).replace(",", "").strip()
        if not cleaned:
            return None
        return float(cleaned)
    except (ValueError, TypeError):
        return None

# -------------------- Display helpers --------------------
def has_findings(data):
    flagged = any(
        isinstance(item, dict) and str(item.get("flag", "")).lower() in ("high", "low")
        for item in data.get("tests", [])
    )
    return flagged or bool(data.get("abnormal_explanations"))

def bmi_info(me):
    height = me.get("height_cm")
    weight = me.get("weight_kg")
    age = me.get("age")
    if not height or not weight or not age or height <= 0 or weight <= 0:
        return None
    if age < 18:
        return (None, "info",
                "For people under 18, BMI should be interpreted using age- and sex-specific growth charts.")
    bmi = float(weight) / ((float(height) / 100) ** 2)
    # Common adult Asian screening cut-offs; not a diagnosis.
    if bmi < 18.5:
        level, message = "warn", "BMI is below the usual adult screening range."
    elif bmi < 23:
        level, message = "ok", "BMI is within the usual screening range used for Asian adults."
    elif bmi < 25:
        level, message = "warn", "BMI is above the usual screening range used for Asian adults."
    else:
        level, message = "warn", "BMI is above the usual screening range. BMI is a screening measure, not a diagnosis."
    return bmi, level, message

def show_bmi(me):
    info = bmi_info(me)
    if info is None:
        st.info(t("add_details_hint"))
        return
    bmi, level, message = info
    if bmi is not None:
        st.metric(f"⚖️ {t('bmi')}", f"{bmi:.1f}")
    {"ok": st.success, "warn": st.warning, "info": st.info}[level](message)

def show_report(data, key_prefix="report"):
    st.subheader(f"✨ {t('summary')}")
    st.write(data.get("summary") or t("no_summary"))

    diagnoses = data.get("diagnoses") or []
    if diagnoses:
        st.markdown(f"**🫀 {t('diagnoses_mentioned')}** " + ", ".join(map(str, diagnoses)))

    medicines = data.get("medicines") or []
    tests = data.get("tests") or []
    col1, col2 = st.columns(2)
    with col1:
        if medicines:
            st.markdown(f"#### 💊 {t('medicines')}")
            st.dataframe(pd.DataFrame(medicines), use_container_width=True, hide_index=True)
    with col2:
        if tests:
            st.markdown(f"#### 🧪 {t('test_results')}")
            st.dataframe(pd.DataFrame(tests), use_container_width=True, hide_index=True)

    for i, item in enumerate(data.get("abnormal_explanations") or []):
        if isinstance(item, dict):
            st.warning(f"**{item.get('item', 'Finding')}**: {item.get('meaning', '')}")

    qa = [
        item for item in (data.get("question_answers") or [])
        if isinstance(item, dict) and item.get("question") and item.get("answer")
    ]
    if qa:
        st.markdown(f"#### 💬 {t('qa_title')}")
        st.caption(t("qa_caption"))
        for i, item in enumerate(qa):
            with st.expander(f"❓ {item['question']}", expanded=False):
                st.write(item["answer"])
    st.caption(f"🛡️ {t('disclaimer')}")

@st.dialog("📋 Document insights", width="large")
def report_dialog(data):
    show_report(data, "dialog")

@st.dialog("✏️ Quick biometric edit", width="large")
def quick_edit_dialog(username, details):
    c1, c2 = st.columns(2)
    first = c1.text_input(t("first_name"), value=details.get("first_name") or "", key="quick_first")
    last = c2.text_input(t("last_name"), value=details.get("last_name") or "", key="quick_last")
    age = c1.number_input(t("age_label"), 0, 120, int(details.get("age") or 20), key="quick_age")
    genders = [t("female"), t("male"), t("other"), t("prefer_not")]
    old_gender = details.get("gender")
    gender_index = genders.index(old_gender) if old_gender in genders else 0
    gender = c2.selectbox(t("gender_label"), genders, index=gender_index, key="quick_gender")
    height = c1.number_input(t("height_label"), 50, 250, int(details.get("height_cm") or 170), key="quick_height")
    weight = c2.number_input(t("weight_label"), 10.0, 300.0, float(details.get("weight_kg") or 70.0), step=0.5, key="quick_weight")
    waist = c1.number_input(t("waist_label"), 30.0, 200.0, float(details.get("waist_cm") or 80.0), step=0.5, key="quick_waist")
    if st.button("✨ Save measurements", type="primary", use_container_width=True, key="quick_save"):
        if not first.strip():
            st.error(t("required_err"))
        else:
            save_details(username, first.strip(), last.strip(), int(age), gender,
                         int(height), float(weight), float(waist))
            st.success(t("details_saved"))
            st.rerun()
