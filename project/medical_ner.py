import logging
from typing import Dict, Set, List, Tuple
import re

logger = logging.getLogger(__name__)

# Try to import scispaCy
try:
    import spacy
    from scispacy.linking import EntityLinker

    # Load the medical model
    try:
        nlp = spacy.load("en_core_sci_sm")
        SCISPACY_AVAILABLE = True
        logger.info("✓ scispaCy medical NER loaded successfully")
    except:
        SCISPACY_AVAILABLE = False
        nlp = None
        logger.warning("⚠️ scispaCy model not found - using fallback")
except ImportError:
    SCISPACY_AVAILABLE = False
    nlp = None
    logger.warning("⚠️ scispaCy not installed - using fallback")


# Mapping of medical concepts to your symptom names
MEDICAL_CONCEPT_MAP = {
    # Cardiovascular
    'chest pain': 'chest_pain',
    'chest discomfort': 'chest_pain',
    'thoracic pain': 'chest_pain',
    'angina': 'chest_pain',
    'cardiac pain': 'chest_pain',

    'dyspnea': 'breathlessness',
    'shortness of breath': 'breathlessness',
    'breathing difficulty': 'breathlessness',
    'respiratory distress': 'breathlessness',

    'diaphoresis': 'sweating',
    'perspiration': 'sweating',
    'sweating': 'sweating',

    'palpitation': 'palpitations',
    'tachycardia': 'tachycardia',
    'bradycardia': 'bradycardia',

    # Neurological
    'headache': 'headache',
    'cephalgia': 'headache',
    'head pain': 'headache',
    'severe headache': 'severe_headache',
    'migraine': 'headache',

    'neck stiffness': 'stiff_neck',
    'nuchal rigidity': 'stiff_neck',
    'stiff neck': 'stiff_neck',

    'photophobia': 'photophobia',
    'light sensitivity': 'photophobia',

    'confusion': 'confusion',
    'altered mental status': 'altered_mental_status',
    'disorientation': 'altered_mental_status',
    'altered consciousness': 'altered_mental_status',

    'facial droop': 'facial_droop',
    'facial paralysis': 'facial_droop',
    'hemiparesis': 'sudden_weakness_one_side',
    'weakness': 'sudden_weakness_one_side',
    'limb weakness': 'sudden_weakness_one_side',

    'dysarthria': 'slurred_speech',
    'speech difficulty': 'slurred_speech',

    'dizziness': 'dizziness',
    'vertigo': 'dizziness',

    # GI/Abdominal
    'abdominal pain': 'abdominal_pain',
    'stomach pain': 'abdominal_pain',
    'belly pain': 'abdominal_pain',

    'nausea': 'nausea',
    'vomiting': 'vomiting',
    'emesis': 'vomiting',

    'loss of appetite': 'loss_of_appetite',
    'anorexia': 'loss_of_appetite',

    'diarrhea': 'diarrhea',
    'constipation': 'constipation',

    # Respiratory
    'cough': 'cough',
    'productive cough': 'cough',
    'hemoptysis': 'blood_in_sputum',
    'coughing blood': 'blood_in_sputum',

    'wheezing': 'wheezing',
    'stridor': 'stridor',

    # Constitutional
    'fever': 'high_fever',
    'pyrexia': 'high_fever',
    'febrile': 'high_fever',

    'fatigue': 'fatigue',
    'tiredness': 'fatigue',
    'weakness': 'fatigue',
    'malaise': 'fatigue',

    'weight loss': 'weight_loss',

    # Musculoskeletal
    'joint pain': 'joint_pain',
    'arthralgia': 'joint_pain',
    'myalgia': 'joint_pain',
    'muscle pain': 'joint_pain',

    # Skin
    'rash': 'skin_rash',
    'erythema': 'erythema',
    'pruritus': 'itching',
    'itching': 'itching',
}


def extract_medical_entities(text: str) -> Tuple[Set[str], List[str]]:
    """
    Extract medical entities from text using scispaCy NER.

    Returns:
        - Set of detected symptom codes
        - List of raw medical entities found
    """
    if not SCISPACY_AVAILABLE or nlp is None:
        logger.warning("scispaCy not available, using fallback")
        return set(), []

    try:
        # Process text with scispaCy
        doc = nlp(text.lower())

        detected_symptoms = set()
        raw_entities = []

        # Extract entities
        for ent in doc.ents:
            entity_text = ent.text.lower().strip()
            raw_entities.append(entity_text)

            # Try to map to our symptom codes
            for concept, symptom_code in MEDICAL_CONCEPT_MAP.items():
                if concept in entity_text or entity_text in concept:
                    detected_symptoms.add(symptom_code)
                    logger.debug(f"✓ NER detected: {symptom_code} from '{entity_text}'")

        # Also check noun chunks for medical terms
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.lower().strip()
            for concept, symptom_code in MEDICAL_CONCEPT_MAP.items():
                if concept in chunk_text:
                    detected_symptoms.add(symptom_code)
                    logger.debug(f"✓ NER detected (chunk): {symptom_code} from '{chunk_text}'")

        return detected_symptoms, raw_entities

    except Exception as e:
        logger.error(f"Error in NER extraction: {e}")
        return set(), []


def extract_symptoms_with_ner(
    text: str,
    fallback_symptom_lookup: Dict[str, str]
) -> Dict[str, bool]:
    """
    MAIN FUNCTION: Extract symptoms using NER + fallback to regex.

    This is what should be called from engine.py

    Args:
        text: Patient description
        fallback_symptom_lookup: Dictionary from engine for fallback

    Returns:
        Dictionary of detected symptoms
    """
    detected = {}

    # Method 1: Try NER first (if available)
    if SCISPACY_AVAILABLE and nlp is not None:
        try:
            ner_symptoms, raw_entities = extract_medical_entities(text)
            for symptom in ner_symptoms:
                detected[symptom] = True

            logger.info(f"NER found {len(ner_symptoms)} symptoms")

            # If NER found enough symptoms, return
            if len(detected) >= 2:
                return detected

        except Exception as e:
            logger.error(f"NER extraction failed: {e}")

    # Method 2: Fallback to enhanced regex matching
    logger.info("Using fallback regex matching")

    text_lower = text.lower().strip()

    # Preprocessing
    text_lower = re.sub(r'[,;:]', ' ', text_lower)
    text_lower = re.sub(r'\s+', ' ', text_lower)

    # Negation detection
    negation_words = ['no', 'not', 'denies', 'without', 'absent', 'negative']

    # Try to match each symptom variant
    for variant, original in fallback_symptom_lookup.items():
        if variant in text_lower:
            # Check for negation
            start_pos = max(0, text_lower.find(variant) - 60)
            context = text_lower[start_pos:text_lower.find(variant)]

            is_negated = any(neg in context.split() for neg in negation_words)

            if not is_negated:
                detected[original] = True
                logger.debug(f"✓ Regex matched: {original} from '{variant}'")

    logger.info(f"Total symptoms detected: {len(detected)}")

    if len(detected) == 0:
        logger.warning(f"NO SYMPTOMS FOUND in: '{text[:150]}...'")

    return detected


def check_scispacy_available() -> bool:
    """Check if scispaCy is properly installed"""
    return SCISPACY_AVAILABLE


def get_ner_status() -> Dict[str, any]:
    """Get status of NER system"""
    return {
        'scispacy_available': SCISPACY_AVAILABLE,
        'model_loaded': nlp is not None,
        'fallback_active': not SCISPACY_AVAILABLE,
        'concept_mappings': len(MEDICAL_CONCEPT_MAP)
    }


if __name__ == "__main__":
    # Test the NER system
    test_cases = [
        "chest pain, breathlessness, and sweating",
        "severe headache, high fever, stiff neck, photophobia",
        "abdominal pain that migrated to right lower quadrant with nausea",
        "58-year-old male with crushing chest pressure radiating to left arm",
    ]

    print("Testing Medical NER System")
    print("=" * 70)
    print(f"Status: {get_ner_status()}")
    print("=" * 70)

    for i, text in enumerate(test_cases, 1):
        print(f"\nTest {i}: {text}")
        symptoms = extract_symptoms_with_ner(text, {})
        print(f"  → Found {len(symptoms)} symptoms: {list(symptoms.keys())}")
