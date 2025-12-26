"""
vital_signs.py - Vital Signs Analysis and Critical Alert Detection

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
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class VitalSignStatus(Enum):
    """Vital sign status levels"""
    NORMAL = "normal"
    BORDERLINE = "borderline"
    ABNORMAL = "abnormal"
    CRITICAL = "critical"


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    URGENT = "urgent"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


# Age-adjusted vital sign ranges
VITAL_RANGES = {
    'temperature_c': {
        'adult': {'low_critical': 35.0, 'low': 36.1, 'high': 37.8, 'high_critical': 40.0},
        'child': {'low_critical': 35.5, 'low': 36.5, 'high': 37.5, 'high_critical': 39.5},
        'infant': {'low_critical': 36.0, 'low': 36.5, 'high': 37.5, 'high_critical': 38.5},
    },
    'heart_rate_bpm': {
        'adult': {'low_critical': 40, 'low': 60, 'high': 100, 'high_critical': 140},
        'elderly': {'low_critical': 40, 'low': 50, 'high': 100, 'high_critical': 120},
        'child': {'low_critical': 50, 'low': 70, 'high': 120, 'high_critical': 160},
        'infant': {'low_critical': 80, 'low': 100, 'high': 160, 'high_critical': 200},
    },
    'respiratory_rate_bpm': {
        'adult': {'low_critical': 8, 'low': 12, 'high': 20, 'high_critical': 30},
        'elderly': {'low_critical': 8, 'low': 12, 'high': 20, 'high_critical': 28},
        'child': {'low_critical': 12, 'low': 15, 'high': 30, 'high_critical': 40},
        'infant': {'low_critical': 20, 'low': 30, 'high': 50, 'high_critical': 60},
    },
    'systolic_bp_mmhg': {
        'adult': {'low_critical': 70, 'low': 90, 'high': 140, 'high_critical': 180},
        'elderly': {'low_critical': 80, 'low': 100, 'high': 150, 'high_critical': 180},
        'child': {'low_critical': 60, 'low': 80, 'high': 120, 'high_critical': 140},
    },
    'diastolic_bp_mmhg': {
        'adult': {'low_critical': 40, 'low': 60, 'high': 90, 'high_critical': 120},
        'elderly': {'low_critical': 50, 'low': 60, 'high': 90, 'high_critical': 110},
        'child': {'low_critical': 35, 'low': 50, 'high': 80, 'high_critical': 100},
    },
    'spo2_percent': {
        'all': {'low_critical': 85, 'low': 92, 'high': 100, 'high_critical': None},
    },
    'gcs_score': {
        'all': {'low_critical': 8, 'low': 13, 'high': 15, 'high_critical': None},
    },
}



@dataclass
class VitalSigns:
    # Core vital signs
    temperature_c: Optional[float] = None
    heart_rate_bpm: Optional[int] = None
    respiratory_rate_bpm: Optional[int] = None
    systolic_bp_mmhg: Optional[int] = None
    diastolic_bp_mmhg: Optional[int] = None
    spo2_percent: Optional[int] = None

    # Additional measurements
    gcs_score: Optional[int] = None  # Glasgow Coma Scale
    pain_score: Optional[int] = None  # 0-10 scale
    blood_glucose_mgdl: Optional[float] = None

    # Patient context
    age_years: Optional[int] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None

    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    measured_by: Optional[str] = None
    location: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

    def is_complete(self) -> bool:
        core_vitals = [
            self.temperature_c,
            self.heart_rate_bpm,
            self.respiratory_rate_bpm,
            self.systolic_bp_mmhg,
            self.spo2_percent
        ]
        return all(v is not None for v in core_vitals)


@dataclass
class RedFlag:
    level: AlertLevel
    title: str
    message: str
    condition: str
    vital_signs_involved: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    time_critical: bool = False
    escalation_required: bool = False
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            'level': self.level.value,
            'title': self.title,
            'message': self.message,
            'condition': self.condition,
            'vital_signs_involved': self.vital_signs_involved,
            'recommended_actions': self.recommended_actions,
            'time_critical': self.time_critical,
            'escalation_required': self.escalation_required,
            'timestamp': self.timestamp
        }


@dataclass
class VitalSignsAnalysis:
    """Complete vital signs analysis result"""
    vitals: VitalSigns
    statuses: Dict[str, VitalSignStatus] = field(default_factory=dict)
    red_flags: List[RedFlag] = field(default_factory=list)
    sirs_criteria_met: int = 0
    sirs_positive: bool = False
    news_score: int = 0
    severity: str = "normal"
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'vitals': self.vitals.to_dict(),
            'statuses': {k: v.value for k, v in self.statuses.items()},
            'red_flags': [rf.to_dict() for rf in self.red_flags],
            'sirs_criteria_met': self.sirs_criteria_met,
            'sirs_positive': self.sirs_positive,
            'news_score': self.news_score,
            'severity': self.severity,
            'recommendations': self.recommendations
        }


class VitalSignsAnalyzer:


    def __init__(self):
        """Initialize analyzer"""
        logger.info("Initializing Vital Signs Analyzer")
        self.total_analyses = 0
        self.critical_alerts = 0

    def _get_age_group(self, age_years: Optional[int]) -> str:

        if age_years is None:
            return 'adult'  # Default assumption

        if age_years < 1:
            return 'infant'
        elif age_years < 12:
            return 'child'
        elif age_years >= 65:
            return 'elderly'
        else:
            return 'adult'

    def _assess_vital_sign(
        self,
        value: Optional[float],
        vital_name: str,
        age_group: str
    ) -> VitalSignStatus:


        if value is None:
            return VitalSignStatus.NORMAL

        # Get ranges for this vital and age group
        ranges = VITAL_RANGES.get(vital_name, {})

        # Try age-specific range, fall back to 'all'
        range_data = ranges.get(age_group) or ranges.get('all')

        if not range_data:
            logger.warning(f"No ranges defined for {vital_name}, {age_group}")
            return VitalSignStatus.NORMAL

        # Check critical ranges first
        if range_data.get('low_critical') and value < range_data['low_critical']:
            return VitalSignStatus.CRITICAL
        if range_data.get('high_critical') and value > range_data['high_critical']:
            return VitalSignStatus.CRITICAL

        # Check abnormal ranges
        if value < range_data.get('low', float('-inf')):
            return VitalSignStatus.ABNORMAL
        if value > range_data.get('high', float('inf')):
            return VitalSignStatus.ABNORMAL

        # Check borderline (within 10% of threshold)
        low = range_data.get('low', float('-inf'))
        high = range_data.get('high', float('inf'))
        low_margin = low * 1.1 if low > 0 else low + abs(low * 0.1)
        high_margin = high * 0.9 if high > 0 else high - abs(high * 0.1)

        if value < low_margin or value > high_margin:
            return VitalSignStatus.BORDERLINE

        return VitalSignStatus.NORMAL

    def _detect_red_flags(
        self,
        vitals: VitalSigns,
        statuses: Dict[str, VitalSignStatus]
    ) -> List[RedFlag]:

        red_flags = []

        # Critical Temperature (Hyperthermia)
        if vitals.temperature_c and vitals.temperature_c >= 40.0:
            red_flags.append(RedFlag(
                level=AlertLevel.EMERGENCY,
                title="CRITICAL HYPERTHERMIA",
                message=f"Temperature {vitals.temperature_c}°C - Immediate cooling measures required",
                condition="Hyperthermia",
                vital_signs_involved=['temperature'],
                recommended_actions=[
                    "Immediate cooling measures (ice packs, cooling blanket)",
                    "Check for heat stroke, infection, drug reaction",
                    "Monitor for seizures",
                    "Consider ICU transfer"
                ],
                time_critical=True,
                escalation_required=True
            ))
            self.critical_alerts += 1

        # Critical Hypothermia
        if vitals.temperature_c and vitals.temperature_c <= 35.0:
            red_flags.append(RedFlag(
                level=AlertLevel.EMERGENCY,
                title="CRITICAL HYPOTHERMIA",
                message=f"Temperature {vitals.temperature_c}°C - Warming required",
                condition="Hypothermia",
                vital_signs_involved=['temperature'],
                recommended_actions=[
                    "Active warming measures",
                    "Warmed IV fluids",
                    "Cardiac monitoring (risk of arrhythmia)",
                    "Consider ICU"
                ],
                time_critical=True,
                escalation_required=True
            ))
            self.critical_alerts += 1

        # Severe Bradycardia
        if vitals.heart_rate_bpm and vitals.heart_rate_bpm <= 40:
            red_flags.append(RedFlag(
                level=AlertLevel.EMERGENCY,
                title="SEVERE BRADYCARDIA",
                message=f"Heart rate {vitals.heart_rate_bpm} bpm - Risk of cardiac arrest",
                condition="Bradycardia",
                vital_signs_involved=['heart_rate'],
                recommended_actions=[
                    "Continuous cardiac monitoring",
                    "12-lead ECG immediately",
                    "Check medications (beta-blockers, etc.)",
                    "Prepare atropine/pacing",
                    "ACLS team notification"
                ],
                time_critical=True,
                escalation_required=True
            ))
            self.critical_alerts += 1

        # Severe Tachycardia
        if vitals.heart_rate_bpm and vitals.heart_rate_bpm >= 140:
            red_flags.append(RedFlag(
                level=AlertLevel.CRITICAL,
                title="SEVERE TACHYCARDIA",
                message=f"Heart rate {vitals.heart_rate_bpm} bpm - Assess for shock/arrhythmia",
                condition="Tachycardia",
                vital_signs_involved=['heart_rate'],
                recommended_actions=[
                    "12-lead ECG",
                    "Assess for shock (septic, hypovolemic, cardiogenic)",
                    "Check for arrhythmia (SVT, AF, VT)",
                    "Fluid status assessment",
                    "Consider cardiology consult"
                ],
                time_critical=True,
                escalation_required=True
            ))
            self.critical_alerts += 1

        # Severe Hypotension
        if vitals.systolic_bp_mmhg and vitals.systolic_bp_mmhg <= 70:
            red_flags.append(RedFlag(
                level=AlertLevel.EMERGENCY,
                title="SEVERE HYPOTENSION / SHOCK",
                message=f"BP {vitals.systolic_bp_mmhg}/{vitals.diastolic_bp_mmhg or '?'} - SHOCK PROTOCOL",
                condition="Hypotensive Shock",
                vital_signs_involved=['blood_pressure'],
                recommended_actions=[
                    "Initiate shock protocol immediately",
                    "Fluid resuscitation (consider pressors)",
                    "Identify shock type (septic/cardiogenic/hypovolemic)",
                    "Blood cultures before antibiotics",
                    "ICU notification",
                    "Activate rapid response team"
                ],
                time_critical=True,
                escalation_required=True
            ))
            self.critical_alerts += 1

        # Hypertensive Emergency
        if vitals.systolic_bp_mmhg and vitals.systolic_bp_mmhg >= 180:
            if vitals.diastolic_bp_mmhg and vitals.diastolic_bp_mmhg >= 120:
                red_flags.append(RedFlag(
                    level=AlertLevel.EMERGENCY,
                    title="HYPERTENSIVE EMERGENCY",
                    message=f"BP {vitals.systolic_bp_mmhg}/{vitals.diastolic_bp_mmhg} - Risk of end-organ damage",
                    condition="Hypertensive Emergency",
                    vital_signs_involved=['blood_pressure'],
                    recommended_actions=[
                        "Assess for end-organ damage (stroke, MI, renal failure)",
                        "Continuous BP monitoring",
                        "IV antihypertensives (nicardipine, labetalol)",
                        "Neuro exam, cardiac markers, renal function",
                        "ICU admission likely required"
                    ],
                    time_critical=True,
                    escalation_required=True
                ))
                self.critical_alerts += 1

        # Critical Hypoxemia
        if vitals.spo2_percent and vitals.spo2_percent <= 85:
            red_flags.append(RedFlag(
                level=AlertLevel.EMERGENCY,
                title="CRITICAL HYPOXEMIA",
                message=f"SpO2 {vitals.spo2_percent}% - Immediate oxygen/airway management",
                condition="Severe Hypoxemia",
                vital_signs_involved=['spo2'],
                recommended_actions=[
                    "High-flow oxygen immediately (non-rebreather mask)",
                    "Assess airway patency",
                    "Consider intubation if worsening",
                    "Chest X-ray STAT",
                    "ABG analysis",
                    "Respiratory therapy consult"
                ],
                time_critical=True,
                escalation_required=True
            ))
            self.critical_alerts += 1

        # Respiratory Distress
        if vitals.respiratory_rate_bpm:
            if vitals.respiratory_rate_bpm <= 8:
                red_flags.append(RedFlag(
                    level=AlertLevel.EMERGENCY,
                    title="SEVERE BRADYPNEA",
                    message=f"Respiratory rate {vitals.respiratory_rate_bpm} - Risk of respiratory arrest",
                    condition="Bradypnea",
                    vital_signs_involved=['respiratory_rate'],
                    recommended_actions=[
                        "Assess airway immediately",
                        "Check for narcotic overdose (naloxone if suspected)",
                        "Prepare for airway management",
                        "Consider ICU/intubation",
                        "Continuous monitoring"
                    ],
                    time_critical=True,
                    escalation_required=True
                ))
                self.critical_alerts += 1
            elif vitals.respiratory_rate_bpm >= 30:
                red_flags.append(RedFlag(
                    level=AlertLevel.CRITICAL,
                    title="SEVERE TACHYPNEA",
                    message=f"Respiratory rate {vitals.respiratory_rate_bpm} - Respiratory distress",
                    condition="Tachypnea",
                    vital_signs_involved=['respiratory_rate'],
                    recommended_actions=[
                        "Assess work of breathing",
                        "Oxygen supplementation",
                        "Check for pneumonia, PE, pulmonary edema",
                        "Consider CPAP/BiPAP",
                        "Respiratory therapy consult"
                    ],
                    time_critical=True,
                    escalation_required=False
                ))

        # Altered Mental Status (GCS)
        if vitals.gcs_score and vitals.gcs_score <= 8:
            red_flags.append(RedFlag(
                level=AlertLevel.EMERGENCY,
                title="SEVERELY ALTERED MENTAL STATUS",
                message=f"GCS {vitals.gcs_score} - Consider airway protection",
                condition="Altered Mental Status",
                vital_signs_involved=['gcs'],
                recommended_actions=[
                    "Protect airway (GCS ≤8 = intubation threshold)",
                    "CT head STAT",
                    "Check glucose immediately",
                    "Toxicology screen",
                    "Neurology consult",
                    "ICU admission"
                ],
                time_critical=True,
                escalation_required=True
            ))
            self.critical_alerts += 1

        # Severe Hyperglycemia
        if vitals.blood_glucose_mgdl and vitals.blood_glucose_mgdl >= 400:
            red_flags.append(RedFlag(
                level=AlertLevel.CRITICAL,
                title="SEVERE HYPERGLYCEMIA",
                message=f"Blood glucose {vitals.blood_glucose_mgdl} mg/dL - Risk of DKA/HHS",
                condition="Hyperglycemia",
                vital_signs_involved=['blood_glucose'],
                recommended_actions=[
                    "Check for DKA (BMP, VBG, ketones, anion gap)",
                    "Start insulin drip if DKA confirmed",
                    "Aggressive IV fluid resuscitation",
                    "Potassium monitoring",
                    "Endocrinology consult"
                ],
                time_critical=True,
                escalation_required=False
            ))

        # Severe Hypoglycemia
        if vitals.blood_glucose_mgdl and vitals.blood_glucose_mgdl <= 50:
            red_flags.append(RedFlag(
                level=AlertLevel.EMERGENCY,
                title="SEVERE HYPOGLYCEMIA",
                message=f"Blood glucose {vitals.blood_glucose_mgdl} mg/dL - Immediate treatment required",
                condition="Hypoglycemia",
                vital_signs_involved=['blood_glucose'],
                recommended_actions=[
                    "D50 IV push immediately (if conscious: PO glucose)",
                    "Continuous glucose monitoring",
                    "Check insulin/sulfonylurea levels",
                    "Assess for altered mental status",
                    "Prevent recurrence"
                ],
                time_critical=True,
                escalation_required=True
            ))
            self.critical_alerts += 1

        return red_flags

    def _calculate_sirs_criteria(self, vitals: VitalSigns) -> Tuple[int, bool]:


        criteria_met = 0

        # Temperature criterion
        if vitals.temperature_c:
            if vitals.temperature_c > 38.0 or vitals.temperature_c < 36.0:
                criteria_met += 1

        # Heart rate criterion
        if vitals.heart_rate_bpm and vitals.heart_rate_bpm > 90:
            criteria_met += 1

        # Respiratory rate criterion
        if vitals.respiratory_rate_bpm and vitals.respiratory_rate_bpm > 20:
            criteria_met += 1

        # WBC criterion would require lab data (not available in vitals)
        # We track 3/4 criteria here

        is_positive = criteria_met >= 2

        if is_positive:
            logger.warning(f"SIRS criteria met: {criteria_met}/4 (3 assessed)")

        return criteria_met, is_positive

    def _calculate_news_score(self, vitals: VitalSigns) -> int:

        score = 0

        # Respiratory rate (0-3 points)
        if vitals.respiratory_rate_bpm:
            rr = vitals.respiratory_rate_bpm
            if rr <= 8:
                score += 3
            elif rr <= 11:
                score += 1
            elif rr <= 20:
                score += 0
            elif rr <= 24:
                score += 2
            else:  # ≥25
                score += 3

        # SpO2 (0-3 points)
        if vitals.spo2_percent:
            spo2 = vitals.spo2_percent
            if spo2 <= 91:
                score += 3
            elif spo2 <= 93:
                score += 2
            elif spo2 <= 95:
                score += 1
            else:  # ≥96
                score += 0

        # Systolic BP (0-3 points)
        if vitals.systolic_bp_mmhg:
            sbp = vitals.systolic_bp_mmhg
            if sbp <= 90:
                score += 3
            elif sbp <= 100:
                score += 2
            elif sbp <= 110:
                score += 1
            elif sbp <= 219:
                score += 0
            else:  # ≥220
                score += 3

        # Heart rate (0-3 points)
        if vitals.heart_rate_bpm:
            hr = vitals.heart_rate_bpm
            if hr <= 40:
                score += 3
            elif hr <= 50:
                score += 1
            elif hr <= 90:
                score += 0
            elif hr <= 110:
                score += 1
            elif hr <= 130:
                score += 2
            else:  # ≥131
                score += 3

        # Temperature (0-3 points)
        if vitals.temperature_c:
            temp = vitals.temperature_c
            if temp <= 35.0:
                score += 3
            elif temp <= 36.0:
                score += 1
            elif temp <= 38.0:
                score += 0
            elif temp <= 39.0:
                score += 1
            else:  # ≥39.1
                score += 2

        # Level of consciousness (0 or 3 points)
        if vitals.gcs_score and vitals.gcs_score < 15:
            score += 3

        return score

    def analyze(self, vitals: VitalSigns) -> VitalSignsAnalysis:

        if not isinstance(vitals, VitalSigns):
            raise ValueError("Invalid vitals data")

        self.total_analyses += 1
        logger.info(f"Analyzing vital signs #{self.total_analyses}")

        try:
            # Determine age group
            age_group = self._get_age_group(vitals.age_years)

            # Assess each vital sign
            statuses = {}

            if vitals.temperature_c is not None:
                statuses['temperature'] = self._assess_vital_sign(
                    vitals.temperature_c, 'temperature_c', age_group
                )

            if vitals.heart_rate_bpm is not None:
                statuses['heart_rate'] = self._assess_vital_sign(
                    vitals.heart_rate_bpm, 'heart_rate_bpm', age_group
                )

            if vitals.respiratory_rate_bpm is not None:
                statuses['respiratory_rate'] = self._assess_vital_sign(
                    vitals.respiratory_rate_bpm, 'respiratory_rate_bpm', age_group
                )

            if vitals.systolic_bp_mmhg is not None:
                statuses['systolic_bp'] = self._assess_vital_sign(
                    vitals.systolic_bp_mmhg, 'systolic_bp_mmhg', age_group
                )

            if vitals.diastolic_bp_mmhg is not None:
                statuses['diastolic_bp'] = self._assess_vital_sign(
                    vitals.diastolic_bp_mmhg, 'diastolic_bp_mmhg', age_group
                )

            if vitals.spo2_percent is not None:
                statuses['spo2'] = self._assess_vital_sign(
                    vitals.spo2_percent, 'spo2_percent', 'all'
                )

            if vitals.gcs_score is not None:
                statuses['gcs'] = self._assess_vital_sign(
                    vitals.gcs_score, 'gcs_score', 'all'
                )

            # Detect red flags
            red_flags = self._detect_red_flags(vitals, statuses)

            # Calculate SIRS criteria
            sirs_met, sirs_positive = self._calculate_sirs_criteria(vitals)

            # Calculate NEWS score
            news_score = self._calculate_news_score(vitals)

            # Determine overall severity
            severity = "normal"
            if any(status == VitalSignStatus.CRITICAL for status in statuses.values()):
                severity = "critical"
            elif any(status == VitalSignStatus.ABNORMAL for status in statuses.values()):
                severity = "abnormal"
            elif any(status == VitalSignStatus.BORDERLINE for status in statuses.values()):
                severity = "borderline"

            # Generate recommendations
            recommendations = []

            if red_flags:
                recommendations.append(
                    f"⚠️ {len(red_flags)} critical alert(s) - immediate attention required"
                )

            if sirs_positive:
                recommendations.append(
                    f"⚠️ SIRS criteria met ({sirs_met}/4) - assess for sepsis"
                )

            if news_score >= 7:
                recommendations.append(
                    f"⚠️ High NEWS score ({news_score}) - urgent medical review required"
                )
            elif news_score >= 5:
                recommendations.append(
                    f"⚠️ Medium NEWS score ({news_score}) - increased monitoring frequency"
                )

            if not vitals.is_complete():
                recommendations.append(
                    "ℹ️ Incomplete vital signs - obtain missing measurements"
                )

            logger.info(
                f"Analysis complete: {severity} severity, "
                f"{len(red_flags)} red flags, NEWS={news_score}"
            )

            return VitalSignsAnalysis(
                vitals=vitals,
                statuses=statuses,
                red_flags=red_flags,
                sirs_criteria_met=sirs_met,
                sirs_positive=sirs_positive,
                news_score=news_score,
                severity=severity,
                recommendations=recommendations
            )

        except Exception as e:
            logger.error(f"Error in vital signs analysis: {e}", exc_info=True)
            raise

    def get_statistics(self) -> Dict[str, Any]:
        """Get analyzer statistics"""
        return {
            'total_analyses': self.total_analyses,
            'critical_alerts': self.critical_alerts
        }



__all__ = [
    'VitalSigns',
    'VitalSignsAnalysis',
    'VitalSignsAnalyzer',
    'RedFlag',
    'AlertLevel',
    'VitalSignStatus',
]
