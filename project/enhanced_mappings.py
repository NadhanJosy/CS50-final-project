"""
app.py - Main Flask Application for Clinical Decision Support System

AI Assistance Disclosure:
This project was started during Week 6 of CS50 and developed over approximately
two months. I used AI tools (Claude / Gemini) as a support resource during
development.

PROJECT OWNERSHIP:
- I designed the overall structure of the project
- I chose which features to build and how they should behave
- I made the key technical decisions throughout development

HOW AI WAS USED:
- Helping troubleshoot errors and unexpected behaviour
- Assisting when I was stuck on specific problems
- Providing examples or suggestions that I then worked from

All code included in this repository was either written by me or reviewed,
adapted, and implemented by me as part of the final system.

"""
from typing import Dict, List, Tuple, Set, Optional
import re
import logging

logger = logging.getLogger(__name__)



MEDICAL_SYNONYMS: Dict[str, str] = {


    # Chest Pain - ALL variations
    'chest pain': 'chest_pain',
    'chest discomfort': 'chest_pain',
    'chest pressure': 'chest_pain',
    'chest tightness': 'chest_pain',
    'chest heaviness': 'chest_pain',
    'crushing chest pain': 'chest_pain',
    'squeezing chest pain': 'chest_pain',
    'stabbing chest pain': 'chest_pain',
    'sharp chest pain': 'chest_pain',
    'dull chest pain': 'chest_pain',
    'burning chest pain': 'chest_pain',
    'precordial pain': 'chest_pain',
    'retrosternal pain': 'chest_pain',
    'substernal pain': 'chest_pain',
    'angina': 'chest_pain',
    'angina pectoris': 'chest_pain',
    'cardiac pain': 'chest_pain',
    'heart pain': 'chest_pain',
    'pain in chest': 'chest_pain',
    'chest ache': 'chest_pain',
    'chest hurts': 'chest_pain',
    'crushing pressure': 'chest_pain',
    'pressure in chest': 'chest_pain',
    'tight chest': 'chest_pain',
    'heavy chest': 'chest_pain',

    # Pain radiation
    'radiating to arm': 'chest_pain_radiating',
    'radiating to left arm': 'chest_pain_radiating',
    'radiating to jaw': 'chest_pain_radiating',
    'radiating to back': 'chest_pain_radiating',
    'radiating to neck': 'chest_pain_radiating',
    'radiating to shoulder': 'chest_pain_radiating',
    'pain radiating': 'chest_pain_radiating',
    'pain spreading': 'chest_pain_radiating',
    'pain going to arm': 'chest_pain_radiating',
    'pain shoots to arm': 'chest_pain_radiating',

    # Sweating - ALL variations
    'sweating': 'sweating',
    'diaphoresis': 'sweating',
    'perspiration': 'sweating',
    'profuse sweating': 'sweating',
    'excessive sweating': 'sweating',
    'cold sweat': 'sweating',
    'cold sweats': 'sweating',
    'clammy': 'sweating',
    'sweaty': 'sweating',
    'drenched in sweat': 'sweating',
    'breaking out in sweat': 'sweating',
    'soaked in sweat': 'sweating',
    'dripping sweat': 'sweating',

    # Breathlessness - ALL variations
    'breathlessness': 'breathlessness',
    'shortness of breath': 'breathlessness',
    'short of breath': 'breathlessness',
    'sob': 'breathlessness',
    'dyspnea': 'breathlessness',
    'difficulty breathing': 'breathlessness',
    'labored breathing': 'breathlessness',
    'hard to breathe': 'breathlessness',
    'cant breathe': 'breathlessness',
    'cannot breathe': 'breathlessness',
    'trouble breathing': 'breathlessness',
    'breathing problems': 'breathlessness',
    'gasping for air': 'breathlessness',
    'air hunger': 'breathlessness',
    'suffocating': 'breathlessness',
    'winded': 'breathlessness',
    'out of breath': 'breathlessness',
    'respiratory distress': 'breathlessness',

    # Palpitations
    'palpitations': 'palpitations',
    'heart racing': 'palpitations',
    'racing heart': 'palpitations',
    'rapid heartbeat': 'palpitations',
    'fast heartbeat': 'palpitations',
    'heart pounding': 'palpitations',
    'pounding heart': 'palpitations',
    'fluttering heart': 'palpitations',
    'irregular heartbeat': 'irregular_heartbeat',
    'skipped beats': 'irregular_heartbeat',

    # Blood pressure
    'hypotension': 'hypotension',
    'low blood pressure': 'hypotension',
    'low bp': 'hypotension',
    'bp drop': 'hypotension',
    'blood pressure dropped': 'hypotension',

    # Heart rate
    'tachycardia': 'tachycardia',
    'fast heart rate': 'tachycardia',
    'rapid pulse': 'tachycardia',
    'elevated heart rate': 'tachycardia',
    'bradycardia': 'bradycardia',
    'slow heart rate': 'bradycardia',
    'slow pulse': 'bradycardia',


    # Headache - ALL variations
    'headache': 'headache',
    'head pain': 'headache',
    'head ache': 'headache',
    'cephalalgia': 'headache',
    'pain in head': 'headache',
    'head hurts': 'headache',
    'head pounding': 'headache',
    'pounding headache': 'headache',
    'throbbing headache': 'headache',
    'migraine': 'headache',
    'severe headache': 'severe_headache',
    'worst headache': 'severe_headache',
    'thunderclap headache': 'severe_headache',
    'intense headache': 'severe_headache',
    'terrible headache': 'severe_headache',
    'splitting headache': 'severe_headache',

    # Neck stiffness
    'stiff neck': 'stiff_neck',
    'neck stiffness': 'stiff_neck',
    'nuchal rigidity': 'stiff_neck',
    'rigid neck': 'stiff_neck',
    'cant move neck': 'stiff_neck',
    'neck pain': 'stiff_neck',
    'neck is stiff': 'stiff_neck',

    # Photophobia
    'photophobia': 'photophobia',
    'light sensitivity': 'photophobia',
    'sensitive to light': 'photophobia',
    'light hurts eyes': 'photophobia',
    'cant tolerate light': 'photophobia',
    'bothered by light': 'photophobia',

    # Confusion / Altered mental status
    'confusion': 'confusion',
    'confused': 'confusion',
    'disorientation': 'altered_mental_status',
    'disoriented': 'altered_mental_status',
    'altered mental status': 'altered_mental_status',
    'ams': 'altered_mental_status',
    'altered consciousness': 'altered_mental_status',
    'altered sensorium': 'altered_mental_status',
    'mental changes': 'altered_mental_status',
    'not thinking clearly': 'confusion',
    'foggy mind': 'confusion',
    'cant think straight': 'confusion',
    'loss of consciousness': 'altered_mental_status',
    'loc': 'altered_mental_status',
    'passed out': 'altered_mental_status',
    'fainted': 'altered_mental_status',
    'syncope': 'dizziness',
    'blacked out': 'altered_mental_status',

    # Stroke symptoms
    'facial droop': 'facial_droop',
    'face drooping': 'facial_droop',
    'droopy face': 'facial_droop',
    'facial asymmetry': 'facial_droop',
    'one side of face drooping': 'facial_droop',
    'facial paralysis': 'facial_droop',
    'bells palsy': 'facial_droop',

    'weakness one side': 'sudden_weakness_one_side',
    'one sided weakness': 'sudden_weakness_one_side',
    'weak on one side': 'sudden_weakness_one_side',
    'hemiparesis': 'sudden_weakness_one_side',
    'hemiplegia': 'sudden_weakness_one_side',
    'right sided weakness': 'sudden_weakness_one_side',
    'left sided weakness': 'sudden_weakness_one_side',
    'arm weakness': 'sudden_weakness_one_side',
    'leg weakness': 'sudden_weakness_one_side',
    'cant move arm': 'sudden_weakness_one_side',
    'cant move leg': 'sudden_weakness_one_side',

    'slurred speech': 'slurred_speech',
    'speech difficulty': 'slurred_speech',
    'trouble speaking': 'slurred_speech',
    'cant speak clearly': 'slurred_speech',
    'aphasia': 'slurred_speech',
    'dysarthria': 'slurred_speech',
    'garbled speech': 'slurred_speech',
    'unclear speech': 'slurred_speech',

    # Dizziness
    'dizziness': 'dizziness',
    'dizzy': 'dizziness',
    'lightheaded': 'dizziness',
    'light headed': 'dizziness',
    'vertigo': 'dizziness',
    'spinning': 'dizziness',
    'room spinning': 'dizziness',
    'unsteady': 'dizziness',
    'balance problems': 'dizziness',

    # Vision
    'vision changes': 'vision_changes',
    'vision problems': 'vision_changes',
    'blurred vision': 'vision_changes',
    'blurry vision': 'vision_changes',
    'vision loss': 'vision_loss',
    'cant see': 'vision_loss',
    'blind': 'vision_loss',
    'blindness': 'vision_loss',
    'lost vision': 'vision_loss',
    'double vision': 'vision_changes',
    'diplopia': 'vision_changes',

    # Numbness/Tingling
    'numbness': 'numbness_tingling',
    'tingling': 'numbness_tingling',
    'pins and needles': 'numbness_tingling',
    'paresthesia': 'numbness_tingling',
    'numb': 'numbness_tingling',
    'loss of sensation': 'numbness_tingling',
    'no feeling': 'numbness_tingling',

    # Cough
    'cough': 'cough',
    'coughing': 'cough',
    'productive cough': 'cough',
    'wet cough': 'cough',
    'dry cough': 'cough',
    'persistent cough': 'cough',
    'chronic cough': 'cough',
    'hacking cough': 'cough',

    # Sputum
    'sputum': 'phlegm',
    'phlegm': 'phlegm',
    'mucus': 'phlegm',
    'bloody sputum': 'blood_in_sputum',
    'blood in sputum': 'blood_in_sputum',
    'hemoptysis': 'blood_in_sputum',
    'coughing blood': 'blood_in_sputum',
    'coughing up blood': 'blood_in_sputum',
    'blood tinged sputum': 'blood_in_sputum',
    'rusty sputum': 'blood_in_sputum',

    # Breathing sounds
    'wheezing': 'wheezing',
    'wheeze': 'wheezing',
    'whistling breathing': 'wheezing',
    'stridor': 'stridor',
    'noisy breathing': 'stridor',

    # Respiratory rate
    'tachypnea': 'tachypnea',
    'rapid breathing': 'tachypnea',
    'fast breathing': 'tachypnea',
    'breathing fast': 'tachypnea',
    'hyperventilation': 'tachypnea',

    # General abdominal pain
    'abdominal pain': 'abdominal_pain',
    'stomach pain': 'abdominal_pain',
    'belly pain': 'abdominal_pain',
    'tummy pain': 'abdominal_pain',
    'stomach ache': 'abdominal_pain',
    'stomach hurts': 'abdominal_pain',
    'belly hurts': 'abdominal_pain',
    'pain in stomach': 'abdominal_pain',
    'pain in abdomen': 'abdominal_pain',

    # Abdominal quadrants
    'right lower quadrant': 'abdominal_pain_rlq',
    'rlq': 'abdominal_pain_rlq',
    'rlq pain': 'abdominal_pain_rlq',
    'right iliac fossa': 'abdominal_pain_rlq',
    'right lower abdomen': 'abdominal_pain_rlq',
    'lower right abdomen': 'abdominal_pain_rlq',
    'mcburney point': 'abdominal_pain_rlq',
    'mcburneys point': 'abdominal_pain_rlq',

    'right upper quadrant': 'abdominal_pain_ruq',
    'ruq': 'abdominal_pain_ruq',
    'ruq pain': 'abdominal_pain_ruq',
    'right upper abdomen': 'abdominal_pain_ruq',
    'upper right abdomen': 'abdominal_pain_ruq',

    'left lower quadrant': 'abdominal_pain_llq',
    'llq': 'abdominal_pain_llq',
    'llq pain': 'abdominal_pain_llq',
    'left lower abdomen': 'abdominal_pain_llq',
    'lower left abdomen': 'abdominal_pain_llq',

    'left upper quadrant': 'abdominal_pain_luq',
    'luq': 'abdominal_pain_luq',
    'luq pain': 'abdominal_pain_luq',
    'left upper abdomen': 'abdominal_pain_luq',
    'upper left abdomen': 'abdominal_pain_luq',

    'epigastric': 'epigastric_pain',
    'epigastric pain': 'epigastric_pain',
    'upper abdominal pain': 'epigastric_pain',
    'upper stomach pain': 'epigastric_pain',
    'pain above stomach': 'epigastric_pain',

    'periumbilical': 'abdominal_pain',
    'periumbilical pain': 'abdominal_pain',
    'around belly button': 'abdominal_pain',
    'around umbilicus': 'abdominal_pain',
    'near belly button': 'abdominal_pain',
    'around navel': 'abdominal_pain',

    # Appendicitis-specific
    'rebound tenderness': 'rebound_tenderness',
    'rebound': 'rebound_tenderness',
    'rebound pain': 'rebound_tenderness',
    'guarding': 'guarding',
    'abdominal guarding': 'guarding',
    'rigid abdomen': 'guarding',
    'tense abdomen': 'guarding',
    'murphy sign': 'murphy_sign',
    "murphy's sign": 'murphy_sign',
    'murphys sign': 'murphy_sign',

    'migrating pain': 'migrating_pain',
    'pain migration': 'migrating_pain',
    'pain moved': 'migrating_pain',
    'pain shifted': 'migrating_pain',
    'pain started': 'migrating_pain',
    'pain began': 'migrating_pain',

    'radiating to back': 'pain_radiating_to_back',
    'back radiation': 'pain_radiating_to_back',
    'pain to back': 'pain_radiating_to_back',
    'pain in back': 'pain_radiating_to_back',

    # Nausea/Vomiting
    'nausea': 'nausea',
    'nauseous': 'nausea',
    'nauseated': 'nausea',
    'feeling sick': 'nausea',
    'queasy': 'nausea',
    'sick to stomach': 'nausea',

    'vomiting': 'vomiting',
    'vomit': 'vomiting',
    'throwing up': 'vomiting',
    'emesis': 'vomiting',
    'vomited': 'vomiting',
    'puking': 'vomiting',
    'retching': 'vomiting',
    'hematemesis': 'vomiting',
    'bloody vomit': 'vomiting',
    'vomiting blood': 'vomiting',
    'coffee ground': 'vomiting',

    # Appetite
    'loss of appetite': 'loss_of_appetite',
    'no appetite': 'loss_of_appetite',
    'decreased appetite': 'loss_of_appetite',
    'not hungry': 'loss_of_appetite',
    'cant eat': 'loss_of_appetite',
    'dont want to eat': 'loss_of_appetite',
    'anorexia': 'loss_of_appetite',

    # Bowel
    'diarrhea': 'diarrhea',
    'loose stools': 'diarrhea',
    'watery stools': 'diarrhea',
    'constipation': 'constipation',
    'cant poop': 'constipation',

    'bloody stool': 'bloody_stool',
    'blood in stool': 'bloody_stool',
    'melena': 'bloody_stool',
    'black stool': 'bloody_stool',
    'tarry stool': 'bloody_stool',
    'hematochezia': 'bloody_stool',
    'bright red blood': 'bloody_stool',
    'rectal bleeding': 'bloody_stool',

    'abdominal distention': 'abdominal_distention',
    'bloating': 'abdominal_distention',
    'bloated': 'abdominal_distention',
    'distended abdomen': 'abdominal_distention',
    'swollen belly': 'abdominal_distention',


    'high fever': 'high_fever',
    'fever': 'high_fever',
    'febrile': 'high_fever',
    'pyrexia': 'high_fever',
    'elevated temperature': 'high_fever',
    'temp': 'high_fever',
    'temperature': 'high_fever',
    'hot': 'high_fever',
    'burning up': 'high_fever',
    'feverish': 'high_fever',
    'hyperthermia': 'high_fever',

    'low grade fever': 'mild_fever',
    'mild fever': 'mild_fever',
    'slight fever': 'mild_fever',

    'fatigue': 'fatigue',
    'tired': 'fatigue',
    'tiredness': 'fatigue',
    'exhaustion': 'fatigue',
    'exhausted': 'fatigue',
    'weakness': 'fatigue',
    'weak': 'fatigue',
    'malaise': 'fatigue',
    'lethargy': 'fatigue',
    'lethargic': 'fatigue',
    'asthenia': 'fatigue',
    'no energy': 'fatigue',
    'low energy': 'fatigue',
    'feeling weak': 'fatigue',
    'run down': 'fatigue',

    'weight loss': 'weight_loss',
    'losing weight': 'weight_loss',
    'lost weight': 'weight_loss',
    'unintentional weight loss': 'weight_loss',
    'cachexia': 'weight_loss',
    'wasting': 'weight_loss',


    'joint pain': 'joint_pain',
    'arthralgia': 'joint_pain',
    'joints hurt': 'joint_pain',
    'painful joints': 'joint_pain',
    'aching joints': 'joint_pain',

    'muscle pain': 'joint_pain',
    'myalgia': 'joint_pain',
    'muscles hurt': 'joint_pain',
    'muscle aches': 'joint_pain',
    'body aches': 'joint_pain',
    'body pain': 'joint_pain',

    'leg swelling': 'leg_swelling',
    'swollen leg': 'leg_swelling',
    'leg edema': 'leg_swelling',
    'edema': 'leg_swelling',
    'puffy legs': 'leg_swelling',

    'leg pain': 'leg_pain',
    'calf pain': 'calf_pain',
    'calf tenderness': 'calf_pain',
    'pain in calf': 'calf_pain',


    'rash': 'skin_rash',
    'skin rash': 'skin_rash',
    'spots': 'skin_rash',
    'red spots': 'skin_rash',
    'skin eruption': 'skin_rash',

    'itching': 'itching',
    'itchy': 'itching',
    'pruritus': 'itching',
    'scratching': 'itching',

    'erythema': 'erythema',
    'redness': 'erythema',
    'red skin': 'erythema',
    'skin redness': 'erythema',

    'warmth': 'skin_warmth',
    'warm to touch': 'skin_warmth',
    'hot skin': 'skin_warmth',

    'urticaria': 'urticaria',
    'hives': 'urticaria',
    'welts': 'urticaria',

    'flank pain': 'flank_pain',
    'side pain': 'flank_pain',
    'pain in side': 'flank_pain',
    'costovertebral angle tenderness': 'flank_pain',
    'cvat': 'flank_pain',

    'decreased urine': 'decreased_urine_output',
    'oliguria': 'decreased_urine_output',
    'anuria': 'decreased_urine_output',
    'no urine': 'decreased_urine_output',
    'not urinating': 'decreased_urine_output',
    'low urine output': 'decreased_urine_output',

    'frequent urination': 'polyuria',
    'polyuria': 'polyuria',
    'excessive urination': 'polyuria',
    'urinating a lot': 'polyuria',
    'peeing a lot': 'polyuria',


    'excessive thirst': 'excessive_hunger',
    'polydipsia': 'excessive_hunger',
    'very thirsty': 'excessive_hunger',
    'always thirsty': 'excessive_hunger',
    'increased thirst': 'excessive_hunger',

    'excessive hunger': 'excessive_hunger',
    'polyphagia': 'excessive_hunger',
    'always hungry': 'excessive_hunger',
    'increased hunger': 'excessive_hunger',
    'increased appetite': 'excessive_hunger',
}


# Location to disease mapping (unchanged, but keeping it)
LOCATION_DISEASE_MAP: Dict[str, List[str]] = {
    'right lower quadrant': ['Appendicitis', 'Urinary tract infection', 'Pyelonephritis'],
    'rlq': ['Appendicitis', 'Urinary tract infection', 'Pyelonephritis'],
    'mcburney': ['Appendicitis'],
    'right iliac fossa': ['Appendicitis'],
    'right upper quadrant': ['Cholecystitis', 'Hepatitis B', 'Hepatitis C', 'Chronic cholestasis'],
    'ruq': ['Cholecystitis', 'Hepatitis B', 'Hepatitis C', 'Chronic cholestasis'],
    'epigastric': ['GERD', 'Peptic ulcer diseae', 'Gastroenteritis', 'Acute Pancreatitis'],
    'epigastrium': ['GERD', 'Peptic ulcer diseae', 'Gastroenteritis', 'Acute Pancreatitis'],
    'left upper quadrant': ['Gastroenteritis', 'Peptic ulcer diseae'],
    'luq': ['Gastroenteritis', 'Peptic ulcer diseae'],
    'left lower quadrant': ['Diverticulitis', 'Urinary tract infection'],
    'llq': ['Diverticulitis', 'Urinary tract infection'],
    'periumbilical': ['Gastroenteritis', 'Appendicitis', 'Bowel Obstruction'],
    'around umbilicus': ['Gastroenteritis', 'Appendicitis', 'Bowel Obstruction'],
    'retrosternal': ['Heart attack', 'GERD', 'Aortic Dissection'],
    'substernal': ['Heart attack', 'GERD', 'Aortic Dissection'],
    'flank': ['Pyelonephritis', 'Renal Failure', 'Acute Kidney Injury'],
    'costovertebral angle': ['Pyelonephritis', 'Renal Failure'],
}


# Clinical patterns (keeping your existing ones)
CRITICAL_PATTERNS: Dict[str, Dict] = {
    'appendicitis_classic': {
        'symptoms': ['abdominal_pain_rlq', 'vomiting', 'loss_of_appetite'],
        'disease': 'Appendicitis',
        'boost': 3.0,
        'keywords': ['rlq', 'right lower quadrant', 'mcburney', 'migrated', 'periumbilical',
                     'rebound', 'guarding', 'right iliac fossa'],
        'description': 'Classic appendicitis presentation with RLQ pain'
    },
    'appendicitis_migrating': {
        'symptoms': ['abdominal_pain', 'migrating_pain'],
        'disease': 'Appendicitis',
        'boost': 2.5,
        'keywords': ['periumbilical', 'moved to rlq', 'migrated', 'started around belly button'],
        'description': 'Appendicitis with characteristic pain migration'
    },
    'meningitis_classic': {
        'symptoms': ['severe_headache', 'high_fever', 'stiff_neck'],
        'disease': 'Meningitis',
        'boost': 3.0,
        'keywords': ['photophobia', 'nuchal', 'severe headache', 'worsening', 'worst headache',
                     'confusion', 'altered mental'],
        'description': 'Classic meningitis triad with nuchal rigidity'
    },
    'mi_classic': {
        'symptoms': ['chest_pain', 'sweating', 'breathlessness'],
        'disease': 'Heart attack',
        'boost': 3.0,
        'keywords': ['radiating', 'arm', 'jaw', 'sudden onset', 'crushing', 'pressure',
                     'left arm', 'diaphoresis', 'nausea'],
        'description': 'Classic MI presentation with radiation'
    },
}


def enhance_symptom_extraction(
    text: str,
    base_symptoms: Dict[str, bool]
) -> Tuple[Dict[str, bool], List[Dict], Dict[str, List[str]]]:
    """Enhanced symptom extraction with better preprocessing"""

    if not text or not isinstance(text, str):
        logger.warning("Invalid text input for symptom enhancement")
        return base_symptoms.copy(), [], {}

    # Preprocessing - make text more matchable
    text_lower = text.lower().strip()

    # Remove extra punctuation but keep important ones
    text_lower = re.sub(r'[,;:]', ' ', text_lower)
    text_lower = re.sub(r'\s+', ' ', text_lower)

    enhanced = base_symptoms.copy()
    matched_patterns: List[Dict] = []
    location_context: Dict[str, List[str]] = {}

    try:
        # Step 1: Check for anatomical locations
        for location, associated_diseases in LOCATION_DISEASE_MAP.items():
            if location in text_lower:
                location_context[location] = associated_diseases
                logger.debug(f"Detected anatomical location: {location}")

                # Map location-specific symptoms
                if 'rlq' in location or 'right lower quadrant' in location:
                    enhanced['abdominal_pain_rlq'] = True
                elif 'ruq' in location or 'right upper quadrant' in location:
                    enhanced['abdominal_pain_ruq'] = True
                elif 'llq' in location or 'left lower quadrant' in location:
                    enhanced['abdominal_pain_llq'] = True
                elif 'epigastric' in location:
                    enhanced['epigastric_pain'] = True

        # Step 2: Check for critical clinical patterns
        for pattern_name, pattern_info in CRITICAL_PATTERNS.items():
            symptoms_present = [
                s for s in pattern_info['symptoms']
                if enhanced.get(s, False)
            ]

            keywords_present = [
                k for k in pattern_info['keywords']
                if k.lower() in text_lower
            ]

            min_symptoms = 2
            min_keywords = 1

            if len(symptoms_present) >= min_symptoms and len(keywords_present) >= min_keywords:
                matched_patterns.append({
                    'pattern': pattern_name,
                    'disease': pattern_info['disease'],
                    'boost': pattern_info['boost'],
                    'confidence': min(
                        1.0,
                        (len(symptoms_present) / len(pattern_info['symptoms'])) * 0.5 +
                        (len(keywords_present) / len(pattern_info['keywords'])) * 0.5
                    ),
                    'evidence': {
                        'symptoms': symptoms_present,
                        'keywords': keywords_present,
                        'description': pattern_info.get('description', '')
                    }
                })
                logger.info(f"Matched clinical pattern: {pattern_name}")

        return enhanced, matched_patterns, location_context

    except Exception as e:
        logger.error(f"Error in symptom enhancement: {e}", exc_info=True)
        return base_symptoms.copy(), [], {}


def apply_pattern_boosts(
    posteriors: Dict[str, float],
    matched_patterns: List[Dict],
    location_context: Dict[str, List[str]]
) -> Dict[str, float]:
    """Apply pattern-based probability boosts"""

    if not posteriors or not isinstance(posteriors, dict):
        logger.warning("Invalid posteriors for pattern boost application")
        return {}

    boosted = posteriors.copy()

    try:
        # Apply pattern-based boosts
        for pattern in matched_patterns:
            disease = pattern.get('disease')
            boost = pattern.get('boost', 1.0)
            confidence = pattern.get('confidence', 1.0)

            if disease and disease in boosted:
                effective_boost = 1.0 + (boost - 1.0) * confidence
                boosted[disease] *= effective_boost
                logger.debug(
                    f"Applied pattern boost to {disease}: "
                    f"{boost:.2f}x (confidence: {confidence:.2f})"
                )

        # Apply location-based boosts
        location_boost = 1.5
        for location, diseases in location_context.items():
            for disease in diseases:
                if disease in boosted:
                    boosted[disease] *= location_boost
                    logger.debug(
                        f"Applied location boost to {disease} "
                        f"for {location}: {location_boost}x"
                    )

        return boosted

    except Exception as e:
        logger.error(f"Error applying pattern boosts: {e}", exc_info=True)
        return posteriors.copy()


__all__ = [
    'MEDICAL_SYNONYMS',
    'LOCATION_DISEASE_MAP',
    'CRITICAL_PATTERNS',
    'enhance_symptom_extraction',
    'apply_pattern_boosts',
]
