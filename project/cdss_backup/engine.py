import json
import math
import re
import logging
from typing import Dict, List, Tuple, Optional, Set, Any
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict

# Import enhanced mappings with fallback
try:
    from enhanced_mappings import (
        MEDICAL_SYNONYMS,
        CRITICAL_PATTERNS,
        LOCATION_DISEASE_MAP,
        enhance_symptom_extraction,
        apply_pattern_boosts
    )
    ENHANCED_MAPPINGS_AVAILABLE = True
except ImportError:
    logging.warning(
        "Enhanced mappings not available - falling back to basic mode. "
        "Install enhanced_mappings.py for full functionality."
    )
    MEDICAL_SYNONYMS = {}
    CRITICAL_PATTERNS = {}
    LOCATION_DISEASE_MAP = {}
    ENHANCED_MAPPINGS_AVAILABLE = False

    def enhance_symptom_extraction(text, base_symptoms):
        return base_symptoms, [], {}

    def apply_pattern_boosts(posteriors, patterns, locations):
        return posteriors

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES FOR TYPE SAFETY
# ============================================================================

@dataclass
class DiagnosticResult:
    """Structured diagnostic result with full type safety"""
    success: bool
    query: str = ""
    symptoms_detected: int = 0
    symptoms_list: List[str] = field(default_factory=list)
    confidence: float = 0.0
    confidence_level: str = "VERY LOW"
    differential_diagnosis: List[Dict[str, Any]] = field(default_factory=list)
    top_diagnosis: str = ""
    top_probability: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    is_urgent: bool = False
    is_critical: bool = False
    urgency_score: int = 0
    warnings: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    processing_time_ms: float = 0.0
    error: Optional[str] = None
    debug_info: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class EngineConfig:
    """Engine configuration with defaults"""
    model_path: str = 'trained_model_v2.json'
    fallback_model_path: str = 'trained_model.json'
    confidence_threshold_high: float = 0.75
    confidence_threshold_moderate: float = 0.55
    confidence_threshold_low: float = 0.35
    min_probability_threshold: float = 0.0001
    symptom_penalty_factor: float = 0.75
    min_symptoms_for_confidence: int = 3
    negation_window_chars: int = 60
    enable_enhanced_mappings: bool = True
    enable_pattern_matching: bool = True
    enable_location_detection: bool = True
    log_level: str = 'INFO'


# ============================================================================
# MAIN DIAGNOSTIC ENGINE CLASS
# ============================================================================

class DiagnosticEngine:
    """
    Production-ready diagnostic engine with enhanced intelligence.

    This engine combines Bayesian inference with rule-based pattern matching
    to provide hospital-grade diagnostic suggestions. It includes:
    - Comprehensive medical term recognition
    - Clinical pattern detection
    - Anatomical location awareness
    - Real-time red flag detection
    - Full error handling and logging
    """

    def __init__(
        self,
        config: Optional[EngineConfig] = None,
        model_path: Optional[str] = None
    ):
        """
        Initialize the diagnostic engine.

        Args:
            config: Engine configuration object
            model_path: Optional override for model file path

        Raises:
            FileNotFoundError: If model file cannot be found
            ValueError: If model file is invalid or corrupted
        """
        self.config = config or EngineConfig()
        if model_path:
            self.config.model_path = model_path

        logger.info("=" * 70)
        logger.info("Initializing Enhanced Diagnostic Engine v2.0")
        logger.info("=" * 70)

        # Load model with fallback
        self.model = self._load_model()

        # Extract model components with validation
        self.symptom_to_disease = self.model.get('symptom_to_disease', {})
        self.disease_priors = self.model.get('priors', {})
        self.symptom_mappings = self.model.get('symptom_mappings', {})
        self.all_diseases = set(self.disease_priors.keys())

        if not self.symptom_to_disease or not self.disease_priors:
            raise ValueError("Model file is invalid - missing required components")

        # Build comprehensive symptom lookup
        self.symptom_lookup = self._build_symptom_lookup()

        # Define critical and urgent conditions
        self.critical_conditions = {
            'Heart attack', 'Stroke', 'Sepsis',
            'Pulmonary Embolism', 'Acute liver failure',
            'Paralysis (brain hemorrhage)', 'Meningitis',
            'Aortic Dissection', 'Anaphylaxis',
            'Diabetic Ketoacidosis', 'Acute Pancreatitis',
            'Bowel Obstruction'
        }

        self.urgent_conditions = {
            'Pneumonia', 'Appendicitis', 'Tuberculosis',
            'Typhoid', 'Malaria', 'Dengue', 'Cholecystitis',
            'Diverticulitis', 'Pyelonephritis', 'Cellulitis',
            'Deep Vein Thrombosis', 'Renal Failure',
            'Acute Kidney Injury', 'Endocarditis'
        }

        # Statistics
        self.total_diagnoses = 0
        self.critical_detections = 0

        # Log initialization success
        logger.info(f"✓ Model loaded: {self.config.model_path}")
        logger.info(f"✓ Symptoms: {len(self.symptom_to_disease)}")
        logger.info(f"✓ Diseases: {len(self.all_diseases)}")
        logger.info(f"✓ Critical conditions: {len(self.critical_conditions)}")
        logger.info(f"✓ Enhanced mappings: {ENHANCED_MAPPINGS_AVAILABLE}")
        if ENHANCED_MAPPINGS_AVAILABLE:
            logger.info(f"✓ Medical synonyms: {len(MEDICAL_SYNONYMS)}")
            logger.info(f"✓ Clinical patterns: {len(CRITICAL_PATTERNS)}")
        logger.info("=" * 70)

    def _load_model(self) -> Dict[str, Any]:
        """
        Load model file with fallback mechanism.

        Returns:
            Loaded model dictionary

        Raises:
            FileNotFoundError: If neither primary nor fallback model exists
            ValueError: If model file is corrupted or invalid JSON
        """
        model_paths = [
            self.config.model_path,
            self.config.fallback_model_path
        ]

        for path in model_paths:
            try:
                model_file = Path(path)
                if not model_file.exists():
                    logger.warning(f"Model file not found: {path}")
                    continue

                logger.info(f"Loading model from: {path}")
                with open(model_file, 'r', encoding='utf-8') as f:
                    model = json.load(f)

                # Validate model structure
                required_keys = ['symptom_to_disease', 'priors']
                if not all(key in model for key in required_keys):
                    logger.error(f"Model file {path} missing required keys")
                    continue

                logger.info(f"Successfully loaded model from: {path}")
                return model

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in {path}: {e}")
                continue
            except Exception as e:
                logger.error(f"Error loading model from {path}: {e}")
                continue

        # If we get here, no model could be loaded
        raise FileNotFoundError(
            f"Could not load model from any of: {', '.join(model_paths)}"
        )

    def _build_symptom_lookup(self) -> Dict[str, str]:
        """
        Build comprehensive symptom lookup dictionary.

        Returns:
            Dictionary mapping all symptom variants to canonical forms
        """
        lookup = {}

        # Add base mappings from model
        for original, variants in self.symptom_mappings.items():
            if not isinstance(variants, list):
                continue
            for variant in variants:
                if isinstance(variant, str):
                    lookup[variant.lower()] = original

        # Add enhanced medical synonyms if available
        if ENHANCED_MAPPINGS_AVAILABLE:
            for synonym, target in MEDICAL_SYNONYMS.items():
                lookup[synonym.lower()] = target

        # Add common abbreviations
        abbreviations = {
            'cp': 'chest_pain',
            'sob': 'breathlessness',
            'n/v': 'nausea',
            'n&v': 'nausea',
            'abd pain': 'abdominal_pain',
            'ha': 'headache',
            'bp': 'blood_pressure',
            'hr': 'heart_rate',
            'rr': 'respiratory_rate',
            'temp': 'high_fever',
            'wt loss': 'weight_loss',
            'loc': 'altered_mental_status',
            'ams': 'altered_mental_status',
        }

        for abbr, target in abbreviations.items():
            lookup[abbr] = target

        logger.debug(f"Built symptom lookup with {len(lookup)} entries")
        return lookup

    def extract_symptoms(self, text: str) -> Dict[str, bool]:
        """
        Extract symptoms from clinical text with negation handling.

        Args:
            text: Raw clinical text input

        Returns:
            Dictionary of detected symptoms (symptom -> True/False)

        Raises:
            ValueError: If text is empty or invalid
        """
        if not text or not isinstance(text, str):
            raise ValueError("Text input must be a non-empty string")

        text_lower = text.lower().strip()
        detected = {}

        # Negation words for context analysis
        negation_words = [
            'no', 'not', 'denies', 'without', 'absent',
            'negative', 'negative for', 'ruled out', 'r/o'
        ]

        # Search for each symptom variant
        for variant, original in self.symptom_lookup.items():
            # Create word boundary pattern
            pattern = r'\b' + re.escape(variant) + r'\b'

            try:
                match = re.search(pattern, text_lower)

                if match:
                    # Check for negation in surrounding context
                    start_pos = max(0, match.start() - self.config.negation_window_chars)
                    context = text_lower[start_pos:match.start()]

                    is_negated = any(
                        neg_word in context.split()
                        for neg_word in negation_words
                    )

                    if not is_negated:
                        detected[original] = True
                        logger.debug(f"Detected symptom: {original} (from '{variant}')")
                    else:
                        logger.debug(f"Negated symptom: {original} (from '{variant}')")

            except re.error as e:
                logger.warning(f"Regex error for variant '{variant}': {e}")
                continue

        logger.info(f"Extracted {len(detected)} symptoms from input")
        return detected

    def compute_diagnosis(
        self,
        symptoms: Dict[str, bool],
        text: str = ""
    ) -> Dict[str, float]:
        """
        Compute disease probabilities using hybrid Bayesian + pattern-based approach.

        Args:
            symptoms: Dictionary of detected symptoms
            text: Original clinical text (for pattern matching)

        Returns:
            Dictionary of disease probabilities (disease -> probability)

        Raises:
            ValueError: If symptoms dictionary is empty or invalid
        """
        if not symptoms or not isinstance(symptoms, dict):
            raise ValueError("Symptoms must be a non-empty dictionary")

        posteriors = {}

        # Step 1: Base Bayesian calculation
        logger.debug("Computing Bayesian posteriors")
        for disease in self.all_diseases:
            # Start with prior probability
            prob = self.disease_priors.get(disease, 0.0001)

            if prob <= 0:
                continue

            # Multiply by likelihood for each present symptom
            for symptom, is_present in symptoms.items():
                if not is_present:
                    continue

                # Get P(symptom|disease)
                p_symptom_given_disease = (
                    self.symptom_to_disease
                    .get(symptom, {})
                    .get(disease, 0)
                )

                if p_symptom_given_disease > 0:
                    prob *= p_symptom_given_disease
                else:
                    # Symptom not associated with this disease - small penalty
                    prob *= 0.05

            if prob > 0:
                posteriors[disease] = prob

        # Step 2: Apply pattern-based boosts if enabled
        if (self.config.enable_pattern_matching and
            text and
            ENHANCED_MAPPINGS_AVAILABLE):

            logger.debug("Applying pattern-based boosts")
            try:
                _, matched_patterns, location_context = enhance_symptom_extraction(
                    text, symptoms
                )
                posteriors = apply_pattern_boosts(
                    posteriors, matched_patterns, location_context
                )
            except Exception as e:
                logger.error(f"Error in pattern matching: {e}", exc_info=True)
                # Continue with base posteriors if pattern matching fails

        # Step 3: Normalize probabilities
        total = sum(posteriors.values())
        if total > 0:
            posteriors = {
                disease: prob / total
                for disease, prob in posteriors.items()
            }

        # Step 4: Filter very low probabilities
        posteriors = {
            disease: prob
            for disease, prob in posteriors.items()
            if prob >= self.config.min_probability_threshold
        }

        logger.info(
            f"Computed {len(posteriors)} disease probabilities "
            f"(filtered from {len(self.all_diseases)})"
        )

        return posteriors

    def calculate_confidence(
        self,
        posteriors: Dict[str, float],
        n_symptoms: int
    ) -> Tuple[float, str]:
        """
        Calculate diagnostic confidence based on multiple factors.

        Args:
            posteriors: Disease posterior probabilities
            n_symptoms: Number of symptoms detected

        Returns:
            Tuple of (confidence_score, confidence_level)
        """
        if not posteriors:
            return 0.0, "VERY LOW"

        sorted_probs = sorted(posteriors.values(), reverse=True)
        top_prob = sorted_probs[0]

        # Factor 1: Top probability (40% weight)
        prob_factor = top_prob * 0.4

        # Factor 2: Gap between top 2 diagnoses (30% weight)
        if len(sorted_probs) > 1:
            gap = sorted_probs[0] - sorted_probs[1]
            gap_factor = min(gap / 0.3, 1.0) * 0.3
        else:
            gap_factor = 0.3  # Maximum gap if only one diagnosis

        # Factor 3: Symptom count (30% weight)
        symptom_factor = min(n_symptoms / 5.0, 1.0) * 0.3

        # Calculate base confidence
        confidence = prob_factor + gap_factor + symptom_factor
        confidence = min(confidence, 1.0)

        # Penalty for insufficient symptoms
        if n_symptoms < self.config.min_symptoms_for_confidence:
            confidence *= self.config.symptom_penalty_factor
            logger.debug(
                f"Applied symptom penalty: {n_symptoms} symptoms "
                f"(min: {self.config.min_symptoms_for_confidence})"
            )

        # Determine confidence level
        if confidence >= self.config.confidence_threshold_high:
            level = "HIGH"
        elif confidence >= self.config.confidence_threshold_moderate:
            level = "MODERATE"
        elif confidence >= self.config.confidence_threshold_low:
            level = "LOW"
        else:
            level = "VERY LOW"

        logger.debug(
            f"Confidence: {confidence:.3f} ({level}) - "
            f"Top prob: {top_prob:.3f}, Gap factor: {gap_factor:.3f}, "
            f"Symptom factor: {symptom_factor:.3f}"
        )

        return round(confidence, 4), level

    def get_supporting_symptoms(
        self,
        disease: str,
        symptoms: Dict[str, bool]
    ) -> List[Tuple[str, float]]:
        """
        Get symptoms that support a specific diagnosis.

        Args:
            disease: Disease name
            symptoms: Detected symptoms dictionary

        Returns:
            List of (symptom_name, match_score) tuples, sorted by score
        """
        supporting = []

        for symptom, is_present in symptoms.items():
            if not is_present:
                continue

            # Get symptom probability for this disease
            prob = (
                self.symptom_to_disease
                .get(symptom, {})
                .get(disease, 0)
            )

            if prob > 0:
                # Get clean symptom name for display
                clean_name = (
                    self.symptom_mappings
                    .get(symptom, [symptom])[0]
                    if isinstance(self.symptom_mappings.get(symptom), list)
                    else symptom
                )
                supporting.append((clean_name, prob))

        # Sort by probability (descending)
        supporting.sort(key=lambda x: x[1], reverse=True)
        return supporting

    def assess_urgency(
        self,
        disease: str,
        confidence: float
    ) -> Tuple[bool, bool, int]:
        """
        Assess urgency level of a diagnosis.

        Args:
            disease: Disease name
            confidence: Confidence score

        Returns:
            Tuple of (is_urgent, is_critical, urgency_score)
            urgency_score is 0-10 scale
        """
        is_critical = disease in self.critical_conditions
        is_urgent = disease in self.urgent_conditions or is_critical

        if is_critical:
            urgency_score = min(10, max(8, int(9 * confidence)))
            self.critical_detections += 1
            logger.warning(f"CRITICAL condition detected: {disease}")
        elif is_urgent:
            urgency_score = min(10, max(6, int(7 * confidence)))
            logger.info(f"Urgent condition detected: {disease}")
        else:
            urgency_score = min(10, int(3 * confidence))

        return is_urgent, is_critical, urgency_score

    def generate_recommendations(
        self,
        top_disease: str,
        confidence: float,
        n_symptoms: int,
        is_urgent: bool,
        is_critical: bool
    ) -> List[str]:
        """
        Generate evidence-based clinical recommendations.

        Args:
            top_disease: Top diagnosis
            confidence: Confidence score
            n_symptoms: Number of symptoms
            is_urgent: Urgency flag
            is_critical: Critical flag

        Returns:
            List of recommendation strings
        """
        recs = []

        # Critical condition recommendations
        if is_critical:
            recs.append(
                f"🚨 CRITICAL: {top_disease} - IMMEDIATE emergency evaluation required"
            )

            # Disease-specific emergency protocols
            emergency_protocols = {
                'Heart attack': "⚠️ STAT: ECG, Troponin I/T, CK-MB - Activate cardiac catheterization lab",
                'Stroke': "⚠️ STAT: CT head, neurological assessment - Activate stroke team (time window critical)",
                'Sepsis': "⚠️ STAT: Blood cultures x2, lactate, CBC, BMP - Start broad spectrum antibiotics within 1 hour",
                'Meningitis': "⚠️ STAT: Lumbar puncture, blood cultures, CT head if indicated - Start empiric antibiotics immediately",
                'Pulmonary Embolism': "⚠️ STAT: CT pulmonary angiography, D-dimer, ABG - Consider thrombolytics",
                'Anaphylaxis': "⚠️ STAT: IM Epinephrine 0.3mg, establish IV access, continuous monitoring",
                'Aortic Dissection': "⚠️ STAT: CT angiography, cardiothoracic surgery consult - BP control critical",
                'Diabetic Ketoacidosis': "⚠️ STAT: BMP, VBG, beta-hydroxybutyrate - Start insulin drip and IVF",
                'Acute Pancreatitis': "⚠️ STAT: Lipase, LFTs, imaging - Aggressive IVF resuscitation",
            }

            protocol = emergency_protocols.get(top_disease)
            if protocol:
                recs.append(protocol)
            else:
                recs.append("⚠️ Call emergency services immediately - initiate emergency protocols")

        # Urgent condition recommendations
        elif is_urgent:
            recs.append(
                f"⚠️ URGENT: {top_disease} requires prompt evaluation within 24 hours"
            )

            urgent_workup = {
                'Pneumonia': "📋 Order: Chest X-ray, CBC with differential, sputum culture, consider blood cultures",
                'Appendicitis': "📋 Surgical consultation stat, CBC with differential, CT abdomen/pelvis with contrast",
                'Cholecystitis': "📋 RUQ ultrasound, CBC, LFTs, lipase - Surgical consultation",
                'Pyelonephritis': "📋 Urinalysis with culture, CBC, BMP, renal ultrasound - Start empiric antibiotics",
                'Deep Vein Thrombosis': "📋 Venous duplex ultrasound, D-dimer, Wells score - Consider anticoagulation",
                'Cellulitis': "📋 Blood cultures if systemic symptoms, consider imaging - Start antibiotics",
            }

            workup = urgent_workup.get(top_disease)
            if workup:
                recs.append(workup)

        # Confidence-based recommendations
        if confidence < 0.6:
            recs.append(
                "⚠️ Moderate confidence - comprehensive diagnostic workup strongly recommended"
            )
            recs.append("📋 Consider specialist consultation for definitive diagnosis")

        # Symptom count recommendations
        if n_symptoms < 3:
            recs.append(
                "ℹ️ Limited symptom data - detailed history and physical examination essential"
            )
            recs.append("📋 Consider systematic review of systems to identify additional symptoms")

        # Standard recommendations (always included)
        recs.append(
            "✓ Clinical correlation required - use professional medical judgment"
        )
        recs.append(
            "📋 Order confirmatory tests based on differential diagnosis and clinical context"
        )
        recs.append(
            "📚 Review evidence-based guidelines for current management protocols"
        )

        return recs

    def generate_warnings(
        self,
        differential: List[Dict[str, Any]],
        confidence: float
    ) -> List[str]:
        """
        Generate clinical warnings based on differential.

        Args:
            differential: Differential diagnosis list
            confidence: Overall confidence score

        Returns:
            List of warning strings
        """
        warnings = []

        # Check for critical conditions in differential
        for i, item in enumerate(differential[:5]):
            disease = item.get('disease', '')
            prob = item.get('probability', 0)

            if disease in self.critical_conditions and prob > 0.03:
                warnings.append(
                    f"⚠️ {disease} at {prob:.1%} (Rank #{i+1}) - "
                    f"MUST be ruled out with appropriate testing"
                )

        # Low confidence warning
        if confidence < 0.5:
            warnings.append(
                "⚠️ Low diagnostic confidence - specialist consultation strongly recommended"
            )
            warnings.append(
                "📋 Consider additional testing to narrow differential diagnosis"
            )

        # Multiple high-probability diagnoses
        high_prob_count = sum(
            1 for item in differential
            if item.get('probability', 0) > 0.15
        )

        if high_prob_count >= 3:
            warnings.append(
                f"⚠️ Multiple possible diagnoses ({high_prob_count}) with similar probabilities - "
                f"comprehensive evaluation needed"
            )

        # Very close top diagnoses
        if len(differential) >= 2:
            top_prob = differential[0].get('probability', 0)
            second_prob = differential[1].get('probability', 0)

            if abs(top_prob - second_prob) < 0.05:
                warnings.append(
                    "⚠️ Top diagnoses very close in probability - "
                    "additional clinical data needed for differentiation"
                )

        return warnings

    def diagnose(
        self,
        query: str,
        return_full: bool = True,
        user_id: Optional[int] = None
    ) -> DiagnosticResult:
        """
        Main diagnosis function - hospital-grade with full error handling.

        Args:
            query: Clinical text input
            return_full: If False, return only top 10 diagnoses
            user_id: Optional user ID for audit trail

        Returns:
            DiagnosticResult object with complete diagnosis

        Raises:
            ValueError: If query is empty or invalid
        """
        start_time = datetime.utcnow()
        self.total_diagnoses += 1

        try:
            # Validate input
            if not query or not isinstance(query, str):
                raise ValueError("Query must be a non-empty string")

            if len(query) > 10000:
                logger.warning(f"Query exceeds recommended length: {len(query)} characters")

            logger.info(f"Starting diagnosis #{self.total_diagnoses} for user {user_id}")
            logger.debug(f"Query: {query[:200]}...")

            # Step 1: Extract symptoms
            symptoms = self.extract_symptoms(query)

            # Enhanced symptom extraction
            if ENHANCED_MAPPINGS_AVAILABLE:
                symptoms, matched_patterns, location_context = enhance_symptom_extraction(
                    query, symptoms
                )
            else:
                matched_patterns = []
                location_context = {}

            if not symptoms:
                logger.warning("No symptoms detected in query")
                return DiagnosticResult(
                    success=False,
                    query=query,
                    error='No symptoms detected in query',
                    recommendations=[
                        'Include specific symptoms: fever, cough, chest pain, headache, etc.',
                        'Use medical terminology or common clinical descriptions',
                        'Example: "Patient presents with chest pain, sweating, and shortness of breath"'
                    ]
                )

            # Step 2: Compute diagnosis
            posteriors = self.compute_diagnosis(symptoms, query)

            if not posteriors:
                logger.warning("Unable to generate differential diagnosis")
                return DiagnosticResult(
                    success=False,
                    query=query,
                    symptoms_detected=len(symptoms),
                    symptoms_list=list(symptoms.keys()),
                    error='Unable to generate diagnosis from detected symptoms'
                )

            # Step 3: Calculate confidence
            n_symptoms = len([s for s in symptoms.values() if s])
            confidence, conf_level = self.calculate_confidence(posteriors, n_symptoms)

            # Step 4: Sort and format differential
            sorted_diseases = sorted(
                posteriors.items(),
                key=lambda x: x[1],
                reverse=True
            )

            if not return_full:
                sorted_diseases = sorted_diseases[:10]

            top_name, top_prob = sorted_diseases[0]

            # Step 5: Assess urgency
            is_urgent, is_critical, urgency_score = self.assess_urgency(
                top_name, confidence
            )

            # Step 6: Build differential diagnosis
            differential = []
            for rank, (disease, prob) in enumerate(sorted_diseases, 1):
                supporting = self.get_supporting_symptoms(disease, symptoms)

                # Determine disease-specific confidence
                if prob >= 0.5:
                    d_conf = "HIGH"
                elif prob >= 0.2:
                    d_conf = "MODERATE"
                else:
                    d_conf = "LOW"

                differential.append({
                    'rank': rank,
                    'disease': disease,
                    'probability': round(prob, 4),
                    'confidence': d_conf,
                    'supporting_symptoms': [s for s, _ in supporting[:5]],
                    'symptom_match_scores': [
                        {'symptom': s, 'score': round(p, 3)}
                        for s, p in supporting[:3]
                    ]
                })

            # Step 7: Generate recommendations and warnings
            recommendations = self.generate_recommendations(
                top_name, confidence, n_symptoms, is_urgent, is_critical
            )
            warnings = self.generate_warnings(differential, confidence)

            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Build debug info
            debug_info = None
            if matched_patterns or location_context:
                debug_info = {
                    'patterns_matched': len(matched_patterns),
                    'pattern_details': [
                        {
                            'pattern': p.get('pattern'),
                            'disease': p.get('disease'),
                            'confidence': round(p.get('confidence', 0), 3)
                        }
                        for p in matched_patterns
                    ],
                    'locations_detected': list(location_context.keys()),
                    'enhanced_mappings_used': ENHANCED_MAPPINGS_AVAILABLE
                }

            logger.info(
                f"Diagnosis completed: {top_name} ({conf_level} confidence) "
                f"in {processing_time:.1f}ms"
            )

            return DiagnosticResult(
                success=True,
                query=query,
                symptoms_detected=n_symptoms,
                symptoms_list=[s for s in symptoms if symptoms[s]],
                confidence=confidence,
                confidence_level=conf_level,
                differential_diagnosis=differential,
                top_diagnosis=top_name,
                top_probability=round(top_prob, 4),
                recommendations=recommendations,
                is_urgent=is_urgent,
                is_critical=is_critical,
                urgency_score=urgency_score,
                warnings=warnings,
                processing_time_ms=round(processing_time, 2),
                debug_info=debug_info
            )

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return DiagnosticResult(
                success=False,
                query=query,
                error=str(e)
            )

        except Exception as e:
            logger.error(f"Unexpected error in diagnosis: {e}", exc_info=True)
            return DiagnosticResult(
                success=False,
                query=query,
                error=f"Internal error: {str(e)}"
            )

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get engine statistics for monitoring.

        Returns:
            Dictionary of engine statistics
        """
        return {
            'total_diagnoses': self.total_diagnoses,
            'critical_detections': self.critical_detections,
            'diseases_available': len(self.all_diseases),
            'symptoms_tracked': len(self.symptom_to_disease),
            'enhanced_mappings': ENHANCED_MAPPINGS_AVAILABLE,
            'medical_synonyms': len(MEDICAL_SYNONYMS) if ENHANCED_MAPPINGS_AVAILABLE else 0,
            'clinical_patterns': len(CRITICAL_PATTERNS) if ENHANCED_MAPPINGS_AVAILABLE else 0,
            'model_file': self.config.model_path
        }


# ============================================================================
# SINGLETON PATTERN
# ============================================================================

_engine_instance: Optional[DiagnosticEngine] = None
_engine_lock = None

def get_engine(
    config: Optional[EngineConfig] = None,
    force_reload: bool = False
) -> DiagnosticEngine:
    """
    Get singleton diagnostic engine instance.

    Args:
        config: Optional engine configuration
        force_reload: Force reload of engine (for testing)

    Returns:
        DiagnosticEngine instance
    """
    global _engine_instance

    if _engine_instance is None or force_reload:
        logger.info("Creating new engine instance")
        _engine_instance = DiagnosticEngine(config)

    return _engine_instance


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    'DiagnosticEngine',
    'DiagnosticResult',
    'EngineConfig',
    'get_engine',
]
